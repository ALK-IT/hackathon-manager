class ResourceError(Exception):
    status_code = 400
    error_code = "RESOURCE_ERROR"
    detail = "Resource operation failed."


class ResourceNotFoundError(ResourceError):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    detail = "Resource does not exist or you do not have access to it."


class ResourcePermissionError(ResourceError):
    status_code = 403
    error_code = "RESOURCE_PERMISSION_DENIED"
    detail = "Only the hackathon organizer can manage resources."
