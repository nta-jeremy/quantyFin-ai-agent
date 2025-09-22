"""
Unit tests for historical data domain models.

This module tests the Pydantic models and enums in the historical_models.py module,
ensuring proper validation, constraints, and business logic compliance.
"""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from app.core.domain.historical_models import (
    AssetType,
    AuthenticationError,
    DataCorruptionError,
    DataSourceUnavailableError,
    DataValidationError,
    HistoricalDataError,
    HistoricalDataRequest,
    HistoricalDataResponse,
    InsufficientDataError,
    IntradayDataResponse,
    InvalidDateRangeError,
    InvalidParameterError,
    NetworkError,
    OHLCVTData,
    RateLimitExceededError,
    RealTimeQuoteResponse,
    SymbolNotFoundError,
    TimeInterval,
    TimeoutError,
)


class TestTimeInterval:
    """Test cases for TimeInterval enum."""

    def test_interval_values(self):
        """Test that all expected interval values are present."""
        expected_intervals = ["1m", "5m", "15m", "30m", "1H", "1D", "1W", "1M"]
        actual_intervals = [interval.value for interval in TimeInterval]

        assert set(actual_intervals) == set(expected_intervals)

    def test_interval_count(self):
        """Test that we have the expected number of intervals."""
        assert len(TimeInterval) == 8


class TestAssetType:
    """Test cases for AssetType enum."""

    def test_asset_type_values(self):
        """Test that all expected asset type values are present."""
        expected_types = [
            "stock",
            "index",
            "futures",
            "warrant",
            "bond",
            "etf",
            "forex",
            "crypto",
            "world_index",
        ]
        actual_types = [asset_type.value for asset_type in AssetType]

        assert set(actual_types) == set(expected_types)

    def test_asset_type_count(self):
        """Test that we have the expected number of asset types."""
        assert len(AssetType) == 9


class TestOHLCVTData:
    """Test cases for OHLCVTData model."""

    def test_valid_ohlcv_data(self):
        """Test creation with valid OHLCV data."""
        timestamp = datetime.now(timezone.utc)
        data = OHLCVTData(
            time=timestamp,
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000,
        )

        assert data.time == timestamp
        assert data.open == 100.0
        assert data.high == 105.0
        assert data.low == 95.0
        assert data.close == 102.0
        assert data.volume == 1000000

    def test_invalid_negative_prices(self):
        """Test that negative prices are rejected."""
        timestamp = datetime.now(timezone.utc)

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            OHLCVTData(
                time=timestamp,
                open=-100.0,  # Invalid negative price
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000,
            )

    def test_invalid_negative_volume(self):
        """Test that negative volume is rejected."""
        timestamp = datetime.now(timezone.utc)

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            OHLCVTData(
                time=timestamp,
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=-1000,  # Invalid negative volume
            )

    def test_high_less_than_low_validation(self):
        """Test that high < low validation works."""
        timestamp = datetime.now(timezone.utc)

        with pytest.raises(
            ValueError,
            match="High price must be greater than or equal to low price",
        ):
            OHLCVTData(
                time=timestamp,
                open=100.0,
                high=90.0,  # High less than low
                low=95.0,
                close=102.0,
                volume=1000000,
            )

    def test_low_greater_than_high_validation(self):
        """Test that low > high validation works."""
        timestamp = datetime.now(timezone.utc)

        with pytest.raises(
            ValueError,
            match="Low price must be less than or equal to high price",
        ):
            OHLCVTData(
                time=timestamp,
                open=100.0,
                high=105.0,
                low=110.0,  # Low greater than high
                close=102.0,
                volume=1000000,
            )

    def test_valid_equal_high_low(self):
        """Test that equal high and low prices are allowed."""
        timestamp = datetime.now(timezone.utc)
        data = OHLCVTData(
            time=timestamp,
            open=100.0,
            high=100.0,  # Equal to low
            low=100.0,  # Equal to high
            close=100.0,
            volume=1000000,
        )

        assert data.high == data.low == 100.0


class TestHistoricalDataRequest:
    """Test cases for HistoricalDataRequest model."""

    def test_valid_request(self):
        """Test creation with valid request data."""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) - timedelta(days=1)

        request = HistoricalDataRequest(
            symbol="VNM",
            start_date=start_date,
            end_date=end_date,
            interval=TimeInterval.DAY_1,
            asset_type=AssetType.STOCK,
            data_source="VCI",
        )

        assert request.symbol == "VNM"
        assert request.start_date == start_date
        assert request.end_date == end_date
        assert request.interval == TimeInterval.DAY_1
        assert request.asset_type == AssetType.STOCK
        assert request.data_source == "VCI"

    def test_invalid_symbol_too_short(self):
        """Test that too short symbols are rejected."""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) - timedelta(days=1)

        with pytest.raises(
            ValueError, match="ensure this value has at least 1 character"
        ):
            HistoricalDataRequest(
                symbol="",  # Empty symbol
                start_date=start_date,
                end_date=end_date,
            )

    def test_invalid_symbol_too_long(self):
        """Test that too long symbols are rejected."""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) - timedelta(days=1)

        with pytest.raises(
            ValueError, match="ensure this value has at most 20 characters"
        ):
            HistoricalDataRequest(
                symbol="VERY_LONG_SYMBOL_NAME_THAT_EXCEEDS_LIMIT",
                start_date=start_date,
                end_date=end_date,
            )

    def test_end_date_before_start_date(self):
        """Test that end date before start date is rejected."""
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) - timedelta(
            days=30
        )  # Before start date

        with pytest.raises(
            ValueError, match="End date must be after start date"
        ):
            HistoricalDataRequest(
                symbol="VNM", start_date=start_date, end_date=end_date
            )

    def test_start_date_in_future(self):
        """Test that future start date is rejected."""
        start_date = datetime.now(timezone.utc) + timedelta(
            days=1
        )  # Future date
        end_date = datetime.now(timezone.utc) + timedelta(days=2)

        with pytest.raises(
            ValueError, match="Start date cannot be in the future"
        ):
            HistoricalDataRequest(
                symbol="VNM", start_date=start_date, end_date=end_date
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) - timedelta(days=1)

        request = HistoricalDataRequest(
            symbol="VNM",
            start_date=start_date,
            end_date=end_date,
            # No interval, asset_type, or data_source specified
        )

        assert request.interval == TimeInterval.DAY_1
        assert request.asset_type == AssetType.STOCK
        assert request.data_source is None


class TestHistoricalDataResponse:
    """Test cases for HistoricalDataResponse model."""

    def test_valid_response(self):
        """Test creation with valid response data."""
        timestamp = datetime.now(timezone.utc)
        data_points = [
            OHLCVTData(
                time=timestamp,
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000,
            )
        ]

        response = HistoricalDataResponse(
            symbol="VNM",
            asset_type=AssetType.STOCK,
            data_source="VCI",
            interval=TimeInterval.DAY_1,
            data=data_points,
            total_records=1,
        )

        assert response.symbol == "VNM"
        assert response.asset_type == AssetType.STOCK
        assert response.data_source == "VCI"
        assert response.interval == TimeInterval.DAY_1
        assert response.data == data_points
        assert response.total_records == 1
        assert response.retrieved_at is not None

    def test_empty_data_list(self):
        """Test response with empty data list."""
        response = HistoricalDataResponse(
            symbol="VNM",
            asset_type=AssetType.STOCK,
            data_source="VCI",
            interval=TimeInterval.DAY_1,
            data=[],
            total_records=0,
        )

        assert response.data == []
        assert response.total_records == 0

    def test_invalid_negative_total_records(self):
        """Test that negative total_records is rejected."""
        timestamp = datetime.now(timezone.utc)
        data_points = [
            OHLCVTData(
                time=timestamp,
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000,
            )
        ]

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            HistoricalDataResponse(
                symbol="VNM",
                asset_type=AssetType.STOCK,
                data_source="VCI",
                interval=TimeInterval.DAY_1,
                data=data_points,
                total_records=-1,  # Invalid negative count
            )


class TestIntradayDataResponse:
    """Test cases for IntradayDataResponse model."""

    def test_valid_intraday_response(self):
        """Test creation with valid intraday response data."""
        timestamp = datetime.now(timezone.utc)
        data_points = [
            OHLCVTData(
                time=timestamp,
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000,
            )
        ]

        response = IntradayDataResponse(
            symbol="VNM", data=data_points, total_records=1
        )

        assert response.symbol == "VNM"
        assert response.data == data_points
        assert response.total_records == 1
        assert response.retrieved_at is not None


class TestRealTimeQuoteResponse:
    """Test cases for RealTimeQuoteResponse model."""

    def test_valid_real_time_quote(self):
        """Test creation with valid real-time quote data."""
        timestamp = datetime.now(timezone.utc)

        quote = RealTimeQuoteResponse(
            symbol="VNM",
            time=timestamp,
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000,
        )

        assert quote.symbol == "VNM"
        assert quote.time == timestamp
        assert quote.open == 100.0
        assert quote.high == 105.0
        assert quote.low == 95.0
        assert quote.close == 102.0
        assert quote.volume == 1000000


class TestHistoricalDataError:
    """Test cases for HistoricalDataError exception hierarchy."""

    def test_base_historical_data_error(self):
        """Test base HistoricalDataError creation."""
        error = HistoricalDataError("Test error", "VNM", AssetType.STOCK)

        assert str(error) == "Test error for VNM (stock)"
        assert error.symbol == "VNM"
        assert error.asset_type == AssetType.STOCK

    def test_data_source_unavailable_error(self):
        """Test DataSourceUnavailableError creation."""
        error = DataSourceUnavailableError(
            "Service down", "VNM", AssetType.STOCK
        )

        assert isinstance(error, HistoricalDataError)
        assert "Service down for VNM (stock)" in str(error)

    def test_symbol_not_found_error(self):
        """Test SymbolNotFoundError creation."""
        error = SymbolNotFoundError(
            "Symbol not found", "UNKNOWN", AssetType.STOCK
        )

        assert isinstance(error, HistoricalDataError)
        assert "Symbol not found for UNKNOWN (stock)" in str(error)

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError creation."""
        error = RateLimitExceededError(
            "Too many requests", "VNM", AssetType.STOCK
        )

        assert isinstance(error, HistoricalDataError)
        assert "Too many requests for VNM (stock)" in str(error)

    def test_invalid_parameter_error(self):
        """Test InvalidParameterError creation."""
        error = InvalidParameterError(
            "Invalid parameters", "VNM", AssetType.STOCK
        )

        assert isinstance(error, HistoricalDataError)
        assert "Invalid parameters for VNM (stock)" in str(error)

    def test_data_validation_error(self):
        """Test DataValidationError creation."""
        error = DataValidationError(
            "Data validation failed", "VNM", AssetType.STOCK
        )

        assert isinstance(error, HistoricalDataError)
        assert "Data validation failed for VNM (stock)" in str(error)

    def test_network_error(self):
        """Test NetworkError creation."""
        error = NetworkError("Network error", "VNM", AssetType.STOCK)

        assert isinstance(error, HistoricalDataError)
        assert "Network error for VNM (stock)" in str(error)

    def test_authentication_error(self):
        """Test AuthenticationError creation."""
        error = AuthenticationError("Auth failed", "VNM", AssetType.STOCK)

        assert isinstance(error, HistoricalDataError)
        assert "Auth failed for VNM (stock)" in str(error)

    def test_insufficient_data_error(self):
        """Test InsufficientDataError creation."""
        error = InsufficientDataError(
            "Not enough data", "VNM", AssetType.STOCK
        )

        assert isinstance(error, HistoricalDataError)
        assert "Not enough data for VNM (stock)" in str(error)

    def test_timeout_error(self):
        """Test TimeoutError creation."""
        error = TimeoutError("Request timeout", "VNM", AssetType.STOCK)

        assert isinstance(error, HistoricalDataError)
        assert "Request timeout for VNM (stock)" in str(error)

    def test_data_corruption_error(self):
        """Test DataCorruptionError creation."""
        error = DataCorruptionError("Data corrupted", "VNM", AssetType.STOCK)

        assert isinstance(error, HistoricalDataError)
        assert "Data corrupted for VNM (stock)" in str(error)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from HistoricalDataError."""
        exception_classes = [
            DataSourceUnavailableError,
            SymbolNotFoundError,
            RateLimitExceededError,
            InvalidDateRangeError,
            InvalidParameterError,
            DataValidationError,
            NetworkError,
            AuthenticationError,
            InsufficientDataError,
            TimeoutError,
            DataCorruptionError,
        ]

        for exc_class in exception_classes:
            # Test that each can be instantiated and is a HistoricalDataError
            try:
                error = exc_class("Test message", "TEST", AssetType.STOCK)
                assert isinstance(error, HistoricalDataError)
                assert isinstance(error, Exception)
            except Exception as e:
                pytest.fail(f"Failed to instantiate {exc_class.__name__}: {e}")


class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_request_response_consistency(self):
        """Test that request and response models work together."""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) - timedelta(days=1)

        # Create request
        request = HistoricalDataRequest(
            symbol="VNM",
            start_date=start_date,
            end_date=end_date,
            interval=TimeInterval.DAY_1,
            asset_type=AssetType.STOCK,
        )

        # Create corresponding response
        data_points = [
            OHLCVTData(
                time=start_date,
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000,
            )
        ]

        response = HistoricalDataResponse(
            symbol=request.symbol,
            asset_type=request.asset_type,
            data_source="VCI",
            interval=request.interval,
            data=data_points,
            total_records=len(data_points),
        )

        # Verify consistency
        assert response.symbol == request.symbol
        assert response.asset_type == request.asset_type
        assert response.interval == request.interval

    def test_multiple_data_points(self):
        """Test handling multiple data points in response."""
        base_time = datetime.now(timezone.utc)
        data_points = []

        for i in range(5):
            data_points.append(
                OHLCVTData(
                    time=base_time + timedelta(hours=i),
                    open=100.0 + i,
                    high=105.0 + i,
                    low=95.0 + i,
                    close=102.0 + i,
                    volume=1000000 + i * 1000,
                )
            )

        response = HistoricalDataResponse(
            symbol="VNM",
            asset_type=AssetType.STOCK,
            data_source="VCI",
            interval=TimeInterval.HOUR_1,
            data=data_points,
            total_records=len(data_points),
        )

        assert len(response.data) == 5
        assert response.total_records == 5
        assert all(isinstance(point, OHLCVTData) for point in response.data)
