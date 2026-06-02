"""
report_analyzer.py
==================
Computes attendance statistics using functional programming and NumPy.

PL-2 Concepts: Functional Programming (map, filter, reduce), NumPy, File Handling (CSV)
"""

import os
import csv
import numpy as np
from datetime import date, datetime
from functools import reduce
from collections import defaultdict

from modules.attendance_manager import AttendanceManager


class ReportAnalyzer:
    """
    Analyzes attendance records to produce statistics:
    - Per-student attendance percentage
    - Defaulter detection
    - Most regular student
    - Date-wise attendance trend
    """

    def __init__(self, attendance_manager: AttendanceManager, defaulter_threshold: float = 75.0):
        """
        Args:
            attendance_manager  : Instance of AttendanceManager.
            defaulter_threshold : Minimum attendance % to NOT be a defaulter (default: 75%).
        """
        self.manager = attendance_manager
        self.threshold = defaulter_threshold

    # -----------------------------------------------------------------------
    # Core data helpers
    # -----------------------------------------------------------------------
    def _get_all_dates(self) -> list:
        """Returns sorted list of all unique class dates in the records (normalized to YYYY-MM-DD)."""
        records = self.manager.get_all_records()
        dates = sorted(set(
            self.manager._normalize_date(r["date"]) for r in records
        ))
        return dates

    def _get_student_names(self) -> list:
        """Returns sorted list of all unique student names in the records."""
        records = self.manager.get_all_records()
        names = sorted(set(r["name"] for r in records))
        return names

    def _get_present_dates_for_student(self, name: str) -> list:
        """Returns list of UNIQUE normalized dates a specific student was marked Present."""
        records = self.manager.get_all_records()
        # Normalize each date and deduplicate so double-entries don't inflate the count
        return list(set(
            self.manager._normalize_date(r["date"])
            for r in records
            if r["name"] == name and r["status"] == "Present"
        ))

    # -----------------------------------------------------------------------
    # PL-2: Functional Programming - map, filter, reduce
    # -----------------------------------------------------------------------
    def attendance_percentage(self, name: str) -> float:
        """
        Calculates the attendance percentage for a student.
        Uses NumPy for the mean calculation.

        PL-2: NumPy-based computation
        """
        all_dates   = self._get_all_dates()
        total_days  = len(all_dates)
        if total_days == 0:
            return 0.0

        present_dates = self._get_present_dates_for_student(name)
        # Binary attendance array: 1 = present, 0 = absent
        attendance_array = np.array([1 if d in present_dates else 0 for d in all_dates])
        percentage = float(np.mean(attendance_array) * 100)
        return round(percentage, 2)

    def get_all_percentages(self) -> dict:
        """
        Returns a dict of { student_name: attendance_percentage }.
        Uses map() over student names.

        PL-2: Functional Programming - map
        """
        names   = self._get_student_names()
        percent_list = list(map(lambda n: (n, self.attendance_percentage(n)), names))
        return dict(percent_list)

    def detect_defaulters(self) -> list:
        """
        Returns list of student names with attendance < threshold %.
        Uses filter() over all student names.

        PL-2: Functional Programming - filter
        """
        percentages = self.get_all_percentages()
        defaulters  = list(filter(
            lambda name: percentages[name] < self.threshold,
            percentages.keys()
        ))
        return defaulters

    def most_regular_student(self) -> tuple:
        """
        Finds the student with the highest attendance percentage.
        Uses max() and map() over student names.

        PL-2: Functional Programming - map + reduce
        Returns:
            (student_name, percentage) tuple or (None, 0) if no records.
        """
        percentages = self.get_all_percentages()
        if not percentages:
            return (None, 0.0)
        best_name = max(percentages, key=lambda n: percentages[n])
        return (best_name, percentages[best_name])

    def attendance_trend(self) -> dict:
        """
        Builds a date-wise count of students present per day.
        Uses reduce() to accumulate counts.

        PL-2: Functional Programming - reduce
        Returns:
            dict: { "YYYY-MM-DD": count_of_students_present }
        """
        records  = self.manager.get_all_records()
        present  = [r for r in records if r["status"] == "Present"]
        if not present:
            return {}

        # Use reduce to accumulate counts per date
        def accumulate(acc, record):
            acc[record["date"]] = acc.get(record["date"], 0) + 1
            return acc

        trend = reduce(accumulate, present, {})
        # Sort by date
        return dict(sorted(trend.items()))

    # -----------------------------------------------------------------------
    # Summary CSV generation
    # -----------------------------------------------------------------------
    def generate_summary_csv(self, output_path: str) -> str:
        """
        Writes a per-student summary to reports/attendance_summary.csv.

        Returns:
            Path to the generated file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        percentages = self.get_all_percentages()
        all_dates   = self._get_all_dates()
        defaulters  = set(self.detect_defaulters())
        total_days  = len(all_dates)

        rows = []
        for name, pct in percentages.items():
            present_days = len(self._get_present_dates_for_student(name))
            absent_days  = max(0, total_days - present_days)   # guard: never below 0
            rows.append({
                "name"            : name,
                "total_days"      : total_days,
                "present_days"    : present_days,
                "absent_days"     : absent_days,
                "attendance_%"    : pct,
                "status"          : "DEFAULTER" if name in defaulters else "Regular",
            })

        fields = ["name", "total_days", "present_days", "absent_days", "attendance_%", "status"]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        return output_path

    # -----------------------------------------------------------------------
    # Console report
    # -----------------------------------------------------------------------
    def print_report(self):
        """Prints a formatted attendance report to the console."""
        print("\n" + "=" * 60)
        print("       ATTENDANCE ANALYTICS REPORT")
        print("=" * 60)

        percentages = self.get_all_percentages()
        if not percentages:
            print("  No attendance records found.")
            return

        all_dates  = self._get_all_dates()
        defaulters = set(self.detect_defaulters())
        best_name, best_pct = self.most_regular_student()

        print(f"  Total class days recorded : {len(all_dates)}")
        print(f"  Defaulter threshold        : {self.threshold}%")
        print()
        print(f"  {'Student Name':<25} {'Attendance %':>12}  {'Status'}")
        print(f"  {'-'*25} {'-'*12}  {'-'*10}")

        for name, pct in sorted(percentages.items(), key=lambda x: x[1], reverse=True):
            status = "DEFAULTER" if name in defaulters else "Regular"
            print(f"  {name:<25} {pct:>11.1f}%  {status}")

        print()
        print(f"  Most Regular  : {best_name}  ({best_pct:.1f}%)")
        print(f"  Defaulters    : {', '.join(defaulters) if defaulters else 'None'}")
        print("=" * 60)
