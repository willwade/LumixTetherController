#!/usr/bin/env python3
"""
LUMIX Remote Control SDK - Python ctypes wrapper

Direct API calls to LUMIX cameras using the official Panasonic SDK.
No coordinate clicking needed - direct programmatic control!

References:
- LumixRemoteControlLibraryBeta1.00/Library/LMX_func_api.h
- LumixRemoteControlLibraryBeta1.00/TetherSDKSample/GetSetParameters01/main.cpp
"""

import ctypes
import sys
from pathlib import Path
from typing import Optional

# Path to the Lumix SDK library
def get_dll_path() -> Path:
    """
    Get the path to Lmxptpif.dll.

    For frozen apps (PyInstaller), looks next to the executable.
    For development, looks in the project root (DLL from LUMIX SDK).
    """
    # Check if running as frozen app (PyInstaller, etc.)
    if getattr(sys, 'frozen', False):
        # Frozen app - DLL should be next to executable
        return Path(sys.executable).parent / "Lmxptpif.dll"

    # Development mode - look in project root
    return Path(__file__).parent / "Lmxptpif.dll"


DLL_PATH = get_dll_path()

# Constants from LMX_lib_type.h
LMX_BOOL_TRUE = 1
LMX_BOOL_FALSE = 0

# ISO constants from LMX_lib_def.h
LMX_DEF_ISO_AUTO = 0xFFFFFFFF
LMX_DEF_ISO_I_ISO = 0xFFFFFFFE
LMX_DEF_ISO_UNKNOWN = 0xFFFFFFFD

# Aperture constants from LMX_lib_def.h
LMX_DEF_F_AUTO = 0xFFFF
LMX_DEF_F_UNKNOWN = 0xFFFE

# White balance constants from LMX_lib_def.h
LMX_DEF_WB_AUTO = 0x0002
LMX_DEF_WB_DAYLIGHT = 0x0004
LMX_DEF_WB_CLOUD = 0x8008
LMX_DEF_WB_TENGSTEN = 0x0006  # Incandescent
LMX_DEF_WB_WHITESET = 0x8009
LMX_DEF_WB_FLASH = 0x0007
LMX_DEF_WB_FLUORESCENT = 0x0005
LMX_DEF_WB_BLACK_WHITE = 0x800A
LMX_DEF_WB_SHADE = 0x800F
LMX_DEF_WB_KEEP = 0x800B  # WB setting 1
LMX_DEF_WB_KEEP2 = 0x800C  # WB setting 2
LMX_DEF_WB_KEEP3 = 0x800D  # WB setting 3
LMX_DEF_WB_KEEP4 = 0x800E  # WB setting 4

# AF/AE Control constants
LMX_DEF_LIB_TAG_REC_CTRL_AFAE_AF_ONESHOT = 0x03000024

# Shutter release constants
LMX_DEF_LIB_TAG_REC_CTRL_RELEASE_ONESHOT = 0x03000021


# Define ctypes structures
class LMXDevInfo(ctypes.Structure):
    """Device information structure."""
    _fields_ = [
        ("dev_Index", ctypes.c_uint32),
        ("dev_MakerName", ctypes.c_wchar * 256),
        ("dev_MakerName_Length", ctypes.c_uint32),
        ("dev_ModelName", ctypes.c_wchar * 256),
        ("dev_ModelName_Length", ctypes.c_uint32),
    ]


class LMXConnectDeviceInfo(ctypes.Structure):
    """PnP device information structure."""
    _fields_ = [
        ("find_PnpDevice_Count", ctypes.c_uint32),
        ("find_PnpDevice_IDs", ctypes.c_wchar_p * 512),
        ("find_PnpDevice_Info", LMXDevInfo * 512),
    ]


class LMXStructRecCtrl(ctypes.Structure):
    """Recording control structure."""
    _fields_ = [
        ("CtrlID", ctypes.c_uint32),
        ("ParamData", ctypes.c_uint32 * 512),
    ]


# Global DLL handle
lmx_dll: Optional[ctypes.CDLL] = None


def load_dll() -> Optional[ctypes.CDLL]:
    """Load the Lmxptpif.dll library."""
    global lmx_dll

    if lmx_dll is not None:
        return lmx_dll

    if not DLL_PATH.exists():
        print(f"Error: DLL not found at {DLL_PATH}")
        return None

    try:
        lmx_dll = ctypes.CDLL(str(DLL_PATH))
        print(f"Loaded Lmxptpif.dll from {DLL_PATH}")
        return lmx_dll
    except Exception as e:
        print(f"Error loading Lmxptpif.dll: {e}")
        return None


class LumixSDK:
    """
    Python wrapper for the LUMIX Remote Control Library SDK.

    Provides direct API access to camera controls without coordinate clicking.
    """

    def __init__(self):
        """Initialize the Lumix SDK."""
        dll = load_dll()
        if dll is None:
            raise RuntimeError("Failed to load Lmxptpif.dll")

        # Initialize the SDK
        try:
            init_func = dll.LMX_func_api_Init
            init_func.argtypes = []
            init_func.restype = None
            init_func()
            print("Lumix SDK initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Lumix SDK: {e}")

        self.dll = dll
        self.device_index: Optional[int] = None
        self.is_open = False

    def get_devices(self) -> list[dict]:
        """
        Get list of available LUMIX devices.

        Returns:
            List of device info dictionaries
        """
        try:
            get_device_func = self.dll.LMX_func_api_Get_PnPDeviceInfo
            get_device_func.argtypes = [
                ctypes.POINTER(LMXConnectDeviceInfo),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            get_device_func.restype = ctypes.c_uint8

            dev_info = LMXConnectDeviceInfo()
            ret_error = ctypes.c_uint32()

            result = get_device_func(dev_info, ctypes.byref(ret_error))

            if result == LMX_BOOL_FALSE:
                print(f"Get devices failed with error: {hex(ret_error.value)}")
                return []

            devices = []
            count = dev_info.find_PnpDevice_Count
            print(f"Found {count} device(s)")

            for i in range(count):
                info = dev_info.find_PnpDevice_Info[i]
                devices.append({
                    "index": info.dev_Index,
                    "maker": info.dev_MakerName,
                    "model": info.dev_ModelName,
                })

            return devices

        except Exception as e:
            print(f"Error getting devices: {e}")
            return []

    def select_device(self, index: int = 0) -> bool:
        """
        Select a LUMIX device by index.

        Args:
            index: Device index (0-based)

        Returns:
            True if successful, False otherwise
        """
        try:
            select_func = self.dll.LMX_func_api_Select_PnPDevice
            select_func.argtypes = [
                ctypes.c_uint32,
                ctypes.POINTER(LMXConnectDeviceInfo),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            select_func.restype = ctypes.c_uint8

            # First get device info
            dev_info = LMXConnectDeviceInfo()
            ret_error = ctypes.c_uint32()

            get_device_func = self.dll.LMX_func_api_Get_PnPDeviceInfo
            get_device_func.argtypes = [
                ctypes.POINTER(LMXConnectDeviceInfo),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            get_device_func.restype = ctypes.c_uint8

            if get_device_func(dev_info, ctypes.byref(ret_error)) == LMX_BOOL_FALSE:
                print("Failed to get device info for selection")
                return False

            # Now select the device
            result = select_func(index, dev_info, ctypes.byref(ret_error))

            if result == LMX_BOOL_FALSE:
                print(f"Select device failed with error: {hex(ret_error.value)}")
                return False

            self.device_index = index
            print(f"Selected device {index}")
            return True

        except Exception as e:
            print(f"Error selecting device: {e}")
            return False

    def open_session(self) -> bool:
        """
        Open a session with the selected device.

        Returns:
            True if successful, False otherwise
        """
        if self.device_index is None:
            print("No device selected")
            return False

        try:
            open_func = self.dll.LMX_func_api_Open_Session
            open_func.argtypes = [
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            open_func.restype = ctypes.c_uint8

            device_connect_ver = ctypes.c_uint32()
            ret_error = ctypes.c_uint32()

            # Use connection version 0x00010001 as per sample
            result = open_func(0x00010001, ctypes.byref(device_connect_ver), ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Open session failed with error: {hex(ret_error.value)}")
                return False

            self.is_open = True
            print(f"Session opened (version: {hex(device_connect_ver.value)})")
            return True

        except Exception as e:
            print(f"Error opening session: {e}")
            return False

    def close_session(self) -> bool:
        """Close the device session."""
        if not self.is_open:
            return True

        try:
            close_func = self.dll.LMX_func_api_Close_Session
            close_func.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
            close_func.restype = ctypes.c_uint8

            ret_error = ctypes.c_uint32()
            result = close_func(ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Close session failed with error: {hex(ret_error.value)}")
                return False

            self.is_open = False
            print("Session closed")
            return True

        except Exception as e:
            print(f"Error closing session: {e}")
            return False

    def close_device(self) -> bool:
        """Close the device connection."""
        try:
            close_func = self.dll.LMX_func_api_Close_Device
            close_func.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
            close_func.restype = ctypes.c_uint8

            ret_error = ctypes.c_uint32()
            result = close_func(ctypes.byref(ret_error))

            if result == LMX_BOOL_FALSE:
                print(f"Close device failed with error: {hex(ret_error.value)}")
                return False

            print("Device closed")
            return True

        except Exception as e:
            print(f"Error closing device: {e}")
            return False

    # ISO Functions

    def set_iso(self, iso_value: int) -> bool:
        """
        Set ISO directly via SDK.

        Args:
            iso_value: ISO value (e.g., 100, 200, 400, 800, 1600, 3200)
                      Or use LMX_DEF_ISO_AUTO for auto

        Returns:
            True if successful, False otherwise
        """
        if not self.is_open:
            print("Session not open")
            return False

        try:
            set_func = self.dll.LMX_func_api_ISO_Set_Param
            set_func.argtypes = [
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
            ]
            set_func.restype = ctypes.c_uint8

            ret_error = ctypes.c_uint32()
            result = set_func(iso_value, ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Set ISO failed with error: {hex(ret_error.value)}")
                return False

            print(f"ISO set to {iso_value}")
            return True

        except Exception as e:
            print(f"Error setting ISO: {e}")
            return False

    def get_iso(self) -> Optional[int]:
        """
        Get current ISO value.

        Returns:
            Current ISO value or None
        """
        if not self.is_open:
            return None

        try:
            get_func = self.dll.LMX_func_api_ISO_Get_Param
            get_func.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            get_func.restype = ctypes.c_uint8

            param = ctypes.c_uint32()
            ret_error = ctypes.c_uint32()
            result = get_func(ctypes.byref(param), ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Get ISO failed with error: {hex(ret_error.value)}")
                return None

            return param.value

        except Exception as e:
            print(f"Error getting ISO: {e}")
            return None

    # Aperture Functions

    def set_aperture(self, aperture_value: int) -> bool:
        """
        Set aperture directly via SDK.

        Args:
            aperture_value: Aperture value (SDK-specific encoding)
                           Use int(f_number * 10) e.g., f/2.8 = 28, f/4.0 = 40
                           Or use LMX_DEF_F_AUTO for auto

        Returns:
            True if successful, False otherwise
        """
        if not self.is_open:
            print("Session not open")
            return False

        try:
            set_func = self.dll.LMX_func_api_Aperture_Set_Param
            set_func.argtypes = [
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
            ]
            set_func.restype = ctypes.c_uint8

            ret_error = ctypes.c_uint32()
            result = set_func(aperture_value, ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Set aperture failed with error: {hex(ret_error.value)}")
                return False

            print(f"Aperture set to {aperture_value}")
            return True

        except Exception as e:
            print(f"Error setting aperture: {e}")
            return False

    def set_aperture_f_stop(self, f_number: float) -> bool:
        """
        Set aperture using f-stop number (e.g., 2.8 for f/2.8).

        Args:
            f_number: f-stop number (e.g., 2.8, 4.0, 5.6)

        Returns:
            True if successful, False otherwise
        """
        # Convert f/2.8 to SDK value (28)
        sdk_value = int(f_number * 10)
        return self.set_aperture(sdk_value)

    def get_aperture(self) -> Optional[int]:
        """Get current aperture value (SDK encoding)."""
        if not self.is_open:
            return None

        try:
            get_func = self.dll.LMX_func_api_Aperture_Get_Param
            get_func.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            get_func.restype = ctypes.c_uint8

            param = ctypes.c_uint32()
            ret_error = ctypes.c_uint32()
            result = get_func(ctypes.byref(param), ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Get aperture failed with error: {hex(ret_error.value)}")
                return None

            return param.value

        except Exception as e:
            print(f"Error getting aperture: {e}")
            return None

    # White Balance Functions

    def set_white_balance(self, wb_value: int) -> bool:
        """
        Set white balance directly via SDK.

        Args:
            wb_value: White balance SDK value
                      Use constants like LMX_DEF_WB_AUTO, LMX_DEF_WB_DAYLIGHT, etc.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_open:
            print("Session not open")
            return False

        try:
            set_func = self.dll.LMX_func_api_WB_Set_Param
            set_func.argtypes = [
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
            ]
            set_func.restype = ctypes.c_uint8

            ret_error = ctypes.c_uint32()
            result = set_func(wb_value, ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Set WB failed with error: {hex(ret_error.value)}")
                return False

            print(f"White balance set to {wb_value:#x}")
            return True

        except Exception as e:
            print(f"Error setting WB: {e}")
            return False

    def get_white_balance(self) -> Optional[int]:
        """Get current white balance value."""
        if not self.is_open:
            return None

        try:
            get_func = self.dll.LMX_func_api_WB_Get_Param
            get_func.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            get_func.restype = ctypes.c_uint8

            param = ctypes.c_uint32()
            ret_error = ctypes.c_uint32()
            result = get_func(ctypes.byref(param), ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Get WB failed with error: {hex(ret_error.value)}")
                return None

            return param.value

        except Exception as e:
            print(f"Error getting WB: {e}")
            return None

    # Shutter Control

    def trigger_shutter(self) -> bool:
        """
        Trigger shutter using SDK (if available).

        Returns:
            True if successful, False otherwise
        """
        if not self.is_open:
            print("Session not open")
            return False

        try:
            rec_ctrl = LMXStructRecCtrl()
            rec_ctrl.CtrlID = LMX_DEF_LIB_TAG_REC_CTRL_RELEASE_ONESHOT
            # Initialize ParamData array
            for i in range(512):
                rec_ctrl.ParamData[i] = 0
            rec_ctrl.ParamData[0] = 1  # One shot

            shutter_func = self.dll.LMX_func_api_Rec_Ctrl_Release
            shutter_func.argtypes = [
                ctypes.POINTER(LMXStructRecCtrl),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            shutter_func.restype = ctypes.c_uint8

            ret_error = ctypes.c_uint32()
            result = shutter_func(rec_ctrl, ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Shutter failed with error: {hex(ret_error.value)}")
                return False

            print("Shutter triggered")
            return True

        except Exception as e:
            print(f"Error triggering shutter: {e}")
            return False

    def autofocus(self) -> bool:
        """
        Trigger one-shot autofocus using SDK.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_open:
            print("Session not open")
            return False

        try:
            rec_ctrl = LMXStructRecCtrl()
            rec_ctrl.CtrlID = LMX_DEF_LIB_TAG_REC_CTRL_AFAE_AF_ONESHOT
            # Initialize ParamData array
            for i in range(512):
                rec_ctrl.ParamData[i] = 0
            rec_ctrl.ParamData[0] = 1  # One shot AF

            af_func = self.dll.LMX_func_api_Rec_Ctrl_AF_AE
            af_func.argtypes = [
                ctypes.POINTER(LMXStructRecCtrl),
                ctypes.POINTER(ctypes.c_uint32),
            ]
            af_func.restype = ctypes.c_uint8

            ret_error = ctypes.c_uint32()
            result = af_func(rec_ctrl, ctypes.byref(ret_error))

            # SDK quirk: result=0 with error=0x0 means success
            if result == 0 and ret_error.value != 0:
                print(f"Autofocus failed with error: {hex(ret_error.value)}")
                return False

            print("Autofocus triggered")
            return True

        except Exception as e:
            print(f"Error triggering autofocus: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        if self.is_open:
            self.close_session()
        self.close_device()


def create_sdk() -> Optional[LumixSDK]:
    """
    Create and initialize a LumixSDK instance.

    Returns:
        LumixSDK instance if successful, None otherwise
    """
    try:
        sdk = LumixSDK()
        return sdk
    except Exception as e:
        print(f"Could not create LumixSDK: {e}")
        return None


if __name__ == "__main__":
    print("Testing LUMIX SDK...")
    sdk = create_sdk()

    if sdk:
        print("\nGetting devices...")
        devices = sdk.get_devices()

        if devices:
            print(f"\nFound {len(devices)} device(s):")
            for dev in devices:
                print(f"  - {dev['model']}")

            # Try to connect
            print("\nAttempting to connect...")
            if sdk.select_device(0):
                if sdk.open_session():
                    print("Session opened successfully!")

                    # Try to get current values
                    current_iso = sdk.get_iso()
                    print(f"Current ISO: {current_iso}")

                    current_aperture = sdk.get_aperture()
                    print(f"Current Aperture: {current_aperture}")

                    current_wb = sdk.get_white_balance()
                    print(f"Current WB: {current_wb:#x}")

                    # Test autofocus
                    if sdk.autofocus():
                        print("Autofocus successful")

                    # Test setting ISO to 800
                    if sdk.set_iso(800):
                        print("Set ISO to 800")

                    # Test setting aperture to f/4.0
                    if sdk.set_aperture_f_stop(4.0):
                        print("Set aperture to f/4.0")

                    # Test setting white balance to daylight
                    if sdk.set_white_balance(LMX_DEF_WB_DAYLIGHT):
                        print("Set white balance to Daylight")

                    # Test shutter
                    print("Triggering shutter in 3 seconds...")
                    import time
                    time.sleep(3)
                    if sdk.trigger_shutter():
                        print("Shutter triggered successfully!")

                    sdk.close_session()
                else:
                    print("Failed to open session")
            else:
                print("Failed to select device")
        else:
            print("No devices found")

        sdk.close_device()
    else:
        print("Failed to initialize SDK")
