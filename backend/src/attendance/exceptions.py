class AttendanceError(Exception):
    status_code = 400
    error_code = "ATTENDANCE_ERROR"
    detail = "Attendance operation failed."


class AttendancePermissionError(AttendanceError):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    detail = "Only hackathon organizers can manage check-in sessions."
