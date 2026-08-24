from src.common.errors import APIError, ErrorCode


class RegistrationError(APIError):
    status_code = 400
    error_code = ErrorCode.REGISTRATION_ERROR
    detail = "Registration operation failed."


class QuestionNotFoundError(RegistrationError):
    status_code = 404
    error_code = ErrorCode.QUESTION_NOT_FOUND
    detail = "Registration question does not exist."


class RegistrationQuestionsLockedError(RegistrationError):
    status_code = 409
    error_code = ErrorCode.REGISTRATION_QUESTIONS_LOCKED
    detail = "Registration questions cannot be changed after registration has opened."


class InvalidPermission(RegistrationError):
    status_code = 403
    error_code = ErrorCode.PERMISSION_DENIED
    detail = "You do not have permission to perform this operation."


class InvalidRegistrationQuestionError(RegistrationError):
    status_code = 422
    error_code = ErrorCode.INVALID_REGISTRATION_QUESTION
    detail = "One or more questions do not belong to this hackathon."


class MissingRequiredAnswersError(RegistrationError):
    status_code = 422
    error_code = ErrorCode.MISSING_REQUIRED_ANSWERS
    detail = "Answers to all required questions must be provided."


class RegistrationAlreadyExistsError(RegistrationError):
    status_code = 409
    error_code = ErrorCode.ALREADY_REGISTERED
    detail = "The user is already registered for this hackathon."


class RegistrationClosedError(RegistrationError):
    status_code = 409
    error_code = ErrorCode.REGISTRATION_CLOSED
    detail = "Registration for this hackathon is closed."


class RegistrationNotFoundError(RegistrationError):
    status_code = 404
    error_code = ErrorCode.REGISTRATION_NOT_FOUND
    detail = "Registration does not exist."
