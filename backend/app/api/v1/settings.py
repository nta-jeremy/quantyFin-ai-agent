import re
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.logging import trace_id_var, logger
from app.core.exceptions import BadRequestException
from app.models.crawler_config import CrawlerConfig

router = APIRouter()

SUPPORTED_SOURCES_MAP = {
    "cafef": "CafeF",
    "vneconomy": "VnEconomy",
    "vietstock": "Vietstock",
    "tuoitre": "TuoiTre",
    "thanhnien": "ThanhNien",
    "vnbusiness": "VnBusiness",
    "ndh": "NDH"
}

class CrawlerConfigUpdate(BaseModel):
    schedule_time: str = Field(..., description="Thời gian chạy định dạng HH:MM (00:00 - 23:59)")
    active_sources: str = Field(..., description="Danh sách các nguồn cào hoạt động, phân tách bằng dấu phẩy")

@router.get("/crawler")
def get_crawler_settings(session: Session = Depends(get_session)):
    try:
        stmt = select(CrawlerConfig)
        config = session.exec(stmt).first()
        if not config:
            # Fallback if not seeded (do not write to DB on GET)
            config = CrawlerConfig()
        
        
        return {
            "data": {
                "id": config.id,
                "schedule_time": config.schedule_time,
                "active_sources": config.active_sources,
                "supported_sources": list(SUPPORTED_SOURCES_MAP.values())
            },
            "error": None,
            "meta": {
                "trace_id": trace_id_var.get()
            }
        }
    except Exception as e:
        logger.error(f"Error getting crawler config: {str(e)}")
        raise e

@router.put("/crawler")
def update_crawler_settings(
    request: Request,
    payload: CrawlerConfigUpdate,
    session: Session = Depends(get_session)
):
    # 1. Validate schedule_time
    time_pattern = r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
    if not re.match(time_pattern, payload.schedule_time.strip()):
        raise BadRequestException("Định dạng schedule_time phải là HH:MM từ 00:00 đến 23:59")

    # 2. Validate active_sources
    source_list = list(dict.fromkeys([s.strip().lower() for s in payload.active_sources.split(",") if s.strip()]))
    if not source_list:
        raise BadRequestException("active_sources không được để trống")

    for src in source_list:
        if src not in SUPPORTED_SOURCES_MAP:
            raise BadRequestException(f"Nguồn cào không hợp lệ: {src}. Các nguồn được hỗ trợ: {', '.join(SUPPORTED_SOURCES_MAP.keys())}")

    cleaned_sources = ",".join(source_list)

    try:
        stmt = select(CrawlerConfig)
        config = session.exec(stmt).first()
        if not config:
            config = CrawlerConfig(
                schedule_time=payload.schedule_time.strip(),
                active_sources=cleaned_sources
            )
            session.add(config)
        else:
            config.schedule_time = payload.schedule_time.strip()
            config.active_sources = cleaned_sources
            session.add(config)
        
        session.commit()
        session.refresh(config)

        # 3. Trigger scheduler event to recalculate schedule
        if hasattr(request.app.state, "scheduler_update_event") and request.app.state.scheduler_update_event is not None:
            event = request.app.state.scheduler_update_event
            loop = getattr(request.app.state, "scheduler_update_loop", None)
            if loop is not None:
                loop.call_soon_threadsafe(event.set)
            else:
                event.set()
            logger.info("Scheduler update event triggered thread-safely after config update.")

        return {
            "data": {
                "id": config.id,
                "schedule_time": config.schedule_time,
                "active_sources": config.active_sources,
                "supported_sources": list(SUPPORTED_SOURCES_MAP.values())
            },
            "error": None,
            "meta": {
                "trace_id": trace_id_var.get()
            }
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating crawler config: {str(e)}")
        raise e
