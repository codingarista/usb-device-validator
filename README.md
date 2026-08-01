# USB Device Validator

A modular USB hardware validation and test automation tool, refactored from a single-file script into a layered, testable architecture. Built to demonstrate practical hardware validation and test automation engineering practices: device detection, automated read/write validation, structured reporting, and database-backed test history.

## Features

- **Real device detection (Windows)** — queries WMI via PowerShell to detect connected USB mass storage drives and portable devices (e.g. phones in MTP mode), with graceful simulation fallback when no real device is present.
- **Type-aware validation** — automatically adapts test logic to the connected device type (USB storage vs. portable device vs. none), avoiding false PASS/FAIL results for device types that don't support direct file I/O.
- **Automated reporting** — generates an HTML test report and a JSON log for every run.
- **Database persistence** — every test run is automatically written to a MySQL database, so testers no longer need to manually archive HTML reports.
- **Test history & aggregate analysis** — every individual read/write/detect result is also logged to a CSV history file. `analyzer.py` reads that history with `pandas` to compute pass rate and per-test-type failure rate, then generates a bar chart and a standalone aggregate HTML report — the same "which test point fails most often" pattern used in manufacturing quality workflows.
- **Unit tested** — core modules (`detector`, `validator`, `reporter`) are covered by `pytest` unit tests.

## Architecture

```
usb-device-validator/
├── src/
│   ├── main.py        # Entry point; orchestrates the full test pipeline
│   ├── detector.py     # USB device detection (Windows WMI + simulation fallback)
│   ├── validator.py    # Read/write validation logic, type-aware
│   ├── reporter.py     # HTML report + JSON log generation
│   ├── db.py            # MySQL persistence layer
│   ├── history_logger.py # Appends each test result to logs/test_history.csv
│   └── analyzer.py      # Aggregate stats (pandas) + chart + HTML report over test history
├── tests/                # pytest unit tests
├── reports/              # Generated HTML reports (+ a committed sample)
├── logs/                 # Generated JSON test logs, test_history.csv, aggregate_report.html, failure_rate_by_type.png
├── check_usb.py          # Original single-file script (kept for reference)
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # + testing dependencies
├── .env.example           # Template for local database credentials
└── README.md
```

**Data flow:** `detector` produces a standardized `DeviceInfo` → `validator` consumes it and produces a `ValidationResult` → `main` combines both into a result dict → `reporter` and `db` each independently persist that result (HTML/JSON to disk, a row to MySQL). `validator` also logs each individual test outcome via `history_logger` to `logs/test_history.csv`; `analyzer` reads that accumulated history independently, on demand, to produce aggregate statistics and reports.

Each module has a single, isolated responsibility and no module reaches into another's internals — this keeps every layer independently testable and replaceable (e.g. swapping the detection backend for a Linux implementation later requires no changes to `validator`, `reporter`, or `db`).

## Prerequisites

- Python 3.10+
- Windows 10/11 (current detection backend uses PowerShell/WMI — see [Known Limitations](#known-limitations))
- A MySQL 8.x server reachable from your machine (see setup below)

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
# or, to also run the test suite:
pip install -r requirements-dev.txt
```

### 2. Set up MySQL

This project was developed and tested against MySQL running inside **WSL2 (Ubuntu)**, connected to from Windows via WSL2's automatic `localhost` port forwarding. Any reachable MySQL 8.x instance works.

**Using WSL2 + Ubuntu:**

```bash
# Inside WSL2
sudo apt update
sudo apt install -y mysql-server
sudo service mysql start
sudo mysql
```

Inside the MySQL prompt:

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'your_password';
CREATE DATABASE usb_validator;
FLUSH PRIVILEGES;
EXIT;
```

Then create the table:

```sql
CREATE TABLE test_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(255) NOT NULL,
    connector_type VARCHAR(20),
    device_type VARCHAR(30),
    first_test_date DATETIME,
    last_test_date DATETIME,
    retry_count INT DEFAULT 1,
    detect_status VARCHAR(10),
    read_status VARCHAR(10),
    write_status VARCHAR(10),
    fail_reason TEXT,
    manual_check TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

From Windows, verify connectivity:

```bash
python3 -c "from db import test_connection; print(test_connection())"
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your actual database credentials. **`.env` is gitignored and must never be committed.**

## Usage

```bash
cd src
python3 main.py
```

This will:
1. Detect any connected USB device (real device if found, simulated otherwise)
2. Run type-appropriate validation (read/write test, or skip with a clear reason if not applicable)
3. Generate `reports/usb_test_report.html` and a timestamped log in `logs/`
4. Insert the result as a row in the `test_records` MySQL table

If the database is unreachable, the test still completes and local HTML/JSON artifacts are still saved — a warning is printed instead of a hard failure, since database persistence is treated as a convenience layer, not a single point of failure for the test run itself.

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Test History & Aggregate Analysis

Beyond single-run validation, this tool tracks test results over time and generates aggregate quality reports — the same "which test point fails most often" analysis pattern used in manufacturing ICT quality workflows.

**How it works:**

- Every `validate_device()` run logs each individual test result (read/write/detect) to `logs/test_history.csv`.
- `analyzer.py` reads the accumulated history and computes:
  - Overall pass rate across all logged tests
  - Failure rate broken down by test type, with sample size (`n=`) shown alongside each rate to avoid misleading conclusions from small samples
- Results are visualized as a bar chart (`logs/failure_rate_by_type.png`) and compiled into a standalone HTML report (`logs/aggregate_report.html`), kept separate from the per-run report generated by `reporter.py`.

**Usage:**

```bash
# Run validation multiple times to build up history
python run_once.py

# Generate the aggregate analysis report
python src/analyzer.py
```

Example output:

```
總測試筆數: 44
整體PASS率: 68.2%

各測試項目失敗率:
write_test    63.6%
read_test      0.0%
```

## Known Limitations

Documented honestly, since these are hardware/OS boundaries rather than implementation shortcuts:

- **Connector type (USB-A vs. USB-C) detection is best-effort only.** Windows does not expose the physical connector shape via standard WMI classes. Detection falls back to text-matching the device's friendly name (e.g. "Type-C"), and reports `"unknown"` when this isn't derivable — it does not guess.
- **Portable devices (e.g. phones in MTP mode) cannot be read/write tested.** They don't expose a drive letter or filesystem-level access the way USB mass storage does, so validation for this device type is limited to presence detection; read/write status is reported as `SKIPPED` with an explicit reason.
- **Real detection is currently Windows-only** (via PowerShell/WMI). A Linux detection backend (via `/sys/block` and `/sys/class/typec`) was drafted during development but removed before being verified against real hardware in a Linux environment — it is not included in this version to avoid shipping unverified code.
- **Read/write validation is currently simulated** (`random.choice`) for USB mass storage devices. Real file I/O and speed measurement is a planned follow-up.

## Roadmap

- [ ] Real file I/O read/write test implementation (replacing simulation)
- [ ] Linux detection backend, verified against real hardware
- [ ] `tests/test_db.py` with mocked database calls
- [ ] Retry logic for transient read/write failures
- [ ] Persist test history to SQLite/MySQL instead of CSV, once history volume grows

## Author

Arista (@codingArista)

USB Hardware Validation & Test Automation Portfolio Project
A self-developed test automation and data analysis project with AI-assisted development.

Built with:

- Python
- Pandas
- Matplotlib
- MySQL
- pytest
- GitHub
- Git