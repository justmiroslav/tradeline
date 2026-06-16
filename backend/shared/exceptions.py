from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from utils.logger import brief, logger

class AppError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=self.status_code, detail=detail)

class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND

class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT

class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED

class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN

class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST

class PlanLimitError(ForbiddenError):
    pass

class DuplicateKeyError(ConflictError):
    pass

class InvalidCodeError(BadRequestError):
    pass

class TooManyRequestsError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

class EmailDeliveryError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY

class AiUnavailableError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY

class ExchangeError(BadRequestError):
    pass

class InvalidCredentialsError(ExchangeError):
    pass

class KeyNotReadOnlyError(ExchangeError):
    pass

class KeyAccessRestrictedError(ExchangeError):
    pass

class IpNotWhitelistedError(ExchangeError):
    status_code = status.HTTP_403_FORBIDDEN

class IpNotRestrictedError(ExchangeError):
    pass

class RateLimitError(ExchangeError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

    def __init__(self, detail: str, retry_after: int | None = None) -> None:
        super().__init__(detail)
        self.retry_after = retry_after

class ExchangeUnavailableError(ExchangeError):
    status_code = status.HTTP_502_BAD_GATEWAY

_QUIET_STATUSES = (status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND)

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.warning(f"[http] {request.method} {request.url.path} → {type(exc).__name__}: {exc.detail}")
        elif exc.status_code not in _QUIET_STATUSES:
            logger.info(f"[http] {request.method} {request.url.path} → {type(exc).__name__}: {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": type(exc).__name__, "detail": exc.detail}
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTPException", "detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"[http] {request.method} {request.url.path} → unhandled {brief(exc)}")
        return JSONResponse(
            status_code=500,
            content={"error": "InternalError", "detail": "Internal server error"}
        )
