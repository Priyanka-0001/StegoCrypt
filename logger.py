# logger.py

import sqlite3
from datetime import datetime
import csv
import os

# Base directory of project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database file path
DB_FILE = os.path.join(BASE_DIR, "database.db")


def init_db():
    """Initialize SQLite database with required tables."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Table for general logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                message TEXT
            )
        ''')

        # Table for VirusTotal scan results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS virustotal_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                timestamp TEXT,
                harmless INTEGER,
                malicious INTEGER,
                suspicious INTEGER,
                undetected INTEGER
            )
        ''')


def log_event(message):
    """Log a user or system action with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (timestamp, message) VALUES (?, ?)",
            (timestamp, message)
        )

    # Print also for terminal debugging
    print(f"[{timestamp}] {message}")


def log_virustotal_result(filename, harmless, malicious, suspicious, undetected):
    """Log VirusTotal scan result for the given file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO virustotal_results 
            (filename, timestamp, harmless, malicious, suspicious, undetected)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, timestamp, harmless, malicious, suspicious, undetected))

    print(f"[{timestamp}] VirusTotal results logged for {filename}")


def fetch_logs():
    """Return all system logs from the DB."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Latest logs first
        cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
        return cursor.fetchall()


def fetch_virustotal_logs():
    """Return all VirusTotal logs from the DB."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM virustotal_results ORDER BY timestamp DESC")
        return cursor.fetchall()


def export_logs_to_csv(filename="logs_output.csv"):
    """Export both activity and VirusTotal logs to CSV file."""

    logs = fetch_logs()
    vt_logs = fetch_virustotal_logs()

    # Write logs into CSV
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Activity logs
        writer.writerow(["Log ID", "Timestamp", "Message"])
        for log in logs:
            writer.writerow(log)

        writer.writerow([])  # separator

        # VirusTotal logs
        writer.writerow(["VirusTotal Results"])
        writer.writerow([
            "ID", "Filename", "Timestamp",
            "Harmless", "Malicious", "Suspicious", "Undetected"
        ])

        for vt in vt_logs:
            writer.writerow(vt)

    print(f"[+] Logs saved to {filename}")