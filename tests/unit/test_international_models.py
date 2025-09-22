"""
Unit tests for international market data domain models.

This module tests the Pydantic models and enums in the international_models.py module,
ensuring proper validation, constraints, and business logic compliance.
"""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from app.core.domain.historical_models import AssetType, TimeInterval
from app.core.domain.international_models import (
    CryptocurrenciesResponse,
    CryptoCurrency,
    CryptoCurrencyData,
    CryptoResponse,
    CurrencyCode,
    ForexPair,
    ForexPairData,
    ForexPairsResponse,
    ForexRateResponse,
    InternationalDataResponse,
    InternationalDataUnavailableError,
    InternationalMarketError,
    InternationalMarketRequest,
    InternationalMarketResponse,
    InvalidCryptoError,
    InvalidForexPairError,
    InvalidIndexError,
    WorldIndex,
    WorldIndexData,
    WorldIndexResponse,
    WorldIndicesResponse,
)


class TestCurrencyCode:
    """Test cases for CurrencyCode enum."""

    def test_currency_code_values(self):
        """Test that all expected currency codes are present."""
        expected_currencies = [
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "AUD",
            "CAD",
            "CHF",
            "CNY",
            "VND",
            "KRW",
        ]
        actual_currencies = [currency.value for currency in CurrencyCode]

        assert set(actual_currencies) == set(expected_currencies)

    def test_currency_code_count(self):
        """Test that we have the expected number of currency codes."""
        assert len(CurrencyCode) == 10


class TestForexPair:
    """Test cases for ForexPair model."""

    def test_valid_forex_pair(self):
        """Test creation with valid forex pair data."""
        forex_pair = ForexPair(
            symbol="USDVND",
            base_currency=CurrencyCode.USD,
            quote_currency=CurrencyCode.VND,
            name="US Dollar to Vietnamese Dong",
            precision=4,
            trading_hours="24/7",
            data_source="MSN",
        )

        assert forex_pair.symbol == "USDVND"
        assert forex_pair.base_currency == CurrencyCode.USD
        assert forex_pair.quote_currency == CurrencyCode.VND
        assert forex_pair.name == "US Dollar to Vietnamese Dong"
        assert forex_pair.precision == 4
        assert forex_pair.trading_hours == "24/7"
        assert forex_pair.data_source == "MSN"

    def test_invalid_symbol_too_short(self):
        """Test that too short symbols are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value has at least 6 characters"
        ):
            ForexPair(
                symbol="USD",  # Too short
                base_currency=CurrencyCode.USD,
                quote_currency=CurrencyCode.VND,
                name="US Dollar to Vietnamese Dong",
            )

    def test_invalid_symbol_too_long(self):
        """Test that too long symbols are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value has at most 10 characters"
        ):
            ForexPair(
                symbol="USDVNDLONG",  # Too long
                base_currency=CurrencyCode.USD,
                quote_currency=CurrencyCode.VND,
                name="US Dollar to Vietnamese Dong",
            )

    def test_invalid_precision_too_low(self):
        """Test that precision less than 1 is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            ForexPair(
                symbol="USDVND",
                base_currency=CurrencyCode.USD,
                quote_currency=CurrencyCode.VND,
                name="US Dollar to Vietnamese Dong",
                precision=0,  # Invalid precision
            )

    def test_invalid_precision_too_high(self):
        """Test that precision greater than 8 is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is less than or equal to 8"
        ):
            ForexPair(
                symbol="USDVND",
                base_currency=CurrencyCode.USD,
                quote_currency=CurrencyCode.VND,
                name="US Dollar to Vietnamese Dong",
                precision=9,  # Invalid precision
            )

    def test_symbol_format_validator(self):
        """Test symbol format validation."""
        # Test valid symbol
        forex_pair = ForexPair(
            symbol="usdvnd",  # Should be converted to uppercase
            base_currency=CurrencyCode.USD,
            quote_currency=CurrencyCode.VND,
            name="US Dollar to Vietnamese Dong",
        )
        assert forex_pair.symbol == "USDVND"

    def test_default_values(self):
        """Test that default values are applied correctly."""
        forex_pair = ForexPair(
            symbol="USDVND",
            base_currency=CurrencyCode.USD,
            quote_currency=CurrencyCode.VND,
            name="US Dollar to Vietnamese Dong",
            # No precision, trading_hours, or data_source specified
        )

        assert forex_pair.precision == 4
        assert forex_pair.trading_hours == "24/7"
        assert forex_pair.data_source == "MSN"


class TestWorldIndex:
    """Test cases for WorldIndex model."""

    def test_valid_world_index(self):
        """Test creation with valid world index data."""
        index = WorldIndex(
            symbol="SPX",
            name="S&P 500",
            country="United States",
            exchange="NYSE",
            currency=CurrencyCode.USD,
            description="Standard & Poor's 500 Index",
            data_source="MSN",
        )

        assert index.symbol == "SPX"
        assert index.name == "S&P 500"
        assert index.country == "United States"
        assert index.exchange == "NYSE"
        assert index.currency == CurrencyCode.USD
        assert index.description == "Standard & Poor's 500 Index"
        assert index.data_source == "MSN"

    def test_invalid_country_too_short(self):
        """Test that too short country names are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value has at least 2 characters"
        ):
            WorldIndex(
                symbol="SPX",
                name="S&P 500",
                country="U",  # Too short
                exchange="NYSE",
            )

    def test_invalid_country_too_long(self):
        """Test that too long country names are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value has at most 50 characters"
        ):
            WorldIndex(
                symbol="SPX",
                name="S&P 500",
                country="Very Long Country Name That Exceeds The Maximum Limit",
                exchange="NYSE",
            )

    def test_invalid_exchange_too_short(self):
        """Test that too short exchange names are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value has at least 1 character"
        ):
            WorldIndex(
                symbol="SPX",
                name="S&P 500",
                country="United States",
                exchange="",  # Empty exchange
            )

    def test_symbol_format_validator(self):
        """Test symbol format validation."""
        # Test valid symbol
        index = WorldIndex(
            symbol="spx",  # Should be converted to uppercase
            name="S&P 500",
            country="United States",
            exchange="NYSE",
        )
        assert index.symbol == "SPX"

        # Test invalid symbol with special characters
        with pytest.raises(
            ValueError, match="Index symbol must be alphanumeric"
        ):
            WorldIndex(
                symbol="SPX@",  # Contains special character
                name="S&P 500",
                country="United States",
                exchange="NYSE",
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        index = WorldIndex(
            symbol="SPX",
            name="S&P 500",
            country="United States",
            exchange="NYSE",
            # No currency, description, or data_source specified
        )

        assert index.currency == CurrencyCode.USD
        assert index.description is None
        assert index.data_source == "MSN"


class TestCryptoCurrency:
    """Test cases for CryptoCurrency model."""

    def test_valid_crypto_currency(self):
        """Test creation with valid cryptocurrency data."""
        crypto = CryptoCurrency(
            symbol="BTC",
            name="Bitcoin",
            coin_id="bitcoin",
            market_cap_rank=1,
            max_supply=21000000.0,
            circulating_supply=19000000.0,
            data_source="MSN",
        )

        assert crypto.symbol == "BTC"
        assert crypto.name == "Bitcoin"
        assert crypto.coin_id == "bitcoin"
        assert crypto.market_cap_rank == 1
        assert crypto.max_supply == 21000000.0
        assert crypto.circulating_supply == 19000000.0
        assert crypto.data_source == "MSN"

    def test_invalid_symbol_too_short(self):
        """Test that too short symbols are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value has at least 2 characters"
        ):
            CryptoCurrency(
                symbol="B", name="Bitcoin", coin_id="bitcoin"  # Too short
            )

    def test_invalid_symbol_too_long(self):
        """Test that too long symbols are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value has at most 10 characters"
        ):
            CryptoCurrency(
                symbol="BITCOINLONG",  # Too long
                name="Bitcoin",
                coin_id="bitcoin",
            )

    def test_invalid_market_cap_rank(self):
        """Test that invalid market cap rank is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            CryptoCurrency(
                symbol="BTC", name="Bitcoin", market_cap_rank=0  # Invalid rank
            )

    def test_invalid_max_supply(self):
        """Test that negative max supply is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CryptoCurrency(
                symbol="BTC",
                name="Bitcoin",
                max_supply=-1000.0,  # Invalid negative supply
            )

    def test_invalid_circulating_supply(self):
        """Test that negative circulating supply is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CryptoCurrency(
                symbol="BTC",
                name="Bitcoin",
                circulating_supply=-1000.0,  # Invalid negative supply
            )

    def test_symbol_format_validator(self):
        """Test symbol format validation."""
        # Test valid symbol
        crypto = CryptoCurrency(
            symbol="btc", name="Bitcoin"  # Should be converted to uppercase
        )
        assert crypto.symbol == "BTC"

        # Test invalid symbol with numbers
        with pytest.raises(
            ValueError, match="Crypto symbol must be alphabetic"
        ):
            CryptoCurrency(symbol="BTC1", name="Bitcoin")  # Contains number

    def test_default_values(self):
        """Test that default values are applied correctly."""
        crypto = CryptoCurrency(
            symbol="BTC",
            name="Bitcoin",
            # No optional fields specified
        )

        assert crypto.coin_id is None
        assert crypto.market_cap_rank is None
        assert crypto.max_supply is None
        assert crypto.circulating_supply is None
        assert crypto.data_source == "MSN"


class TestResponseModels:
    """Test cases for response models."""

    def test_international_data_response(self):
        """Test InternationalDataResponse model."""
        timestamp = datetime.now(timezone.utc)
        data_points = [
            {"time": timestamp.isoformat(), "price": 100.0, "volume": 1000}
        ]

        response = InternationalDataResponse(
            symbol="USDVND",
            asset_type="forex",
            data_source="MSN",
            interval="1D",
            data=data_points,
            total_records=1,
        )

        assert response.symbol == "USDVND"
        assert response.asset_type == "forex"
        assert response.data_source == "MSN"
        assert response.interval == "1D"
        assert response.data == data_points
        assert response.total_records == 1
        assert response.retrieved_at is not None

    def test_forex_pairs_response(self):
        """Test ForexPairsResponse model."""
        forex_pairs = [
            ForexPair(
                symbol="USDVND",
                base_currency=CurrencyCode.USD,
                quote_currency=CurrencyCode.VND,
                name="US Dollar to Vietnamese Dong",
            ),
            ForexPair(
                symbol="EURUSD",
                base_currency=CurrencyCode.EUR,
                quote_currency=CurrencyCode.USD,
                name="Euro to US Dollar",
            ),
        ]

        response = ForexPairsResponse(pairs=forex_pairs, total_pairs=2)

        assert len(response.pairs) == 2
        assert response.total_pairs == 2
        assert response.retrieved_at is not None

    def test_world_indices_response(self):
        """Test WorldIndicesResponse model."""
        indices = [
            WorldIndex(
                symbol="SPX",
                name="S&P 500",
                country="United States",
                exchange="NYSE",
            ),
            WorldIndex(
                symbol="NKY",
                name="Nikkei 225",
                country="Japan",
                exchange="TSE",
            ),
        ]

        response = WorldIndicesResponse(indices=indices, total_indices=2)

        assert len(response.indices) == 2
        assert response.total_indices == 2
        assert response.retrieved_at is not None

    def test_cryptocurrencies_response(self):
        """Test CryptocurrenciesResponse model."""
        cryptos = [
            CryptoCurrency(symbol="BTC", name="Bitcoin", market_cap_rank=1),
            CryptoCurrency(symbol="ETH", name="Ethereum", market_cap_rank=2),
        ]

        response = CryptocurrenciesResponse(
            cryptocurrencies=cryptos, total_cryptos=2
        )

        assert len(response.cryptocurrencies) == 2
        assert response.total_cryptos == 2
        assert response.retrieved_at is not None


class TestInternationalMarketError:
    """Test cases for InternationalMarketError exception hierarchy."""

    def test_base_international_market_error(self):
        """Test base InternationalMarketError creation."""
        error = InternationalMarketError("Test error", "USDVND", "forex")

        assert str(error) == "Test error for USDVND (forex)"
        assert error.symbol == "USDVND"
        assert error.asset_type == "forex"

    def test_invalid_forex_pair_error(self):
        """Test InvalidForexPairError creation."""
        error = InvalidForexPairError("Invalid pair", "INVALID", "forex")

        assert isinstance(error, InternationalMarketError)
        assert "Invalid pair for INVALID (forex)" in str(error)

    def test_invalid_index_error(self):
        """Test InvalidIndexError creation."""
        error = InvalidIndexError("Invalid index", "INVALID", "index")

        assert isinstance(error, InternationalMarketError)
        assert "Invalid index for INVALID (index)" in str(error)

    def test_invalid_crypto_error(self):
        """Test InvalidCryptoError creation."""
        error = InvalidCryptoError("Invalid crypto", "INVALID", "crypto")

        assert isinstance(error, InternationalMarketError)
        assert "Invalid crypto for INVALID (crypto)" in str(error)

    def test_international_data_unavailable_error(self):
        """Test InternationalDataUnavailableError creation."""
        error = InternationalDataUnavailableError(
            "Data unavailable", "USDVND", "forex"
        )

        assert isinstance(error, InternationalMarketError)
        assert "Data unavailable for USDVND (forex)" in str(error)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from InternationalMarketError."""
        exception_classes = [
            InvalidForexPairError,
            InvalidIndexError,
            InvalidCryptoError,
            InternationalDataUnavailableError,
        ]

        for exc_class in exception_classes:
            # Test that each can be instantiated and is an InternationalMarketError
            try:
                error = exc_class("Test message", "TEST", "test")
                assert isinstance(error, InternationalMarketError)
                assert isinstance(error, Exception)
            except Exception as e:
                pytest.fail(f"Failed to instantiate {exc_class.__name__}: {e}")


class TestAdditionalDataModels:
    """Test cases for additional data models."""

    def test_forex_pair_data(self):
        """Test ForexPairData model."""
        timestamp = datetime.now(timezone.utc)
        forex_data = ForexPairData(
            symbol="USDVND",
            base_currency=CurrencyCode.USD,
            quote_currency=CurrencyCode.VND,
            name="US Dollar to Vietnamese Dong",
            type="forex",
            exchange="Forex",
            is_active=True,
            last_updated=timestamp,
        )

        assert forex_data.symbol == "USDVND"
        assert forex_data.base_currency == CurrencyCode.USD
        assert forex_data.quote_currency == CurrencyCode.VND
        assert forex_data.name == "US Dollar to Vietnamese Dong"
        assert forex_data.type == "forex"
        assert forex_data.exchange == "Forex"
        assert forex_data.is_active is True
        assert forex_data.last_updated == timestamp

    def test_forex_rate_response(self):
        """Test ForexRateResponse model."""
        timestamp = datetime.now(timezone.utc)
        rate_response = ForexRateResponse(
            rate=24500.0,
            timestamp=timestamp,
            change_24h=100.0,
            change_percent_24h=0.41,
            high_24h=24600.0,
            low_24h=24400.0,
            volume_24h=50000000.0,
        )

        assert rate_response.rate == 24500.0
        assert rate_response.timestamp == timestamp
        assert rate_response.change_24h == 100.0
        assert rate_response.change_percent_24h == 0.41
        assert rate_response.high_24h == 24600.0
        assert rate_response.low_24h == 24400.0
        assert rate_response.volume_24h == 50000000.0

    def test_world_index_data(self):
        """Test WorldIndexData model."""
        timestamp = datetime.now(timezone.utc)
        index_data = WorldIndexData(
            symbol="SPX",
            name="S&P 500",
            country="United States",
            region="North America",
            currency=CurrencyCode.USD,
            current_value=4500.0,
            change=50.0,
            change_percent=1.12,
            last_updated=timestamp,
            is_active=True,
        )

        assert index_data.symbol == "SPX"
        assert index_data.name == "S&P 500"
        assert index_data.country == "United States"
        assert index_data.region == "North America"
        assert index_data.currency == CurrencyCode.USD
        assert index_data.current_value == 4500.0
        assert index_data.change == 50.0
        assert index_data.change_percent == 1.12
        assert index_data.last_updated == timestamp
        assert index_data.is_active is True

    def test_world_index_response(self):
        """Test WorldIndexResponse model."""
        timestamp = datetime.now(timezone.utc)
        index_response = WorldIndexResponse(
            name="S&P 500",
            country="United States",
            region="North America",
            currency=CurrencyCode.USD,
            current_value=4500.0,
            open=4450.0,
            high=4520.0,
            low=4430.0,
            previous_close=4450.0,
            change=50.0,
            change_percent=1.12,
            volume=1000000000.0,
            market_cap=45000000000000.0,
            last_updated=timestamp,
        )

        assert index_response.name == "S&P 500"
        assert index_response.country == "United States"
        assert index_response.region == "North America"
        assert index_response.currency == CurrencyCode.USD
        assert index_response.current_value == 4500.0
        assert index_response.open == 4450.0
        assert index_response.high == 4520.0
        assert index_response.low == 4430.0
        assert index_response.previous_close == 4450.0
        assert index_response.change == 50.0
        assert index_response.change_percent == 1.12
        assert index_response.volume == 1000000000.0
        assert index_response.market_cap == 45000000000000.0
        assert index_response.last_updated == timestamp

    def test_crypto_currency_data(self):
        """Test CryptoCurrencyData model."""
        timestamp = datetime.now(timezone.utc)
        crypto_data = CryptoCurrencyData(
            symbol="BTC",
            name="Bitcoin",
            price_usd=45000.0,
            market_cap_usd=850000000000.0,
            volume_24h_usd=20000000000.0,
            change_24h_percent=2.5,
            circulating_supply=19000000.0,
            max_supply=21000000.0,
            rank=1,
            last_updated=timestamp,
            is_active=True,
        )

        assert crypto_data.symbol == "BTC"
        assert crypto_data.name == "Bitcoin"
        assert crypto_data.price_usd == 45000.0
        assert crypto_data.market_cap_usd == 850000000000.0
        assert crypto_data.volume_24h_usd == 20000000000.0
        assert crypto_data.change_24h_percent == 2.5
        assert crypto_data.circulating_supply == 19000000.0
        assert crypto_data.max_supply == 21000000.0
        assert crypto_data.rank == 1
        assert crypto_data.last_updated == timestamp
        assert crypto_data.is_active is True

    def test_crypto_response(self):
        """Test CryptoResponse model."""
        timestamp = datetime.now(timezone.utc)
        crypto_response = CryptoResponse(
            name="Bitcoin",
            description="Decentralized digital currency",
            price_usd=45000.0,
            market_cap_usd=850000000000.0,
            volume_24h_usd=20000000000.0,
            change_1h_percent=0.5,
            change_24h_percent=2.5,
            change_7d_percent=5.0,
            circulating_supply=19000000.0,
            max_supply=21000000.0,
            total_supply=19000000.0,
            ath_price_usd=69000.0,
            ath_date=datetime(2021, 11, 10, tzinfo=timezone.utc),
            rank=1,
            last_updated=timestamp,
        )

        assert crypto_response.name == "Bitcoin"
        assert crypto_response.description == "Decentralized digital currency"
        assert crypto_response.price_usd == 45000.0
        assert crypto_response.market_cap_usd == 850000000000.0
        assert crypto_response.volume_24h_usd == 20000000000.0
        assert crypto_response.change_1h_percent == 0.5
        assert crypto_response.change_24h_percent == 2.5
        assert crypto_response.change_7d_percent == 5.0
        assert crypto_response.circulating_supply == 19000000.0
        assert crypto_response.max_supply == 21000000.0
        assert crypto_response.total_supply == 19000000.0
        assert crypto_response.ath_price_usd == 69000.0
        assert crypto_response.ath_date == datetime(
            2021, 11, 10, tzinfo=timezone.utc
        )
        assert crypto_response.rank == 1
        assert crypto_response.last_updated == timestamp


class TestMarketRequestResponse:
    """Test cases for market request and response models."""

    def test_international_market_request(self):
        """Test InternationalMarketRequest model."""
        request = InternationalMarketRequest(
            symbol="USDVND",
            asset_type=AssetType.FOREX,
            data_source="MSN",
            interval=TimeInterval.DAY_1,
        )

        assert request.symbol == "USDVND"
        assert request.asset_type == AssetType.FOREX
        assert request.data_source == "MSN"
        assert request.interval == TimeInterval.DAY_1

    def test_international_market_request_defaults(self):
        """Test InternationalMarketRequest default values."""
        request = InternationalMarketRequest(
            symbol="USDVND",
            asset_type=AssetType.FOREX,
            # No data_source or interval specified
        )

        assert request.data_source == "MSN"
        assert request.interval == TimeInterval.DAY_1

    def test_international_market_response(self):
        """Test InternationalMarketResponse model."""
        data_points = [
            {"time": datetime.now(timezone.utc).isoformat(), "price": 24500.0}
        ]

        response = InternationalMarketResponse(
            symbol="USDVND",
            asset_type=AssetType.FOREX,
            data_source="MSN",
            interval=TimeInterval.DAY_1,
            data=data_points,
            total_records=1,
        )

        assert response.symbol == "USDVND"
        assert response.asset_type == AssetType.FOREX
        assert response.data_source == "MSN"
        assert response.interval == TimeInterval.DAY_1
        assert response.data == data_points
        assert response.total_records == 1
        assert response.retrieved_at is not None
