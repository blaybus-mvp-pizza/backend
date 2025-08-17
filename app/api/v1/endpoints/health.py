from fastapi import APIRouter


class HealthAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get("/", summary="Health check")
        async def health() -> dict:
            return {"status": "ok"}


api = HealthAPI().router
