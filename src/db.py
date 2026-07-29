"""Database persistence layer for test records (MySQL)."""

import os

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error as MySQLError

load_dotenv()

DB_HOST = os.environ.get("USB_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("USB_DB_PORT", "3306"))
DB_USER = os.environ.get("USB_DB_USER", "root")
DB_PASSWORD = os.environ.get("USB_DB_PASSWORD")
DB_NAME = os.environ.get("USB_DB_NAME", "usb_validator")


def _get_connection():
    """Create a new MySQL connection using settings loaded from .env."""
    if not DB_PASSWORD:
        raise RuntimeError(
            "USB_DB_PASSWORD is not set. Copy .env.example to .env and fill in your credentials."
        )

    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def save_test_record(result: dict) -> int:
    """Insert a test result into the test_records table.

    Returns the inserted row's auto-increment id.
    Raises mysql.connector.Error on connection/query failure.
    """
    query = """
        INSERT INTO test_records (
            device_name, connector_type, device_type,
            first_test_date, last_test_date, retry_count,
            detect_status, read_status, write_status,
            fail_reason, manual_check
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        result["device"],
        result["connector_type"],
        result["device_type"],
        result["first_test_date"],
        result["last_test_date"],
        result["retry_count"],
        result["detect"],
        result["read_test"],
        result["write_test"],
        result["fail_reason"],
        result["manual_check"],
    )

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def fetch_recent_records(limit: int = 10) -> list[dict]:
    """Fetch the most recent test records, newest first."""
    query = """
        SELECT id, device_name, connector_type, device_type,
               first_test_date, last_test_date, retry_count,
               detect_status, read_status, write_status,
               fail_reason, manual_check, created_at
        FROM test_records
        ORDER BY created_at DESC
        LIMIT %s
    """

    conn = _get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    finally:
        conn.close()


def test_connection() -> bool:
    """Return True if a connection to the database can be established."""
    try:
        conn = _get_connection()
        conn.close()
        return True
    except (MySQLError, RuntimeError):
        return False