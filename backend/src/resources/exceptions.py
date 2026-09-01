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
    error_code = "PERMISSION_DENIED"
    detail = "Only hackathon organizers can manage resources."


class ResourceItemNotFoundError(ResourceError):
    status_code = 404
    error_code = "RESOURCE_ITEM_NOT_FOUND"
    detail = "Resource item does not exist for this resource."


class ResourceRecipientNotFoundError(ResourceError):
    status_code = 404
    error_code = "RESOURCE_RECIPIENT_NOT_FOUND"
    detail = "Registration or team does not exist for this hackathon."


class ResourceItemUnavailableError(ResourceError):
    status_code = 409
    error_code = "RESOURCE_ITEM_UNAVAILABLE"
    detail = "Resource item is already assigned or revoked."


class ResourceTargetMismatchError(ResourceError):
    status_code = 409
    error_code = "RESOURCE_TARGET_MISMATCH"
    detail = "The selected recipient does not match the resource target."
