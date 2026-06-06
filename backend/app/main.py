import uuid
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from sqlmodel import Session, select, SQLModel
from sqlalchemy import text
from datetime import datetime, time, timedelta

from app.core.config import settings
from app.core.logging import trace_id_var, logger
from app.core.exceptions import BaseAppException
from app.core.db import get_session, engine
from app.models.stock import StockTicker, StockPrice
from app.models.crawler_config import CrawlerConfig
from app.services.stock_data import ingest_all_active_tickers
from app.services.crawler import ingest_news_articles


def init_db():
    try:
        SQLModel.metadata.create_all(engine)
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if "news_articles" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("news_articles")]
            if any(c not in columns for c in ["sentiment_score", "raw_entities", "raw_relationships"]):
                with Session(engine) as session:
                    if "sentiment_score" not in columns:
                        session.execute(text("ALTER TABLE news_articles ADD COLUMN sentiment_score FLOAT"))
                    if "raw_entities" not in columns:
                        session.execute(text("ALTER TABLE news_articles ADD COLUMN raw_entities JSON"))
                    if "raw_relationships" not in columns:
                        session.execute(text("ALTER TABLE news_articles ADD COLUMN raw_relationships JSON"))
                    session.commit()
                logger.info("Migrated news_articles table structure successfully.")
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
            
            # Seed default CrawlerConfig if none exists
            try:
                config_stmt = select(CrawlerConfig)
                existing_config = session.exec(config_stmt).first()
                if not existing_config:
                    default_config = CrawlerConfig(id=1)
                    session.add(default_config)
                    session.commit()
                    logger.info("Seeded default CrawlerConfig.")
            except Exception as seed_config_err:
                session.rollback()
                logger.warning(f"Error seeding default CrawlerConfig: {str(seed_config_err)}")

            logger.info("Database initialized and initial stock tickers seeded successfully.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {str(e)}")
        raise e


def get_crawler_config_from_db() -> tuple[str, str]:
    with Session(engine) as session:
        config = session.exec(select(CrawlerConfig)).first()
        if not config:
            return "22:00", "cafef,vneconomy,vietstock,tuoitre,thanhnien,vnbusiness,ndh"
        return config.schedule_time, config.active_sources


async def scheduled_crawler_task(event: Optional[asyncio.Event] = None):
    """
    Background task that runs the crawler dynamically based on settings in database (AC 3, 4, 5).
    """
    logger.info("Starting background scheduled crawler task.")
    from datetime import timezone as dt_timezone, timedelta as dt_timedelta
    ICT = dt_timezone(dt_timedelta(hours=7))
    last_run_date = None
    while True:
        try:
            # Generate and set trace_id for automatic scheduler run
            trace_id = f"sched-{uuid.uuid4()}"
            token = trace_id_var.set(trace_id)
            
            try:
                # 1. Fetch CrawlerConfig safely in thread
                schedule_time_str, active_sources = await asyncio.to_thread(get_crawler_config_from_db)
                
                try:
                    h, m = map(int, schedule_time_str.split(":"))
                    target_tod = time(h, m, 0)
                except Exception as parse_err:
                    logger.error(f"Error parsing schedule time {schedule_time_str}, fallback to 22:00: {parse_err}")
                    target_tod = time(22, 0, 0)
                    
                now = datetime.now(dt_timezone.utc).astimezone(ICT)
                target_time = datetime.combine(now.date(), target_tod, tzinfo=ICT)
                if last_run_date == now.date():
                    target_time += timedelta(days=1)
                    
                sleep_seconds = (target_time - now).total_seconds()
                if sleep_seconds < 0:
                    sleep_seconds = 0.1
                logger.info(f"Scheduled crawler: next run at {target_time.isoformat()} (sleeping for {sleep_seconds:.1f}s, active sources: {active_sources})")
            finally:
                trace_id_var.reset(token)

            # Wait asynchronously for event or timeout
            if event:
                try:
                    # max(0.1, sleep_seconds) prevents negative/too-small timeout which raises TimeoutError immediately
                    await asyncio.wait_for(event.wait(), timeout=max(0.1, sleep_seconds))
                    # Event was set! Clear immediately to avoid missing next update
                    event.clear()
                    logger.info("Scheduler configuration update event detected. Reloading config...")
                    continue
                except asyncio.TimeoutError:
                    # Timeout reached, proceed to ingestion
                    logger.info("Schedule timeout reached. Triggering automatic crawler run...")
            else:
                await asyncio.sleep(sleep_seconds)

            # Set trace_id for ingestion execution
            token = trace_id_var.set(trace_id)
            try:
                logger.info("Triggering automatic daily stock data and news ingestion...")
                
                def run_ticker_ingestion():
                    with Session(engine) as session:
                        ingest_all_active_tickers(session)

                def run_news_ingestion(sources_str):
                    with Session(engine) as session:
                        ingest_news_articles(session, active_sources=sources_str)

                # Run in separate threads concurrently to keep event loop responsive
                await asyncio.gather(
                    asyncio.to_thread(run_ticker_ingestion),
                    asyncio.to_thread(run_news_ingestion, active_sources)
                )

                def run_ai_pipeline():
                    from app.services.ai_pipeline import process_pending_news_articles
                    with Session(engine) as session:
                        process_pending_news_articles(session)

                logger.info("Triggering automatic AI pipeline for ingested news...")
                await asyncio.to_thread(run_ai_pipeline)

                last_run_date = now.date()
                logger.info("Automatic daily stock data, news ingestion, and AI processing completed successfully.")
            finally:
                trace_id_var.reset(token)
            
            # Wait at least 60 seconds before next loop to avoid double-triggering
            if event:
                try:
                    await asyncio.wait_for(event.wait(), timeout=60.0)
                    event.clear()
                    logger.info("Configuration updated during cooldown. Reloading...")
                except asyncio.TimeoutError:
                    pass
            else:
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Background scheduled crawler task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in background scheduled crawler task: {str(e)}")
            # Sleep 5 minutes before retrying on general errors (or can be interrupted by event)
            if event:
                try:
                    await asyncio.wait_for(event.wait(), timeout=300.0)
                    event.clear()
                except asyncio.TimeoutError:
                    pass
            else:
                await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the scheduler update event in app.state
    loop = asyncio.get_running_loop()
    app.state.scheduler_update_event = asyncio.Event()
    app.state.scheduler_update_loop = loop
    init_db()
    # Start background scheduler task
    scheduler_task = asyncio.create_task(scheduled_crawler_task(app.state.scheduler_update_event))
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


from app.core.limiter import limiter

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan
)

from app.api.v1.stocks import router as stocks_router
from app.api.v1.news import router as news_router
from app.api.v1.settings import router as settings_router
app.include_router(stocks_router, prefix="/api/v1/stocks", tags=["stocks"])
app.include_router(news_router, prefix="/api/v1/news", tags=["news"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["settings"])

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
