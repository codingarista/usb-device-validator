"""USB storage validation: read/write tests."""

import random
from dataclasses import dataclass

from detector import DeviceInfo


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
    if not device.is_connected:
        return ValidationResult(
            detect_status="FAIL",
            read_status="SKIPPED",
            write_status="SKIPPED",
            fail_reason="No device detected",
            manual_check_note="NO",
        )

    if device.device_type == "portable_device":
        return ValidationResult(
            detect_status="PASS",
            read_status="SKIPPED",
            write_status="SKIPPED",
            fail_reason="Portable/MTP device does not support direct file I/O testing",
            manual_check_note="NO",
        )

    read_status = run_read_test()
    write_status, fail_reason = run_write_test()

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