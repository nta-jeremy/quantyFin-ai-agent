import uuid
import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from sqlmodel import Session, text, select, SQLModel
from datetime import datetime, time, timedelta

from app.core.config import settings
from app.core.logging import trace_id_var, logger
from app.core.exceptions import BaseAppException
from app.core.db import get_session, engine
from app.models.stock import StockTicker, StockPrice
from app.services.stock_data import ingest_all_active_tickers


def init_db():
    try:
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            initial_tickers = [
                {"ticker": "VNINDEX", "name": "Chỉ số VN-Index", "market": "HOSE"},
                {"ticker": "VIC", "name": "Tập đoàn Vingroup - CTCP", "market": "HOSE"},
                {"ticker": "VNM", "name": "Công ty Cổ phần Sữa Việt Nam", "market": "HOSE"},
                {"ticker": "FPT", "name": "Công ty Cổ phần FPT", "market": "HOSE"},
            ]
            for ticker_data in initial_tickers:
                try:
                    statement = select(StockTicker).where(StockTicker.ticker == ticker_data["ticker"])
                    existing = session.exec(statement).first()
                    if not existing:
                        new_ticker = StockTicker(
                            ticker=ticker_data["ticker"],
                            name=ticker_data["name"],
                            market=ticker_data["market"],
                            is_active=True
                        )
                        session.add(new_ticker)
                        session.commit()
                except Exception as seed_err:
                    session.rollback()
                    logger.warning(f"Error seeding ticker {ticker_data['ticker']} (might already exist): {str(seed_err)}")
            logger.info("Database initialized and initial stock tickers seeded successfully.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {str(e)}")
        raise e


async def scheduled_crawler_task():
    """
    Background task that runs the crawler every day at 22:00 (AC 1).
    """
    logger.info("Starting background scheduled crawler task.")
    while True:
        try:
            now = datetime.now()
            # Target time is 22:00 today
            target_time = datetime.combine(now.date(), time(22, 0, 0))
            if now >= target_time:
                # If 22:00 has passed today, target tomorrow
                target_time += timedelta(days=1)
                
            sleep_seconds = (target_time - now).total_seconds()
            logger.info(f"Scheduled crawler: next run at {target_time.isoformat()} (sleeping for {sleep_seconds:.1f}s)")
            await asyncio.sleep(sleep_seconds)
            
            # Trigger ingestion
            logger.info("Triggering automatic daily stock data ingestion...")
            with Session(engine) as session:
                ingest_all_active_tickers(session)
            logger.info("Automatic daily stock data ingestion completed successfully.")
            
            # Wait at least 60 seconds before next loop to avoid double-triggering
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Background scheduled crawler task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in background scheduled crawler task: {str(e)}")
            # Sleep 5 minutes before retrying on general errors
            await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start background scheduler task
    scheduler_task = asyncio.create_task(scheduled_crawler_task())
    yield
    # Shutdown / clean up
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
        
    try:
        from app.core.neo4j import neo4j_manager
        neo4j_manager.close()
        logger.info("Neo4j driver closed successfully on shutdown.")
    except Exception as e:
        logger.error(f"Error closing Neo4j driver on shutdown: {str(e)}")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan
)

from app.api.v1.stocks import router as stocks_router
app.include_router(stocks_router, prefix="/api/v1/stocks", tags=["stocks"])

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
    # Allow Swagger UI/ReDoc to load assets by exempting their paths from default-src 'self'
    if not any(request.url.path.startswith(p) for p in ["/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"]):
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
def health_check(request: Request, session: Session = Depends(get_session)):
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
