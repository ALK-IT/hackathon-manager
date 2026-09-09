from fastapi import status

from src.common.errors import APIError, ErrorCode


class ResourceError(APIError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.RESOURCE_ERROR
    detail = "Resource operation failed."


class ResourceNotFoundError(ResourceError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.RESOURCE_NOT_FOUND
    detail = "Resource does not exist or you do not have access to it."


class ResourcePermissionError(ResourceError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.PERMISSION_DENIED
    detail = "Only hackathon organizers can manage resources."


class ResourceItemNotFoundError(ResourceError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.RESOURCE_ITEM_NOT_FOUND
    detail = "Resource item does not exist for this resource."


class ResourceRecipientNotFoundError(ResourceError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.RESOURCE_RECIPIENT_NOT_FOUND
    detail = "Registration or team does not exist for this hackathon."


class ResourceItemUnavailableError(ResourceError):
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.RESOURCE_ITEM_UNAVAILABLE
    detail = "Resource item is already assigned or revoked."


class ResourceTargetMismatchError(ResourceError):
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.RESOURCE_TARGET_MISMATCH
    detail = "The selected recipient does not match the resource target."
