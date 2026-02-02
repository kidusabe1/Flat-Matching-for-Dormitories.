from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class NotFoundError(AppError):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)


class BadRequestError(AppError):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail)


class InvalidTransitionError(AppError):
    def __init__(self, detail: str = "Invalid state transition"):
        super().__init__(status_code=409, detail=detail)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
