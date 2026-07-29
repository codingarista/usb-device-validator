"""USB device detection module."""

import json
import platform
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DeviceInfo:
    """Standardized USB device information."""

    is_connected: bool
    device_name: str
    connector_type: str = "unknown"     # "USB-A" | "USB-C" | "unknown"
    device_type: str = "unknown"        # "usb_storage" | "portable_device" | "simulated" | "none"
    vendor_id: Optional[str] = None
    product_id: Optional[str] = None
    serial_number: Optional[str] = None
    mount_point: Optional[str] = None
    device_path: Optional[str] = None
    total_capacity_gb: Optional[float] = None
    free_capacity_gb: Optional[float] = None
    detected_at: datetime = field(default_factory=datetime.now)


# Joins USB disk drives -> partitions -> logical disks (drive letters) in one query.
_POWERSHELL_STORAGE_QUERY = """
Get-CimInstance Win32_DiskDrive | Where-Object { $_.InterfaceType -eq 'USB' } | ForEach-Object {
    $disk = $_
    $partitions = Get-CimAssociatedInstance -InputObject $disk -ResultClassName Win32_DiskPartition
    foreach ($partition in $partitions) {
        $logicalDisks = Get-CimAssociatedInstance -InputObject $partition -ResultClassName Win32_LogicalDisk
        foreach ($ld in $logicalDisks) {
            [PSCustomObject]@{
                Model = $disk.Model
                PNPDeviceID = $disk.PNPDeviceID
                DriveLetter = $ld.DeviceID
                Size = $ld.Size
                FreeSpace = $ld.FreeSpace
            }
        }
    }
} | ConvertTo-Json
"""

# Portable devices (MTP) - phones, cameras, etc. show up under the WPD PnP class,
# not under Win32_DiskDrive, and have no drive letter or queryable capacity.
_POWERSHELL_PORTABLE_QUERY = """
Get-PnpDevice -Class WPD -Status OK | Select-Object FriendlyName, InstanceId | ConvertTo-Json
"""


def _run_powershell(script: str) -> list[dict]:
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []

    if completed.returncode != 0 or not completed.stdout.strip():
        return []

    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []

    if isinstance(data, dict):
        data = [data]

    return data


def _guess_connector_type(model_name: str) -> str:
    """Best-effort connector type guess based on device name text.

    Windows does not expose USB-A vs USB-C connector shape via standard
    WMI classes. This only catches cases where the vendor's device name
    happens to mention it.
    """
    name = (model_name or "").lower()
    if "type-c" in name or "usb-c" in name or "usb c" in name:
        return "USB-C"
    if "type-a" in name or "usb-a" in name:
        return "USB-A"
    return "unknown"


def _storage_drive_to_device_info(drive: dict) -> DeviceInfo:
    size = drive.get("Size")
    free = drive.get("FreeSpace")

    return DeviceInfo(
        is_connected=True,
        device_name=drive.get("Model") or "Unknown USB Device",
        connector_type=_guess_connector_type(drive.get("Model", "")),
        device_type="usb_storage",
        mount_point=drive.get("DriveLetter"),
        device_path=drive.get("PNPDeviceID"),
        total_capacity_gb=round(int(size) / (1024 ** 3), 2) if size else None,
        free_capacity_gb=round(int(free) / (1024 ** 3), 2) if free else None,
    )


def _portable_device_to_device_info(device: dict) -> DeviceInfo:
    return DeviceInfo(
        is_connected=True,
        device_name=device.get("FriendlyName") or "Unknown Portable Device",
        connector_type="unknown",  # not derivable from WPD info
        device_type="portable_device",
        device_path=device.get("InstanceId"),
        mount_point=None,
        total_capacity_gb=None,
        free_capacity_gb=None,
    )


def _simulate_device() -> DeviceInfo:
    """Fallback simulated device, used when no real device is found."""
    return DeviceInfo(
        is_connected=True,
        device_name="SanDisk USB 3.0",
        connector_type="USB-A",
        device_type="simulated",
        total_capacity_gb=32.0,
        free_capacity_gb=18.5,
    )


def detect_usb_device(fallback_simulation: bool = True) -> DeviceInfo:
    """Detect whether a USB device is currently connected.

    Detection order on Windows:
      1. USB mass storage drives (drive letter, capacity available)
      2. Portable devices / MTP, e.g. phones (no drive letter, no capacity)
      3. Fallback to simulated data if fallback_simulation is True
    """
    if platform.system() == "Windows":
        drives = _run_powershell(_POWERSHELL_STORAGE_QUERY)
        if drives:
            return _storage_drive_to_device_info(drives[0])

        portable_devices = _run_powershell(_POWERSHELL_PORTABLE_QUERY)
        if portable_devices:
            return _portable_device_to_device_info(portable_devices[0])

    if fallback_simulation:
        return _simulate_device()

    return DeviceInfo(is_connected=False, device_name="", device_type="none")


def list_usb_devices() -> list[DeviceInfo]:
    """List all currently detected USB devices (storage + portable)."""
    if platform.system() == "Windows":
        drives = _run_powershell(_POWERSHELL_STORAGE_QUERY)
        devices = [_storage_drive_to_device_info(d) for d in drives]

        portable_devices = _run_powershell(_POWERSHELL_PORTABLE_QUERY)
        devices.extend(_portable_device_to_device_info(d) for d in portable_devices)

        if devices:
            return devices

    return [detect_usb_device()]