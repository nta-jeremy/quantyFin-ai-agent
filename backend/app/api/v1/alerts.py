from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, select
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import datetime as dt
from sqlalchemy.orm import selectinload

from app.core.db import get_session
from app.core.logging import trace_id_var, logger
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.alert import AlertRule, TriggeredAlert
from app.models.stock import StockTicker
from app.services.risk_monitor import check_and_trigger_alerts

router = APIRouter()

# Input Validation Models
class AlertRuleCreate(BaseModel):
    ticker_id: int = Field(..., alias="tickerId")
    price_threshold: float = Field(-0.03, alias="priceThreshold")
    sentiment_threshold: float = Field(-0.5, alias="sentimentThreshold")
    is_active: bool = Field(True, alias="isActive")

    @field_validator("price_threshold")
    @classmethod
    def validate_price_threshold(cls, v: float) -> float:
        if v > 0.0:
            raise ValueError("Ngưỡng biến động giá (priceThreshold) phải là số âm hoặc bằng 0 (ví dụ: -0.03 đại diện cho giảm 3%)")
        return v

    @field_validator("sentiment_threshold")
    @classmethod
    def validate_sentiment_threshold(cls, v: float) -> float:
        if not (-1.0 <= v <= 1.0):
            raise ValueError("Ngưỡng điểm cảm xúc (sentimentThreshold) phải nằm trong khoảng [-1.0, 1.0]")
        return v

    class Config:
        populate_by_name = True


# Response Serializer Models
class MetaModel(BaseModel):
    trace_id: Optional[str] = Field(None, alias="trace_id")

class AlertRuleResponse(BaseModel):
    id: int
    ticker_id: int = Field(..., alias="tickerId")
    ticker: Optional[str] = None
    price_threshold: float = Field(..., alias="priceThreshold")
    sentiment_threshold: float = Field(..., alias="sentimentThreshold")
    is_active: bool = Field(..., alias="isActive")
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")

    class Config:
        populate_by_name = True
        from_attributes = True

class AlertRulesListResponse(BaseModel):
    data: List[AlertRuleResponse]
    error: Optional[str] = None
    meta: MetaModel

class TriggeredAlertResponse(BaseModel):
    id: int
    rule_id: Optional[int] = Field(None, alias="ruleId")
    ticker: str
    level: str
    title: str
    message: str
    is_dismissed: bool = Field(..., alias="isDismissed")
    triggered_at: Optional[str] = Field(None, alias="triggeredAt")

    class Config:
        populate_by_name = True
        from_attributes = True

class TriggeredAlertsListResponse(BaseModel):
    data: List[TriggeredAlertResponse]
    error: Optional[str] = None
    meta: MetaModel

class DismissAlertResponseData(BaseModel):
    id: int
    is_dismissed: bool = Field(..., alias="isDismissed")

    class Config:
        populate_by_name = True
        from_attributes = True

class DismissAlertResponse(BaseModel):
    data: DismissAlertResponseData
    error: Optional[str] = None
    meta: MetaModel

class CreateUpdateRuleResponse(BaseModel):
    data: AlertRuleResponse
    error: Optional[str] = None
    meta: MetaModel


@router.get("", response_model=TriggeredAlertsListResponse)
async def get_alerts(
    is_dismissed: Optional[bool] = Query(None, alias="isDismissed"),
    level: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Lấy danh sách các cảnh báo đã kích hoạt, hỗ trợ bộ lọc và định dạng camelCase.
    """
    try:
        stmt = select(TriggeredAlert)
        
        if is_dismissed is not None:
            stmt = stmt.where(TriggeredAlert.is_dismissed == is_dismissed)
        if level:
            stmt = stmt.where(TriggeredAlert.level == level)
        if ticker:
            stmt = stmt.where(TriggeredAlert.ticker == ticker.upper().strip())
            
        stmt = stmt.order_by(TriggeredAlert.triggered_at.desc())
        alerts = session.exec(stmt).all()
        
        items = []
        for a in alerts:
            items.append(
                TriggeredAlertResponse(
                    id=a.id,
                    ruleId=a.rule_id,
                    ticker=a.ticker,
                    level=a.level,
                    title=a.title,
                    message=a.message,
                    isDismissed=a.is_dismissed,
                    triggeredAt=a.triggered_at.isoformat() if a.triggered_at else None
                )
            )
        
        return TriggeredAlertsListResponse(
            data=items,
            error=None,
            meta=MetaModel(trace_id=trace_id_var.get())
        )
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi lấy danh sách cảnh báo: {str(e)}")
        raise e


@router.post("/{alert_id}/dismiss", response_model=DismissAlertResponse)
async def dismiss_alert(alert_id: int, session: Session = Depends(get_session)):
    """
    Đóng (dismiss) cảnh báo theo ID.
    """
    try:
        alert = session.get(TriggeredAlert, alert_id)
        if not alert:
            raise NotFoundException(f"Không tìm thấy cảnh báo rủi ro với ID {alert_id}")
            
        alert.is_dismissed = True
        session.add(alert)
        session.commit()
        session.refresh(alert)
        
        return DismissAlertResponse(
            data=DismissAlertResponseData(
                id=alert.id,
                isDismissed=alert.is_dismissed
            ),
            error=None,
            meta=MetaModel(trace_id=trace_id_var.get())
        )
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi đóng cảnh báo ID {alert_id}: {str(e)}")
        raise e


@router.get("/rules", response_model=AlertRulesListResponse)
async def get_rules(session: Session = Depends(get_session)):
    """
    Lấy danh sách các luật cấu hình cảnh báo.
    """
    try:
        stmt = select(AlertRule).options(selectinload(AlertRule.ticker)).order_by(AlertRule.id.asc())
        rules = session.exec(stmt).all()
        
        items = []
        for r in rules:
            items.append(
                AlertRuleResponse(
                    id=r.id,
                    tickerId=r.ticker_id,
                    ticker=r.ticker.ticker if r.ticker else None,
                    priceThreshold=r.price_threshold,
                    sentimentThreshold=r.sentiment_threshold,
                    isActive=r.is_active,
                    createdAt=r.created_at.isoformat() if r.created_at else None,
                    updatedAt=r.updated_at.isoformat() if r.updated_at else None
                )
            )
        
        return AlertRulesListResponse(
            data=items,
            error=None,
            meta=MetaModel(trace_id=trace_id_var.get())
        )
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi lấy danh sách luật cảnh báo: {str(e)}")
        raise e


@router.post("/rules", response_model=CreateUpdateRuleResponse)
async def create_or_update_rule(payload: AlertRuleCreate, session: Session = Depends(get_session)):
    """
    Tạo mới hoặc cập nhật luật cấu hình cảnh báo cho một mã cổ phiếu.
    """
    try:
        ticker = session.get(StockTicker, payload.ticker_id)
        if not ticker:
            raise NotFoundException(f"Không tìm thấy mã cổ phiếu với ID {payload.ticker_id}")
            
        # Tìm xem đã có luật cho ticker_id này chưa
        stmt = select(AlertRule).where(AlertRule.ticker_id == payload.ticker_id)
        rule = session.exec(stmt).first()
        
        if rule:
            # Cập nhật
            rule.price_threshold = payload.price_threshold
            rule.sentiment_threshold = payload.sentiment_threshold
            rule.is_active = payload.is_active
            rule.updated_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
            logger.info(f"Cập nhật luật cảnh báo ID {rule.id} cho ticker {ticker.ticker}")
        else:
            # Tạo mới
            rule = AlertRule(
                ticker_id=payload.ticker_id,
                price_threshold=payload.price_threshold,
                sentiment_threshold=payload.sentiment_threshold,
                is_active=payload.is_active
            )
            logger.info(f"Tạo mới luật cảnh báo cho ticker {ticker.ticker}")
            
        session.add(rule)
        session.commit()
        session.refresh(rule)
        
        return CreateUpdateRuleResponse(
            data=AlertRuleResponse(
                id=rule.id,
                tickerId=rule.ticker_id,
                priceThreshold=rule.price_threshold,
                sentimentThreshold=rule.sentiment_threshold,
                isActive=rule.is_active,
                createdAt=rule.created_at.isoformat() if rule.created_at else None,
                updatedAt=rule.updated_at.isoformat() if rule.updated_at else None
            ),
            error=None,
            meta=MetaModel(trace_id=trace_id_var.get())
        )
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi tạo/cập nhật luật cảnh báo: {str(e)}")
        raise e


@router.post("/process-monitor", response_model=TriggeredAlertsListResponse)
async def trigger_risk_monitor(session: Session = Depends(get_session)):
    """
    Kích hoạt quét rủi ro thủ công và trả về danh sách cảnh báo mới vừa được tạo.
    """
    try:
        logger.info("Kích hoạt quét rủi ro thủ công qua API.")
        alerts = check_and_trigger_alerts(session)
        
        items = []
        for a in alerts:
            items.append(
                TriggeredAlertResponse(
                    id=a.id,
                    ruleId=a.rule_id,
                    ticker=a.ticker,
                    level=a.level,
                    title=a.title,
                    message=a.message,
                    isDismissed=a.is_dismissed,
                    triggeredAt=a.triggered_at.isoformat() if a.triggered_at else None
                )
            )
        
        return TriggeredAlertsListResponse(
            data=items,
            error=None,
            meta=MetaModel(trace_id=trace_id_var.get())
        )
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi kích hoạt quét rủi ro thủ công: {str(e)}")
        raise e
