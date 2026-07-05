from fastapi import FastAPI

from api.routes.body import router as body_router
from api.routes.face import router as face_router
from api.routes.health import router as health_router

app = FastAPI(title="Twenty-eight", version="0.1.0")

app.include_router(health_router)
app.include_router(face_router)
app.include_router(body_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Twenty-eight API"}
