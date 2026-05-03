from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, consent, health
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Privacy-first, human-in-the-loop AI system for mental health support",
    debug=settings.debug,
)

app.add_exception_handler(AppException, app_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(consent.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
