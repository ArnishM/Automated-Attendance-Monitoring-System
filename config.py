"""
config.py
=========
Central configuration for the Attendance Monitoring System.
Edit this file to match your classroom setup.
"""

import os

# ── Project base directory ─────────────────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR  = os.path.join(BASE_DIR, "known_faces")
ATTENDANCE_CSV   = os.path.join(BASE_DIR, "attendance.csv")
STUDENTS_JSON    = os.path.join(BASE_DIR, "students.json")
REPORTS_DIR      = os.path.join(BASE_DIR, "reports")

# ── Location Restriction ────────────────────────────────────────────────────
# Set LOCATION_CHECK_ENABLED = False to disable location gating (e.g., for demo)
LOCATION_CHECK_ENABLED = True
ALLOWED_CITY           = "Nagpur"    # <-- Change this to your classroom city
ALLOWED_COUNTRY        = "IN"         # ISO country code (e.g. "IN" for India)

# ── Attendance Analytics ────────────────────────────────────────────────────
DEFAULTER_THRESHOLD = 75.0            # Students below this % are flagged as defaulters

# ── Face Recognition ────────────────────────────────────────────────────────
# Tolerance: lower = stricter matching. 0.6 is the default face_recognition value.
FACE_RECOGNITION_TOLERANCE = 0.55

# ── Video Settings ──────────────────────────────────────────────────────────
CAMERA_INDEX    = 0        # Try 1 or 2 if your default camera doesn't open
FRAME_SCALE     = 0.25     # Scale down frames for faster processing (0.25 = 1/4 size)
WINDOW_WIDTH    = 900
WINDOW_HEIGHT   = 650

# ── Appearance ──────────────────────────────────────────────────────────────
COLOR_KNOWN   = (0, 220, 80)    # Green box for recognized students
COLOR_UNKNOWN = (0, 0, 220)     # Red box for unknown faces
COLOR_MARKED  = (255, 180, 0)   # Blue for already-marked students
