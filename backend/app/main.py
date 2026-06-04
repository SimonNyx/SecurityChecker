from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, assessments, users, ai_config, pdf
from app.config import settings

app = FastAPI(title="SecurityChecker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(ai_config.router, prefix="/api/v1")
app.include_router(pdf.router, prefix="/api/v1")
