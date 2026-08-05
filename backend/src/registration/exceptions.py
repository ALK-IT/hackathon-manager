class RegistrationError(Exception):
    status_code = 400
    error_code = "REGISTRATION_ERROR"
    detail = "Registration operation failed."

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class QuestionNotFoundError(RegistrationError):
    status_code = 404
    error_code = "QUESTION_NOT_FOUND"
    detail = "Registration question does not exist."


class InvalidPermission(RegistrationError):
    status_code = 403
    error_code = "REGISTRATION_PERMISSION_DENIED"
    detail = "You do not have permission to perform this operation."


class InvalidRegistrationQuestionError(RegistrationError):
    status_code = 422
    error_code = "INVALID_REGISTRATION_QUESTION"
    detail = "One or more questions do not belong to this hackathon."


class MissingRequiredAnswersError(RegistrationError):
    status_code = 422
    error_code = "MISSING_REQUIRED_ANSWERS"
    detail = "Answers to all required questions must be provided."


class RegistrationAlreadyExistsError(RegistrationError):
    status_code = 409
    error_code = "REGISTRATION_ALREADY_EXISTS"
    detail = "The user is already registered for this hackathon."


class RegistrationNotFoundError(RegistrationError):
    status_code = 404
    error_code = "REGISTRATION_NOT_FOUND"
    detail = "Registration does not exist."