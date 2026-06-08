from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from datetime import date, datetime, timedelta
from typing import Optional

from app.core.db import get_session
from app.core.logging import trace_id_var, logger
from app.core.exceptions import BadRequestException
from app.models.stock import StockTicker, StockPrice
from app.services.stock_data import ingest_all_active_tickers

router = APIRouter()

@router.post("/ingest")
def trigger_ingestion(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    """
    Trigger ingestion of stock data manually for all active tickers.
    """
    # Date validations
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise BadRequestException("Định dạng start_date phải là YYYY-MM-DD")
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise BadRequestException("Định dạng end_date phải là YYYY-MM-DD")
            
    if start_dt and end_dt:
        if start_dt > end_dt:
            raise BadRequestException("start_date không được lớn hơn end_date")

    try:
        stats = ingest_all_active_tickers(session, start_date, end_date)
        return {
            "data": {
                "successCount": stats["success_count"],
                "failedTickers": stats["failed_tickers"],
                "details": stats["details"]
            },
            "error": None,
            "meta": {
                "trace_id": trace_id_var.get()
            }
        }
    except Exception as e:
        logger.error(f"Error during manual ingestion: {str(e)}")
        raise e


@router.get("/tickers")
async def get_tickers(session: Session = Depends(get_session)):
    """
    Retrieve all stock tickers being monitored.
    """
    statement = select(StockTicker)
    tickers = session.exec(statement).all()
    return {
        "data": [
            {
                "id": t.id,
                "ticker": t.ticker,
                "name": t.name,
                "market": t.market,
                "isActive": t.is_active
            }
            for t in tickers
        ],
        "error": None,
        "meta": {
            "trace_id": trace_id_var.get()
        }
    }


@router.get("/prices")
async def get_prices(
    ticker: str = Query(..., description="Stock ticker (e.g. VNM, VIC, VNINDEX)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    """
    Retrieve historical price data for a stock ticker.
    """
    # Check if ticker exists
    ticker = ticker.upper().strip()
    ticker_stmt = select(StockTicker).where(StockTicker.ticker == ticker)
    ticker_obj = session.exec(ticker_stmt).first()
    if not ticker_obj:
        raise BadRequestException(f"Không tìm thấy mã chứng khoán {ticker}")

    # Parse and validate dates
    start_d = None
    end_d = None
    if start_date:
        try:
            start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise BadRequestException("Định dạng start_date phải là YYYY-MM-DD")
    else:
        start_d = (datetime.now() - timedelta(days=30)).date()

    if end_date:
        try:
            end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise BadRequestException("Định dạng end_date phải là YYYY-MM-DD")
    else:
        end_d = datetime.now().date()
        
    if start_d and end_d:
        if start_d > end_d:
            raise BadRequestException("start_date không được lớn hơn end_date")

    # Query price history
    price_stmt = select(StockPrice).where(
        StockPrice.ticker_id == ticker_obj.id,
        StockPrice.date >= start_d,
        StockPrice.date <= end_d
    ).order_by(StockPrice.date.asc())
    
    prices = session.exec(price_stmt).all()
    
    return {
        "data": [
            {
                "id": p.id,
                "tickerId": p.ticker_id,
                "date": p.date.strftime("%Y-%m-%d"),
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume
            }
            for p in prices
        ],
        "error": None,
        "meta": {
            "trace_id": trace_id_var.get()
        }
    }
