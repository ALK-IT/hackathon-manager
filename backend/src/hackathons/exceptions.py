class HackathonError(Exception):
    status_code = 400
    error_code = "HACKATHON_ERROR"
    detail = "Hackathon operation failed."


class AdminRequiredError(HackathonError):
    status_code = 403
    error_code = "ADMIN_REQUIRED"
    detail = "Only an administrator can create a hackathon."


class HackathonNotFoundError(HackathonError):
    status_code = 404
    error_code = "HACKATHON_NOT_FOUND"
    detail = "Hackathon does not exist or you do not have access to it."


class CoOrganizerUserNotFoundError(HackathonError):
    status_code = 404
    error_code = "CO_ORGANIZER_USER_NOT_FOUND"
    detail = "User selected as a co-organizer does not exist."


class CoOrganizerAlreadyAssignedError(HackathonError):
    status_code = 409
    error_code = "CO_ORGANIZER_ALREADY_ASSIGNED"
    detail = "User is already a co-organizer of this hackathon."


class OrganizerCannotBeCoOrganizerError(HackathonError):
    status_code = 409
    error_code = "ORGANIZER_CANNOT_BE_CO_ORGANIZER"
    detail = "Hackathon owner cannot also be a co-organizer."


class CoOrganizerSearchRateLimitExceededError(HackathonError):
    status_code = 429
    error_code = "CO_ORGANIZER_SEARCH_RATE_LIMIT_EXCEEDED"
    detail = "Too many co-organizer searches. Try again later."


class InvalidDateRangeError(HackathonError):
    status_code = 422
    error_code = "INVALID_DATE_RANGE"
    detail = "end_date must be later than start_date."


class InvalidRegistrationDeadlineError(HackathonError):
    status_code = 422
    error_code = "INVALID_REGISTRATION_DEADLINE"
    detail = "registration_deadline must be earlier than start_date."


class InvalidRegistrationWindowError(HackathonError):
    status_code = 422
    error_code = "INVALID_REGISTRATION_WINDOW"
    detail = "registration_opens_at must be earlier than registration_deadline."


class InvalidTeamSizeError(HackathonError):
    status_code = 422
    error_code = "INVALID_TEAM_SIZE"
    detail = "max_team_size cannot be greater than capacity."


class InvalidConfirmNameError(HackathonError):
    status_code = 400
    error_code = "INVALID_CONFIRM_NAME"
    detail = "The provided name does not match the hackathon name."


class RegistrationAlreadyOpenError(HackathonError):
    status_code = 409
    error_code = "REGISTRATION_ALREADY_OPEN"
    detail = "Registration is already open."


class RegistrationAlreadyClosedError(HackathonError):
    status_code = 409
    error_code = "REGISTRATION_ALREADY_CLOSED"
    detail = "Registration is already closed."


class RegistrationDeadlinePassedError(HackathonError):
    status_code = 409
    error_code = "REGISTRATION_DEADLINE_PASSED"
    detail = "Registration deadline has passed."
