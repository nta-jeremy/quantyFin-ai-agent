# Vnstock Listing API Implementation Draft

**Date:** 2025-01-27  
**Author:** AI Assistant  
**Purpose:** Research and implementation plan for vnstock listing information API integration

## Overview

This document outlines the research findings and implementation approach for integrating vnstock's listing information API into the quantyFin-ai-agent project. The vnstock library provides comprehensive listing data for Vietnamese stock markets, including symbols, exchanges, industry classifications, and market groups.

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

Add new models to `app/core/domain/models.py`:

```python
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class MarketGroup(str, Enum):
    """Vietnamese market groups."""
    VN30 = "VN30"
    VN100 = "VN100"
    VN_MID_CAP = "VNMidCap"
    VN_SMALL_CAP = "VNSmallCap"
    VN_ALL_SHARE = "VNAllShare"
    HNX30 = "HNX30"
    HNX_CON = "HNXCon"
    HNX_FIN = "HNXFin"
    HNX_L_CAP = "HNXLCap"
    HNX_MS_CAP = "HNXMSCap"
    HNX_MAN = "HNXMan"
    ETF = "ETF"
    FU_INDEX = "FU_INDEX"
    CW = "CW"

class ICBIndustry(BaseModel):
    """Industry Classification Benchmark industry."""
    icb_name: str
    en_icb_name: str
    icb_code: str
    level: int

class StockSymbol(BaseModel):
    """Stock symbol information."""
    ticker: str
    organ_name: str
    symbol_id: Optional[int] = None
    exchange: Optional[str] = None
    icb_industry: Optional[str] = None

class ExchangeSymbol(BaseModel):
    """Detailed symbol information by exchange."""
    symbol: str
    symbol_id: int
    type: str
    exchange: str
    en_organ_name: Optional[str] = None
    en_organ_short_name: Optional[str] = None
    organ_short_name: Optional[str] = None
    organ_name: Optional[str] = None

class IndustrySymbol(BaseModel):
    """Symbol with industry classification."""
    symbol: str
    organ_name: str
    en_organ_name: Optional[str] = None
    icb_name3: str
    en_icb_name3: Optional[str] = None
    icb_name2: Optional[str] = None
    en_icb_name2: Optional[str] = None
    icb_name4: Optional[str] = None
    en_icb_name4: Optional[str] = None
    com_type_code: Optional[str] = None
    icb_code1: Optional[str] = None
    icb_code2: Optional[str] = None
    icb_code3: Optional[str] = None
    icb_code4: Optional[str] = None

class InternationalSymbol(BaseModel):
    """International market symbol."""
    symbol: str
    symbol_id: str
    exchange_name: str
    exchange_code_mic: str
    short_name: str
    friendly_name: str
    eng_name: str
    description: str
    local_name: str
    locale: str
```

### 2. Extend VnstockAdapter

Add new methods to `app/infrastructure/data_sources/vnstock_adapter.py`:

```python
from typing import List, Optional
from app.core.domain.models import (
    StockSymbol, ExchangeSymbol, IndustrySymbol, 
    ICBIndustry, InternationalSymbol, MarketGroup
)

class VnstockAdapter(ABC):
    # ... existing methods ...

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
    async def get_symbols_by_group(self, group: MarketGroup) -> List[str]:
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

### 3. Create Concrete Implementation

Create `app/infrastructure/data_sources/vnstock_listing_adapter.py`:

```python
"""Concrete implementation of vnstock listing adapter."""

import asyncio
from typing import List, Optional
import pandas as pd
from vnstock import Listing
from vnstock.explorer.msn.listing import Listing as MSNListing

from app.core.domain.models import (
    StockSymbol, ExchangeSymbol, IndustrySymbol, 
    ICBIndustry, InternationalSymbol, MarketGroup
)
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapter, VnstockAdapterConfig

class VnstockListingAdapter(VnstockAdapter):
    """Concrete implementation for vnstock listing data."""
    
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
                    ticker=row['ticker'],
                    organ_name=row['organ_name']
                )
                for _, row in df.iterrows()
            ]
        
        return await self._execute_with_retry(_fetch_symbols)
    
    async def get_symbols_by_exchange(self) -> List[ExchangeSymbol]:
        """Get symbols by exchange."""
        await self._rate_limit()
        
        def _fetch_exchange_symbols():
            df = self.listing.symbols_by_exchange()
            return [
                ExchangeSymbol(
                    symbol=row['symbol'],
                    symbol_id=row['id'],
                    type=row['type'],
                    exchange=row['exchange'],
                    en_organ_name=row.get('en_organ_name'),
                    en_organ_short_name=row.get('en_organ_short_name'),
                    organ_short_name=row.get('organ_short_name'),
                    organ_name=row.get('organ_name')
                )
                for _, row in df.iterrows()
            ]
        
        return await self._execute_with_retry(_fetch_exchange_symbols)
    
    async def get_symbols_by_group(self, group: MarketGroup) -> List[str]:
        """Get symbols by market group."""
        await self._rate_limit()
        
        def _fetch_group_symbols():
            series = self.listing.symbols_by_group(group.value)
            return series.tolist()
        
        return await self._execute_with_retry(_fetch_group_symbols)
    
    async def get_symbols_by_industry(self) -> List[IndustrySymbol]:
        """Get symbols by industry classification."""
        await self._rate_limit()
        
        def _fetch_industry_symbols():
            df = self.listing.symbols_by_industries()
            return [
                IndustrySymbol(
                    symbol=row['symbol'],
                    organ_name=row['organ_name'],
                    en_organ_name=row.get('en_organ_name'),
                    icb_name3=row['icb_name3'],
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
                    icb_name=row['icb_name'],
                    en_icb_name=row['en_icb_name'],
                    icb_code=row['icb_code'],
                    level=row['level']
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
                    symbol=row['symbol'],
                    symbol_id=row['symbol_id'],
                    exchange_name=row['exchange_name'],
                    exchange_code_mic=row['exchange_code_mic'],
                    short_name=row['short_name'],
                    friendly_name=row['friendly_name'],
                    eng_name=row['eng_name'],
                    description=row['description'],
                    local_name=row['local_name'],
                    locale=row['locale']
                )
                for _, row in df.iterrows()
            ]
        
        return await self._execute_with_retry(_search_symbols)
    
    # Implement other required abstract methods...
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1D") -> List[VietnameseStock]:
        # Implementation for historical data
        pass
    
    # ... other abstract method implementations
```

### 4. Create Service Layer

Create `app/core/application/listing_service.py`:

```python
"""Service for listing data operations."""

from typing import List, Optional
from app.core.domain.models import (
    StockSymbol, ExchangeSymbol, IndustrySymbol, 
    ICBIndustry, InternationalSymbol, MarketGroup
)
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapter

class ListingService:
    """Service for listing data operations."""
    
    def __init__(self, vnstock_adapter: VnstockAdapter):
        self.vnstock_adapter = vnstock_adapter
    
    async def get_all_symbols(self) -> List[StockSymbol]:
        """Get all stock symbols."""
        return await self.vnstock_adapter.get_all_symbols()
    
    async def get_symbols_by_exchange(self) -> List[ExchangeSymbol]:
        """Get symbols by exchange."""
        return await self.vnstock_adapter.get_symbols_by_exchange()
    
    async def get_vn30_symbols(self) -> List[str]:
        """Get VN30 constituent symbols."""
        return await self.vnstock_adapter.get_symbols_by_group(MarketGroup.VN30)
    
    async def get_symbols_by_industry(self) -> List[IndustrySymbol]:
        """Get symbols by industry classification."""
        return await self.vnstock_adapter.get_symbols_by_industry()
    
    async def get_icb_industries(self) -> List[ICBIndustry]:
        """Get ICB industry classifications."""
        return await self.vnstock_adapter.get_icb_industries()
    
    async def search_international_symbols(self, query: str) -> List[InternationalSymbol]:
        """Search international symbols."""
        return await self.vnstock_adapter.search_international_symbols(query)
    
    async def get_symbols_by_exchange_name(self, exchange: str) -> List[ExchangeSymbol]:
        """Get symbols filtered by exchange name."""
        all_symbols = await self.get_symbols_by_exchange()
        return [s for s in all_symbols if s.exchange == exchange]
    
    async def get_symbols_by_industry_name(self, industry_name: str) -> List[IndustrySymbol]:
        """Get symbols filtered by industry name."""
        all_symbols = await self.get_symbols_by_industry()
        return [s for s in all_symbols if industry_name.lower() in s.icb_name3.lower()]
```

### 5. Create API Endpoints

Add to `app/interfaces/api/v1/`:

```python
"""API endpoints for listing data."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.core.application.listing_service import ListingService
from app.core.domain.models import MarketGroup
from app.interfaces.api.auth_dependencies import get_current_user

router = APIRouter(prefix="/listing", tags=["listing"])

@router.get("/symbols", response_model=List[StockSymbol])
async def get_all_symbols(
    listing_service: ListingService = Depends(),
    current_user = Depends(get_current_user)
):
    """Get all stock symbols."""
    return await listing_service.get_all_symbols()

@router.get("/symbols/exchange", response_model=List[ExchangeSymbol])
async def get_symbols_by_exchange(
    listing_service: ListingService = Depends(),
    current_user = Depends(get_current_user)
):
    """Get symbols by exchange."""
    return await listing_service.get_symbols_by_exchange()

@router.get("/symbols/vn30", response_model=List[str])
async def get_vn30_symbols(
    listing_service: ListingService = Depends(),
    current_user = Depends(get_current_user)
):
    """Get VN30 constituent symbols."""
    return await listing_service.get_vn30_symbols()

@router.get("/symbols/group/{group_name}", response_model=List[str])
async def get_symbols_by_group(
    group_name: MarketGroup,
    listing_service: ListingService = Depends(),
    current_user = Depends(get_current_user)
):
    """Get symbols by market group."""
    return await listing_service.get_symbols_by_group(group_name)

@router.get("/symbols/industry", response_model=List[IndustrySymbol])
async def get_symbols_by_industry(
    listing_service: ListingService = Depends(),
    current_user = Depends(get_current_user)
):
    """Get symbols by industry classification."""
    return await listing_service.get_symbols_by_industry()

@router.get("/industries", response_model=List[ICBIndustry])
async def get_icb_industries(
    listing_service: ListingService = Depends(),
    current_user = Depends(get_current_user)
):
    """Get ICB industry classifications."""
    return await listing_service.get_icb_industries()

@router.get("/international/search", response_model=List[InternationalSymbol])
async def search_international_symbols(
    query: str,
    listing_service: ListingService = Depends(),
    current_user = Depends(get_current_user)
):
    """Search international symbols."""
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    return await listing_service.search_international_symbols(query)
```

## Data Structure Analysis

### Symbol Data Types

1. **Basic Symbol Info** (`all_symbols()`)
   - 1,598 entries
   - Columns: `ticker`, `organ_name`
   - Simple list of all available symbols

2. **Exchange Symbol Info** (`symbols_by_exchange()`)
   - 2,478 entries
   - Detailed information including exchange, company names in multiple languages
   - Covers HOSE, HNX, UPCOM exchanges

3. **Group Symbols** (`symbols_by_group()`)
   - VN30: 30 symbols
   - VN100: 100 symbols
   - Various market cap and sector groups

4. **Industry Classification** (`symbols_by_industries()`)
   - 1,592 entries with ICB classification
   - 4-level industry hierarchy
   - Both Vietnamese and English names

5. **ICB Industries** (`industries_icb()`)
   - 156 industry categories
   - Hierarchical structure (levels 1-4)

## Error Handling Considerations

1. **Rate Limiting**: vnstock has built-in rate limiting, but additional throttling may be needed
2. **Data Source Availability**: Different sources may have different data availability
3. **Network Timeouts**: Implement proper timeout handling for external API calls
4. **Data Validation**: Validate returned data against expected schemas
5. **Caching**: Implement caching for frequently accessed listing data

## Performance Considerations

1. **Caching Strategy**: 
   - Cache listing data for 24 hours (changes infrequently)
   - Cache industry classifications for 7 days
   - Cache group symbols for 1 hour

2. **Batch Operations**: 
   - Process multiple symbols in batches
   - Use async/await for concurrent operations

3. **Memory Management**:
   - Stream large datasets instead of loading all at once
   - Implement pagination for large result sets

## Testing Strategy

1. **Unit Tests**: Test individual adapter methods
2. **Integration Tests**: Test service layer with mock adapters
3. **E2E Tests**: Test complete API endpoints
4. **Data Validation Tests**: Verify data structure and content

## Dependencies

Add to `pyproject.toml`:

```toml
[tool.poetry.dependencies]
vnstock = "^3.0.0"
pandas = "^2.0.0"
```

## Implementation Checklist

- [ ] Add new domain models for listing data
- [ ] Extend VnstockAdapter abstract class with listing methods
- [ ] Create VnstockListingAdapter concrete implementation
- [ ] Create ListingService for business logic
- [ ] Add API endpoints for listing data
- [ ] Implement caching strategy
- [ ] Add comprehensive error handling
- [ ] Create unit and integration tests
- [ ] Update API documentation
- [ ] Add rate limiting and monitoring

## Next Steps

1. Review and approve this implementation plan
2. Start with domain models and basic adapter structure
3. Implement core listing functions one by one
4. Add comprehensive testing
5. Deploy and monitor performance

## References

- [Vnstock Documentation - Listing Information](https://vnstocks.com/docs/vnstock/thong-tin-niem-yet)
- [Vnstock GitHub Repository](https://github.com/thinh-vu/vnstock)
- [Context7 Vnstock Library Documentation](https://context7.io)
