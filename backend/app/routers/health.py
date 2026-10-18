from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness: процесс жив. Зависимости не проверяем, чтобы не перезапускать реплики из-за БД."""
    return {"status": "ok"}
