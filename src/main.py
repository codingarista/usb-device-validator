import time
from datetime import datetime

from detector import detect_usb_device
from validator import validate_device
from reporter import generate_html_report, save_test_log
from db import save_test_record


def simulate_progress():
    print("=== USB Auto Checker ===")
    print("Start USB test...\n")

    for i in range(101):
        print(f"\rTesting progress: {i:3d}%", end="")
        time.sleep(0.03)

    print("\n")


def usb_test():
    test_time = datetime.now()

    device = detect_usb_device()
    result = validate_device(device)

    return {
        "device": device.device_name,
        "connector_type": device.connector_type,
        "device_type": device.device_type,
        "first_test_date": test_time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_test_date": test_time.strftime("%Y-%m-%d %H:%M:%S"),
        "retry_count": result.retry_count,
        "detect": result.detect_status,
        "read_test": result.read_status,
        "write_test": result.write_status,
        "fail_reason": result.fail_reason,
        "manual_check": result.manual_check_note,
    }


if __name__ == "__main__":
    simulate_progress()

    result = usb_test()

    print("Test Result:")
    print(result)

    html_path = generate_html_report(result)
    print("HTML report generated:")
    print(html_path)

    log_path = save_test_log(result)
    print("Test log saved:")
    print(log_path)

    try:
        record_id = save_test_record(result)
        print(f"Test record saved to database (id={record_id})")
    except Exception as e:
        print(f"WARNING: failed to save test record to database: {e}")

    print("\nUSB test completed.")