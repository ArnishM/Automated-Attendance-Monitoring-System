"""
exceptions.py
=============
Custom exception classes for the Attendance Monitoring System.

PL-2 Concept: Custom Exception Handling
"""


class AttendanceSystemError(Exception):
    """Base exception class for all system errors."""
    def __init__(self, message="An error occurred in the attendance system."):
        self.message = message
        super().__init__(self.message)


class UnknownFaceError(AttendanceSystemError):
    """Raised when a face is detected in the frame but does not match any registered student."""
    def __init__(self, message="Unknown face detected. Not in the student database."):
        super().__init__(message)


class NoFaceDetectedError(AttendanceSystemError):
    """Raised when no face is detected in the camera frame at all."""
    def __init__(self, message="No face detected in the current frame."):
        super().__init__(message)


class LocationRestrictionError(AttendanceSystemError):
    """Raised when the user's IP/location is not in the authorized classroom network."""
    def __init__(self, detected_location="Unknown", allowed_location="Not configured"):
        self.detected_location = detected_location
        self.allowed_location = allowed_location
        message = (
            f"Location check failed!\n"
            f"  Your location : {detected_location}\n"
            f"  Allowed location : {allowed_location}\n"
            f"Attendance can only be marked from the authorized classroom."
        )
        super().__init__(message)


class DuplicateAttendanceError(AttendanceSystemError):
    """Raised when a student tries to mark attendance more than once on the same day."""
    def __init__(self, student_name="Student", date="today"):
        self.student_name = student_name
        self.date = date
        message = f"Duplicate attendance! '{student_name}' already marked present on {date}."
        super().__init__(message)


class StudentNotFoundError(AttendanceSystemError):
    """Raised when a student ID is not found in the students.json database."""
    def __init__(self, student_id=""):
        self.student_id = student_id
        message = f"Student with ID '{student_id}' not found in the database."
        super().__init__(message)
