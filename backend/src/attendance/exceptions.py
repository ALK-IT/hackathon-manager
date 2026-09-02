class AttendanceError(Exception):
    status_code = 400
    error_code = "ATTENDANCE_ERROR"
    detail = "Attendance operation failed."


class AttendancePermissionError(AttendanceError):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    detail = "Only hackathon organizers can manage check-in sessions."


class CheckInNotAllowedError(AttendanceError):
    status_code = 403
    error_code = "CHECK_IN_NOT_ALLOWED"
    detail = "Only participants with an accepted registration can check in."


class InvalidCheckInTokenError(AttendanceError):
    status_code = 400
    error_code = "INVALID_CHECK_IN_TOKEN"
    detail = "The check-in token is invalid or has expired."
