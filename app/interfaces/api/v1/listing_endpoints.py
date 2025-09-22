"""
Listing endpoints for Vietnamese stock market data.

This module provides API endpoints for accessing Vietnamese stock
including symbols, exchanges, industries, and market groups.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import HTTPBearer

from app.core.application.listing_service_factory import (
    ListingServiceFactory,
    create_listing_service,
)
from app.core.domain.enums import VietnameseExchange, VnstockDataSource
from app.interfaces.api.auth_dependencies import (
    get_current_active_user,
    rate_limit_dependency,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

listing_router = APIRouter(prefix="/listing", tags=["Listing"])


async def get_listing_service() -> ListingServiceFactory:
    """Get listing service instance."""
    return create_listing_service()


@listing_router.get(
    "/symbols",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get all stock symbols",
    description=(
        "Retrieve all available Vietnamese stock symbols with company names"
    ),
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_all_symbols_endpoint(
    listing_service: ListingServiceFactory = Depends(get_listing_service),
    data_source: Optional[VnstockDataSource] = None,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    force_refresh: bool = Query(
        False, description="Force refresh cached data"
    ),
) -> List[dict]:
    """
    Get all stock symbols from vnstock listing data.

    Returns:
        List[dict]: List of stock symbols with company information
    """
    try:
        symbols, metadata = await listing_service.all_stock_symbols(
            data_source=data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

        # Convert domain models to dictionaries for API response
        return [
            {
                "ticker": symbol.ticker,
                "organ_name": symbol.organ_name,
            }
            for symbol in symbols
        ]

    except Exception as e:
        logger.error("Failed to get all symbols", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symbols: {str(e)}",
        )


@listing_router.get(
    "/symbols/exchange",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get symbols by exchange",
    description=(
        "Retrieve symbols with exchange details, optionally filtered by "
        "specific exchange"
    ),
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_symbols_by_exchange_endpoint(
    exchange: Optional[VietnameseExchange] = Query(
        None, description="Filter by specific exchange"
    ),
    listing_service: ListingServiceFactory = Depends(get_listing_service),
    data_source: Optional[VnstockDataSource] = None,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    force_refresh: bool = Query(
        False, description="Force refresh cached data"
    ),
) -> List[dict]:
    """
    Get stock symbols filtered by exchange.

    Args:
        exchange: Vietnamese exchange to filter by

    Returns:
        List[dict]: List of exchange symbols with detailed information
    """
    try:
        if exchange:
            exchange_symbols, metadata = (
                await listing_service.symbols_by_exchange(
                    exchange=exchange,
                    data_source=data_source,
                    use_cache=use_cache,
                    force_refresh=force_refresh,
                )
            )
            # Convert ExchangeSymbol objects to dictionaries
            return [
                {
                    "symbol": symbol.symbol,
                    "symbol_id": symbol.symbol_id,
                    "type": symbol.type,
                    "exchange": symbol.exchange.value,
                    "en_organ_name": symbol.en_organ_name,
                    "en_organ_short_name": symbol.en_organ_short_name,
                    "organ_short_name": symbol.organ_short_name,
                    "organ_name": symbol.organ_name,
                }
                for symbol in exchange_symbols
            ]
        else:
            # If no exchange specified, get all symbols
            stock_symbols, metadata = await listing_service.all_stock_symbols(
                data_source=data_source,
                use_cache=use_cache,
                force_refresh=force_refresh,
            )
            # Convert StockSymbol objects to dictionaries
            return [
                {
                    "symbol": symbol.ticker,
                    "organ_name": symbol.organ_name,
                }
                for symbol in stock_symbols
            ]

    except Exception as e:
        logger.error("Failed to get symbols by exchange", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symbols by exchange: {str(e)}",
        )


@listing_router.get(
    "/symbols/vn30",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get VN30 constituent symbols",
    description="Retrieve the current list of 30 VN30 member symbols",
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_vn30_symbols_endpoint(
    listing_service: ListingServiceFactory = Depends(get_listing_service),
    data_source: Optional[VnstockDataSource] = None,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    force_refresh: bool = Query(
        False, description="Force refresh cached data"
    ),
) -> List[str]:
    """
    Get VN30 index constituent symbols.

    Returns:
        List[str]: List of VN30 ticker symbols
    """
    try:
        constituents, metadata = await listing_service.vn30_constituents(
            data_source=data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )
        return constituents

    except Exception as e:
        logger.error("Failed to get VN30 constituents", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve VN30 constituents: {str(e)}",
        )


@listing_router.get(
    "/symbols/group/{group_name}",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get symbols by market group",
    description="Retrieve symbols belonging to a specific market group",
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_symbols_by_group_endpoint(
    group_name: str = Path(
        ...,
        description="Market group name",
        regex=(
            r"^(VN30|VN100|VNMidCap|VNSmallCap|VNAllShare|HNX30|HNXCon|HNXFin|"
            r"HNXLCap|HNXMSCap|HNXMan|ETF|FU_INDEX|CW)$"
        ),
    ),
    listing_service: ListingServiceFactory = Depends(get_listing_service),
    data_source: Optional[VnstockDataSource] = None,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    force_refresh: bool = Query(
        False, description="Force refresh cached data"
    ),
) -> List[str]:
    """
    Get stock symbols filtered by market group.

    Args:
        group_name: Market group name (e.g., VN30, VN100, HNX30)

    Returns:
        List[str]: List of symbols from the specified market group
    """
    try:
        symbols, metadata = await listing_service.symbols_by_market_group(
            group=group_name,
            data_source=data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

        # Extract symbol tickers from the result
        return [symbol.ticker for symbol in symbols]

    except Exception as e:
        logger.error(
            "Failed to get symbols by group",
            exc_info=True,
            extra={"group": group_name},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Failed to retrieve symbols for group {group_name}: {str(e)}"
            ),
        )


@listing_router.get(
    "/symbols/industry",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get symbols by industry classification",
    description=(
        "Retrieve symbols with industry classification details, "
        "optionally filtered by industry"
    ),
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_symbols_by_industry_endpoint(
    industry_name: Optional[str] = Query(
        None, description="Filter by industry name (case-insensitive)"
    ),
    listing_service: ListingServiceFactory = Depends(get_listing_service),
    data_source: Optional[VnstockDataSource] = None,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    force_refresh: bool = Query(
        False, description="Force refresh cached data"
    ),
) -> List[dict]:
    """
    Get stock symbols filtered by industry.

    Args:
        industry_name: Industry name to filter by (case-insensitive)

    Returns:
        List[dict]: List of industry symbols with classification details
    """
    try:
        if industry_name:
            industry_symbols, metadata = (
                await listing_service.symbols_by_industry(
                    industry=industry_name,
                    data_source=data_source,
                    use_cache=use_cache,
                    force_refresh=force_refresh,
                )
            )
            # Convert IndustrySymbol objects to dictionaries
            return [
                {
                    "symbol": symbol.symbol,
                    "organ_name": symbol.organ_name,
                    "en_organ_name": symbol.en_organ_name,
                    "icb_name3": symbol.icb_name3,
                    "en_icb_name3": symbol.en_icb_name3,
                    "icb_name2": symbol.icb_name2,
                    "en_icb_name2": symbol.en_icb_name2,
                    "icb_name4": symbol.icb_name4,
                    "en_icb_name4": symbol.en_icb_name4,
                    "com_type_code": symbol.com_type_code,
                    "icb_code1": symbol.icb_code1,
                    "icb_code2": symbol.icb_code2,
                    "icb_code3": symbol.icb_code3,
                    "icb_code4": symbol.icb_code4,
                }
                for symbol in industry_symbols
            ]
        else:
            # If no industry specified, get all symbols
            stock_symbols, metadata = await listing_service.all_stock_symbols(
                data_source=data_source,
                use_cache=use_cache,
                force_refresh=force_refresh,
            )
            # Convert StockSymbol objects to dictionaries
            return [
                {
                    "symbol": symbol.ticker,
                    "organ_name": symbol.organ_name,
                }
                for symbol in stock_symbols
            ]

    except Exception as e:
        logger.error("Failed to get symbols by industry", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symbols by industry: {str(e)}",
        )


@listing_router.get(
    "/industries",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get ICB industry classifications",
    description="Retrieve all available ICB industry classifications",
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_icb_industries_endpoint(
    listing_service: ListingServiceFactory = Depends(get_listing_service),
    data_source: Optional[VnstockDataSource] = None,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    force_refresh: bool = Query(
        False, description="Force refresh cached data"
    ),
) -> List[dict]:
    """
    Get ICB industry classification hierarchy.

    Returns:
        List[dict]: List of ICB industry classifications
    """
    try:
        industries, metadata = await listing_service.icb_industries(
            data_source=data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

        # Convert domain models to dictionaries for API response
        return [
            {
                "icb_name": industry.icb_name,
                "en_icb_name": industry.en_icb_name,
                "icb_code": industry.icb_code,
                "level": industry.level,
            }
            for industry in industries
        ]

    except Exception as e:
        logger.error("Failed to get ICB industries", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ICB industries: {str(e)}",
        )


@listing_router.get(
    "/international/search",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Search international symbols",
    description=(
        "Search for international market symbols (FX, crypto, indices)"
    ),
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def search_international_symbols_endpoint(
    query: str = Query(
        ..., min_length=1, description="Search query (minimum 1 character)"
    ),
    listing_service: ListingServiceFactory = Depends(get_listing_service),
    data_source: Optional[VnstockDataSource] = None,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    force_refresh: bool = Query(
        False, description="Force refresh cached data"
    ),
) -> List[dict]:
    """
    Search international market symbols.

    Args:
        query: Search query for international symbols

    Returns:
        List[dict]: List of matching international symbols
    """
    try:
        symbols, metadata = await listing_service.international_symbols(
            data_source=data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

        # Filter symbols based on search query (case-insensitive)
        filtered_symbols = [
            symbol
            for symbol in symbols
            if query.lower() in symbol.symbol.lower()
            or query.lower() in symbol.eng_name.lower()
            or query.lower() in symbol.short_name.lower()
        ]

        # Convert domain models to dictionaries for API response
        return [
            {
                "symbol": symbol.symbol,
                "symbol_id": symbol.symbol_id,
                "exchange_name": symbol.exchange_name,
                "exchange_code_mic": symbol.exchange_code_mic,
                "short_name": symbol.short_name,
                "friendly_name": symbol.friendly_name,
                "eng_name": symbol.eng_name,
                "description": symbol.description,
                "local_name": symbol.local_name,
                "locale": symbol.locale,
            }
            for symbol in filtered_symbols
        ]

    except Exception as e:
        logger.error(
            "Failed to search international symbols",
            exc_info=True,
            extra={"query": query},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search international symbols: {str(e)}",
        )


@listing_router.get(
    "/exchanges",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get all available exchanges",
    description="Retrieve list of all available Vietnamese stock exchanges",
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_exchanges_endpoint() -> List[str]:
    """
    Get all available Vietnamese stock exchanges.

    Returns:
        List[str]: List of exchange codes (HOSE, HNX, UPCOM)
    """
    try:
        return [exchange.value for exchange in VietnameseExchange]

    except Exception as e:
        logger.error("Failed to get exchanges", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exchanges: {str(e)}",
        )


@listing_router.get(
    "/market-groups",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get all available market groups",
    description="Retrieve list of all available Vietnamese market groups",
    dependencies=[
        Depends(get_current_active_user),
        Depends(rate_limit_dependency),
    ],
)
async def get_market_groups_endpoint() -> List[str]:
    """
    Get all available Vietnamese market groups.

    Returns:
        List[str]: List of market group names
    """
    try:
        # Return predefined list of market groups as per OpenAPI spec
        return [
            "VN30",
            "VN100",
            "VNMidCap",
            "VNSmallCap",
            "VNAllShare",
            "HNX30",
            "HNXCon",
            "HNXFin",
            "HNXLCap",
            "HNXMSCap",
            "HNXMan",
            "ETF",
            "FU_INDEX",
            "CW",
        ]

    except Exception as e:
        logger.error("Failed to get market groups", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market groups: {str(e)}",
        )
