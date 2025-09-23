"""
Financial reporting API endpoints for QuantyFinAI Agent.

This module contains endpoints for retrieving financial reports and data
following hexagonal architecture principles and constitutional requirements.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.application.financial_report_service import FinancialReportService
from app.core.domain.data_source_models import DataSource
from app.core.domain.financial_reports import (
    BalanceSheetResponse,
    ComprehensiveFinancialResponse,
    FinancialReportRequest,
)
from app.core.domain.historical_models import (
    DataSourceUnavailableError,
    DataValidationError,
    InvalidParameterError,
    SymbolNotFoundError,
)

from ..auth_dependencies import (
    get_current_active_user,
    rate_limit_dependency,
    require_api_role,
)
from .dependencies import get_financial_report_service

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["financial-reports"])


@router.get(
    "/balance-sheet/{symbol}",
    response_model=Dict[str, Any],
    summary="Get Balance Sheet Data",
    description="""
    Retrieve balance sheet data for a specific company.

    This endpoint provides comprehensive balance sheet information including assets, liabilities,
    and equity data. The data is retrieved from multiple sources (VCI, TCBS) with automatic
    fallback mechanisms and intelligent caching.

    **Features:**
    - Support for both annual and quarterly reports
    - Bilingual support (Vietnamese/English)
    - Intelligent caching with configurable TTL
    - Automatic fallback between data sources
    - Comprehensive data validation and error handling

    **Data Source Priority:**
    1. Primary: User-specified source (VCI or TCBS)
    2. Fallback: VCI (if primary fails)

    **Response Structure:**
    - data: Array of balance sheet records with detailed financial metrics
    - metadata: Response information including source, timing, and cache status
    """,
)
async def get_balance_sheet(
    symbol: str,
    source: DataSource = Query(DataSource.VCI, description="Data source preference"),
    period: str = Query("year", regex="^(year|quarter)$", description="Report period"),
    language: str = Query("vi", regex="^(vi|en)$", description="Report language"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    rate_limit_ok: bool = Depends(rate_limit_dependency),
    financial_service: FinancialReportService = Depends(get_financial_report_service),
) -> Dict[str, Any]:
    """Get balance sheet data for a company symbol."""
    logger.info(
        "Balance sheet request received",
        symbol=symbol.upper(),
        source=source.value,
        period=period,
        language=language,
        use_cache=use_cache,
    )

    try:
        response = await financial_service.get_balance_sheet(
            symbol=symbol.upper(),
            source=source,
            period=period,
            language=language,
            use_cache=use_cache,
        )

        logger.info(
            "Balance sheet request completed successfully",
            symbol=symbol.upper(),
            record_count=len(response.data) if response.data else 0,
            source_used=response.metadata.source if response.metadata else source.value,
            cache_used=response.metadata.from_cache if response.metadata else False,
        )

        return {
            "success": True,
            "data": response.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except SymbolNotFoundError as e:
        logger.warning(
            "Balance sheet request failed - symbol not found",
            symbol=symbol.upper(),
            error=str(e),
        )
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        logger.warning(
            "Balance sheet request failed - invalid parameters",
            symbol=symbol.upper(),
            error=str(e),
        )
        raise HTTPException(status_code=422, detail=str(e))
    except DataSourceUnavailableError as e:
        logger.error(
            "Balance sheet request failed - data source unavailable",
            symbol=symbol.upper(),
            source=source.value,
            error=str(e),
        )
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(
            "Balance sheet request failed - unexpected error",
            symbol=symbol.upper(),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/income-statement/{symbol}",
    response_model=Dict[str, Any],
    summary="Get Income Statement Data",
    description="""
    Retrieve income statement data for a specific company.

    This endpoint provides comprehensive income statement information including revenue,
    expenses, and profitability metrics. The data is retrieved from multiple sources
    with automatic fallback mechanisms and intelligent caching.

    **Features:**
    - Support for both annual and quarterly reports
    - Bilingual support (Vietnamese/English)
    - Intelligent caching with configurable TTL
    - Automatic fallback between data sources
    - Comprehensive data validation and error handling

    **Key Metrics Provided:**
    - Total revenue and operating revenue
    - Cost of goods sold and gross profit
    - Operating expenses and income
    - Net income and EPS data
    """,
)
async def get_income_statement(
    symbol: str,
    source: DataSource = Query(DataSource.VCI, description="Data source preference"),
    period: str = Query("year", regex="^(year|quarter)$", description="Report period"),
    language: str = Query("vi", regex="^(vi|en)$", description="Report language"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    rate_limit_ok: bool = Depends(rate_limit_dependency),
    financial_service: FinancialReportService = Depends(get_financial_report_service),
) -> Dict[str, Any]:
    """Get income statement data for a company symbol."""
    try:
        response = await financial_service.get_income_statement(
            symbol=symbol.upper(),
            source=source,
            period=period,
            language=language,
            use_cache=use_cache,
        )

        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DataSourceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/cash-flow/{symbol}",
    response_model=Dict[str, Any],
    summary="Get Cash Flow Statement Data",
    description="""
    Retrieve cash flow statement data for a specific company.

    This endpoint provides comprehensive cash flow information including operating,
    investing, and financing activities. The data is retrieved from multiple sources
    with automatic fallback mechanisms and intelligent caching.

    **Features:**
    - Support for both annual and quarterly reports
    - Bilingual support (Vietnamese/English)
    - Intelligent caching with configurable TTL
    - Automatic fallback between data sources
    - Comprehensive data validation and error handling

    **Key Metrics Provided:**
    - Operating cash flow and changes in working capital
    - Capital expenditures and investing activities
    - Financing activities and dividend payments
    - Free cash flow calculations
    """,
)
async def get_cash_flow(
    symbol: str,
    source: DataSource = Query(DataSource.VCI, description="Data source preference"),
    period: str = Query("year", regex="^(year|quarter)$", description="Report period"),
    language: str = Query("vi", regex="^(vi|en)$", description="Report language"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    rate_limit_ok: bool = Depends(rate_limit_dependency),
    financial_service: FinancialReportService = Depends(get_financial_report_service),
) -> Dict[str, Any]:
    """Get cash flow statement data for a company symbol."""
    try:
        response = await financial_service.get_cash_flow(
            symbol=symbol.upper(),
            source=source,
            period=period,
            language=language,
            use_cache=use_cache,
        )

        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DataSourceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/financial-ratios/{symbol}",
    response_model=Dict[str, Any],
    summary="Get Financial Ratios Data",
    description="""
    Retrieve financial ratios and metrics for a specific company.

    This endpoint provides comprehensive financial ratios including valuation,
    profitability, liquidity, leverage, and efficiency metrics. The data is retrieved
    from multiple sources with automatic fallback mechanisms and intelligent caching.

    **Features:**
    - Support for both annual and quarterly ratios
    - Bilingual support (Vietnamese/English)
    - Intelligent caching with configurable TTL
    - Automatic fallback between data sources
    - Comprehensive data validation and error handling

    **Ratio Categories Provided:**
    - Valuation ratios (P/E, P/B, P/S, EV/EBITDA)
    - Profitability ratios (ROE, ROA, margins)
    - Liquidity ratios (Current, Quick, Cash ratios)
    - Leverage ratios (D/E, D/A, interest coverage)
    - Efficiency ratios (Asset turnover, inventory turnover)
    """,
)
async def get_financial_ratios(
    symbol: str,
    source: DataSource = Query(DataSource.VCI, description="Data source preference"),
    period: str = Query("year", regex="^(year|quarter)$", description="Report period"),
    language: str = Query("vi", regex="^(vi|en)$", description="Report language"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    rate_limit_ok: bool = Depends(rate_limit_dependency),
    financial_service: FinancialReportService = Depends(get_financial_report_service),
) -> Dict[str, Any]:
    """Get financial ratios data for a company symbol."""
    try:
        response = await financial_service.get_financial_ratios(
            symbol=symbol.upper(),
            source=source,
            period=period,
            language=language,
            use_cache=use_cache,
        )

        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DataSourceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/comprehensive/{symbol}",
    response_model=Dict[str, Any],
    summary="Get Comprehensive Financial Data",
    description="""
    Retrieve comprehensive financial data from all report types for a specific company.

    This endpoint provides a complete financial overview including balance sheet,
    income statement, cash flow, and financial ratios data in a single response.
    The data is retrieved concurrently from multiple sources with automatic fallback
    mechanisms and intelligent caching.

    **Features:**
    - Concurrent fetching of all report types for optimal performance
    - Support for both annual and quarterly reports
    - Bilingual support (Vietnamese/English)
    - Intelligent caching with configurable TTL
    - Automatic fallback between data sources
    - Data quality metrics and processing time tracking
    - Comprehensive data validation and error handling

    **Data Quality Metrics Provided:**
    - Completeness indicators for each report type
    - Record counts and latest available dates
    - Processing time performance metrics
    - Data source and cache status information

    **Use Cases:**
    - Comprehensive financial analysis
    - Investment research and due diligence
    - Financial modeling and valuation
    - Risk assessment and analysis
    """,
)
async def get_comprehensive_financial_data(
    symbol: str,
    source: DataSource = Query(DataSource.VCI, description="Data source preference"),
    period: str = Query("year", regex="^(year|quarter)$", description="Report period"),
    language: str = Query("vi", regex="^(vi|en)$", description="Report language"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    rate_limit_ok: bool = Depends(rate_limit_dependency),
    financial_service: FinancialReportService = Depends(get_financial_report_service),
) -> Dict[str, Any]:
    """Get comprehensive financial data for a company symbol."""
    try:
        response = await financial_service.get_comprehensive_financial_data(
            symbol=symbol.upper(),
            source=source,
            period=period,
            language=language,
            use_cache=use_cache,
        )

        return {
            "success": True,
            "data": response.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DataSourceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/cache",
    response_model=Dict[str, Any],
    summary="Clear Financial Reports Cache",
    description="""
    Clear cached financial reports data.

    This endpoint allows clearing the cache for financial reports data.
    Supports selective clearing by symbol, report type, or data source.

    **Parameters:**
    - symbol: Specific symbol to clear (optional, clears all if not specified)
    - report_type: Specific report type to clear (optional, clears all if not specified)
    - source: Specific data source to clear (optional, clears all if not specified)

    **Use Cases:**
    - Force refresh of cached data
    - Clear stale or outdated cache entries
    - Troubleshooting cache-related issues
    - Memory management and cache optimization
    """,
)
async def clear_financial_cache(
    symbol: Optional[str] = Query(None, description="Specific symbol to clear"),
    report_type: Optional[str] = Query(None, description="Specific report type to clear"),
    source: Optional[DataSource] = Query(None, description="Specific data source to clear"),
    current_user: Dict[str, Any] = Depends(require_api_role),
    financial_service: FinancialReportService = Depends(get_financial_report_service),
) -> Dict[str, Any]:
    """Clear cached financial reports data."""
    try:
        result = await financial_service.clear_cache(
            symbol=symbol.upper() if symbol else None,
            report_type=report_type,
            source=source,
        )

        return {
            "success": True,
            "message": f"Cache cleared successfully",
            "keys_removed": result.keys_removed,
            "bytes_freed": result.bytes_freed,
            "timestamp": result.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get(
    "/metrics",
    response_model=Dict[str, Any],
    summary="Get Financial Reports Service Metrics",
    description="""
    Retrieve performance metrics for the financial reports service.

    This endpoint provides comprehensive metrics including cache performance,
    data source health, and service-level indicators.

    **Metrics Provided:**
    - Cache performance (hit rate, memory usage, key counts)
    - Data source health and availability
    - Service performance and availability
    - Error rates and response times

    **Use Cases:**
    - Service monitoring and health checks
    - Performance optimization and tuning
    - Capacity planning and scaling
    - Troubleshooting and diagnostics
    """,
)
async def get_financial_metrics(
    current_user: Dict[str, Any] = Depends(require_api_role),
    financial_service: FinancialReportService = Depends(get_financial_report_service),
) -> Dict[str, Any]:
    """Get financial reports service metrics."""
    try:
        metrics = await financial_service.get_service_metrics()

        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")