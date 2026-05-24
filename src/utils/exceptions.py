"""Custom exceptions and FastAPI exception handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "error"):
        self.message = message
        self.status_code = status_code
        self.code = code


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401, code="authentication_error")


class AuthorizationError(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403, code="authorization_error")


class ApplicationNotFound(AppException):
    def __init__(self, app_id: str):
        super().__init__(f"Application '{app_id}' not found", status_code=404, code="application_not_found")


class ApplicationRevoked(AppException):
    def __init__(self, app_id: str):
        super().__init__(f"Application '{app_id}' is revoked", status_code=403, code="application_revoked")


class CredentialNotFound(AppException):
    def __init__(self, cred_id: str):
        super().__init__(f"Credential '{cred_id}' not found", status_code=404, code="credential_not_found")


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422, code="validation_error")


class RateLimitExceeded(AppException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429, code="rate_limit_exceeded")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
