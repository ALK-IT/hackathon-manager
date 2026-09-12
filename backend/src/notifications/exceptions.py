from src.common.errors import APIError, ErrorCode


class NotificationNotFoundError(APIError):
    status_code = 404
    error_code = ErrorCode.NOTIFICATION_NOT_FOUND
    detail = "Notification does not exist."
