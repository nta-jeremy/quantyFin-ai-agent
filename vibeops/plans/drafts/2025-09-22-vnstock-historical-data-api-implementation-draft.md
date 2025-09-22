# Vnstock Historical Data API Implementation Draft

**Date:** 2025-09-22  
**Author:** AI Assistant  
**Status:** Draft  
**Priority:** High  

## Executive Summary

This document outlines the comprehensive implementation plan for integrating vnstock historical data API capabilities into the quantyFin-ai-agent system. The implementation will extend the current Vietnamese market data functionality to support advanced historical data retrieval, multiple asset types, various time intervals, and international market data.

## Table of Contents

1. [Research Findings](#research-findings)
2. [Current State Analysis](#current-state-analysis)
3. [Implementation Plan](#implementation-plan)
4. [Technical Architecture](#technical-architecture)
5. [API Design](#api-design)
6. [Domain Models](#domain-models)
7. [Implementation Tasks](#implementation-tasks)
8. [Testing Strategy](#testing-strategy)
9. [Performance Considerations](#performance-considerations)
10. [Future Enhancements](#future-enhancements)

## Research Findings

### Vnstock Historical Data Capabilities

Based on comprehensive research using Context7 and web search, vnstock provides extensive historical data functionality:

#### 1. Data Sources
- **VCI**: Primary Vietnamese market data source with comprehensive coverage
- **TCBS**: Alternative Vietnamese market data source
- **MSN**: International market data (forex, world indices, crypto)

#### 2. Supported Asset Types
- **Vietnamese Stocks**: All listed companies on HOSE, HNX, UPCOM
- **Indices**: VNINDEX, HNXINDEX, UPCOMINDEX, VN30, HNX30
- **Futures Contracts**: VN30F1M, VN30F2411 (supports both naming conventions)
- **Warrants**: CFPT2314 and other covered warrants
- **Bonds**: Listed bonds like CII424002 (VCI source only)
- **ETFs**: E1VFVN30 and other exchange-traded funds
- **Forex Pairs**: USDVND, JPYVND, USDEUR, etc.
- **World Indices**: DJI, INX, COMP, RUT, UKX, DAX, N225, HSI, etc.
- **Cryptocurrencies**: BTC, ETH, and other major cryptocurrencies

#### 3. Time Intervals
- **Intraday**: 1m, 5m, 15m, 30m, 1H
- **Daily**: 1D (default)
- **Weekly**: 1W
- **Monthly**: 1M

#### 4. Data Format (OHLCVT)
- **Open**: Opening price
- **High**: Highest price
- **Low**: Lowest price
- **Close**: Closing price
- **Volume**: Trading volume
- **Time**: Timestamp

#### 5. Key Features
- Real-time data during trading hours
- Historical data with adjustable date ranges
- Multiple data source fallback support
- Caching capabilities
- Rate limiting and retry mechanisms
- Support for both Vietnamese and English languages

## Current State Analysis

### Existing Implementation

The current codebase already has a solid foundation:

#### 1. VnstockAdapter Abstract Base Class
- Located: `app/infrastructure/data_sources/vnstock_adapter.py`
- Provides abstract methods for historical data, company info, financial reports
- Includes retry logic, rate limiting, and error handling
- Supports multiple data sources (VCI, TCBS, MSN)

#### 2. VietnameseMarketService
- Located: `app/core/application/vietnamese_market_service.py`
- Orchestrates multiple data sources with fallback support
- Implements business logic for market data operations
- Provides unified interface for different data sources

#### 3. Domain Models
- Located: `app/core/domain/`
- Comprehensive models for Vietnamese market data
- Support for company information, financial reports, stock data
- Listing models for symbols, industries, exchanges

### Identified Gaps

1. **Limited Historical Data Support**: Current implementation focuses on basic historical data without advanced features
2. **No International Market Support**: Missing forex, world indices, and crypto data
3. **Limited Time Interval Support**: Only basic daily data supported
4. **No Intraday Data**: Missing real-time and intraday trading data
5. **Limited Asset Type Support**: Missing futures, warrants, bonds, ETFs
6. **No Advanced Caching**: Basic caching without sophisticated strategies
7. **Limited API Endpoints**: Missing comprehensive historical data endpoints

## Implementation Plan

### Phase 1: Enhanced Historical Data Models

#### 1.1 Historical Data Models
Create comprehensive models for historical data:

```python
# app/core/domain/historical_models.py

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

class TimeInterval(str, Enum):
    """Supported time intervals for historical data."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1H"
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1M"

class AssetType(str, Enum):
    """Supported asset types."""
    STOCK = "stock"
    INDEX = "index"
    FUTURES = "futures"
    WARRANT = "warrant"
    BOND = "bond"
    ETF = "etf"
    FOREX = "forex"
    CRYPTO = "crypto"
    WORLD_INDEX = "world_index"

class OHLCVTData(BaseModel):
    """OHLCVT historical data point."""
    time: datetime = Field(..., description="Timestamp")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="Highest price")
    low: float = Field(..., ge=0, description="Lowest price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

class HistoricalDataRequest(BaseModel):
    """Request model for historical data."""
    symbol: str = Field(..., min_length=1, description="Asset symbol")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    interval: TimeInterval = Field(TimeInterval.DAY_1, description="Time interval")
    asset_type: AssetType = Field(AssetType.STOCK, description="Asset type")
    data_source: Optional[str] = Field(None, description="Preferred data source")

class HistoricalDataResponse(BaseModel):
    """Response model for historical data."""
    symbol: str = Field(..., description="Asset symbol")
    asset_type: AssetType = Field(..., description="Asset type")
    data_source: str = Field(..., description="Data source used")
    interval: TimeInterval = Field(..., description="Time interval")
    data: List[OHLCVTData] = Field(..., description="Historical data points")
    total_records: int = Field(..., description="Total number of records")
    retrieved_at: datetime = Field(..., description="Retrieval timestamp")
```

#### 1.2 International Market Models
Create models for international market data:

```python
# app/core/domain/international_models.py

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class ForexPair(BaseModel):
    """Forex pair information."""
    symbol: str = Field(..., description="Forex pair symbol (e.g., USDVND)")
    base_currency: str = Field(..., description="Base currency")
    quote_currency: str = Field(..., description="Quote currency")
    symbol_id: Optional[str] = Field(None, description="Symbol ID for MSN source")

class WorldIndex(BaseModel):
    """World index information."""
    symbol: str = Field(..., description="Index symbol (e.g., DJI)")
    name: str = Field(..., description="Index name")
    country: str = Field(..., description="Country")
    symbol_id: Optional[str] = Field(None, description="Symbol ID for MSN source")

class CryptoCurrency(BaseModel):
    """Cryptocurrency information."""
    symbol: str = Field(..., description="Crypto symbol (e.g., BTC)")
    name: str = Field(..., description="Cryptocurrency name")
    symbol_id: Optional[str] = Field(None, description="Symbol ID for MSN source")
```

### Phase 2: Enhanced Vnstock Adapters

#### 2.1 Historical Data Adapter
Extend the VnstockAdapter with comprehensive historical data support:

```python
# app/infrastructure/data_sources/vnstock_historical_adapter.py

from typing import List, Optional
from datetime import datetime
from vnstock import Vnstock, Quote
from app.core.domain.historical_models import (
    HistoricalDataRequest,
    HistoricalDataResponse,
    OHLCVTData,
    TimeInterval,
    AssetType
)

class VnstockHistoricalAdapter:
    """Enhanced adapter for vnstock historical data."""
    
    def __init__(self, data_source: str = "VCI"):
        self.data_source = data_source
        self.vnstock = Vnstock()
    
    async def get_historical_data(
        self, 
        request: HistoricalDataRequest
    ) -> HistoricalDataResponse:
        """Get historical data for any supported asset type."""
        
        if request.asset_type == AssetType.STOCK:
            return await self._get_stock_data(request)
        elif request.asset_type == AssetType.INDEX:
            return await self._get_index_data(request)
        elif request.asset_type == AssetType.FUTURES:
            return await self._get_futures_data(request)
        elif request.asset_type == AssetType.WARRANT:
            return await self._get_warrant_data(request)
        elif request.asset_type == AssetType.BOND:
            return await self._get_bond_data(request)
        elif request.asset_type == AssetType.ETF:
            return await self._get_etf_data(request)
        elif request.asset_type == AssetType.FOREX:
            return await self._get_forex_data(request)
        elif request.asset_type == AssetType.CRYPTO:
            return await self._get_crypto_data(request)
        elif request.asset_type == AssetType.WORLD_INDEX:
            return await self._get_world_index_data(request)
        else:
            raise ValueError(f"Unsupported asset type: {request.asset_type}")
    
    async def _get_stock_data(self, request: HistoricalDataRequest) -> HistoricalDataResponse:
        """Get Vietnamese stock historical data."""
        stock = self.vnstock.stock(symbol=request.symbol, source=self.data_source)
        df = stock.quote.history(
            start=request.start_date.strftime('%Y-%m-%d'),
            end=request.end_date.strftime('%Y-%m-%d'),
            interval=request.interval.value
        )
        
        data = [
            OHLCVTData(
                time=row['time'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            for _, row in df.iterrows()
        ]
        
        return HistoricalDataResponse(
            symbol=request.symbol,
            asset_type=request.asset_type,
            data_source=self.data_source,
            interval=request.interval,
            data=data,
            total_records=len(data),
            retrieved_at=datetime.now()
        )
    
    async def _get_forex_data(self, request: HistoricalDataRequest) -> HistoricalDataResponse:
        """Get forex historical data."""
        fx = self.vnstock.fx(symbol=request.symbol, source='MSN')
        df = fx.quote.history(
            start=request.start_date.strftime('%Y-%m-%d'),
            end=request.end_date.strftime('%Y-%m-%d'),
            interval=request.interval.value
        )
        
        # Convert to OHLCVTData format
        data = [
            OHLCVTData(
                time=row['time'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=0  # Forex doesn't have volume
            )
            for _, row in df.iterrows()
        ]
        
        return HistoricalDataResponse(
            symbol=request.symbol,
            asset_type=request.asset_type,
            data_source='MSN',
            interval=request.interval,
            data=data,
            total_records=len(data),
            retrieved_at=datetime.now()
        )
    
    # Similar methods for other asset types...
```

#### 2.2 Intraday Data Adapter
Create adapter for real-time and intraday data:

```python
# app/infrastructure/data_sources/vnstock_intraday_adapter.py

from typing import List, Optional
from datetime import datetime
from vnstock import Vnstock
from app.core.domain.historical_models import OHLCVTData

class VnstockIntradayAdapter:
    """Adapter for real-time and intraday data."""
    
    def __init__(self, data_source: str = "VCI"):
        self.data_source = data_source
        self.vnstock = Vnstock()
    
    async def get_intraday_data(
        self, 
        symbol: str, 
        page_size: int = 10000
    ) -> List[OHLCVTData]:
        """Get intraday trading data."""
        stock = self.vnstock.stock(symbol=symbol, source=self.data_source)
        df = stock.quote.intraday(symbol=symbol, page_size=page_size, show_log=False)
        
        data = [
            OHLCVTData(
                time=row['time'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            for _, row in df.iterrows()
        ]
        
        return data
    
    async def get_real_time_quote(self, symbol: str) -> Optional[OHLCVTData]:
        """Get real-time quote."""
        stock = self.vnstock.stock(symbol=symbol, source=self.data_source)
        quote = stock.quote.price_board([symbol])
        
        if quote is not None and not quote.empty:
            row = quote.iloc[0]
            return OHLCVTData(
                time=datetime.now(),
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
        
        return None
```

### Phase 3: Enhanced Services

#### 3.1 Historical Data Service
Create a comprehensive service for historical data:

```python
# app/core/application/historical_data_service.py

from typing import List, Optional
from datetime import datetime, timedelta
from app.core.domain.historical_models import (
    HistoricalDataRequest,
    HistoricalDataResponse,
    TimeInterval,
    AssetType
)
from app.infrastructure.data_sources.vnstock_historical_adapter import VnstockHistoricalAdapter
from app.infrastructure.cache.redis_adapter import RedisAdapter

class HistoricalDataService:
    """Service for historical data operations."""
    
    def __init__(self, cache_adapter: Optional[RedisAdapter] = None):
        self.cache_adapter = cache_adapter
        self.vci_adapter = VnstockHistoricalAdapter("VCI")
        self.tcbs_adapter = VnstockHistoricalAdapter("TCBS")
        self.msn_adapter = VnstockHistoricalAdapter("MSN")
    
    async def get_historical_data(
        self, 
        request: HistoricalDataRequest
    ) -> HistoricalDataResponse:
        """Get historical data with caching and fallback support."""
        
        # Check cache first
        cache_key = self._generate_cache_key(request)
        if self.cache_adapter:
            cached_data = await self.cache_adapter.get(cache_key)
            if cached_data:
                return HistoricalDataResponse.parse_obj(cached_data)
        
        # Try different data sources based on asset type
        adapters = self._get_adapters_for_asset_type(request.asset_type)
        
        for adapter in adapters:
            try:
                data = await adapter.get_historical_data(request)
                
                # Cache the result
                if self.cache_adapter:
                    await self.cache_adapter.set(
                        cache_key, 
                        data.dict(), 
                        ttl=300  # 5 minutes
                    )
                
                return data
                
            except Exception as e:
                continue
        
        raise RuntimeError(f"Failed to fetch historical data for {request.symbol}")
    
    def _get_adapters_for_asset_type(self, asset_type: AssetType) -> List[VnstockHistoricalAdapter]:
        """Get appropriate adapters for asset type."""
        if asset_type in [AssetType.FOREX, AssetType.CRYPTO, AssetType.WORLD_INDEX]:
            return [self.msn_adapter]
        else:
            return [self.vci_adapter, self.tcbs_adapter]
    
    def _generate_cache_key(self, request: HistoricalDataRequest) -> str:
        """Generate cache key for request."""
        return f"historical_data:{request.symbol}:{request.asset_type.value}:{request.interval.value}:{request.start_date.strftime('%Y%m%d')}:{request.end_date.strftime('%Y%m%d')}"
```

#### 3.2 International Market Service
Create service for international market data:

```python
# app/core/application/international_market_service.py

from typing import List, Optional
from app.core.domain.international_models import ForexPair, WorldIndex, CryptoCurrency
from app.core.domain.historical_models import HistoricalDataRequest, AssetType
from app.infrastructure.data_sources.vnstock_historical_adapter import VnstockHistoricalAdapter

class InternationalMarketService:
    """Service for international market data."""
    
    def __init__(self):
        self.msn_adapter = VnstockHistoricalAdapter("MSN")
    
    async def get_available_forex_pairs(self) -> List[ForexPair]:
        """Get available forex pairs."""
        # Implementation to fetch available forex pairs
        pass
    
    async def get_available_world_indices(self) -> List[WorldIndex]:
        """Get available world indices."""
        # Implementation to fetch available world indices
        pass
    
    async def get_available_cryptocurrencies(self) -> List[CryptoCurrency]:
        """Get available cryptocurrencies."""
        # Implementation to fetch available cryptocurrencies
        pass
    
    async def get_forex_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: TimeInterval = TimeInterval.DAY_1
    ) -> HistoricalDataResponse:
        """Get forex historical data."""
        request = HistoricalDataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            asset_type=AssetType.FOREX
        )
        return await self.msn_adapter.get_historical_data(request)
```

### Phase 4: API Endpoints

#### 4.1 Historical Data Endpoints
Create comprehensive API endpoints:

```python
# app/interfaces/api/v1/historical_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.domain.historical_models import (
    HistoricalDataRequest,
    HistoricalDataResponse,
    TimeInterval,
    AssetType
)
from app.core.application.historical_data_service import HistoricalDataService
from app.interfaces.api.auth_dependencies import get_current_user

router = APIRouter(prefix="/api/v1/historical", tags=["Historical Data"])

@router.get("/data", response_model=HistoricalDataResponse)
async def get_historical_data(
    symbol: str = Query(..., description="Asset symbol"),
    start_date: datetime = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="End date (YYYY-MM-DD)"),
    interval: TimeInterval = Query(TimeInterval.DAY_1, description="Time interval"),
    asset_type: AssetType = Query(AssetType.STOCK, description="Asset type"),
    data_source: Optional[str] = Query(None, description="Preferred data source"),
    current_user = Depends(get_current_user)
):
    """Get historical data for any supported asset."""
    
    request = HistoricalDataRequest(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        asset_type=asset_type,
        data_source=data_source
    )
    
    service = HistoricalDataService()
    return await service.get_historical_data(request)

@router.get("/data/bulk", response_model=List[HistoricalDataResponse])
async def get_bulk_historical_data(
    symbols: List[str] = Query(..., description="List of asset symbols"),
    start_date: datetime = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="End date (YYYY-MM-DD)"),
    interval: TimeInterval = Query(TimeInterval.DAY_1, description="Time interval"),
    asset_type: AssetType = Query(AssetType.STOCK, description="Asset type"),
    current_user = Depends(get_current_user)
):
    """Get historical data for multiple assets."""
    
    service = HistoricalDataService()
    results = []
    
    for symbol in symbols:
        request = HistoricalDataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            asset_type=asset_type
        )
        
        try:
            data = await service.get_historical_data(request)
            results.append(data)
        except Exception as e:
            # Log error but continue with other symbols
            continue
    
    return results

@router.get("/data/intraday")
async def get_intraday_data(
    symbol: str = Query(..., description="Asset symbol"),
    page_size: int = Query(10000, description="Number of records to fetch"),
    current_user = Depends(get_current_user)
):
    """Get intraday trading data."""
    
    from app.infrastructure.data_sources.vnstock_intraday_adapter import VnstockIntradayAdapter
    
    adapter = VnstockIntradayAdapter()
    data = await adapter.get_intraday_data(symbol, page_size)
    
    return {
        "symbol": symbol,
        "data": data,
        "total_records": len(data),
        "retrieved_at": datetime.now()
    }

@router.get("/data/real-time")
async def get_real_time_quote(
    symbol: str = Query(..., description="Asset symbol"),
    current_user = Depends(get_current_user)
):
    """Get real-time quote."""
    
    from app.infrastructure.data_sources.vnstock_intraday_adapter import VnstockIntradayAdapter
    
    adapter = VnstockIntradayAdapter()
    quote = await adapter.get_real_time_quote(symbol)
    
    if quote is None:
        raise HTTPException(status_code=404, detail="Real-time quote not available")
    
    return quote
```

#### 4.2 International Market Endpoints
Create endpoints for international market data:

```python
# app/interfaces/api/v1/international_endpoints.py

from fastapi import APIRouter, Depends, Query
from typing import List
from app.core.application.international_market_service import InternationalMarketService
from app.interfaces.api.auth_dependencies import get_current_user

router = APIRouter(prefix="/api/v1/international", tags=["International Markets"])

@router.get("/forex/pairs")
async def get_forex_pairs(current_user = Depends(get_current_user)):
    """Get available forex pairs."""
    service = InternationalMarketService()
    return await service.get_available_forex_pairs()

@router.get("/indices")
async def get_world_indices(current_user = Depends(get_current_user)):
    """Get available world indices."""
    service = InternationalMarketService()
    return await service.get_available_world_indices()

@router.get("/crypto")
async def get_cryptocurrencies(current_user = Depends(get_current_user)):
    """Get available cryptocurrencies."""
    service = InternationalMarketService()
    return await service.get_available_cryptocurrencies()
```

## Technical Architecture

### 1. Data Flow Architecture

```
Client Request
    ↓
API Endpoint
    ↓
Historical Data Service
    ↓
Vnstock Historical Adapter
    ↓
Vnstock Library
    ↓
Data Source (VCI/TCBS/MSN)
    ↓
Response Processing
    ↓
Caching (Redis)
    ↓
Client Response
```

### 2. Caching Strategy

- **L1 Cache**: In-memory caching for frequently accessed data
- **L2 Cache**: Redis caching for persistent data storage
- **Cache Keys**: Structured keys based on symbol, asset type, interval, date range
- **TTL Strategy**: Different TTL based on data type and interval
  - Real-time data: 30 seconds
  - Intraday data: 5 minutes
  - Daily data: 1 hour
  - Historical data: 24 hours

### 3. Error Handling

- **Retry Logic**: Exponential backoff with jitter
- **Fallback Sources**: Automatic fallback between VCI, TCBS, MSN
- **Circuit Breaker**: Prevent cascading failures
- **Graceful Degradation**: Return partial data when possible

## API Design

### 1. RESTful Endpoints

#### Historical Data
- `GET /api/v1/historical/data` - Get historical data for single asset
- `GET /api/v1/historical/data/bulk` - Get historical data for multiple assets
- `GET /api/v1/historical/data/intraday` - Get intraday trading data
- `GET /api/v1/historical/data/real-time` - Get real-time quote

#### International Markets
- `GET /api/v1/international/forex/pairs` - Get available forex pairs
- `GET /api/v1/international/indices` - Get available world indices
- `GET /api/v1/international/crypto` - Get available cryptocurrencies

### 2. Query Parameters

#### Common Parameters
- `symbol`: Asset symbol (required)
- `start_date`: Start date in YYYY-MM-DD format (required)
- `end_date`: End date in YYYY-MM-DD format (required)
- `interval`: Time interval (1m, 5m, 15m, 30m, 1H, 1D, 1W, 1M)
- `asset_type`: Asset type (stock, index, futures, warrant, bond, etf, forex, crypto, world_index)
- `data_source`: Preferred data source (VCI, TCBS, MSN)

#### Response Format
```json
{
  "symbol": "VCI",
  "asset_type": "stock",
  "data_source": "VCI",
  "interval": "1D",
  "data": [
    {
      "time": "2024-01-01T00:00:00Z",
      "open": 100.0,
      "high": 105.0,
      "low": 98.0,
      "close": 103.0,
      "volume": 1000000
    }
  ],
  "total_records": 1,
  "retrieved_at": "2024-01-01T12:00:00Z"
}
```

## Domain Models

### 1. Historical Data Models

```python
# app/core/domain/historical_models.py

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

class TimeInterval(str, Enum):
    """Supported time intervals for historical data."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1H"
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1M"

class AssetType(str, Enum):
    """Supported asset types."""
    STOCK = "stock"
    INDEX = "index"
    FUTURES = "futures"
    WARRANT = "warrant"
    BOND = "bond"
    ETF = "etf"
    FOREX = "forex"
    CRYPTO = "crypto"
    WORLD_INDEX = "world_index"

class OHLCVTData(BaseModel):
    """OHLCVT historical data point."""
    time: datetime = Field(..., description="Timestamp")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="Highest price")
    low: float = Field(..., ge=0, description="Lowest price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

class HistoricalDataRequest(BaseModel):
    """Request model for historical data."""
    symbol: str = Field(..., min_length=1, description="Asset symbol")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    interval: TimeInterval = Field(TimeInterval.DAY_1, description="Time interval")
    asset_type: AssetType = Field(AssetType.STOCK, description="Asset type")
    data_source: Optional[str] = Field(None, description="Preferred data source")

class HistoricalDataResponse(BaseModel):
    """Response model for historical data."""
    symbol: str = Field(..., description="Asset symbol")
    asset_type: AssetType = Field(..., description="Asset type")
    data_source: str = Field(..., description="Data source used")
    interval: TimeInterval = Field(..., description="Time interval")
    data: List[OHLCVTData] = Field(..., description="Historical data points")
    total_records: int = Field(..., description="Total number of records")
    retrieved_at: datetime = Field(..., description="Retrieval timestamp")
```

### 2. International Market Models

```python
# app/core/domain/international_models.py

from typing import Optional
from pydantic import BaseModel, Field

class ForexPair(BaseModel):
    """Forex pair information."""
    symbol: str = Field(..., description="Forex pair symbol (e.g., USDVND)")
    base_currency: str = Field(..., description="Base currency")
    quote_currency: str = Field(..., description="Quote currency")
    symbol_id: Optional[str] = Field(None, description="Symbol ID for MSN source")

class WorldIndex(BaseModel):
    """World index information."""
    symbol: str = Field(..., description="Index symbol (e.g., DJI)")
    name: str = Field(..., description="Index name")
    country: str = Field(..., description="Country")
    symbol_id: Optional[str] = Field(None, description="Symbol ID for MSN source")

class CryptoCurrency(BaseModel):
    """Cryptocurrency information."""
    symbol: str = Field(..., description="Crypto symbol (e.g., BTC)")
    name: str = Field(..., description="Cryptocurrency name")
    symbol_id: Optional[str] = Field(None, description="Symbol ID for MSN source")
```

## Implementation Tasks

### Phase 1: Foundation (Week 1-2)
- [ ] Create historical data domain models
- [ ] Create international market domain models
- [ ] Extend VnstockAdapter with historical data methods
- [ ] Create VnstockHistoricalAdapter
- [ ] Create VnstockIntradayAdapter
- [ ] Update existing domain models

### Phase 2: Services (Week 3-4)
- [ ] Create HistoricalDataService
- [ ] Create InternationalMarketService
- [ ] Implement caching strategies
- [ ] Add error handling and retry logic
- [ ] Create service tests

### Phase 3: API Endpoints (Week 5-6)
- [ ] Create historical data API endpoints
- [ ] Create international market API endpoints
- [ ] Add authentication and authorization
- [ ] Implement request validation
- [ ] Add API documentation

### Phase 4: Testing (Week 7-8)
- [ ] Create unit tests for adapters
- [ ] Create integration tests for services
- [ ] Create API endpoint tests
- [ ] Performance testing
- [ ] Load testing

### Phase 5: Deployment (Week 9-10)
- [ ] Update Docker configuration
- [ ] Update environment variables
- [ ] Database migrations (if needed)
- [ ] Deployment scripts
- [ ] Monitoring and logging

## Testing Strategy

### 1. Unit Tests
- Test individual adapter methods
- Test service business logic
- Test domain model validation
- Test error handling scenarios

### 2. Integration Tests
- Test adapter integration with vnstock library
- Test service integration with multiple adapters
- Test caching integration
- Test fallback mechanisms

### 3. API Tests
- Test endpoint functionality
- Test request validation
- Test response formatting
- Test authentication and authorization

### 4. Performance Tests
- Test response times for different data sizes
- Test concurrent request handling
- Test memory usage
- Test cache performance

### 5. Load Tests
- Test system under high load
- Test rate limiting effectiveness
- Test error handling under load
- Test resource utilization

## Performance Considerations

### 1. Data Volume
- **Large Date Ranges**: Implement pagination for large datasets
- **Memory Management**: Stream large datasets to avoid memory issues
- **Data Compression**: Compress responses for large datasets

### 2. Caching Strategy
- **Multi-level Caching**: In-memory + Redis caching
- **Cache Warming**: Pre-populate frequently accessed data
- **Cache Invalidation**: Smart invalidation based on data freshness

### 3. Rate Limiting
- **Per-user Limits**: Limit requests per user
- **Per-source Limits**: Respect data source rate limits
- **Burst Handling**: Allow short bursts with longer cooldowns

### 4. Database Optimization
- **Indexing**: Proper indexing for historical data queries
- **Partitioning**: Partition large tables by date
- **Archiving**: Archive old data to maintain performance

## Future Enhancements

### 1. Advanced Features
- **Technical Indicators**: Calculate and return technical indicators
- **Data Aggregation**: Aggregate data at different time levels
- **Data Export**: Export data in various formats (CSV, Excel, JSON)
- **Real-time Streaming**: WebSocket support for real-time data

### 2. Machine Learning Integration
- **Predictive Analytics**: Use historical data for predictions
- **Pattern Recognition**: Identify trading patterns
- **Anomaly Detection**: Detect unusual market behavior
- **Sentiment Analysis**: Integrate news sentiment with price data

### 3. Advanced Caching
- **Predictive Caching**: Cache data based on usage patterns
- **Distributed Caching**: Multi-node cache distribution
- **Cache Analytics**: Monitor cache performance and hit rates

### 4. Data Quality
- **Data Validation**: Validate data quality and completeness
- **Data Cleaning**: Clean and normalize data
- **Data Enrichment**: Add additional metadata to data points
- **Data Lineage**: Track data source and processing history

## Conclusion

This implementation plan provides a comprehensive roadmap for integrating vnstock historical data API capabilities into the quantyFin-ai-agent system. The phased approach ensures systematic development while maintaining system stability and performance.

The implementation will significantly enhance the system's capabilities by providing:
- Comprehensive historical data access
- Support for multiple asset types
- International market data
- Advanced caching and performance optimization
- Robust error handling and fallback mechanisms

The modular architecture ensures maintainability and extensibility for future enhancements, while the comprehensive testing strategy ensures reliability and performance.

## References

1. [Vnstock Documentation - Historical Data](https://vnstocks.com/docs/vnstock/thong-ke-gia-lich-su)
2. [Vnstock GitHub Repository](https://github.com/thinh-vu/vnstock)
3. [Context7 Vnstock Documentation](https://context7.io)
4. [FastAPI Documentation](https://fastapi.tiangolo.com/)
5. [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

---

**Document Status**: Draft  
**Last Updated**: 2025-09-22  
**Next Review**: 2025-09-29  
**Approval Required**: Yes
