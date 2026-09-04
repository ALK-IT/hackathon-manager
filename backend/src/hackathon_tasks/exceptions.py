class TaskError(Exception):
    status_code = 400
    error_code = "TASK_ERROR"
    detail = "Task operation failed."


class TaskNotFoundError(TaskError):
    status_code = 404
    error_code = "TASK_NOT_FOUND"
    detail = "Task does not exist for this hackathon."


class TaskPermissionDeniedError(TaskError):
    status_code = 403
    error_code = "TASK_PERMISSION_DENIED"
    detail = "You do not have permission to perform this operation."


class TasksNotReleasedError(TaskError):
    status_code = 403
    error_code = "TASKS_NOT_RELEASED"
    detail = "Tasks have not been released yet."


class InvalidTaskVisibilityDateError(TaskError):
    status_code = 422
    error_code = "INVALID_TASK_VISIBILITY_DATE"
    detail = "visible_from must be earlier than the hackathon end date."


class TeamRequiredForSubmissionError(TaskError):
    status_code = 409
    error_code = "TEAM_REQUIRED_FOR_SUBMISSION"
    detail = "You must belong to a team to submit a solution."


class TaskSubmissionClosedError(TaskError):
    status_code = 409
    error_code = "TASK_SUBMISSION_CLOSED"
    detail = "Solutions cannot be submitted after the hackathon has ended."
