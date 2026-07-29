import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from detector import DeviceInfo
from validator import validate_device, run_read_test, run_write_test, ValidationResult


def _make_device(is_connected=True, device_type="usb_storage"):
    return DeviceInfo(
        is_connected=is_connected,
        device_name="Test Device",
        device_type=device_type,
    )


def test_validate_device_returns_validationresult():
    result = validate_device(_make_device())
    assert isinstance(result, ValidationResult)


def test_not_connected_sets_detect_fail_and_skips_tests():
    result = validate_device(_make_device(is_connected=False))
    assert result.detect_status == "FAIL"
    assert result.read_status == "SKIPPED"
    assert result.write_status == "SKIPPED"
    assert result.fail_reason != ""


def test_portable_device_skips_read_write():
    result = validate_device(_make_device(device_type="portable_device"))
    assert result.detect_status == "PASS"
    assert result.read_status == "SKIPPED"
    assert result.write_status == "SKIPPED"
    assert result.fail_reason != ""
    assert result.manual_check_required is False


def test_usb_storage_runs_real_tests():
    result = validate_device(_make_device(device_type="usb_storage"))
    assert result.detect_status == "PASS"
    assert result.read_status in ("PASS", "FAIL")
    assert result.write_status in ("PASS", "FAIL")


def test_simulated_device_runs_tests_like_storage():
    result = validate_device(_make_device(device_type="simulated"))
    assert result.detect_status == "PASS"
    assert result.read_status in ("PASS", "FAIL")
    assert result.write_status in ("PASS", "FAIL")


def test_run_read_test_status_is_valid():
    for _ in range(20):
        status = run_read_test()
        assert status in ("PASS", "FAIL")


def test_run_write_test_status_is_valid():
    for _ in range(20):
        status, _ = run_write_test()
        assert status in ("PASS", "FAIL")


def test_write_fail_always_has_reason():
    for _ in range(20):
        status, fail_reason = run_write_test()
        if status == "FAIL":
            assert fail_reason != ""
        else:
            assert fail_reason == ""


def test_manual_check_flag_matches_write_status_for_storage():
    for _ in range(20):
        result = validate_device(_make_device(device_type="usb_storage"))
        if result.write_status == "FAIL":
            assert result.manual_check_required is True
            assert result.fail_reason != ""
        else:
            assert result.manual_check_required is False
            assert result.manual_check_note == "NO"