import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.v1.endpoints import analysis, pharmacy, settings, push, medication_schedules, family, stacks
from app.services.push_scheduler import check_medication_reminders

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: medication reminder check every 60s
    scheduler.add_job(
        check_medication_reminders, "interval", seconds=60, id="med_reminder"
    )
    scheduler.start()
    logger.info("APScheduler started: medication reminder job running every 60s")
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="HealthStack API",
    description="Step-by-Step Analysis API for Symptoms & Prescriptions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 설정 (React 프론트엔드 연동)
origins = [
    "http://localhost:3000",
    "http://localhost:3002",
    "http://localhost:5173",
    "http://localhost:8000",
]
_cors_env = os.getenv("CORS_ORIGINS", "")
if _cors_env:
    origins.extend([o.strip() for o in _cors_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router 등록
app.include_router(analysis.router, prefix="/api/v1/analyze", tags=["Analysis"])
app.include_router(pharmacy.router, prefix="/api/v1/pharmacy", tags=["Pharmacy"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(push.router, prefix="/api/v1/push", tags=["Push"])
app.include_router(medication_schedules.router, prefix="/api/v1/medication-schedules", tags=["MedicationSchedules"])
app.include_router(family.router, prefix="/api/v1/family", tags=["Family"])
app.include_router(stacks.router, prefix="/api/v1/stacks", tags=["Stacks"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions to ensure CORS headers are included."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )


@app.get("/")
def root():
    return {"message": "HealthStack API is running. Visit /docs for documentation."}
