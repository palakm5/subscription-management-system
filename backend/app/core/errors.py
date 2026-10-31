from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from pymongo.errors import DuplicateKeyError
import logging

logger = logging.getLogger("brightloop.errors")

class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

class InvalidTransition(AppException):
    def __init__(self, message: str = "Invalid state transition", details: any = None):
        super().__init__(code="INVALID_STATE_TRANSITION", message=message, status_code=status.HTTP_409_CONFLICT, details=details)

class EntityNotFound(AppException):
    def __init__(self, message: str = "Resource not found", details: any = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)

class PermissionDenied(AppException):
    def __init__(self, message: str = "Permission denied", details: any = None):
        super().__init__(code="PERMISSION_DENIED", message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)

class AuthenticationFailed(AppException):
    def __init__(self, message: str = "Authentication failed", details: any = None):
        super().__init__(code="AUTHENTICATION_FAILED", message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)

class BusinessRuleViolation(AppException):
    def __init__(self, message: str, details: any = None):
        super().__init__(code="BUSINESS_RULE_VIOLATION", message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)

class DuplicateEntity(AppException):
    def __init__(self, message: str = "A resource with this identifier already exists", details: any = None):
        super().__init__(code="DUPLICATE_ENTITY", message=message, status_code=status.HTTP_409_CONFLICT, details=details)

def error_response(code: str, message: str, status_code: int, details: any = None) -> JSONResponse:
    payload = {
        "error": {
            "code": code,
            "message": message
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)

async def app_exception_handler(request: Request, exc: AppException):
    return error_response(code=exc.code, message=exc.message, status_code=exc.status_code, details=exc.details)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        details = jsonable_encoder(exc.errors())
    except Exception:
        details = str(exc)
    msg = "Request payload validation failed"
    if isinstance(details, list) and len(details) > 0 and isinstance(details[0], dict) and "msg" in details[0]:
        msg = details[0]["msg"]
    return error_response(
        code="VALIDATION_ERROR",
        message=msg,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details
    )

async def duplicate_key_exception_handler(request: Request, exc: DuplicateKeyError):
    return error_response(
        code="DUPLICATE_KEY",
        message="Duplicate key constraint violated in the database",
        status_code=status.HTTP_409_CONFLICT,
        details=str(exc)
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", exc)
    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
