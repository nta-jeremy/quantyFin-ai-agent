import time
import pandas as pd
from typing import Optional
from datetime import datetime, date, timedelta, timezone
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.stock import StockTicker, StockPrice
from app.core.exceptions import CrawlerException
from app.core.logging import logger

def fetch_stock_prices(ticker: str, start_date: str, end_date: str) -> list[dict]:
    """
    Fetch OHLCV historical prices for a stock ticker from vnstock.
    Tries multiple sources (VCI, TCBS) for maximum reliability (especially VNINDEX).
    """
    sources = ['VCI', 'TCBS']
    last_err = None
    for source in sources:
        try:
            logger.info(f"Fetching stock prices for ticker={ticker} from source={source} ({start_date} to {end_date})")
            from vnstock import Vnstock
            stock = Vnstock().stock(symbol=ticker, source=source)
            df = stock.quote.history(start=start_date, end=end_date, interval='1D')
            
            if df is None or df.empty:
                logger.warning(f"No price data returned for ticker={ticker} from source={source}")
                continue
                
            prices = []
            # Standardize column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Check if date/time column is present
            date_col = None
            for col in ['time', 'date', 'datetime']:
                if col in df.columns:
                    date_col = col
                    break
                    
            if not date_col:
                raise CrawlerException(f"Could not find date column in vnstock DataFrame. Columns: {list(df.columns)}")
                
            # Verify required columns are present (EH6)
            required_cols = {"open", "high", "low", "close", "volume"}
            if not required_cols.issubset(df.columns):
                raise CrawlerException(f"Missing required columns in vnstock DataFrame: {required_cols - set(df.columns)}")

            for _, row in df.iterrows():
                try:
                    # Parse date
                    raw_date = row[date_col]
                    if isinstance(raw_date, (date, datetime)):
                        parsed_date = raw_date if isinstance(raw_date, date) else raw_date.date()
                    elif hasattr(raw_date, "to_pydatetime"): # pandas Timestamp
                        parsed_date = raw_date.to_pydatetime().date()
                    else:
                        parsed_date = pd.to_datetime(raw_date).date()
                    
                    prices.append({
                        "date": parsed_date,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": int(row["volume"])
                    })
                except Exception as row_err:
                    logger.error(f"Error parsing row {row.to_dict()} for ticker {ticker}: {str(row_err)}")
                    continue
            
            if prices:
                return prices
        except Exception as e:
            logger.warning(f"Error fetching stock prices for {ticker} from source={source}: {str(e)}")
            last_err = e
            continue
            
    if last_err:
        logger.exception(f"All sources failed for {ticker}. Last error: {str(last_err)}")
        if isinstance(last_err, CrawlerException):
            raise last_err
        raise CrawlerException(f"Lỗi khi cào dữ liệu giá của mã {ticker}: {str(last_err)}")
        
    return []


def upsert_stock_prices(session: Session, prices: list[dict]):
    """
    Upsert stock prices into the database, handling ON CONFLICT.
    Safer checking on dialect name and transaction savepoint handling (EH5, BH11).
    """
    if not prices:
        return
        
    try:
        with session.begin_nested():
            bind = session.get_bind()
            if bind and bind.dialect.name == "postgresql":
                # Fast PostgreSQL upsert using ON CONFLICT
                stmt = pg_insert(StockPrice).values(prices)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["ticker_id", "date"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                        "updated_at": func.now()
                    }
                )
                session.exec(stmt)
            else:
                # Fallback for SQLite and other databases (used in tests) (EH5)
                for p in prices:
                    statement = select(StockPrice).where(
                        StockPrice.ticker_id == p["ticker_id"],
                        StockPrice.date == p["date"]
                    )
                    existing = session.exec(statement).first()
                    if existing:
                        existing.open = p["open"]
                        existing.high = p["high"]
                        existing.low = p["low"]
                        existing.close = p["close"]
                        existing.volume = p["volume"]
                        existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None) # BH12
                        session.add(existing)
                    else:
                        new_price = StockPrice(**p)
                        session.add(new_price)
        session.commit()
    except Exception as e:
        logger.error(f"Error upserting stock prices: {str(e)}")
        raise e


def ingest_all_active_tickers(session: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Ingest OHLCV prices for all active tickers and VNINDEX.
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
    # Get all active tickers
    statement = select(StockTicker).where(StockTicker.is_active == True)
    active_tickers = session.exec(statement).all()
    
    results = {
        "success_count": 0,
        "failed_tickers": [],
        "details": {}
    }
    
    for ticker_obj in active_tickers:
        ticker = ticker_obj.ticker
        try:
            prices = fetch_stock_prices(ticker, start_date, end_date)
            if prices:
                # Add ticker_id to each price dict
                for price_dict in prices:
                    price_dict["ticker_id"] = ticker_obj.id
                
                upsert_stock_prices(session, prices)
                results["success_count"] += 1
                results["details"][ticker] = f"Successfully upserted {len(prices)} price records."
            else:
                results["details"][ticker] = "No data returned."
        except Exception as e:
            logger.error(f"Failed to ingest ticker {ticker}: {str(e)}")
            results["failed_tickers"].append(ticker)
            results["details"][ticker] = f"Error: {str(e)}"
            
        # Delay to avoid IP blocking (1.5 seconds)
        time.sleep(1.5)
        
    # Raise CrawlerException if 100% of crawls failed (AA3)
    if len(active_tickers) > 0 and results["success_count"] == 0:
        raise CrawlerException("Toàn bộ tiến trình cào dữ liệu cho tất cả các mã chứng khoán đều thất bại.")
        
    return results
