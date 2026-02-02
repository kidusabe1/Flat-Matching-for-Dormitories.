from google.cloud.firestore_v1 import AsyncClient

from app.config import get_settings

_db: AsyncClient | None = None


def get_db() -> AsyncClient:
    global _db
    if _db is None:
        settings = get_settings()
        _db = AsyncClient(project=settings.project_id)
    return _db
