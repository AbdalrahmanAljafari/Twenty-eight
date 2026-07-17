from fastapi import FastAPI

from api.routes.body_Apose import router as body_apose_router
from api.routes.body_standardize import router as body_standardize_router
from api.routes.face import router as face_router
from api.routes.health import router as health_router

app = FastAPI(title="Twenty-eight", version="0.1.0")

app.include_router(health_router)
app.include_router(face_router)
app.include_router(body_apose_router)
app.include_router(body_standardize_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Twenty-eight API"}
