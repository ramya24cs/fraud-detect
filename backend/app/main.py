
import os

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.predictions import router as predictions_router
from backend.app.api.review_queue import router as review_queue_router
from backend.app.api.feedback import router as feedback_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.models import router as models_router
from backend.app.api.model_admin import router as model_admin_router
from backend.app.api.audit_logs import router as audit_logs_router

from backend.app.services.database_health_service import (
    check_database_connection,
)

app = FastAPI(
    title="Cost-Sensitive Fraud Detection API",
    description=(
        "Backend API for cost-sensitive fraud detection, "
        "account-history anomaly assessments, transaction predictions, "
        "operator review, feedback, dashboards, model registry, and audit logs."
    ),
    version="1.0.0",
)

# CORS configuration
origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "HEAD",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["Authorization", "Content-Type"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(predictions_router)
app.include_router(review_queue_router)
app.include_router(feedback_router)
app.include_router(dashboard_router)
app.include_router(models_router)
app.include_router(model_admin_router)
app.include_router(audit_logs_router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Return basic API information."""
    return {
        "message": "Cost-Sensitive Fraud Detection API",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.head("/", include_in_schema=False)
def head_root() -> Response:
    """Return headers without a response body."""
    return Response(status_code=200)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Return no content when no favicon is configured."""
    return Response(status_code=204)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Check API and database availability."""
    database_status = check_database_connection()

    if database_status["status"] != "ok":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "service": "fraud-detection-api",
                "database": "unavailable",
            },
        )

    return {
        "status": "ok",
        "service": "fraud-detection-api",
        "database": "connected",
    }
