"""
International market data API endpoints for QuantyFinAI Agent.

This module contains endpoints for retrieving international market data
including forex, world indices, and cryptocurrency data.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.core.application.international_market_service import (
    InternationalMarketService,
)
from app.core.domain.historical_models import (
    AssetType,
    DataSourceUnavailableError,
    DataValidationError,
    HistoricalDataError,
    InvalidParameterError,
    NetworkError,
    RateLimitExceededError,
    SymbolNotFoundError,
    TimeInterval,
    TimeoutError,
)
from app.core.domain.international_models import (
    CryptoCurrency,
    ForexPair,
    WorldIndex,
)

from ..auth_dependencies import (
    get_current_active_user,
    rate_limit_dependency,
    require_api_role,
)
from .dependencies import get_international_market_service

router = APIRouter(tags=["international-data"])


@router.get("/forex/pairs", response_model=List[Dict[str, Any]])
async def get_forex_pairs(
    base_currency: str = Query(
        None, description="Filter by base currency (e.g., 'USD')"
    ),
    quote_currency: str = Query(
        None, description="Filter by quote currency (e.g., 'EUR')"
    ),
    limit: int = Query(
        100, description="Maximum number of pairs to return", ge=1, le=1000
    ),
    international_service: InternationalMarketService = Depends(
        get_international_market_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> List[Dict[str, Any]]:
    """
    Get available forex currency pairs.

    Features:
    - Comprehensive forex pair listing
    - Optional filtering by base/quote currencies
    - Pagination support
    - Real-time data availability check
    """
    try:
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise InvalidParameterError(
                "limit must be between 1 and 1000",
                "forex_pairs",
                AssetType.FOREX,
            )

        # Get forex pairs
        pairs = await international_service.get_forex_pairs(
            base_currency=base_currency.upper() if base_currency else None,
            quote_currency=quote_currency.upper() if quote_currency else None,
            limit=limit,
        )

        return [
            {
                "symbol": pair.symbol,
                "base_currency": pair.base_currency,
                "quote_currency": pair.quote_currency,
                "name": pair.name,
                "type": pair.type,
                "exchange": pair.exchange,
                "is_active": pair.is_active,
                "last_updated": (
                    pair.last_updated.isoformat()
                    if pair.last_updated
                    else None
                ),
            }
            for pair in pairs
        ]

    except HistoricalDataError as e:
        if isinstance(e, SymbolNotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        elif isinstance(e, RateLimitExceededError):
            raise HTTPException(status_code=429, detail=str(e))
        elif isinstance(e, InvalidParameterError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, DataSourceUnavailableError):
            raise HTTPException(status_code=503, detail=str(e))
        elif isinstance(e, (NetworkError, TimeoutError)):
            raise HTTPException(status_code=502, detail=str(e))
        elif isinstance(e, DataValidationError):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving forex pairs: {str(e)}",
        )


@router.get("/forex/rate", response_model=Dict[str, Any])
async def get_forex_rate(
    base_currency: str = Query(..., description="Base currency (e.g., 'USD')"),
    quote_currency: str = Query(
        ..., description="Quote currency (e.g., 'EUR')"
    ),
    data_source: str = Query("MSN", description="Data source (MSN)"),
    international_service: InternationalMarketService = Depends(
        get_international_market_service
    ),
) -> Dict[str, Any]:
    """
    Get current forex exchange rate.

    Features:
    - Real-time exchange rates
    - Multiple currency pairs supported
    - Rate change tracking
    - Historical rate data available
    """
    try:
        # Validate currencies
        if not base_currency or len(base_currency) != 3:
            raise InvalidParameterError(
                "base_currency must be a 3-letter currency code",
                f"{base_currency}/{quote_currency}",
                AssetType.FOREX,
            )

        if not quote_currency or len(quote_currency) != 3:
            raise InvalidParameterError(
                "quote_currency must be a 3-letter currency code",
                f"{base_currency}/{quote_currency}",
                AssetType.FOREX,
            )

        # Get exchange rate
        rate_data = await international_service.get_forex_rate(
            base_currency=base_currency.upper(),
            quote_currency=quote_currency.upper(),
            data_source=data_source.upper(),
        )

        return {
            "symbol": f"{base_currency.upper()}{quote_currency.upper()}",
            "base_currency": base_currency.upper(),
            "quote_currency": quote_currency.upper(),
            "rate": rate_data.get("rate", 0),
            "timestamp": rate_data.get(
                "timestamp", datetime.now(timezone.utc)
            ).isoformat(),
            "change_24h": rate_data.get("change_24h", 0),
            "change_percent_24h": rate_data.get("change_percent_24h", 0),
            "high_24h": rate_data.get("high_24h", 0),
            "low_24h": rate_data.get("low_24h", 0),
            "volume_24h": rate_data.get("volume_24h", 0),
            "data_source": data_source.upper(),
        }

    except HistoricalDataError as e:
        if isinstance(e, SymbolNotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        elif isinstance(e, RateLimitExceededError):
            raise HTTPException(status_code=429, detail=str(e))
        elif isinstance(e, InvalidParameterError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, DataSourceUnavailableError):
            raise HTTPException(status_code=503, detail=str(e))
        elif isinstance(e, (NetworkError, TimeoutError)):
            raise HTTPException(status_code=502, detail=str(e))
        elif isinstance(e, DataValidationError):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving forex rate: {str(e)}",
        )


@router.get("/indices", response_model=List[Dict[str, Any]])
async def get_world_indices(
    region: str = Query(
        None, description="Filter by region (e.g., 'US', 'EU', 'ASIA')"
    ),
    limit: int = Query(
        100, description="Maximum number of indices to return", ge=1, le=500
    ),
    international_service: InternationalMarketService = Depends(
        get_international_market_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> List[Dict[str, Any]]:
    """
    Get available world market indices.

    Features:
    - Comprehensive world indices listing
    - Regional filtering
    - Major indices coverage (S&P 500, Dow Jones, Nikkei, etc.)
    - Real-time price data
    """
    try:
        # Validate parameters
        if limit < 1 or limit > 500:
            raise InvalidParameterError(
                "limit must be between 1 and 500",
                "world_indices",
                AssetType.WORLD_INDEX,
            )

        # Get world indices
        indices = await international_service.get_world_indices(
            region=region.upper() if region else None, limit=limit
        )

        return [
            {
                "symbol": index.symbol,
                "name": index.name,
                "country": index.country,
                "region": index.region,
                "currency": index.currency,
                "current_value": index.current_value,
                "change": index.change,
                "change_percent": index.change_percent,
                "last_updated": (
                    index.last_updated.isoformat()
                    if index.last_updated
                    else None
                ),
                "is_active": index.is_active,
            }
            for index in indices
        ]

    except HistoricalDataError as e:
        if isinstance(e, SymbolNotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        elif isinstance(e, RateLimitExceededError):
            raise HTTPException(status_code=429, detail=str(e))
        elif isinstance(e, InvalidParameterError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, DataSourceUnavailableError):
            raise HTTPException(status_code=503, detail=str(e))
        elif isinstance(e, (NetworkError, TimeoutError)):
            raise HTTPException(status_code=502, detail=str(e))
        elif isinstance(e, DataValidationError):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving world indices: {str(e)}",
        )


@router.get("/indices/{symbol}", response_model=Dict[str, Any])
async def get_world_index_details(
    symbol: str = Path(
        ..., description="Index symbol (e.g., 'SPX', 'DJI', 'NKY')"
    ),
    data_source: str = Query("MSN", description="Data source (MSN)"),
    international_service: InternationalMarketService = Depends(
        get_international_market_service
    ),
) -> Dict[str, Any]:
    """
    Get detailed information for a specific world market index.

    Features:
    - Detailed index information
    - Historical performance data
    - Constituent information
    - Real-time price updates
    """
    try:
        # Validate symbol
        if not symbol or len(symbol) > 10:
            raise InvalidParameterError(
                "symbol must be between 1 and 10 characters",
                symbol,
                AssetType.WORLD_INDEX,
            )

        # Get index details
        index_data = await international_service.get_world_index_details(
            symbol=symbol.upper(), data_source=data_source.upper()
        )

        return {
            "symbol": symbol.upper(),
            "name": index_data.get("name", ""),
            "country": index_data.get("country", ""),
            "region": index_data.get("region", ""),
            "currency": index_data.get("currency", ""),
            "current_value": index_data.get("current_value", 0),
            "open": index_data.get("open", 0),
            "high": index_data.get("high", 0),
            "low": index_data.get("low", 0),
            "previous_close": index_data.get("previous_close", 0),
            "change": index_data.get("change", 0),
            "change_percent": index_data.get("change_percent", 0),
            "volume": index_data.get("volume", 0),
            "market_cap": index_data.get("market_cap", 0),
            "last_updated": index_data.get(
                "last_updated", datetime.now(timezone.utc)
            ).isoformat(),
            "data_source": data_source.upper(),
        }

    except HistoricalDataError as e:
        if isinstance(e, SymbolNotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        elif isinstance(e, RateLimitExceededError):
            raise HTTPException(status_code=429, detail=str(e))
        elif isinstance(e, InvalidParameterError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, DataSourceUnavailableError):
            raise HTTPException(status_code=503, detail=str(e))
        elif isinstance(e, (NetworkError, TimeoutError)):
            raise HTTPException(status_code=502, detail=str(e))
        elif isinstance(e, DataValidationError):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving index details: {str(e)}",
        )


@router.get("/crypto", response_model=List[Dict[str, Any]])
async def get_cryptocurrencies(
    sort_by: str = Query(
        "market_cap",
        description="Sort by: market_cap, price, volume_24h, change_24h",
    ),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    limit: int = Query(
        100,
        description="Maximum number of cryptocurrencies to return",
        ge=1,
        le=1000,
    ),
    min_market_cap: float = Query(
        None, description="Minimum market cap filter", ge=0
    ),
    international_service: InternationalMarketService = Depends(
        get_international_market_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> List[Dict[str, Any]]:
    """
    Get available cryptocurrencies with market data.

    Features:
    - Comprehensive cryptocurrency listing
    - Market data and rankings
    - Sorting and filtering options
    - Real-time price updates
    """
    try:
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise InvalidParameterError(
                "limit must be between 1 and 1000",
                "cryptocurrencies",
                AssetType.CRYPTO,
            )

        valid_sort_by = ["market_cap", "price", "volume_24h", "change_24h"]
        if sort_by not in valid_sort_by:
            raise InvalidParameterError(
                f"sort_by must be one of: {', '.join(valid_sort_by)}",
                "cryptocurrencies",
                AssetType.CRYPTO,
            )

        valid_sort_order = ["asc", "desc"]
        if sort_order not in valid_sort_order:
            raise InvalidParameterError(
                f"sort_order must be one of: {', '.join(valid_sort_order)}",
                "cryptocurrencies",
                AssetType.CRYPTO,
            )

        # Get cryptocurrencies
        cryptocurrencies = await international_service.get_cryptocurrencies(
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            min_market_cap=min_market_cap,
        )

        return [
            {
                "symbol": crypto.symbol,
                "name": crypto.name,
                "price_usd": crypto.price_usd,
                "market_cap_usd": crypto.market_cap_usd,
                "volume_24h_usd": crypto.volume_24h_usd,
                "change_24h_percent": crypto.change_24h_percent,
                "circulating_supply": crypto.circulating_supply,
                "max_supply": crypto.max_supply,
                "rank": crypto.rank,
                "last_updated": (
                    crypto.last_updated.isoformat()
                    if crypto.last_updated
                    else None
                ),
                "is_active": crypto.is_active,
            }
            for crypto in cryptocurrencies
        ]

    except HistoricalDataError as e:
        if isinstance(e, SymbolNotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        elif isinstance(e, RateLimitExceededError):
            raise HTTPException(status_code=429, detail=str(e))
        elif isinstance(e, InvalidParameterError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, DataSourceUnavailableError):
            raise HTTPException(status_code=503, detail=str(e))
        elif isinstance(e, (NetworkError, TimeoutError)):
            raise HTTPException(status_code=502, detail=str(e))
        elif isinstance(e, DataValidationError):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving cryptocurrencies: {str(e)}",
        )


@router.get("/crypto/{symbol}", response_model=Dict[str, Any])
async def get_cryptocurrency_details(
    symbol: str = Path(
        ..., description="Cryptocurrency symbol (e.g., 'BTC', 'ETH')"
    ),
    data_source: str = Query("MSN", description="Data source (MSN)"),
    international_service: InternationalMarketService = Depends(
        get_international_market_service
    ),
) -> Dict[str, Any]:
    """
    Get detailed information for a specific cryptocurrency.

    Features:
    - Detailed cryptocurrency information
    - Historical price data
    - Market statistics
    - Social and development metrics
    """
    try:
        # Validate symbol
        if not symbol or len(symbol) > 10:
            raise InvalidParameterError(
                "symbol must be between 1 and 10 characters",
                symbol,
                AssetType.CRYPTO,
            )

        # Get cryptocurrency details
        crypto_data = await international_service.get_cryptocurrency_details(
            symbol=symbol.upper(), data_source=data_source.upper()
        )

        return {
            "symbol": symbol.upper(),
            "name": crypto_data.get("name", ""),
            "description": crypto_data.get("description", ""),
            "price_usd": crypto_data.get("price_usd", 0),
            "market_cap_usd": crypto_data.get("market_cap_usd", 0),
            "volume_24h_usd": crypto_data.get("volume_24h_usd", 0),
            "change_1h_percent": crypto_data.get("change_1h_percent", 0),
            "change_24h_percent": crypto_data.get("change_24h_percent", 0),
            "change_7d_percent": crypto_data.get("change_7d_percent", 0),
            "circulating_supply": crypto_data.get("circulating_supply", 0),
            "max_supply": crypto_data.get("max_supply", 0),
            "total_supply": crypto_data.get("total_supply", 0),
            "ath_price_usd": crypto_data.get("ath_price_usd", 0),
            "ath_date": (
                crypto_data.get("ath_date", "").isoformat()
                if crypto_data.get("ath_date")
                else None
            ),
            "rank": crypto_data.get("rank", 0),
            "last_updated": crypto_data.get(
                "last_updated", datetime.now(timezone.utc)
            ).isoformat(),
            "data_source": data_source.upper(),
        }

    except HistoricalDataError as e:
        if isinstance(e, SymbolNotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        elif isinstance(e, RateLimitExceededError):
            raise HTTPException(status_code=429, detail=str(e))
        elif isinstance(e, InvalidParameterError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, DataSourceUnavailableError):
            raise HTTPException(status_code=503, detail=str(e))
        elif isinstance(e, (NetworkError, TimeoutError)):
            raise HTTPException(status_code=502, detail=str(e))
        elif isinstance(e, DataValidationError):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving cryptocurrency details: {str(e)}",
        )
