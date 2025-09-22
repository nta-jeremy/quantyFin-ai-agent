"""
Data conversion utilities for vnstock DataFrame to Pydantic model
transformations.

This module provides pure functions to convert vnstock library DataFrame
outputs to our domain models, following functional programming principles.
"""

from typing import Any, List

import pandas as pd
import structlog

from app.core.domain.enums import VietnameseExchange
from app.core.domain.listing_models import (
    ExchangeSymbol,
    ICBIndustry,
    IndustrySymbol,
    InternationalSymbol,
    StockSymbol,
)

logger = structlog.get_logger(__name__)


def convert_dataframe_to_stock_symbols(df: pd.DataFrame) -> List[StockSymbol]:
    """Convert vnstock DataFrame to StockSymbol models.

    Args:
        df: DataFrame from vnstock listing data

    Returns:
        List of StockSymbol models

    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    if df.empty:
        return []

    required_columns = ["ticker", "organ_name"]
    _validate_dataframe_columns(df, required_columns, "StockSymbol")

    stock_symbols = []
    for _, row in df.iterrows():
        try:
            ticker = str(row["ticker"]).strip()
            organ_name = str(row["organ_name"]).strip()

            if not ticker or not organ_name:
                logger.warning(
                    "Skipping row with empty ticker or organ_name",
                    row=row.to_dict(),
                )
                continue

            stock_symbol = StockSymbol(
                ticker=ticker,
                organ_name=organ_name,
            )
            stock_symbols.append(stock_symbol)

        except Exception as e:
            logger.error(
                "Error converting row to StockSymbol",
                row=row.to_dict(),
                error=str(e),
            )
            continue

    return stock_symbols


def convert_dataframe_to_exchange_symbols(
    df: pd.DataFrame,
) -> List[ExchangeSymbol]:
    """Convert vnstock DataFrame to ExchangeSymbol models.

    Args:
        df: DataFrame from vnstock listing data with exchange information

    Returns:
        List of ExchangeSymbol models

    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    if df.empty:
        return []

    required_columns = ["ticker", "organ_name", "exchange"]
    _validate_dataframe_columns(df, required_columns, "ExchangeSymbol")

    exchange_symbols = []
    for _, row in df.iterrows():
        try:
            symbol = str(row["ticker"]).strip()
            organ_name = str(row["organ_name"]).strip()
            exchange_str = str(row["exchange"]).strip().upper()

            if not symbol or not organ_name or not exchange_str:
                logger.warning(
                    "Skipping row with missing required fields",
                    row=row.to_dict(),
                )
                continue

            # Map exchange string to enum
            try:
                exchange = VietnameseExchange(exchange_str)
            except ValueError:
                logger.warning(
                    "Invalid exchange value, skipping row",
                    exchange=exchange_str,
                    row=row.to_dict(),
                )
                continue

            # Extract optional fields if available
            symbol_id = int(row.get("id", 1)) if pd.notna(row.get("id")) else 1
            security_type = str(row.get("type", "Stock")).strip()
            en_organ_name = str(row.get("en_organ_name", "")).strip() or None
            en_organ_short_name = (
                str(row.get("en_organ_short_name", "")).strip() or None
            )
            organ_short_name = (
                str(row.get("organ_short_name", "")).strip() or None
            )

            exchange_symbol = ExchangeSymbol(
                symbol=symbol,
                symbol_id=symbol_id,
                type=security_type,
                exchange=exchange,
                en_organ_name=en_organ_name,
                en_organ_short_name=en_organ_short_name,
                organ_short_name=organ_short_name,
                organ_name=organ_name,
            )
            exchange_symbols.append(exchange_symbol)

        except Exception as e:
            logger.error(
                "Error converting row to ExchangeSymbol",
                row=row.to_dict(),
                error=str(e),
            )
            continue

    return exchange_symbols


def convert_dataframe_to_industry_symbols(
    df: pd.DataFrame,
) -> List[IndustrySymbol]:
    """Convert vnstock DataFrame to IndustrySymbol models.

    Args:
        df: DataFrame from vnstock listing data with industry classification

    Returns:
        List of IndustrySymbol models

    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    if df.empty:
        return []

    required_columns = ["ticker", "organ_name", "icb_name3"]
    _validate_dataframe_columns(df, required_columns, "IndustrySymbol")

    industry_symbols = []
    for _, row in df.iterrows():
        try:
            symbol = str(row["ticker"]).strip()
            organ_name = str(row["organ_name"]).strip()
            icb_name3 = str(row["icb_name3"]).strip()

            if not symbol or not organ_name or not icb_name3:
                logger.warning(
                    "Skipping row with missing required fields",
                    row=row.to_dict(),
                )
                continue

            # Extract optional fields
            en_organ_name = str(row.get("en_organ_name", "")).strip() or None
            en_icb_name3 = str(row.get("en_icb_name3", "")).strip() or None
            icb_name2 = str(row.get("icb_name2", "")).strip() or None
            en_icb_name2 = str(row.get("en_icb_name2", "")).strip() or None
            icb_name4 = str(row.get("icb_name4", "")).strip() or None
            en_icb_name4 = str(row.get("en_icb_name4", "")).strip() or None

            # Company type and ICB codes
            com_type_code = str(row.get("com_type_code", "")).strip() or None
            icb_codes = {
                f"icb_code{i}": str(row.get(f"icb_code{i}", "")).strip()
                or None
                for i in range(1, 5)
            }

            industry_symbol = IndustrySymbol(
                symbol=symbol,
                organ_name=organ_name,
                en_organ_name=en_organ_name,
                icb_name3=icb_name3,
                en_icb_name3=en_icb_name3,
                icb_name2=icb_name2,
                en_icb_name2=en_icb_name2,
                icb_name4=icb_name4,
                en_icb_name4=en_icb_name4,
                com_type_code=com_type_code,
                **icb_codes,
            )
            industry_symbols.append(industry_symbol)

        except Exception as e:
            logger.error(
                "Error converting row to IndustrySymbol",
                row=row.to_dict(),
                error=str(e),
            )
            continue

    return industry_symbols


def convert_dataframe_to_icb_industries(df: pd.DataFrame) -> List[ICBIndustry]:
    """Convert vnstock DataFrame to ICBIndustry models.

    Args:
        df: DataFrame from vnstock ICB industry data

    Returns:
        List of ICBIndustry models

    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    if df.empty:
        return []

    required_columns = ["icb_name", "en_icb_name", "icb_code", "level"]
    _validate_dataframe_columns(df, required_columns, "ICBIndustry")

    icb_industries = []
    for _, row in df.iterrows():
        try:
            icb_name = str(row["icb_name"]).strip()
            en_icb_name = str(row["en_icb_name"]).strip()
            icb_code = str(row["icb_code"]).strip()
            level = int(row["level"])

            if not icb_name or not en_icb_name or not icb_code:
                logger.warning(
                    "Skipping row with missing required fields",
                    row=row.to_dict(),
                )
                continue

            if level < 1 or level > 4:
                logger.warning(
                    "Invalid ICB level, skipping row",
                    level=level,
                    row=row.to_dict(),
                )
                continue

            icb_industry = ICBIndustry(
                icb_name=icb_name,
                en_icb_name=en_icb_name,
                icb_code=icb_code,
                level=level,
            )
            icb_industries.append(icb_industry)

        except Exception as e:
            logger.error(
                "Error converting row to ICBIndustry",
                row=row.to_dict(),
                error=str(e),
            )
            continue

    return icb_industries


def convert_dataframe_to_international_symbols(
    df: pd.DataFrame,
) -> List[InternationalSymbol]:
    """Convert vnstock DataFrame to InternationalSymbol models.

    Args:
        df: DataFrame from vnstock international symbols data

    Returns:
        List of InternationalSymbol models

    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    if df.empty:
        return []

    required_columns = ["symbol", "symbol_id", "exchange_name", "short_name"]
    _validate_dataframe_columns(df, required_columns, "InternationalSymbol")

    international_symbols = []
    for _, row in df.iterrows():
        try:
            symbol = str(row["symbol"]).strip()
            symbol_id = str(row["symbol_id"]).strip()
            exchange_name = str(row["exchange_name"]).strip()
            exchange_code_mic = (
                str(row.get("exchange_code_mic", "")).strip().upper()
            )
            short_name = str(row["short_name"]).strip()
            friendly_name = str(row.get("friendly_name", short_name)).strip()
            eng_name = str(row.get("eng_name", short_name)).strip()
            description = (
                str(row.get("description", "")).strip()
                or "No description available"
            )
            local_name = str(row.get("local_name", short_name)).strip()
            locale = str(row.get("locale", "en-US")).strip().lower()

            if not all([symbol, symbol_id, exchange_name, short_name]):
                logger.warning(
                    "Skipping row with missing required fields",
                    row=row.to_dict(),
                )
                continue

            # Validate MIC code format
            if (
                not exchange_code_mic
                or len(exchange_code_mic) != 4
                or not exchange_code_mic.isalpha()
            ):
                logger.warning(
                    "Invalid MIC code, skipping row",
                    mic_code=exchange_code_mic,
                    row=row.to_dict(),
                )
                continue

            # Validate locale format
            if not _validate_locale_format(locale):
                logger.warning(
                    "Invalid locale format, using default",
                    locale=locale,
                    row=row.to_dict(),
                )
                locale = "en-us"

            international_symbol = InternationalSymbol(
                symbol=symbol,
                symbol_id=symbol_id,
                exchange_name=exchange_name,
                exchange_code_mic=exchange_code_mic,
                short_name=short_name,
                friendly_name=friendly_name,
                eng_name=eng_name,
                description=description,
                local_name=local_name,
                locale=locale,
            )
            international_symbols.append(international_symbol)

        except Exception as e:
            logger.error(
                "Error converting row to InternationalSymbol",
                row=row.to_dict(),
                error=str(e),
            )
            continue

    return international_symbols


def extract_vn30_constituents(df: pd.DataFrame) -> List[str]:
    """Extract VN30 constituent symbols from DataFrame.

    Args:
        df: DataFrame containing VN30 constituents data

    Returns:
        List of VN30 ticker symbols
    """
    if df.empty:
        return []

    if "ticker" not in df.columns:
        logger.error(
            "DataFrame missing required 'ticker' column for VN30 constituents"
        )
        return []

    # Extract unique, valid ticker symbols
    tickers = []
    for ticker in df["ticker"].dropna().unique():
        ticker_str = str(ticker).strip().upper()
        if ticker_str and ticker_str.isalpha() and 2 <= len(ticker_str) <= 4:
            tickers.append(ticker_str)
        else:
            logger.warning(
                "Invalid ticker format in VN30 constituents", ticker=ticker
            )

    return tickers


def clean_and_validate_dataframe(
    df: pd.DataFrame, operation_name: str
) -> pd.DataFrame:
    """Clean and validate DataFrame for conversion operations.

    Args:
        df: Input DataFrame
        operation_name: Name of operation for logging

    Returns:
        Cleaned DataFrame

    Raises:
        ValueError: If DataFrame is invalid after cleaning
    """
    if df.empty:
        logger.warning(f"Empty DataFrame provided for {operation_name}")
        return df

    # Remove completely empty rows
    df_cleaned = df.dropna(how="all")

    if df_cleaned.empty:
        logger.warning(
            f"DataFrame contains no valid data for {operation_name}"
        )
        return df_cleaned

    # Log cleaning statistics
    removed_rows = len(df) - len(df_cleaned)
    if removed_rows > 0:
        logger.info(
            f"Cleaned DataFrame for {operation_name}",
            original_rows=len(df),
            cleaned_rows=len(df_cleaned),
            removed_rows=removed_rows,
        )

    return df_cleaned


def _validate_dataframe_columns(
    df: pd.DataFrame, required_columns: List[str], model_name: str
) -> None:
    """Validate that DataFrame contains required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        model_name: Name of the model for error messages

    Raises:
        ValueError: If required columns are missing
    """
    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]
    if missing_columns:
        error_msg = (
            f"Missing required columns for {model_name}: {missing_columns}"
        )
        logger.error(
            error_msg,
            available_columns=list(df.columns),
            required_columns=required_columns,
        )
        raise ValueError(error_msg)


def _validate_locale_format(locale: str) -> bool:
    """Validate locale format (xx-XX).

    Args:
        locale: Locale string to validate

    Returns:
        True if valid, False otherwise
    """
    parts = locale.split("-")
    return (
        len(parts) == 2
        and len(parts[0]) == 2
        and len(parts[1]) == 2
        and parts[0].isalpha()
        and parts[1].isalpha()
    )


def safe_string_conversion(value: Any, default: str = "") -> str:
    """Safely convert any value to string, handling NaN and None.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        String representation or default
    """
    if pd.isna(value) or value is None:
        return default

    try:
        result = str(value).strip()
        return default if not result else result
    except Exception:
        return default


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """Safely convert value to integer, handling NaN and None.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    if pd.isna(value) or value is None:
        return default

    try:
        return int(float(value))
    except Exception:
        return default
