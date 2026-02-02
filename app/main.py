from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.error_handler import register_error_handlers
from app.routes import health, rooms, users


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="BIU Dormitory Exchange Platform",
        description="Lease transfer and room swap matching for Bar-Ilan University dormitories",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(rooms.router)

    return app


app = create_app()
