"""
Unit tests for vnstock data conversion utilities.

Tests the pure functions that convert vnstock DataFrame data to Pydantic
models.
"""

import pandas as pd
import pytest

from app.core.domain.enums import VietnameseExchange
from app.core.domain.listing_models import (
    ICBIndustry,
    StockSymbol,
)
from app.infrastructure.data_sources.vnstock_data_converters import (
    clean_and_validate_dataframe,
    convert_dataframe_to_exchange_symbols,
    convert_dataframe_to_icb_industries,
    convert_dataframe_to_industry_symbols,
    convert_dataframe_to_international_symbols,
    convert_dataframe_to_stock_symbols,
    extract_vn30_constituents,
    safe_int_conversion,
    safe_string_conversion,
)


class TestStockSymbolConversion:
    """Test StockSymbol DataFrame conversion."""

    def test_convert_empty_dataframe(self) -> None:
        """Test conversion of empty DataFrame."""
        df = pd.DataFrame()
        result = convert_dataframe_to_stock_symbols(df)
        assert result == []

    def test_convert_valid_stock_symbols(self) -> None:
        """Test conversion of valid stock symbol data."""
        df = pd.DataFrame(
            [
                {"ticker": "VCB", "organ_name": "Vietcombank"},
                {"ticker": "TCB", "organ_name": "Techcombank"},
                {"ticker": "ACB", "organ_name": "Asia Commercial Bank"},
            ]
        )

        result = convert_dataframe_to_stock_symbols(df)

        assert len(result) == 3
        assert all(isinstance(symbol, StockSymbol) for symbol in result)

        # Check first symbol
        vcb = result[0]
        assert vcb.ticker == "VCB"
        assert vcb.organ_name == "Vietcombank"

    def test_convert_with_missing_required_columns(self) -> None:
        """Test conversion with missing required columns raises ValueError."""
        df = pd.DataFrame([{"ticker": "VCB"}])  # Missing organ_name

        with pytest.raises(ValueError, match="Missing required columns"):
            convert_dataframe_to_stock_symbols(df)

    def test_convert_with_empty_values(self) -> None:
        """Test conversion handles empty values correctly."""
        df = pd.DataFrame(
            [
                {"ticker": "VCB", "organ_name": "Vietcombank"},
                {
                    "ticker": "",
                    "organ_name": "Empty Bank",
                },  # Should be skipped
                {"ticker": "TCB", "organ_name": ""},  # Should be skipped
                {"ticker": "ACB", "organ_name": "Asia Commercial Bank"},
            ]
        )

        result = convert_dataframe_to_stock_symbols(df)

        # Should only have 2 valid symbols
        assert len(result) == 2
        tickers = [symbol.ticker for symbol in result]
        assert "VCB" in tickers
        assert "ACB" in tickers
        assert "TCB" not in tickers

    def test_convert_with_whitespace_values(self) -> None:
        """Test conversion handles whitespace correctly."""
        df = pd.DataFrame(
            [
                {"ticker": "  VCB  ", "organ_name": "  Vietcombank  "},
            ]
        )

        result = convert_dataframe_to_stock_symbols(df)

        assert len(result) == 1
        symbol = result[0]
        assert symbol.ticker == "VCB"
        assert symbol.organ_name == "Vietcombank"


class TestExchangeSymbolConversion:
    """Test ExchangeSymbol DataFrame conversion."""

    def test_convert_valid_exchange_symbols(self) -> None:
        """Test conversion of valid exchange symbol data."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "VCB",
                    "organ_name": "Vietcombank",
                    "exchange": "HOSE",
                    "id": 1,
                    "type": "Stock",
                    "en_organ_name": "Vietcombank JSC",
                    "en_organ_short_name": "VCB",
                    "organ_short_name": "Ngan hang TMCP Ngoai thuong VN",
                },
            ]
        )

        result = convert_dataframe_to_exchange_symbols(df)

        assert len(result) == 1
        symbol = result[0]
        assert symbol.symbol == "VCB"
        assert symbol.exchange == VietnameseExchange.HOSE
        assert symbol.symbol_id == 1
        assert symbol.type == "Stock"

    def test_convert_invalid_exchange(self) -> None:
        """Test conversion with invalid exchange value."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "VCB",
                    "organ_name": "Vietcombank",
                    "exchange": "INVALID",
                },
            ]
        )

        result = convert_dataframe_to_exchange_symbols(df)
        # Should skip invalid exchange
        assert len(result) == 0

    def test_convert_missing_optional_fields(self) -> None:
        """Test conversion with missing optional fields uses defaults."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "VCB",
                    "organ_name": "Vietcombank",
                    "exchange": "HOSE",
                },
            ]
        )

        result = convert_dataframe_to_exchange_symbols(df)

        assert len(result) == 1
        symbol = result[0]
        assert symbol.symbol_id == 1  # Default value
        assert symbol.type == "Stock"  # Default value
        assert symbol.en_organ_name is None


class TestIndustrySymbolConversion:
    """Test IndustrySymbol DataFrame conversion."""

    def test_convert_valid_industry_symbols(self) -> None:
        """Test conversion of valid industry symbol data."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "VCB",
                    "organ_name": "Vietcombank",
                    "icb_name3": "Banks",
                    "en_icb_name3": "Banks",
                    "icb_name2": "Financials",
                    "en_icb_name2": "Financials",
                    "icb_name4": "Commercial Banks",
                    "en_icb_name4": "Commercial Banks",
                    "com_type_code": "JSC",
                    "icb_code1": "8000",
                    "icb_code2": "8010",
                    "icb_code3": "801010",
                    "icb_code4": "80101010",
                },
            ]
        )

        result = convert_dataframe_to_industry_symbols(df)

        assert len(result) == 1
        symbol = result[0]
        assert symbol.symbol == "VCB"
        assert symbol.icb_name3 == "Banks"
        assert symbol.en_icb_name3 == "Banks"
        assert symbol.icb_code1 == "8000"
        assert symbol.icb_code4 == "80101010"

    def test_convert_industry_symbols_partial_data(self) -> None:
        """Test conversion with partial industry data."""
        df = pd.DataFrame(
            [
                {
                    "ticker": "VCB",
                    "organ_name": "Vietcombank",
                    "icb_name3": "Banks",
                    # Missing many optional fields
                },
            ]
        )

        result = convert_dataframe_to_industry_symbols(df)

        assert len(result) == 1
        symbol = result[0]
        assert symbol.symbol == "VCB"
        assert symbol.icb_name3 == "Banks"
        assert symbol.en_icb_name3 is None
        assert symbol.icb_code1 is None


class TestICBIndustryConversion:
    """Test ICBIndustry DataFrame conversion."""

    def test_convert_valid_icb_industries(self) -> None:
        """Test conversion of valid ICB industry data."""
        df = pd.DataFrame(
            [
                {
                    "icb_name": "Ngan hang",
                    "en_icb_name": "Banks",
                    "icb_code": "801010",
                    "level": 3,
                },
                {
                    "icb_name": "Tai chinh",
                    "en_icb_name": "Financials",
                    "icb_code": "8000",
                    "level": 1,
                },
            ]
        )

        result = convert_dataframe_to_icb_industries(df)

        assert len(result) == 2
        industry1, industry2 = result

        assert isinstance(industry1, ICBIndustry)
        assert industry1.icb_name == "Ngan hang"
        assert industry1.en_icb_name == "Banks"
        assert industry1.icb_code == "801010"
        assert industry1.level == 3

    def test_convert_invalid_level(self) -> None:
        """Test conversion with invalid ICB level."""
        df = pd.DataFrame(
            [
                {
                    "icb_name": "Test",
                    "en_icb_name": "Test",
                    "icb_code": "123",
                    "level": 5,  # Invalid level (> 4)
                },
            ]
        )

        result = convert_dataframe_to_icb_industries(df)
        # Should skip invalid level
        assert len(result) == 0

    def test_convert_non_numeric_icb_code(self) -> None:
        """Test conversion with non-numeric ICB code."""
        df = pd.DataFrame(
            [
                {
                    "icb_name": "Test",
                    "en_icb_name": "Test",
                    "icb_code": "ABC123",  # Invalid (should be numeric)
                    "level": 2,
                },
            ]
        )

        # Should skip invalid ICB codes due to validation
        result = convert_dataframe_to_icb_industries(df)
        assert len(result) == 0


class TestInternationalSymbolConversion:
    """Test InternationalSymbol DataFrame conversion."""

    def test_convert_valid_international_symbols(self) -> None:
        """Test conversion of valid international symbol data."""
        df = pd.DataFrame(
            [
                {
                    "symbol": "EURUSD",
                    "symbol_id": "EURUSD_1",
                    "exchange_name": "Forex",
                    "exchange_code_mic": "FORE",
                    "short_name": "EUR/USD",
                    "friendly_name": "Euro to US Dollar",
                    "eng_name": "Euro/US Dollar",
                    "description": "Euro vs US Dollar exchange rate",
                    "local_name": "EUR/USD",
                    "locale": "en-US",
                },
            ]
        )

        result = convert_dataframe_to_international_symbols(df)

        assert len(result) == 1
        symbol = result[0]
        assert symbol.symbol == "EURUSD"
        assert symbol.exchange_code_mic == "FORE"
        assert symbol.locale == "en-us"

    def test_convert_invalid_mic_code(self) -> None:
        """Test conversion with invalid MIC code."""
        df = pd.DataFrame(
            [
                {
                    "symbol": "TEST",
                    "symbol_id": "TEST_1",
                    "exchange_name": "Test Exchange",
                    "exchange_code_mic": "123",  # Invalid
                    # (should be 4 letters)
                    "short_name": "Test",
                    "eng_name": "Test",
                    "description": "Test",
                    "local_name": "Test",
                    "locale": "en-US",
                },
            ]
        )

        result = convert_dataframe_to_international_symbols(df)
        # Should skip invalid MIC code
        assert len(result) == 0

    def test_convert_invalid_locale(self) -> None:
        """Test conversion with invalid locale format."""
        df = pd.DataFrame(
            [
                {
                    "symbol": "TEST",
                    "symbol_id": "TEST_1",
                    "exchange_name": "Test Exchange",
                    "exchange_code_mic": "TEST",
                    "short_name": "Test",
                    "eng_name": "Test",
                    "description": "Test",
                    "local_name": "Test",
                    "locale": "invalid-locale-format",
                },
            ]
        )

        result = convert_dataframe_to_international_symbols(df)

        assert len(result) == 1
        symbol = result[0]
        assert symbol.locale == "en-us"  # Should default to en-us


class TestVN30Constituents:
    """Test VN30 constituent extraction."""

    def test_extract_valid_vn30_constituents(self) -> None:
        """Test extraction of valid VN30 constituents."""
        df = pd.DataFrame(
            {
                "ticker": [
                    "VCB",
                    "TCB",
                    "ACB",
                    "HPG",
                    "MSN",
                    "Invalid",
                    "123",
                    "A",
                ],
            }
        )

        result = extract_vn30_constituents(df)

        # Should only include valid tickers (2-4 alpha characters)
        expected = ["VCB", "TCB", "ACB", "HPG", "MSN"]
        assert result == expected

    def test_extract_empty_dataframe(self) -> None:
        """Test extraction from empty DataFrame."""
        df = pd.DataFrame()
        result = extract_vn30_constituents(df)
        assert result == []

    def test_extract_missing_ticker_column(self) -> None:
        """Test extraction when ticker column is missing."""
        df = pd.DataFrame({"symbol": ["VCB", "TCB"]})
        result = extract_vn30_constituents(df)
        assert result == []


class TestDataFrameCleaning:
    """Test DataFrame cleaning utilities."""

    def test_clean_empty_dataframe(self) -> None:
        """Test cleaning empty DataFrame."""
        df = pd.DataFrame()
        result = clean_and_validate_dataframe(df, "test")
        assert result.empty

    def test_clean_dataframe_with_empty_rows(self) -> None:
        """Test cleaning DataFrame with completely empty rows."""
        df = pd.DataFrame(
            [
                {"ticker": "VCB", "organ_name": "Vietcombank"},
                {"ticker": None, "organ_name": None},
                {"ticker": "TCB", "organ_name": "Techcombank"},
                pd.Series([None, None], index=["ticker", "organ_name"]),
            ]
        )

        result = clean_and_validate_dataframe(df, "test")

        # Should remove empty rows, keep valid ones
        assert len(result) == 2
        assert list(result["ticker"]) == ["VCB", "TCB"]

    def test_clean_all_empty_rows(self) -> None:
        """Test cleaning DataFrame with all empty rows."""
        df = pd.DataFrame(
            [
                {"ticker": None, "organ_name": None},
                {"ticker": None, "organ_name": None},
            ]
        )

        result = clean_and_validate_dataframe(df, "test")

        assert result.empty


class TestUtilityFunctions:
    """Test utility conversion functions."""

    def test_safe_string_conversion_valid(self) -> None:
        """Test safe string conversion with valid values."""
        assert safe_string_conversion("test") == "test"
        assert safe_string_conversion("  test  ") == "test"
        assert safe_string_conversion(123) == "123"
        assert safe_string_conversion(123.45) == "123.45"

    def test_safe_string_conversion_empty(self) -> None:
        """Test safe string conversion with empty/None values."""
        assert safe_string_conversion(None) == ""
        assert safe_string_conversion("") == ""
        assert safe_string_conversion("   ") == ""
        assert safe_string_conversion(pd.NA) == ""

    def test_safe_string_conversion_with_default(self) -> None:
        """Test safe string conversion with custom default."""
        assert safe_string_conversion(None, "default") == "default"
        assert safe_string_conversion("", "default") == "default"

    def test_safe_int_conversion_valid(self) -> None:
        """Test safe integer conversion with valid values."""
        assert safe_int_conversion(123) == 123
        assert safe_int_conversion("123") == 123
        assert safe_int_conversion(123.45) == 123
        assert safe_int_conversion("123.7") == 123

    def test_safe_int_conversion_invalid(self) -> None:
        """Test safe integer conversion with invalid values."""
        assert safe_int_conversion(None) == 0
        assert safe_int_conversion("invalid") == 0
        assert safe_int_conversion("abc") == 0
        assert safe_int_conversion(pd.NA) == 0

    def test_safe_int_conversion_with_default(self) -> None:
        """Test safe integer conversion with custom default."""
        assert safe_int_conversion(None, -1) == -1
        assert safe_int_conversion("invalid", -1) == -1


if __name__ == "__main__":
    pytest.main([__file__])
