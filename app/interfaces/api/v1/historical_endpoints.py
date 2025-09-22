"""
Historical data API endpoints for QuantyFinAI Agent.

This module contains endpoints for retrieving historical market data
following hexagonal architecture principles and constitutional requirements.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.application.historical_data_service import HistoricalDataService
from app.core.domain.data_source_models import DataSourceHealth
from app.core.domain.historical_models import (
    AssetType,
    DataSourceUnavailableError,
    DataValidationError,
    HistoricalDataError,
    HistoricalDataRequest,
    HistoricalDataResponse,
    InvalidParameterError,
    NetworkError,
    RateLimitExceededError,
    SymbolNotFoundError,
    TimeInterval,
    TimeoutError,
)

from ..auth_dependencies import (
    get_current_active_user,
    rate_limit_dependency,
    require_api_role,
)
from .dependencies import get_historical_data_service

router = APIRouter(tags=["historical-data"])


@router.get(
    "/data",
    response_model=HistoricalDataResponse,
    summary="Get Historical Market Data",
    description="""
    Retrieve historical market data for a specific asset within a date range.

    This endpoint provides OHLCVT (Open, High, Low, Close, Volume, Time) data for various asset types
    including stocks, indices, futures, forex, and cryptocurrencies. The data is retrieved from
    multiple sources (VCI, TCBS, MSN) with automatic fallback mechanisms.

    **Example Request:**
    ```bash
    curl -X GET "https://api.quantyfin.ai/api/v1/historical/data?symbol=VNM&start_date=2024-01-01&end_date=2024-01-31&interval=1D&asset_type=stock" \
         -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```

    **Example Response:**
    ```json
    {
      "symbol": "VNM",
      "asset_type": "stock",
      "data_source": "VCI",
      "interval": "1D",
      "data": [
        {
          "time": "2024-01-02T00:00:00Z",
          "open": 45.50,
          "high": 46.20,
          "low": 45.30,
          "close": 46.00,
          "volume": 1250000
        }
      ],
      "total_records": 23,
      "retrieved_at": "2024-01-02T10:30:00Z"
    }
    ```

    **Supported Time Intervals:** 1m, 5m, 15m, 30m, 1H, 1D, 1W, 1M

    **Rate Limits:** 100 requests per minute per user
    """,
)
async def get_historical_data(
    symbol: str = Query(
        ..., description="Asset symbol (e.g., 'VNM', 'AAPL')", examples="VNM"
    ),
    start_date: str = Query(
        ...,
        description="Start date in YYYY-MM-DD format",
        examples="2024-01-01",
    ),
    end_date: str = Query(
        ..., description="End date in YYYY-MM-DD format", examples="2024-01-31"
    ),
    interval: TimeInterval = Query(
        TimeInterval.DAY_1, description="Time interval"
    ),
    asset_type: AssetType = Query(AssetType.STOCK, description="Asset type"),
    data_source: Optional[str] = Query(
        None, description="Preferred data source (VCI, TCBS, MSN)"
    ),
    use_cache: bool = Query(True, description="Enable/disable caching"),
    use_fallback: bool = Query(
        True, description="Enable/disable fallback mechanisms"
    ),
    fallback_strategy: str = Query(
        "sequential",
        description="Fallback strategy: sequential, parallel, fastest",
    ),
    historical_service: HistoricalDataService = Depends(
        get_historical_data_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> HistoricalDataResponse:
    """
    Get historical market data for a specified symbol and date range.

    Features:
    - Caching with Redis for improved performance
    - Fallback mechanisms when primary data source fails
    - Rate limiting and circuit breaker protection
    - Comprehensive error handling
    - Support for multiple data sources (VCI, TCBS, MSN)
    """
    try:
        # Parse and validate date parameters
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError as e:
            raise InvalidParameterError(
                f"Invalid date format: {str(e)}", symbol, asset_type
            )

        # Create request object
        request = HistoricalDataRequest(
            symbol=symbol.upper().strip(),
            start_date=start_dt,
            end_date=end_dt,
            interval=interval,
            asset_type=asset_type,
            data_source=data_source.upper() if data_source else None,
        )

        # Validate request
        if len(request.symbol) == 0 or len(request.symbol) > 20:
            raise InvalidParameterError(
                "Symbol must be between 1 and 20 characters",
                symbol,
                asset_type,
            )

        # Get fallback strategy
        from app.core.application.historical_data_service import (
            FallbackStrategy,
        )

        strategy = getattr(
            FallbackStrategy,
            fallback_strategy.upper(),
            FallbackStrategy.SEQUENTIAL,
        )

        # Retrieve historical data
        response = await historical_service.get_historical_data(
            request=request,
            use_cache=use_cache,
            use_fallback=use_fallback,
            fallback_strategy=strategy,
        )

        return response

    except HistoricalDataError as e:
        # Convert domain errors to HTTP status codes
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
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing request: {str(e)}",
        )


@router.get(
    "/data/bulk",
    response_model=List[HistoricalDataResponse],
    summary="Get Bulk Historical Market Data",
    description="""
    Retrieve historical market data for multiple symbols in a single request.

    This endpoint allows you to fetch data for multiple assets efficiently, reducing
    the number of API calls needed for portfolio analysis and bulk operations.

    **Example Request:**
    ```bash
    curl -X GET "https://api.quantyfin.ai/api/v1/historical/data/bulk?symbols=VNM,FPT,MSN&start_date=2024-01-01&end_date=2024-01-31&interval=1D" \
         -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```

    **Example Response:**
    ```json
    [
      {
        "symbol": "VNM",
        "asset_type": "stock",
        "data_source": "VCI",
        "interval": "1D",
        "data": [...],
        "total_records": 23,
        "retrieved_at": "2024-01-02T10:30:00Z"
      },
      {
        "symbol": "FPT",
        "asset_type": "stock",
        "data_source": "TCBS",
        "interval": "1D",
        "data": [...],
        "total_records": 23,
        "retrieved_at": "2024-01-02T10:30:00Z"
      }
    ]
    ```

    **Limits:** Maximum 20 symbols per request
    """,
)
async def get_bulk_historical_data(
    symbols: List[str] = Query(
        ..., description="List of asset symbols", examples=["VNM", "FPT", "MSN"]
    ),
    start_date: str = Query(
        ...,
        description="Start date in YYYY-MM-DD format",
        examples="2024-01-01",
    ),
    end_date: str = Query(
        ..., description="End date in YYYY-MM-DD format", examples="2024-01-31"
    ),
    interval: TimeInterval = Query(
        TimeInterval.DAY_1, description="Time interval"
    ),
    asset_type: AssetType = Query(AssetType.STOCK, description="Asset type"),
    data_source: Optional[str] = Query(
        None, description="Preferred data source (VCI, TCBS, MSN)"
    ),
    use_cache: bool = Query(True, description="Enable/disable caching"),
    use_fallback: bool = Query(
        True, description="Enable/disable fallback mechanisms"
    ),
    fallback_strategy: str = Query(
        "parallel",
        description="Fallback strategy: sequential, parallel, fastest",
    ),
    max_concurrent: int = Query(
        5, description="Maximum concurrent requests", ge=1, le=20
    ),
    historical_service: HistoricalDataService = Depends(
        get_historical_data_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> List[HistoricalDataResponse]:
    """
    Get historical market data for multiple symbols in bulk.

    Features:
    - Concurrent processing for improved performance
    - Batching support for multiple symbols
    - Same caching and fallback mechanisms as single symbol endpoint
    - Rate limiting protection
    """
    try:
        # Validate input parameters
        if not symbols or len(symbols) == 0:
            raise InvalidParameterError(
                "At least one symbol must be provided", "BULK", asset_type
            )

        if len(symbols) > 50:
            raise InvalidParameterError(
                "Maximum 50 symbols per request", "BULK", asset_type
            )

        if max_concurrent < 1 or max_concurrent > 20:
            raise InvalidParameterError(
                "max_concurrent must be between 1 and 20", "BULK", asset_type
            )

        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError as e:
            raise InvalidParameterError(
                f"Invalid date format: {str(e)}", "BULK", asset_type
            )

        # Get fallback strategy
        from app.core.application.historical_data_service import (
            FallbackStrategy,
        )

        strategy = getattr(
            FallbackStrategy,
            fallback_strategy.upper(),
            FallbackStrategy.PARALLEL,
        )

        # Process symbols in bulk
        results = await historical_service.get_bulk_historical_data(
            symbols=symbols,
            start_date=start_dt,
            end_date=end_dt,
            interval=interval,
            asset_type=asset_type,
            data_source=data_source.upper() if data_source else None,
            use_cache=use_cache,
            use_fallback=use_fallback,
            fallback_strategy=strategy,
            max_concurrent=max_concurrent,
        )

        return results

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
            detail=f"Unexpected error processing bulk request: {str(e)}",
        )


@router.get("/data/intraday", response_model=Dict[str, Any])
async def get_intraday_data(
    symbol: str = Query(..., description="Asset symbol (e.g., 'VNM', 'AAPL')"),
    asset_type: AssetType = Query(AssetType.STOCK, description="Asset type"),
    interval: TimeInterval = Query(
        TimeInterval.MINUTE_5, description="Time interval"
    ),
    data_source: Optional[str] = Query(
        None, description="Preferred data source (VCI, TCBS, MSN)"
    ),
    page_size: int = Query(
        100, description="Number of data points to retrieve", ge=1, le=1000
    ),
    historical_service: HistoricalDataService = Depends(
        get_historical_data_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> Dict[str, Any]:
    """
    Get intraday market data for a specified symbol.

    Features:
    - Real-time intraday data retrieval
    - Multiple time intervals supported
    - Configurable page size for data points
    - Caching for frequently accessed data
    """
    try:
        # Validate symbol
        if len(symbol) == 0 or len(symbol) > 20:
            raise InvalidParameterError(
                "Symbol must be between 1 and 20 characters",
                symbol,
                asset_type,
            )

        # Validate page size
        if page_size < 1 or page_size > 1000:
            raise InvalidParameterError(
                "page_size must be between 1 and 1000", symbol, asset_type
            )

        # Get intraday data
        data_points = await historical_service.get_intraday_data(
            symbol=symbol.upper().strip(),
            asset_type=asset_type,
            interval=interval,
            data_source=data_source.upper() if data_source else None,
            page_size=page_size,
        )

        return {
            "symbol": symbol.upper().strip(),
            "asset_type": asset_type.value,
            "interval": interval.value,
            "data": [point.model_dump() for point in data_points],
            "total_records": len(data_points),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
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
            detail=f"Unexpected error processing intraday request: {str(e)}",
        )


@router.get("/data/real-time", response_model=Dict[str, Any])
async def get_real_time_quote(
    symbol: str = Query(..., description="Asset symbol (e.g., 'VNM', 'AAPL')"),
    asset_type: AssetType = Query(AssetType.STOCK, description="Asset type"),
    data_source: Optional[str] = Query(
        None, description="Preferred data source (VCI, TCBS, MSN)"
    ),
    historical_service: HistoricalDataService = Depends(
        get_historical_data_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> Dict[str, Any]:
    """
    Get real-time quote data for a specified symbol.

    Features:
    - Real-time price data
    - Multiple asset types supported
    - Fast response times with caching
    - Data validation and error handling
    """
    try:
        # Validate symbol
        if len(symbol) == 0 or len(symbol) > 20:
            raise InvalidParameterError(
                "Symbol must be between 1 and 20 characters",
                symbol,
                asset_type,
            )

        # Get real-time quote
        quote_data = await historical_service.get_real_time_quote(
            symbol=symbol.upper().strip(),
            asset_type=asset_type,
            data_source=data_source.upper() if data_source else None,
        )

        return {
            "symbol": symbol.upper().strip(),
            "asset_type": asset_type.value,
            "time": quote_data.time.isoformat(),
            "open": quote_data.open,
            "high": quote_data.high,
            "low": quote_data.low,
            "close": quote_data.close,
            "volume": quote_data.volume,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
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
            detail=f"Unexpected error processing real-time quote: {str(e)}",
        )


@router.get("/data/sources/health", response_model=List[DataSourceHealth])
async def get_data_source_health(
    historical_service: HistoricalDataService = Depends(
        get_historical_data_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> List[DataSourceHealth]:
    """
    Get health status of all data sources.

    Features:
    - Real-time health monitoring
    - Response time tracking
    - Success rate calculation
    - Error message reporting
    """
    try:
        health_status = await historical_service.get_all_data_sources_health()
        return health_status

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving data source health: {str(e)}",
        )


@router.get("/data/sources/metrics", response_model=Dict[str, Any])
async def get_data_source_metrics(
    historical_service: HistoricalDataService = Depends(
        get_historical_data_service
    ),
    current_user: dict = Depends(require_api_role),
    rate_limit_passed: dict = Depends(rate_limit_dependency),
) -> Dict[str, Any]:
    """
    Get performance metrics for all data sources.

    Features:
    - Request count tracking
    - Success rate monitoring
    - Response time statistics
    - Cache hit/miss ratios
    """
    try:
        metrics = await historical_service.get_data_sources_metrics()
        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving data source metrics: {str(e)}",
        )
