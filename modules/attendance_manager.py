"""
attendance_manager.py
=====================
Handles all CSV-based attendance record operations.

PL-2 Concepts: OOP, File Handling (CSV), Custom Exception Handling
"""

import csv
import os
import json
from datetime import datetime, date
from modules.exceptions import DuplicateAttendanceError, StudentNotFoundError


class AttendanceManager:
    """
    Manages reading and writing of attendance records stored in a CSV file.
    Also interfaces with students.json as the student master database.
    """

    CSV_FIELDS = ["date", "student_id", "name", "time", "status"]

    def __init__(self, csv_path: str, students_json_path: str):
        """
        Args:
            csv_path          : Path to the main attendance CSV file.
            students_json_path: Path to the students.json database.
        """
        self.csv_path = csv_path
        self.students_json_path = students_json_path
        self._students = self._load_students()
        self._ensure_csv_exists()

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    def _normalize_date(self, date_str: str) -> str:
        """
        Converts any common date format to YYYY-MM-DD.
        Handles: DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY, YYYY/MM/DD.
        Returns the original string if no known format matches.
        """
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                from datetime import datetime as dt
                return dt.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str

    def _load_students(self) -> dict:
        """Loads student records from students.json into a dict keyed by student_id."""
        if not os.path.exists(self.students_json_path):
            return {}
        with open(self.students_json_path, "r") as f:
            data = json.load(f)
        # Normalize to dict: { student_id: { name, email, enrolled_date } }
        if isinstance(data, list):
            return {s["student_id"]: s for s in data}
        return data

    def _ensure_csv_exists(self):
        """Creates the attendance CSV with headers if it does not exist yet."""
        if not os.path.exists(self.csv_path):
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True) if os.path.dirname(self.csv_path) else None
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
                writer.writeheader()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def get_student_name(self, student_id: str) -> str:
        """
        Resolves a student ID to a display name.
        The filename (without extension) from known_faces/ is used as student_id.
        Falls back to the ID itself if not in JSON.
        """
        if student_id in self._students:
            return self._students[student_id]["name"]
        # Gracefully fallback — student image may exist without a JSON entry
        return student_id

    def is_already_marked(self, student_id: str, check_date: date = None) -> bool:
        """Returns True if the student already has an attendance record for the given date."""
        check_date = check_date or date.today()
        date_str = check_date.strftime("%Y-%m-%d")
        records = self.get_all_records()
        return any(
            self._normalize_date(r["date"]) == date_str and r["student_id"] == student_id
            for r in records
        )

    def mark_attendance(self, student_id: str) -> dict:
        """
        Marks attendance for a student at the current timestamp.

        Returns:
            dict: The written attendance record.
        Raises:
            DuplicateAttendanceError : If already marked today.
            StudentNotFoundError     : If student not in JSON AND not in known_faces.
        """
        today = date.today()
        if self.is_already_marked(student_id, today):
            name = self.get_student_name(student_id)
            raise DuplicateAttendanceError(student_name=name, date=today.strftime("%d %b %Y"))

        name = self.get_student_name(student_id)
        now  = datetime.now()
        record = {
            "date"       : today.strftime("%Y-%m-%d"),
            "student_id" : student_id,
            "name"       : name,
            "time"       : now.strftime("%H:%M:%S"),
            "status"     : "Present",
        }

        with open(self.csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
            writer.writerow(record)

        return record

    def get_all_records(self) -> list:
        """Returns all attendance records as a list of dicts."""
        if not os.path.exists(self.csv_path):
            return []
        with open(self.csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def get_today_records(self) -> list:
        """Returns only today's attendance records."""
        today_str = date.today().strftime("%Y-%m-%d")
        return [
            r for r in self.get_all_records()
            if self._normalize_date(r["date"]) == today_str
        ]

    def get_all_student_ids(self) -> list:
        """Returns all unique student IDs found in the known_faces folder."""
        return list(self._students.keys()) if self._students else []

    def reload_students(self):
        """Reloads the student JSON (useful if it was updated externally)."""
        self._students = self._load_students()
