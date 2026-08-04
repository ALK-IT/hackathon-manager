from src.errors import APIError, ErrorCode


class HackathonError(APIError):
    status_code = 400
    error_code = ErrorCode.HACKATHON_ERROR
    detail = "Hackathon operation failed."


class AdminRequiredError(HackathonError):
    status_code = 403
    error_code = ErrorCode.ADMIN_REQUIRED
    detail = "Only an administrator can create a hackathon."


class HackathonNotFoundError(HackathonError):
    status_code = 404
    error_code = ErrorCode.HACKATHON_NOT_FOUND
    detail = "Hackathon does not exist or you do not have access to it."


class HackathonPermissionDeniedError(HackathonError):
    status_code = 403
    error_code = ErrorCode.PERMISSION_DENIED
    detail = "Only the hackathon owner can perform this operation."


class InvalidDateRangeError(HackathonError):
    status_code = 422
    error_code = ErrorCode.INVALID_DATE_RANGE
    detail = "end_date must be later than start_date."


class InvalidTeamSizeError(HackathonError):
    status_code = 422
    error_code = ErrorCode.INVALID_TEAM_SIZE
    detail = "max_team_size cannot be greater than capacity."


class InvalidConfirmNameError(HackathonError):
    status_code = 400
    error_code = ErrorCode.INVALID_CONFIRM_NAME
    detail = "The provided name does not match the hackathon name."


class RegistrationAlreadyOpenError(HackathonError):
    status_code = 409
    error_code = ErrorCode.REGISTRATION_ALREADY_OPEN
    detail = "Registration is already open."


class RegistrationAlreadyClosedError(HackathonError):
    status_code = 409
    error_code = ErrorCode.REGISTRATION_ALREADY_CLOSED
    detail = "Registration is already closed."
