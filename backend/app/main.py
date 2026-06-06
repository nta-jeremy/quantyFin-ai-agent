import uuid
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlmodel import Session, text

from app.core.config import settings
from app.core.logging import trace_id_var, logger
from app.core.exceptions import BaseAppException
from app.core.db import get_session


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Cache-Control"] = "no-store"
    return response

# Trace ID Middleware
@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    token = trace_id_var.set(trace_id)
    try:
        logger.info(f"Request started: {request.method} {request.url.path}")
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        logger.info(f"Request completed: {request.method} {request.url.path} - status={response.status_code}")
        return response
    finally:
        trace_id_var.reset(token)

# Application Exception Handlers
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    trace_id = trace_id_var.get()
    logger.error(f"App exception: {exc.message} (code={exc.code}, status={exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "meta": {
                "trace_id": trace_id
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    trace_id = trace_id_var.get()
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên.",
                "details": "Internal server error"
            },
            "meta": {
                "trace_id": trace_id
            }
        }
    )

# Root endpoints
@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    return {
        "data": {
            "message": "Welcome to quantyFin AI API",
            "version": "1.0.0"
        },
        "error": None,
        "meta": {
            "trace_id": trace_id_var.get()
        }
    }

@app.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request, session: Session = Depends(get_session)):
    health_status = {
        "status": "healthy",
        "postgres": "unknown",
        "neo4j": "unknown"
    }
    
    # Check Postgres Connection
    try:
        session.exec(text("SELECT 1"))
        health_status["postgres"] = "healthy"
    except Exception as e:
        logger.error(f"Postgres healthcheck failed: {str(e)}")
        health_status["postgres"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Check Neo4j Connection
    try:
        from app.core.neo4j import neo4j_manager
        driver = neo4j_manager.get_driver()
        driver.verify_connectivity()
        health_status["neo4j"] = "healthy"
    except Exception as e:
        logger.error(f"Neo4j healthcheck failed: {str(e)}")
        health_status["neo4j"] = "unhealthy"
        health_status["status"] = "unhealthy"

    status_code = 200 if health_status["status"] == "healthy" else 500
    
    return JSONResponse(
        status_code=status_code,
        content={
            "data": health_status,
            "error": None,
            "meta": {
                "trace_id": trace_id_var.get()
            }
        }
    )
