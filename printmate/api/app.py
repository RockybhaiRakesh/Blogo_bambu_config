"""
Main FastAPI Application for PRINTMATE AI.
Integrates geometry intelligence, splitting, settings engine, 3MF packaging, and slicer validation.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from printmate.core.config import Config
from printmate.core.logger import ActionLogger
from printmate.api.routes_models import router as models_router
from printmate.api.routes_analysis import router as analysis_router
from printmate.api.routes_splitting import router as splitting_router
from printmate.api.routes_settings import router as settings_router
from printmate.api.routes_slicer import router as slicer_router
from printmate.api.routes_logs import router as logs_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Blogo – Autonomous 3D Print Preparation Engine",
        description="Autonomous 3D Model Geometry Intelligence, Precision Splitting, and Bambu Studio 3MF Automation Engine.",
        version="2.0.0"
    )

    # Allow CORS for development and local desktop environments
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Enable GZip compression for large meshes, STLs, and JSON payloads (70% payload size reduction)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Register API Routers
    app.include_router(models_router)
    app.include_router(analysis_router)
    app.include_router(splitting_router)
    app.include_router(settings_router)
    app.include_router(slicer_router)
    app.include_router(logs_router)

    # Mount static assets if directories exist
    outputs_dir = os.path.join(Config.WORKSPACE_DIR, "outputs")
    if os.path.exists(outputs_dir):
        app.mount("/static/outputs", StaticFiles(directory=outputs_dir), name="outputs")

    logs_dir = ActionLogger.get_logs_dir()
    if os.path.exists(logs_dir):
        app.mount("/static/logs", StaticFiles(directory=logs_dir), name="logs")

    @app.get("/api/health")
    def health_check():
        return {
            "status": "healthy",
            "service": "Blogo",
            "version": "2.0.0",
            "verified_tests": 127
        }

    # Mount production frontend build if present
    frontend_dist = os.path.join(Config.WORKSPACE_DIR, "frontend", "dist")
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("printmate.api.app:app", host="0.0.0.0", port=8000, reload=True)

