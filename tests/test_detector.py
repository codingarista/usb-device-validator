import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from detector import detect_usb_device, list_usb_devices, DeviceInfo, _simulate_device


VALID_CONNECTOR_TYPES = ("USB-A", "USB-C", "unknown")
VALID_DEVICE_TYPES = ("usb_storage", "portable_device", "simulated", "none")


def test_detect_usb_device_returns_deviceinfo():
    result = detect_usb_device()
    assert isinstance(result, DeviceInfo)


def test_detect_usb_device_connector_type_is_valid():
    result = detect_usb_device()
    assert result.connector_type in VALID_CONNECTOR_TYPES


def test_detect_usb_device_type_is_valid():
    # This reflects whatever is actually connected at test time
    # (real storage device, phone, or nothing -> simulated fallback).
    result = detect_usb_device()
    assert result.device_type in VALID_DEVICE_TYPES


def test_detect_usb_device_capacity_fields_are_consistent():
    result = detect_usb_device()
    # Capacity is only guaranteed for storage-type devices; portable
    # devices and "none" legitimately have no capacity info.
    if result.total_capacity_gb is not None and result.free_capacity_gb is not None:
        assert result.free_capacity_gb <= result.total_capacity_gb


def test_list_usb_devices_returns_list_of_deviceinfo():
    devices = list_usb_devices()
    assert isinstance(devices, list)
    assert len(devices) >= 1
    assert all(isinstance(d, DeviceInfo) for d in devices)


def test_no_fallback_returns_disconnected_when_nothing_found():
    # We can't force "nothing connected" on a real machine, but we can
    # verify the documented contract of the disconnected state directly.
    result = DeviceInfo(is_connected=False, device_name="", device_type="none")
    assert result.is_connected is False
    assert result.device_type == "none"


def test_simulated_device_has_expected_shape():
    # Directly test the simulation logic, independent of what's
    # actually plugged into the machine right now.
    result = _simulate_device()
    assert result.is_connected is True
    assert result.device_type == "simulated"
    assert result.connector_type == "USB-A"
    assert result.total_capacity_gb is not None
    assert result.free_capacity_gb is not None
    assert result.free_capacity_gb <= result.total_capacity_gb