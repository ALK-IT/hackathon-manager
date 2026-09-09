from src.common.errors import APIError, ErrorCode


class AttendanceError(APIError):
    status_code = 400
    error_code = ErrorCode.ATTENDANCE_ERROR
    detail = "Attendance operation failed."


class AttendancePermissionError(AttendanceError):
    status_code = 403
    error_code = ErrorCode.PERMISSION_DENIED
    detail = "Only hackathon organizers can manage check-in sessions."


class CheckInNotAllowedError(AttendanceError):
    status_code = 403
    error_code = ErrorCode.CHECK_IN_NOT_ALLOWED
    detail = "Only participants with an accepted registration can check in."


class InvalidCheckInTokenError(AttendanceError):
    status_code = 400
    error_code = ErrorCode.INVALID_CHECK_IN_TOKEN
    detail = "The check-in token is invalid or has expired."


class HackathonNotInProgressError(AttendanceError):
    status_code = 409
    error_code = ErrorCode.HACKATHON_NOT_IN_PROGRESS
    detail = "Check-in is available only while the hackathon is in progress."
