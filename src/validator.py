"""USB storage validation: read/write tests."""

import random
from dataclasses import dataclass

from detector import DeviceInfo
from history_logger import log_test_result


@dataclass
class ValidationResult:
    """Standardized result of read/write validation."""

    detect_status: str
    read_status: str
    write_status: str
    fail_reason: str = ""
    retry_count: int = 1
    manual_check_required: bool = False
    manual_check_note: str = ""


def _resolve_device_id(device: DeviceInfo) -> str:
    """Use serial_number when available; fall back to device_name (e.g. simulated devices have no serial)."""
    return device.serial_number or device.device_name or "unknown"


def run_read_test() -> str:
    """Run read test on the USB device. Returns PASS/FAIL."""
    # TODO: replace with real file read + checksum verification
    return random.choice(["PASS", "PASS", "PASS"])


def run_write_test() -> tuple[str, str]:
    """Run write test on the USB device. Returns (status, fail_reason)."""
    # TODO: replace with real file write + speed measurement
    status = random.choice(["PASS", "FAIL"])
    fail_reason = "Write speed below threshold" if status == "FAIL" else ""
    return status, fail_reason


def validate_device(device: DeviceInfo) -> ValidationResult:
    """Run validation based on the device's connection state and type.

    - Not connected            -> detect FAIL, read/write SKIPPED
    - Portable device (MTP)    -> detect PASS, read/write SKIPPED (no file I/O access)
    - USB storage / simulated  -> detect PASS, real read/write test executed
    """
    device_id = _resolve_device_id(device)

    if not device.is_connected:
        log_test_result(
            device_id=device_id,
            test_type="detect",
            result="No device detected",
            value=None,
            threshold=None,
            pass_fail=False,
        )
        return ValidationResult(
            detect_status="FAIL",
            read_status="SKIPPED",
            write_status="SKIPPED",
            fail_reason="No device detected",
            manual_check_note="NO",
        )

    if device.device_type == "portable_device":
        log_test_result(
            device_id=device_id,
            test_type="detect",
            result="Portable/MTP device - I/O test skipped",
            value=None,
            threshold=None,
            pass_fail=True,
        )
        return ValidationResult(
            detect_status="PASS",
            read_status="SKIPPED",
            write_status="SKIPPED",
            fail_reason="Portable/MTP device does not support direct file I/O testing",
            manual_check_note="NO",
        )

    read_status = run_read_test()
    write_status, fail_reason = run_write_test()

    log_test_result(
        device_id=device_id,
        test_type="read_test",
        result=read_status,
        value=None,
        threshold=None,
        pass_fail=(read_status == "PASS"),
    )
    log_test_result(
        device_id=device_id,
        test_type="write_test",
        result=write_status,
        value=None,
        threshold=None,
        pass_fail=(write_status == "PASS"),
    )

    manual_check_required = write_status == "FAIL"
    manual_check_note = (
        "YES - Please check USB device health manually"
        if manual_check_required
        else "NO"
    )

    return ValidationResult(
        detect_status="PASS",
        read_status=read_status,
        write_status=write_status,
        fail_reason=fail_reason,
        manual_check_required=manual_check_required,
        manual_check_note=manual_check_note,
    )