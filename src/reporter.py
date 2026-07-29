"""Test report generation and persistence."""

import json
import os
from datetime import datetime


def generate_html_report(result: dict, output_dir: str = None) -> str:
    """Generate HTML report from test result. Returns the output file path."""
    report = f"""
<!DOCTYPE html>
<html>
<head>
<title>USB Auto Test Report</title>
<style>
table {{ border-collapse: collapse; width: 80%; }}
td, th {{ border:1px solid black; padding:8px; }}
</style>
</head>
<body>
<h1>USB Auto Test Report</h1>

<h2>Test Information</h2>
<table>
<tr><th>Item</th><th>Result</th></tr>
<tr><td>Device</td><td>{result["device"]}</td></tr>
<tr><td>Connector Type</td><td>{result["connector_type"]}</td></tr>
<tr><td>First Test Date</td><td>{result["first_test_date"]}</td></tr>
<tr><td>Last Test Date</td><td>{result["last_test_date"]}</td></tr>
<tr><td>Retry Count</td><td>{result["retry_count"]}</td></tr>
</table>

<h2>Test Result</h2>
<table>
<tr><th>Test Item</th><th>Status</th><th>Reason</th></tr>
<tr><td>USB Detection</td><td>{result["detect"]}</td><td>-</td></tr>
<tr><td>Read Test</td><td>{result["read_test"]}</td><td>-</td></tr>
<tr><td>Write Test</td><td>{result["write_test"]}</td><td>{result["fail_reason"]}</td></tr>
</table>

<h2>Manual Inspection</h2>
<p>{result["manual_check"]}</p>

</body>
</html>
"""

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "usb_test_report.html")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report)

    return output_path


def save_test_log(result: dict, log_dir: str = None) -> str:
    """Save test result as a timestamped JSON log. Returns the log file path."""
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"test_{timestamp}.json")

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    return log_path