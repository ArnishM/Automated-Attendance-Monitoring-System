"""
main.py  –  Secure Classroom Face Monitoring & Attendance Analytics System
==========================================================================

Usage:
    python main.py                  # Live attendance marking (location check ON)
    python main.py --demo           # Skip location check (for demo/testing)
    python main.py --report         # Generate analytics + charts only
    python main.py --report --demo  # Same, with verbose output

PL-2 Concepts Covered:
    OOP, File Handling (CSV/JSON), Custom Exceptions, Functional Programming
    (map/filter/reduce), NumPy, Data Visualization, Real-world Automation

Author  : PL-2 Lab Project
Date    : 2026
"""

import cv2
import face_recognition
import os
import sys
import numpy as np
import argparse
from datetime import datetime

# ── Project modules ────────────────────────────────────────────────────────
import config
from modules.exceptions import (
    UnknownFaceError,
    NoFaceDetectedError,
    LocationRestrictionError,
    DuplicateAttendanceError,
)
from modules.location_checker   import LocationChecker
from modules.attendance_manager import AttendanceManager
from modules.report_analyzer    import ReportAnalyzer
from modules.visualizer         import Visualizer


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Parse command-line arguments
# ══════════════════════════════════════════════════════════════════════════════
def parse_args():
    parser = argparse.ArgumentParser(
        description="Secure Classroom Face Monitoring & Attendance System"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode: skips location check, useful for testing"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate attendance report and visualizations, then exit"
    )
    return parser.parse_args()


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Load known face encodings 
# ══════════════════════════════════════════════════════════════════════════════
def load_known_faces(known_faces_dir: str):
    """
    Loads all student images from known_faces/ and encodes them.
    Returns (list_of_encodings, list_of_names).

    This reuses the face encoding logic from the original main.py.
    """
    known_face_encodings = []
    known_face_names     = []

    if not os.path.exists(known_faces_dir):
        print(f"  Warning: '{known_faces_dir}' not found. Creating it...")
        os.makedirs(known_faces_dir, exist_ok=True)
        print(f"   Add student photos as: known_faces/StudentName.jpg")
        return known_face_encodings, known_face_names

    files = os.listdir(known_faces_dir)
    image_files = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    if not image_files:
        print(f"  No images found in '{known_faces_dir}'.")
        print("   Add student photos named exactly like: firstname_lastname.jpg")
        return known_face_encodings, known_face_names

    print(f"\n🔍 Loading known faces from: {known_faces_dir}")
    for filename in image_files:
        image_path = os.path.join(known_faces_dir, filename)
        try:
            image     = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if len(encodings) > 0:
                known_face_encodings.append(encodings[0])
                name = os.path.splitext(filename)[0]  
                known_face_names.append(name)
                print(f"    Loaded: {name}")
            else:
                print(f"     No face found in: {filename}")
        except Exception as e:
            print(f"    Error loading {filename}: {e}")

    print(f"   Total known faces: {len(known_face_names)}\n")
    return known_face_encodings, known_face_names


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Location gate
# ══════════════════════════════════════════════════════════════════════════════
def check_location(demo_mode: bool):
    """
    Validates that this machine is within the authorized classroom.
    Skipped entirely in demo mode.
    Raises LocationRestrictionError if not authorized.
    """
    if demo_mode:
        print("🟡 [DEMO MODE] Location check skipped.")
        return

    if not config.LOCATION_CHECK_ENABLED:
        print("ℹ  Location check is disabled in config.py.")
        return

    print(" Checking classroom location...")
    checker = LocationChecker(
        allowed_city=config.ALLOWED_CITY,
        allowed_country=config.ALLOWED_COUNTRY,
    )
    checker.print_location_info()
    checker.is_authorized()      # Raises LocationRestrictionError if fails
    print(f" Location verified: {config.ALLOWED_CITY}, {config.ALLOWED_COUNTRY}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Live face recognition + attendance marking
# ══════════════════════════════════════════════════════════════════════════════
def run_attendance_session(known_face_encodings, known_face_names,
                           attendance_manager: AttendanceManager):
    """
    Opens the webcam, continuously recognizes faces, and marks attendance.
    Inherits all your original face recognition logic and extends it with:
      - Attendance marking (press SPACE to mark)
      - Colour-coded boxes (green = known, red = unknown, gold = already marked)
      - On-screen HUD with student name and status
    """
    # ── Open camera ──────────────────────────────────────────────────────────
    video_capture = None
    for index in [config.CAMERA_INDEX, 0, 1, 2]:
        print(f" Trying camera index {index}...")
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"   Camera found at index {index}\n")
            video_capture = cap
            break
        cap.release()

    if video_capture is None or not video_capture.isOpened():
        print(" Could not open webcam. Check connection or camera index in config.py.")
        sys.exit(1)

    cv2.namedWindow("Attendance System", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Attendance System", config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

    print("📹 Live attendance session started.")
    print("   SPACE  →  Mark attendance for the recognized face")
    print("   R      →  Show today's attendance in terminal")
    print("   Q      →  Quit\n")

    # ── State ─────────────────────────────────────────────────────────────────
    last_names          = []         # names detected in current frame
    last_face_locations = []
    status_message      = ""         # Temporary on-screen message
    status_timer        = 0          # Frames left to show the message
    show_records        = False      # Toggle: show today's attendance overlay
    records_list        = []         # Cached records for overlay display

    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to grab frame. Exiting...")
                break

            # ── Resize + convert (original logic) ─────────────────────────
            small_frame      = cv2.resize(frame, (0, 0),
                                          fx=config.FRAME_SCALE, fy=config.FRAME_SCALE)
            rgb_small_frame  = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # ── Detect faces (original logic) ──────────────────────────────
            face_locations   = face_recognition.face_locations(rgb_small_frame)
            face_encodings   = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches       = face_recognition.compare_faces(
                    known_face_encodings, face_encoding,
                    tolerance=config.FACE_RECOGNITION_TOLERANCE
                )
                name          = "Unknown"
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]

                face_names.append(name)

            last_names          = face_names
            last_face_locations = face_locations

            # ── Draw boxes + labels ────────────────────────────────────────
            scale = int(1 / config.FRAME_SCALE)
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top    *= scale;  right  *= scale
                bottom *= scale;  left   *= scale

                already_marked = (name != "Unknown" and
                                  attendance_manager.is_already_marked(name))

                if name == "Unknown":
                    color = config.COLOR_UNKNOWN
                elif already_marked:
                    color = config.COLOR_MARKED
                else:
                    color = config.COLOR_KNOWN

                # Face rectangle
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # Name banner
                label = name if name == "Unknown" else (
                    f"{name} [MARKED]" if already_marked else name
                )
                banner_top = max(bottom - 38, top + 2)
                cv2.rectangle(frame, (left, banner_top), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label,
                            (left + 6, bottom - 8),
                            cv2.FONT_HERSHEY_DUPLEX, 0.65,
                            (255, 255, 255), 1)

            # ── HUD overlay ───────────────────────────────────────────────
            h, w = frame.shape[:2]
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 36), (20, 20, 40), cv2.FILLED)
            frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

            today_count = len(attendance_manager.get_today_records())
            hud_text = (f"Faces: {len(face_names)}  |  "
                        f"Marked today: {today_count}  |  "
                        f"SPACE=Mark  R=Records  Q=Quit")
            cv2.putText(frame, hud_text, (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1)

            # ── Status message (appears for ~90 frames) ───────────────────
            if status_timer > 0:
                msg_y = h - 20
                cv2.rectangle(frame, (0, h - 44), (w, h), (20, 20, 50), cv2.FILLED)
                cv2.putText(frame, status_message, (12, msg_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 220, 100), 2)
                status_timer -= 1

            # ── Today's records overlay (shown when R is pressed) ─────────
            if show_records:
                panel_h = min(44 + len(records_list) * 28, h - 60)
                overlay2 = frame.copy()
                cv2.rectangle(overlay2, (10, 44), (420, 44 + panel_h), (15, 25, 55), cv2.FILLED)
                frame = cv2.addWeighted(overlay2, 0.82, frame, 0.18, 0)
                cv2.putText(frame,
                            f"Today's Attendance ({len(records_list)} present) - press R to close",
                            (18, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (180, 220, 255), 1)
                for i, rec in enumerate(records_list):
                    line = f"{i+1}. {rec['name']}   {rec['time']}"
                    cv2.putText(frame, line,
                                (18, 96 + i * 28),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.54, (100, 255, 160), 1)
                if not records_list:
                    cv2.putText(frame, "No attendance marked yet today.",
                                (18, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 180, 180), 1)

            cv2.imshow("Attendance System", frame)

            # ── Key handling ──────────────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == ord("Q"):
                print("\n👋 Session ended by user.")
                break

            elif key == ord("r") or key == ord("R"):
                # Toggle the on-screen records overlay
                show_records = not show_records
                if show_records:
                    records_list = attendance_manager.get_today_records()
                    print(f"\nToday's attendance ({len(records_list)} students):")
                    for rec in records_list:
                        print(f"   {rec['time']}  -  {rec['name']}")

            elif key == ord(" "):
                # SPACE key → mark attendance for the first recognized face
                if not last_names:
                    status_message = "⚠  No face detected in frame!"
                    status_timer   = 90
                else:
                    # Try to mark the first known face found
                    marked_any = False
                    for name in last_names:
                        if name == "Unknown":
                            status_message = " Unknown face – cannot mark attendance."
                            status_timer   = 90
                            continue
                        try:
                            record = attendance_manager.mark_attendance(name)
                            status_message = f"  Attendance marked: {record['name']}  @ {record['time']}"
                            status_timer   = 120
                            print(f" Marked: {record['name']} at {record['time']}")
                            marked_any = True
                        except DuplicateAttendanceError as e:
                            status_message = f"⚠  Already marked: {name}"
                            status_timer   = 90
                            print(f"  {e.message}")
                        except Exception as e:
                            status_message = f" Error: {str(e)[:60]}"
                            status_timer   = 90
                            print(f" Unexpected error: {e}")

    except KeyboardInterrupt:
        print("\n Interrupted by user.")
    finally:
        video_capture.release()
        cv2.destroyAllWindows()

    # ── End-of-session summary ─────────────────────────────────────────────
    records = attendance_manager.get_today_records()
    print(f"\n📋 Session Summary – {datetime.now().strftime('%d %b %Y')}")
    print(f"   Students marked present : {len(records)}")
    for r in records:
        print(f"     {r['name']}  ({r['time']})")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — Report & Visualization mode
# ══════════════════════════════════════════════════════════════════════════════
def run_report(attendance_manager: AttendanceManager):
    """Generates the analytics report and all three charts."""
    analyzer   = ReportAnalyzer(attendance_manager, defaulter_threshold=config.DEFAULTER_THRESHOLD)
    visualizer = Visualizer(analyzer, reports_dir=config.REPORTS_DIR)

    # Terminal report
    analyzer.print_report()

    # Trend info
    trend = analyzer.attendance_trend()
    if trend:
        print("\n Daily Attendance Trend:")
        for d, count in trend.items():
            bar = "█" * count
            print(f"   {d}  {bar}  ({count})")

    # Summary CSV
    summary_path = os.path.join(config.REPORTS_DIR, "attendance_summary.csv")
    saved = analyzer.generate_summary_csv(summary_path)
    print(f"\n Summary CSV saved: {saved}")

    # Charts
    visualizer.generate_all()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("   Secure Classroom Attendance Monitoring System")
    print("=" * 60)

    args = parse_args()

    # ── Shared: Attendance Manager ─────────────────────────────────────────
    attendance_manager = AttendanceManager(
        csv_path=config.ATTENDANCE_CSV,
        students_json_path=config.STUDENTS_JSON
    )

    # ── Report-only mode ───────────────────────────────────────────────────
    if args.report:
        print("\n Report mode – no camera needed.\n")
        run_report(attendance_manager)
        return

    # ── Live attendance mode ───────────────────────────────────────────────
    # 1. Location check (gate)
    try:
        check_location(demo_mode=args.demo)
    except LocationRestrictionError as e:
        print(f"\n {e.message}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"\n  Location check failed (no internet?): {e}")
        print("   Continuing without location verification...\n")

    # 2. Load faces
    known_face_encodings, known_face_names = load_known_faces(config.KNOWN_FACES_DIR)

    # 3. Run webcam session
    run_attendance_session(known_face_encodings, known_face_names, attendance_manager)

    # 4. Auto-generate report after session
    print("\n Generating end-of-session report...")
    run_report(attendance_manager)


if __name__ == "__main__":
    main()
