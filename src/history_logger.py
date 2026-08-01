"""Test history logging: appends each individual test result to a CSV file
for later aggregate analysis (see analyzer.py)."""

import csv
import os
from datetime import datetime

HISTORY_FILE = "logs/test_history.csv"
FIELDNAMES = ["timestamp", "device_id", "test_type", "result", "value", "threshold", "pass_fail"]


def log_test_result(
    device_id: str,
    test_type: str,
    result: str,
    value,
    threshold,
    pass_fail: bool,
) -> None:
    """Append one test result row to the history CSV.

    device_id:  identifier for the tested device (serial number, or device
                name as fallback for devices without a serial)
    test_type:  e.g. "detect" / "read_test" / "write_test"
    result:     human-readable outcome, e.g. "PASS", "No device detected"
    value:      measured value if applicable (e.g. speed in MB/s), else None
    threshold:  threshold used for the pass/fail decision, else None
    pass_fail:  True/False - stored as bool so pandas can treat it as 0/1
    """
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    file_exists = os.path.isfile(HISTORY_FILE)

    with open(HISTORY_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "device_id": device_id,
            "test_type": test_type,
            "result": result,
            "value": value,
            "threshold": threshold,
            "pass_fail": pass_fail,
        })