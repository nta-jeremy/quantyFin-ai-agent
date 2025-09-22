# Vnstock Listing API Implementation Draft

**Date:** 2025-09-20
**Author:** AI Assistant
**Purpose:** Research and implementation plan for vnstock listing information API integration

## Overview

This document outlines the research findings and implementation approach for integrating vnstock's listing information API into the quantyFin-ai-agent project. The vnstock library provides comprehensive listing data for Vietnamese stock markets, including symbols, exchanges, industry classifications, and market groups.

**Architecture Context**: This implementation extends the existing hexagonal architecture pattern, leveraging the established VnstockAdapter abstract class and following the project's functional programming approach.

## Vnstock Listing API Capabilities

### Core Listing Functions

Based on research from [vnstock documentation](https://vnstocks.com/docs/vnstock/thong-tin-niem-yet) and Context7 analysis, the following key functions are available:

#### 1. Symbol Listing Functions

```python
from vnstock import Listing

# Initialize listing object
listing = Listing(source='VCI')  # or 'TCBS', 'MSN'

# Get all stock symbols
all_symbols = listing.all_symbols()
# Returns: DataFrame with columns ['ticker', 'organ_name']
# Sample: 1598 entries with ticker symbols and company names

# Get symbols by exchange
symbols_by_exchange = listing.symbols_by_exchange()
# Returns: DataFrame with detailed exchange information
# Columns: ['symbol', 'id', 'type', 'exchange', 'en_organ_name', 
#          'en_organ_short_name', 'organ_short_name', 'organ_name']
# Sample: 2478 entries across HOSE, HNX, UPCOM exchanges

# Get symbols by market group
vn30_symbols = listing.symbols_by_group('VN30')
# Returns: Series of 30 VN30 constituent symbols
# Supported groups: VN30, VN100, VNMidCap, VNSmallCap, VNAllShare,
#                   HNX30, HNXCon, HNXFin, HNXLCap, HNXMSCap, HNXMan,
#                   ETF, FU_INDEX, CW

# Get symbols by industry classification
symbols_by_industry = listing.symbols_by_industries()
# Returns: DataFrame with ICB industry classifications
# Columns: ['symbol', 'organ_name', 'en_organ_name', 'icb_name3',
#          'en_icb_name3', 'icb_name2', 'en_icb_name2', 'icb_name4',
#          'en_icb_name4', 'com_type_code', 'icb_code1', 'icb_code2',
#          'icb_code3', 'icb_code4']

# Get ICB industry list
industries = listing.industries_icb()
# Returns: DataFrame with industry classifications
# Columns: ['icb_name', 'en_icb_name', 'icb_code', 'level']
# Sample: 156 industry categories
```

#### 2. International Market Functions

```python
from vnstock.explorer.msn.listing import Listing

# Search international symbols (FX, Crypto, Indices)
msn_listing = Listing()
usd_symbols = msn_listing.search_symbol_id('USD')
# Returns: DataFrame with international symbol information
# Columns: ['symbol', 'symbol_id', 'exchange_name', 'exchange_code_mic',
#          'short_name', 'friendly_name', 'eng_name', 'description',
#          'local_name', 'locale']
```

### Data Sources

The vnstock library supports multiple data sources:

1. **VCI (Vietcap)** - Primary Vietnamese market data
2. **TCBS** - Alternative Vietnamese market data source
3. **MSN** - International market data (FX, Crypto, Indices)

## Implementation Approach

### 1. Extend Domain Models

#### 1.1 Update VietnameseMarketGroup Enum

Extend `app/core/domain/enums.py` with additional vnstock market groups:

```python
class VietnameseMarketGroup(str, Enum):
    """Vietnamese market group enumeration."""

    # Existing groups
    VN30 = "VN30"
    VNMIDCAP = "VNMIDCAP"
    VNSMALLCAP = "VNSMALLCAP"
    ETF = "ETF"
    CW = "CW"
    BOND = "BOND"

    # Additional vnstock groups
    VN100 = "VN100"
    VN_ALL_SHARE = "VNAllShare"
    HNX30 = "HNX30"
    HNX_CON = "HNXCon"
    HNX_FIN = "HNXFin"
    HNX_L_CAP = "HNXLCap"
    HNX_MS_CAP = "HNXMSCap"
    HNX_MAN = "HNXMan"
    FU_INDEX = "FU_INDEX"
```

#### 1.2 Create Listing Models

Create `app/core/domain/listing_models.py`:

```python
"""
Listing data domain models for QuantyFinAI Agent.

This module contains models specifically for vnstock listing information.
"""

from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import VietnameseExchange, VietnameseMarketGroup


class ICBIndustry(BaseModel):
    """Industry Classification Benchmark industry."""
    icb_name: str = Field(..., min_length=1)
    en_icb_name: str = Field(..., min_length=1)
    icb_code: str = Field(..., min_length=1)
    level: int = Field(..., ge=1, le=4)


class StockSymbol(BaseModel):
    """Basic stock symbol information."""
    ticker: str = Field(..., min_length=1, max_length=10)
    organ_name: str = Field(..., min_length=1)


class ExchangeSymbol(BaseModel):
    """Detailed symbol information by exchange."""
    symbol: str = Field(..., min_length=1, max_length=10)
    symbol_id: int = Field(..., ge=1)
    type: str = Field(..., min_length=1)
    exchange: VietnameseExchange = Field(...)
    en_organ_name: Optional[str] = Field(default=None, max_length=200)
    en_organ_short_name: Optional[str] = Field(default=None, max_length=50)
    organ_short_name: Optional[str] = Field(default=None, max_length=50)
    organ_name: Optional[str] = Field(default=None, max_length=200)


class IndustrySymbol(BaseModel):
    """Symbol with industry classification."""
    symbol: str = Field(..., min_length=1, max_length=10)
    organ_name: str = Field(..., min_length=1)
    en_organ_name: Optional[str] = Field(default=None, max_length=200)
    icb_name3: str = Field(..., min_length=1)
    en_icb_name3: Optional[str] = Field(default=None, max_length=100)
    icb_name2: Optional[str] = Field(default=None, max_length=100)
    en_icb_name2: Optional[str] = Field(default=None, max_length=100)
    icb_name4: Optional[str] = Field(default=None, max_length=100)
    en_icb_name4: Optional[str] = Field(default=None, max_length=100)
    com_type_code: Optional[str] = Field(default=None, max_length=10)
    icb_code1: Optional[str] = Field(default=None, max_length=10)
    icb_code2: Optional[str] = Field(default=None, max_length=10)
    icb_code3: Optional[str] = Field(default=None, max_length=10)
    icb_code4: Optional[str] = Field(default=None, max_length=10)


class InternationalSymbol(BaseModel):
    """International market symbol."""
    symbol: str = Field(..., min_length=1, max_length=20)
    symbol_id: str = Field(..., min_length=1)
    exchange_name: str = Field(..., min_length=1)
    exchange_code_mic: str = Field(..., min_length=1)
    short_name: str = Field(..., min_length=1)
    friendly_name: str = Field(..., min_length=1)
    eng_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    local_name: str = Field(..., min_length=1)
    locale: str = Field(..., min_length=1)


class ListingData(BaseModel):
    """Listing data with metadata."""
    id: UUID = Field(default_factory=uuid4)
    data_source: str = Field(..., min_length=1)
    retrieved_at: Optional[str] = Field(default=None)
    is_cached: bool = Field(default=False)
    cache_ttl_seconds: int = Field(default=3600)
```

#### 1.3 Update Domain Package

Update `app/core/domain/__init__.py` to include new listing models:

```python
# Import all listing-related models
from .listing_models import (
    ICBIndustry,
    StockSymbol,
    ExchangeSymbol,
    IndustrySymbol,
    InternationalSymbol,
    ListingData,
)

# Add to __all__ list
__all__ = [
    # ... existing models ...
    # Listing models
    "ICBIndustry",
    "StockSymbol",
    "ExchangeSymbol",
    "IndustrySymbol",
    "InternationalSymbol",
    "ListingData",
]
```

### 2. Extend VnstockAdapter

Extend `app/infrastructure/data_sources/vnstock_adapter.py` with new listing methods:

```python
# Add to existing imports
from app.core.domain.listing_models import (
    ICBIndustry,
    StockSymbol,
    ExchangeSymbol,
    IndustrySymbol,
    InternationalSymbol,
)

# Add to VnstockAdapter class
@abstractmethod
async def get_all_symbols(self) -> List[StockSymbol]:
    """Get all stock symbols.

    Returns:
        List of all available stock symbols
    """
    pass

@abstractmethod
async def get_symbols_by_exchange(self) -> List[ExchangeSymbol]:
    """Get symbols by exchange.

    Returns:
        List of symbols with exchange details
    """
    pass

@abstractmethod
async def get_symbols_by_group(self, group: VietnameseMarketGroup) -> List[str]:
    """Get symbols by market group.

    Args:
        group: Market group (VN30, VN100, etc.)

    Returns:
        List of symbols in the group
    """
    pass

@abstractmethod
async def get_symbols_by_industry(self) -> List[IndustrySymbol]:
    """Get symbols by industry classification.

    Returns:
        List of symbols with industry details
    """
    pass

@abstractmethod
async def get_icb_industries(self) -> List[ICBIndustry]:
    """Get ICB industry classifications.

    Returns:
        List of industry classifications
    """
    pass

@abstractmethod
async def search_international_symbols(
    self,
    query: str
) -> List[InternationalSymbol]:
    """Search international symbols.

    Args:
        query: Search query (e.g., 'USD', 'BTC')

    Returns:
        List of matching international symbols
    """
    pass
```

### 3. Update Concrete Implementation

Extend the existing vnstock implementation in `app/infrastructure/data_sources/vnstock_adapter.py` (or create a new listing-specific implementation):

```python
"""Update existing vnstock adapter with listing methods."""

# Add to imports
from vnstock import Listing
from vnstock.explorer.msn.listing import Listing as MSNListing
from app.core.domain.listing_models import (
    ICBIndustry,
    StockSymbol,
    ExchangeSymbol,
    IndustrySymbol,
    InternationalSymbol,
)

# Update the existing adapter class or create listing methods
class VnstockConcreteAdapter(VnstockAdapter):
    """Extended concrete implementation for vnstock data with listing functionality."""

    def __init__(self, config: VnstockAdapterConfig):
        super().__init__(config)
        self.listing = Listing(source=config.data_source.value)
        self.msn_listing = MSNListing() if config.data_source.value == 'MSN' else None

    async def get_all_symbols(self) -> List[StockSymbol]:
        """Get all stock symbols."""
        await self._rate_limit()

        def _fetch_symbols():
            df = self.listing.all_symbols()
            return [
                StockSymbol(
                    ticker=str(row['ticker']),
                    organ_name=str(row['organ_name'])
                )
                for _, row in df.iterrows()
            ]

        return await self._execute_with_retry(_fetch_symbols)

    async def get_symbols_by_exchange(self) -> List[ExchangeSymbol]:
        """Get symbols by exchange."""
        await self._rate_limit()

        def _fetch_exchange_symbols():
            df = self.listing.symbols_by_exchange()
            results = []
            for _, row in df.iterrows():
                try:
                    exchange = VietnameseExchange(row['exchange'])
                    symbol = ExchangeSymbol(
                        symbol=str(row['symbol']),
                        symbol_id=int(row['id']),
                        type=str(row['type']),
                        exchange=exchange,
                        en_organ_name=row.get('en_organ_name'),
                        en_organ_short_name=row.get('en_organ_short_name'),
                        organ_short_name=row.get('organ_short_name'),
                        organ_name=row.get('organ_name')
                    )
                    results.append(symbol)
                except ValueError:
                    # Skip invalid exchange values
                    continue
            return results

        return await self._execute_with_retry(_fetch_exchange_symbols)

    async def get_symbols_by_group(self, group: VietnameseMarketGroup) -> List[str]:
        """Get symbols by market group."""
        await self._rate_limit()

        def _fetch_group_symbols():
            series = self.listing.symbols_by_group(group.value)
            return [str(symbol) for symbol in series.tolist()]

        return await self._execute_with_retry(_fetch_group_symbols)

    async def get_symbols_by_industry(self) -> List[IndustrySymbol]:
        """Get symbols by industry classification."""
        await self._rate_limit()

        def _fetch_industry_symbols():
            df = self.listing.symbols_by_industries()
            return [
                IndustrySymbol(
                    symbol=str(row['symbol']),
                    organ_name=str(row['organ_name']),
                    en_organ_name=row.get('en_organ_name'),
                    icb_name3=str(row['icb_name3']),
                    en_icb_name3=row.get('en_icb_name3'),
                    icb_name2=row.get('icb_name2'),
                    en_icb_name2=row.get('en_icb_name2'),
                    icb_name4=row.get('icb_name4'),
                    en_icb_name4=row.get('en_icb_name4'),
                    com_type_code=row.get('com_type_code'),
                    icb_code1=row.get('icb_code1'),
                    icb_code2=row.get('icb_code2'),
                    icb_code3=row.get('icb_code3'),
                    icb_code4=row.get('icb_code4')
                )
                for _, row in df.iterrows()
            ]

        return await self._execute_with_retry(_fetch_industry_symbols)

    async def get_icb_industries(self) -> List[ICBIndustry]:
        """Get ICB industry classifications."""
        await self._rate_limit()

        def _fetch_industries():
            df = self.listing.industries_icb()
            return [
                ICBIndustry(
                    icb_name=str(row['icb_name']),
                    en_icb_name=str(row['en_icb_name']),
                    icb_code=str(row['icb_code']),
                    level=int(row['level'])
                )
                for _, row in df.iterrows()
            ]

        return await self._execute_with_retry(_fetch_industries)

    async def search_international_symbols(
        self,
        query: str
    ) -> List[InternationalSymbol]:
        """Search international symbols."""
        if not self.msn_listing:
            raise ValueError("MSN listing not available for current data source")

        await self._rate_limit()

        def _search_symbols():
            df = self.msn_listing.search_symbol_id(query)
            return [
                InternationalSymbol(
                    symbol=str(row['symbol']),
                    symbol_id=str(row['symbol_id']),
                    exchange_name=str(row['exchange_name']),
                    exchange_code_mic=str(row['exchange_code_mic']),
                    short_name=str(row['short_name']),
                    friendly_name=str(row['friendly_name']),
                    eng_name=str(row['eng_name']),
                    description=str(row['description']),
                    local_name=str(row['local_name']),
                    locale=str(row['locale'])
                )
                for _, row in df.iterrows()
            ]

        return await self._execute_with_retry(_search_symbols)
```

**Note**: This implementation extends the existing adapter pattern rather than creating a separate adapter class, maintaining consistency with the existing architecture.

### 4. Create Service Layer (Functional Approach)

Create `app/core/application/listing_services.py` using functional programming patterns:

```python
"""Listing data services using functional programming approach."""

from typing import List, Optional, Callable
from functools import lru_cache

from app.core.domain.listing_models import (
    ICBIndustry,
    StockSymbol,
    ExchangeSymbol,
    IndustrySymbol,
    InternationalSymbol,
)
from app.core.domain.enums import VietnameseMarketGroup, VietnameseExchange
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapter
from app.infrastructure.cache.redis_adapter import RedisCacheManager


async def get_all_symbols(vnstock_adapter: VnstockAdapter) -> List[StockSymbol]:
    """Get all stock symbols.

    Args:
        vnstock_adapter: The vnstock adapter instance

    Returns:
        List of all available stock symbols
    """
    return await vnstock_adapter.get_all_symbols()


async def get_symbols_by_exchange(vnstock_adapter: VnstockAdapter) -> List[ExchangeSymbol]:
    """Get symbols by exchange.

    Args:
        vnstock_adapter: The vnstock adapter instance

    Returns:
        List of symbols with exchange details
    """
    return await vnstock_adapter.get_symbols_by_exchange()


async def get_symbols_by_group(
    vnstock_adapter: VnstockAdapter,
    group: VietnameseMarketGroup
) -> List[str]:
    """Get symbols by market group.

    Args:
        vnstock_adapter: The vnstock adapter instance
        group: Market group to filter by

    Returns:
        List of symbols in the specified group
    """
    return await vnstock_adapter.get_symbols_by_group(group)


async def get_vn30_symbols(vnstock_adapter: VnstockAdapter) -> List[str]:
    """Get VN30 constituent symbols.

    Args:
        vnstock_adapter: The vnstock adapter instance

    Returns:
        List of VN30 constituent symbols
    """
    return await get_symbols_by_group(vnstock_adapter, VietnameseMarketGroup.VN30)


async def get_symbols_by_industry(vnstock_adapter: VnstockAdapter) -> List[IndustrySymbol]:
    """Get symbols by industry classification.

    Args:
        vnstock_adapter: The vnstock adapter instance

    Returns:
        List of symbols with industry details
    """
    return await vnstock_adapter.get_symbols_by_industry()


async def get_icb_industries(vnstock_adapter: VnstockAdapter) -> List[ICBIndustry]:
    """Get ICB industry classifications.

    Args:
        vnstock_adapter: The vnstock adapter instance

    Returns:
        List of industry classifications
    """
    return await vnstock_adapter.get_icb_industries()


async def search_international_symbols(
    vnstock_adapter: VnstockAdapter,
    query: str
) -> List[InternationalSymbol]:
    """Search international symbols.

    Args:
        vnstock_adapter: The vnstock adapter instance
        query: Search query string

    Returns:
        List of matching international symbols
    """
    if not query or not query.strip():
        raise ValueError("Query parameter is required")

    return await vnstock_adapter.search_international_symbols(query.strip())


def filter_symbols_by_exchange(
    symbols: List[ExchangeSymbol],
    exchange: VietnameseExchange
) -> List[ExchangeSymbol]:
    """Filter symbols by exchange.

    Args:
        symbols: List of symbols to filter
        exchange: Exchange to filter by

    Returns:
        Filtered list of symbols
    """
    return [symbol for symbol in symbols if symbol.exchange == exchange]


def filter_symbols_by_industry(
    symbols: List[IndustrySymbol],
    industry_name: str
) -> List[IndustrySymbol]:
    """Filter symbols by industry name.

    Args:
        symbols: List of symbols to filter
        industry_name: Industry name to filter by (case-insensitive)

    Returns:
        Filtered list of symbols
    """
    if not industry_name:
        return symbols

    industry_lower = industry_name.lower()
    return [
        symbol for symbol in symbols
        if industry_lower in symbol.icb_name3.lower()
    ]


def get_unique_exchanges(symbols: List[ExchangeSymbol]) -> List[VietnameseExchange]:
    """Get unique exchanges from symbol list.

    Args:
        symbols: List of symbols with exchange information

    Returns:
        List of unique exchanges
    """
    return list(set(symbol.exchange for symbol in symbols))


def get_unique_industries(symbols: List[IndustrySymbol]) -> List[str]:
    """Get unique industries from symbol list.

    Args:
        symbols: List of symbols with industry information

    Returns:
        List of unique industry names
    """
    return list(set(symbol.icb_name3 for symbol in symbols))


# Cached versions for frequently accessed data
@lru_cache(maxsize=128)
def get_cached_vn30_symbols(
    cache_key: str,
    fetch_fn: Callable[[], List[str]]
) -> List[str]:
    """Get cached VN30 symbols.

    Args:
        cache_key: Cache key for this request
        fetch_fn: Function to fetch fresh data

    Returns:
        List of VN30 symbols (cached or fresh)
    """
    return fetch_fn()


@lru_cache(maxsize=64)
def get_cached_industries(
    cache_key: str,
    fetch_fn: Callable[[], List[ICBIndustry]]
) -> List[ICBIndustry]:
    """Get cached industry classifications.

    Args:
        cache_key: Cache key for this request
        fetch_fn: Function to fetch fresh data

    Returns:
        List of industry classifications (cached or fresh)
    """
    return fetch_fn()
```

### 5. Create API Endpoints

Create `app/interfaces/api/v1/listing_endpoints.py` using functional approach:

```python
"""API endpoints for listing data."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.core.application.listing_services import (
    get_all_symbols,
    get_symbols_by_exchange,
    get_symbols_by_group,
    get_vn30_symbols,
    get_symbols_by_industry,
    get_icb_industries,
    search_international_symbols,
    filter_symbols_by_exchange,
    filter_symbols_by_industry,
)
from app.core.domain.enums import VietnameseMarketGroup, VietnameseExchange
from app.core.domain.listing_models import (
    StockSymbol,
    ExchangeSymbol,
    IndustrySymbol,
    ICBIndustry,
    InternationalSymbol,
)
from app.interfaces.api.dependencies import get_vnstock_adapter, get_current_user

router = APIRouter(prefix="/listing", tags=["listing"])


@router.get("/symbols", response_model=List[StockSymbol])
async def get_all_symbols_endpoint(
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Get all stock symbols."""
    return await get_all_symbols(vnstock_adapter)


@router.get("/symbols/exchange", response_model=List[ExchangeSymbol])
async def get_symbols_by_exchange_endpoint(
    exchange: Optional[VietnameseExchange] = Query(None, description="Filter by exchange"),
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Get symbols by exchange, optionally filtered by specific exchange."""
    symbols = await get_symbols_by_exchange(vnstock_adapter)

    if exchange:
        return filter_symbols_by_exchange(symbols, exchange)

    return symbols


@router.get("/symbols/vn30", response_model=List[str])
async def get_vn30_symbols_endpoint(
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Get VN30 constituent symbols."""
    return await get_vn30_symbols(vnstock_adapter)


@router.get("/symbols/group/{group_name}", response_model=List[str])
async def get_symbols_by_group_endpoint(
    group_name: VietnameseMarketGroup,
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Get symbols by market group."""
    return await get_symbols_by_group(vnstock_adapter, group_name)


@router.get("/symbols/industry", response_model=List[IndustrySymbol])
async def get_symbols_by_industry_endpoint(
    industry_name: Optional[str] = Query(None, description="Filter by industry name"),
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Get symbols by industry classification, optionally filtered by industry."""
    symbols = await get_symbols_by_industry(vnstock_adapter)

    if industry_name:
        return filter_symbols_by_industry(symbols, industry_name)

    return symbols


@router.get("/industries", response_model=List[ICBIndustry])
async def get_icb_industries_endpoint(
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Get ICB industry classifications."""
    return await get_icb_industries(vnstock_adapter)


@router.get("/international/search", response_model=List[InternationalSymbol])
async def search_international_symbols_endpoint(
    query: str = Query(..., min_length=1, description="Search query"),
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Search international symbols."""
    return await search_international_symbols(vnstock_adapter, query)


@router.get("/exchanges", response_model=List[VietnameseExchange])
async def get_exchanges_endpoint(
    vnstock_adapter = Depends(get_vnstock_adapter),
    current_user = Depends(get_current_user)
):
    """Get all available exchanges."""
    symbols = await get_symbols_by_exchange(vnstock_adapter)
    from app.core.application.listing_services import get_unique_exchanges
    return get_unique_exchanges(symbols)


@router.get("/market-groups", response_model=List[VietnameseMarketGroup])
async def get_market_groups_endpoint(
    current_user = Depends(get_current_user)
):
    """Get all available market groups."""
    return list(VietnameseMarketGroup)
```

Update `app/interfaces/api/v1/__init__.py` to include listing endpoints:

```python
from .listing_endpoints import router as listing_router

__all__ = ["listing_router"]
```

And include in main FastAPI app:

```python
# In app/main.py or app/interfaces/api/main.py
from app.interfaces.api.v1 import listing_router

app.include_router(listing_router, prefix="/api/v1")
```

## Implementation Considerations

### Error Handling

The implementation leverages the existing error handling patterns in the VnstockAdapter:

1. **Built-in Retry Logic**: Uses existing `_execute_with_retry` method
2. **Rate Limiting**: Leverages existing `_rate_limit` functionality
3. **Data Validation**: Strong typing with Pydantic models ensures data integrity
4. **Exchange Validation**: Handles invalid exchange values gracefully
5. **Query Validation**: Validates input parameters before API calls

### Performance Optimizations

1. **Functional Caching**: Uses `@lru_cache` for frequently accessed data
2. **Memory Efficiency**: Processes data in streams rather than loading all at once
3. **Type Safety**: Strong typing reduces runtime errors and improves performance
4. **Concurrent Operations**: Uses async/await for non-blocking I/O operations

### Integration with Existing Architecture

1. **Hexagonal Architecture**: Follows established port/adapter pattern
2. **Dependency Injection**: Uses FastAPI's dependency injection system
3. **Functional Programming**: Pure functions with clear input/output contracts
4. **Domain-Driven Design**: Separates domain logic from infrastructure concerns

## Dependencies Management

Add to `pyproject.toml`:

```toml
[tool.poetry.dependencies]
vnstock = "^3.0.0"
pandas = "^2.0.0"
```

Ensure these are added to the existing dependency structure rather than creating a new section.

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_listing_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.application.listing_services import get_all_symbols, filter_symbols_by_exchange
from app.core.domain.listing_models import StockSymbol, ExchangeSymbol
from app.core.domain.enums import VietnameseExchange

@pytest.mark.asyncio
async def test_get_all_symbols():
    # Arrange
    mock_adapter = AsyncMock()
    mock_adapter.get_all_symbols.return_value = [
        StockSymbol(ticker="VNM", organ_name="Vietnam Airlines")
    ]

    # Act
    result = await get_all_symbols(mock_adapter)

    # Assert
    assert len(result) == 1
    assert result[0].ticker == "VNM"

def test_filter_symbols_by_exchange():
    # Arrange
    symbols = [
        ExchangeSymbol(symbol="VNM", exchange=VietnameseExchange.HOSE),
        ExchangeSymbol(symbol="FPT", exchange=VietnameseExchange.HNX)
    ]

    # Act
    result = filter_symbols_by_exchange(symbols, VietnameseExchange.HOSE)

    # Assert
    assert len(result) == 1
    assert result[0].symbol == "VNM"
```

### Integration Tests

```python
# tests/integration/test_listing_adapter.py
import pytest
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapterConfig
from app.core.domain.enums import VnstockDataSource

@pytest.mark.asyncio
async def test_adapter_listing_methods():
    # Arrange
    config = VnstockAdapterConfig(data_source=VnstockDataSource.VCI)
    adapter = VnstockConcreteAdapter(config)

    # Act & Assert
    symbols = await adapter.get_all_symbols()
    assert len(symbols) > 0

    exchanges = await adapter.get_symbols_by_exchange()
    assert len(exchanges) > 0
```

## Enhanced Implementation Checklist

### Phase 1: Domain Models and Enums
- [ ] Extend VietnameseMarketGroup enum with additional groups
- [ ] Create listing_models.py with all required models
- [ ] Update domain package imports
- [ ] Add field validators and constraints

### Phase 2: Adapter Extension
- [ ] Add abstract methods to VnstockAdapter
- [ ] Implement concrete adapter methods
- [ ] Add error handling and validation
- [ ] Integrate with existing retry and rate limiting

### Phase 3: Service Layer
- [ ] Create functional service functions
- [ ] Add filtering and utility functions
- [ ] Implement caching strategies
- [ ] Add comprehensive error handling

### Phase 4: API Endpoints
- [ ] Create listing endpoints
- [ ] Add query parameters and validation
- [ ] Implement dependency injection
- [ ] Add proper error responses

### Phase 5: Testing and Documentation
- [ ] Create comprehensive unit tests
- [ ] Add integration tests
- [ ] Write E2E tests for API endpoints
- [ ] Update API documentation
- [ ] Add performance monitoring

### Phase 6: Deployment and Monitoring
- [ ] Deploy to staging environment
- [ ] Monitor performance metrics
- [ ] Set up alerting for errors
- [ ] Optimize based on usage patterns

## Security Considerations

1. **Authentication**: All endpoints require valid user authentication
2. **Rate Limiting**: Implement additional API rate limiting
3. **Input Validation**: Validate all input parameters using Pydantic
4. **Data Sanitization**: Clean all user-provided input
5. **Access Control**: Ensure users only have access to authorized data

## Monitoring and Observability

1. **Logging**: Use existing structlog configuration for operation logging
2. **Metrics**: Track API usage, response times, and error rates
3. **Health Checks**: Add health check endpoints for adapter connectivity
4. **Performance Monitoring**: Monitor memory usage and response times
5. **Cache Monitoring**: Track cache hit/miss ratios

## Migration Strategy

1. **Backward Compatibility**: Ensure existing functionality continues to work
2. **Gradual Rollout**: Deploy to staging first, then production
3. **Feature Flags**: Use feature flags for gradual enablement
4. **Data Migration**: Migrate any existing data if needed
5. **Fallback Mechanisms**: Provide fallbacks for failed operations

## References

- [Vnstock Documentation - Listing Information](https://vnstocks.com/docs/vnstock/thong-tin-niem-yet)
- [Vnstock GitHub Repository](https://github.com/thinh-vu/vnstock)
- [Context7 Vnstock Library Documentation](https://context7.io)
- [Project CLAUDE.md](/Users/tunganh252/Desktop/Study/AI101/quantyFin-ai-agent/CLAUDE.md)
