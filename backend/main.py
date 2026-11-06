"""
ROLLIQ Backend API Application.
Smart Bed-Mobility and Recovery Monitoring System.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from database import init_db
from routers.sensor import router as sensor_router
from routers.sessions import router as sessions_router
from routers.users import router as users_router
from routers.devices import router as devices_router
from routers.analytics import router as analytics_router
from routers.alerts import router as alerts_router
from routers.simulation import router as simulation_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rolliq.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: database initialization and cleanup."""
    logger.info("Initializing ROLLIQ database...")
    await init_db()
    logger.info("ROLLIQ database ready.")
    yield
    logger.info("ROLLIQ backend shutting down.")


app = FastAPI(
    title="ROLLIQ API",
    description="Low-Cost Wearable Edge-Intelligence for Quantifying Human Bed-Mobility Patterns",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sensor_router)
app.include_router(sessions_router)
app.include_router(users_router)
app.include_router(devices_router)
app.include_router(analytics_router)
app.include_router(alerts_router)
app.include_router(simulation_router)


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "ROLLIQ API",
        "version": "1.0.0",
    }


from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Serve frontend build if dist directory exists
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        """Root overview endpoint."""
        return {
            "project": "ROLLIQ",
            "title": "Smart Bed-Mobility and Recovery Monitoring System",
            "status": "online",
            "docs_url": "/docs",
            "health_url": "/health",
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
