import os

from app.routers.users import router as user_router
from fastapi import FastAPI

app = FastAPI(
    title="User Service",
    debug=os.getenv("DEBUG", "false").lower() == "true",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(user_router, prefix="/api/v1")
