from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, assessments, users, ai_config

app = FastAPI(title="SecurityChecker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(ai_config.router, prefix="/api/v1")
