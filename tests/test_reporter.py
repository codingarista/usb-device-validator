import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reporter import generate_html_report, save_test_log


SAMPLE_RESULT = {
    "device": "Test USB",
    "connector_type": "USB-A",
    "first_test_date": "2026-01-01 00:00:00",
    "last_test_date": "2026-01-01 00:00:00",
    "retry_count": 1,
    "detect": "PASS",
    "read_test": "PASS",
    "write_test": "FAIL",
    "fail_reason": "Write speed below threshold",
    "manual_check": "YES - Please check USB device health manually",
}


def test_generate_html_report_creates_file(tmp_path):
    output_path = generate_html_report(SAMPLE_RESULT, output_dir=str(tmp_path))
    assert os.path.isfile(output_path)


def test_generate_html_report_contains_key_fields(tmp_path):
    output_path = generate_html_report(SAMPLE_RESULT, output_dir=str(tmp_path))
    with open(output_path, encoding="utf-8") as f:
        content = f.read()

    assert "Test USB" in content
    assert "USB-A" in content
    assert "Write speed below threshold" in content


def test_save_test_log_creates_json_file(tmp_path):
    log_path = save_test_log(SAMPLE_RESULT, log_dir=str(tmp_path))
    assert os.path.isfile(log_path)
    assert log_path.endswith(".json")


def test_save_test_log_content_matches_input(tmp_path):
    log_path = save_test_log(SAMPLE_RESULT, log_dir=str(tmp_path))
    with open(log_path, encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded == SAMPLE_RESULT


def test_save_test_log_filenames_are_unique(tmp_path):
    import time

    path1 = save_test_log(SAMPLE_RESULT, log_dir=str(tmp_path))
    time.sleep(1.1)  # ensure timestamp granularity differs
    path2 = save_test_log(SAMPLE_RESULT, log_dir=str(tmp_path))
    assert path1 != path2