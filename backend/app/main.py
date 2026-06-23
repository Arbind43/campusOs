from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import (
    academic,
    admin,
    ai,
    assignments,
    attendance,
    auth,
    clubs,
    events,
    helpdesk,
    hostel,
    mess,
    notices,
    placement,
    wellbeing,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="CampusOS API",
    description="AI-powered campus operating system with RBAC — HackOn Amazon",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for live deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — show actual errors in dev
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback
    error_detail = traceback.format_exc()
    print(f"[ERROR] {error_detail}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "traceback": error_detail},
    )


# ── Routers ──────────────────────────────────────────────────────────────── #
PREFIX = "/api/v1"

app.include_router(auth.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)
app.include_router(academic.router, prefix=PREFIX)
app.include_router(hostel.router, prefix=PREFIX)
app.include_router(placement.router, prefix=PREFIX)
app.include_router(wellbeing.router, prefix=PREFIX)
app.include_router(helpdesk.router, prefix=PREFIX)
app.include_router(clubs.router, prefix=PREFIX)
app.include_router(notices.router, prefix=PREFIX)
app.include_router(events.router, prefix=PREFIX)
app.include_router(assignments.router, prefix=PREFIX)
app.include_router(attendance.router, prefix=PREFIX)
app.include_router(mess.router, prefix=PREFIX)
app.include_router(ai.router, prefix=PREFIX)


@app.get("/", tags=["health"])
async def root_health_check():
    return {"status": "ok", "service": "campusos-api", "version": "2.0.0"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "campusos-api", "version": "2.0.0"}

