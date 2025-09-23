"""
Unit tests for FinancialReportService.

This module tests the business logic for financial reporting operations
including caching, fallback mechanisms, and data source coordination.
"""

import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.application.financial_report_service import FinancialReportService
from app.core.domain.cache_models import CacheConfig
from app.core.domain.data_source_models import (
    DataSource,
    DataSourceConfig,
    DataSourceRegistry,
)
from app.core.domain.financial_reports import (
    BalanceSheetResponse,
    BalanceSheetRow,
    FinancialReportRequest,
    FinancialReportServiceMetadata,
)
from app.core.domain.historical_models import (
    DataSourceUnavailableError,
    SymbolNotFoundError,
)
from app.infrastructure.cache.redis_adapter import RedisCacheManager
from app.infrastructure.data_sources.vci_adapter import VCIAdapter


class TestFinancialReportService:
    """Test suite for FinancialReportService."""

    @pytest.fixture
    def mock_cache_manager(self):
        """Create a mock cache manager."""
        cache_manager = MagicMock(spec=RedisCacheManager)
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True
        return cache_manager

    @pytest.fixture
    def mock_data_source_registry(self):
        """Create a mock data source registry."""
        registry = MagicMock(spec=DataSourceRegistry)
        registry.get_adapter.return_value = None
        return registry

    @pytest.fixture
    def mock_vci_adapter(self):
        """Create a mock VCI adapter."""
        adapter = MagicMock(spec=VCIAdapter)
        adapter.get_balance_sheet = AsyncMock()
        adapter.get_income_statement = AsyncMock()
        adapter.get_cash_flow = AsyncMock()
        adapter.get_financial_ratios = AsyncMock()
        return adapter

    @pytest.fixture
    def cache_config(self):
        """Create a test cache configuration."""
        return CacheConfig(
            enabled=True,
            default_ttl=3600,
            max_size=1000,
            strategy="simple",
        )

    @pytest.fixture
    def financial_service(
        self, mock_cache_manager, mock_data_source_registry, cache_config
    ):
        """Create a FinancialReportService instance for testing."""
        return FinancialReportService(
            data_source_registry=mock_data_source_registry,
            cache_manager=mock_cache_manager,
            cache_config=cache_config,
        )

    @pytest.fixture
    def sample_balance_sheet_data(self):
        """Create sample balance sheet data."""
        return [
            BalanceSheetRow(
                period_end=datetime(2023, 12, 31),
                symbol="ACB",
                source=DataSource.VCI,
                total_assets=1000000,
                current_assets=600000,
                cash_and_equivalents=100000,
                non_current_assets=400000,
                total_liabilities=500000,
                current_liabilities=300000,
                non_current_liabilities=200000,
                total_equity=500000,
            ),
            BalanceSheetRow(
                period_end=datetime(2022, 12, 31),
                symbol="ACB",
                source=DataSource.VCI,
                total_assets=900000,
                current_assets=550000,
                cash_and_equivalents=80000,
                non_current_assets=350000,
                total_liabilities=450000,
                current_liabilities=280000,
                non_current_liabilities=170000,
                total_equity=450000,
            ),
        ]

    def test_init(self, mock_cache_manager, mock_data_source_registry, cache_config):
        """Test FinancialReportService initialization."""
        service = FinancialReportService(
            data_source_registry=mock_data_source_registry,
            cache_manager=mock_cache_manager,
            cache_config=cache_config,
        )

        assert service.data_source_registry == mock_data_source_registry
        assert service.cache_manager == mock_cache_manager
        assert service.cache_config == cache_config

    @pytest.mark.asyncio
    async def test_get_balance_sheet_cache_hit(
        self, financial_service, mock_cache_manager, sample_balance_sheet_data
    ):
        """Test balance sheet retrieval with cache hit."""
        # Setup cache to return data
        cached_response = BalanceSheetResponse(
            data=sample_balance_sheet_data,
            metadata=FinancialReportServiceMetadata(
                source=DataSource.VCI,
                from_cache=True,
                retrieved_at=datetime.now(),
                processing_time_ms=50,
                record_count=2,
            ),
        )
        mock_cache_manager.get.return_value = cached_response.model_dump()

        # Execute request
        request = FinancialReportRequest(
            symbol="ACB", source=DataSource.VCI, period="year", language="vi"
        )
        result = await financial_service.get_balance_sheet(
            symbol="ACB",
            source=DataSource.VCI,
            period="year",
            language="vi",
            use_cache=True,
        )

        # Validate response
        assert isinstance(result, BalanceSheetResponse)
        assert len(result.data) == 2
        assert result.metadata.from_cache is True
        assert result.metadata.source == DataSource.VCI

        # Verify cache was checked
        mock_cache_manager.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance_sheet_cache_miss_data_source_success(
        self,
        financial_service,
        mock_cache_manager,
        mock_data_source_registry,
        mock_vci_adapter,
        sample_balance_sheet_data,
    ):
        """Test balance sheet retrieval with cache miss and successful data source."""
        # Setup cache miss and successful adapter response
        mock_cache_manager.get.return_value = None
        mock_vci_adapter.get_balance_sheet.return_value = sample_balance_sheet_data
        mock_data_source_registry.get_adapter.return_value = mock_vci_adapter

        # Execute request
        result = await financial_service.get_balance_sheet(
            symbol="ACB",
            source=DataSource.VCI,
            period="year",
            language="vi",
            use_cache=True,
        )

        # Validate response
        assert isinstance(result, BalanceSheetResponse)
        assert len(result.data) == 2
        assert result.metadata.from_cache is False
        assert result.metadata.source == DataSource.VCI

        # Verify adapter was called
        mock_vci_adapter.get_balance_sheet.assert_called_once_with(
            symbol="ACB", period="year", language="vi"
        )

        # Verify cache was updated
        mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance_sheet_data_source_unavailable_fallback(
        self,
        financial_service,
        mock_cache_manager,
        mock_data_source_registry,
        mock_vci_adapter,
    ):
        """Test balance sheet retrieval with primary data source unavailable."""
        # Setup cache miss and primary adapter failure
        mock_cache_manager.get.return_value = None
        mock_vci_adapter.get_balance_sheet.side_effect = DataSourceUnavailableError(
            "VCI service unavailable"
        )
        mock_data_source_registry.get_adapter.return_value = mock_vci_adapter

        # Execute request and expect failure (no fallback configured in test)
        with pytest.raises(DataSourceUnavailableError):
            await financial_service.get_balance_sheet(
                symbol="ACB",
                source=DataSource.VCI,
                period="year",
                language="vi",
                use_cache=True,
            )

    @pytest.mark.asyncio
    async def test_get_balance_sheet_symbol_not_found(
        self,
        financial_service,
        mock_cache_manager,
        mock_data_source_registry,
        mock_vci_adapter,
    ):
        """Test balance sheet retrieval with symbol not found."""
        # Setup cache miss and symbol not found error
        mock_cache_manager.get.return_value = None
        mock_vci_adapter.get_balance_sheet.side_effect = SymbolNotFoundError(
            "Symbol ACB not found"
        )
        mock_data_source_registry.get_adapter.return_value = mock_vci_adapter

        # Execute request and expect error
        with pytest.raises(SymbolNotFoundError):
            await financial_service.get_balance_sheet(
                symbol="ACB",
                source=DataSource.VCI,
                period="year",
                language="vi",
                use_cache=True,
            )

    @pytest.mark.asyncio
    async def test_get_balance_sheet_cache_disabled(
        self,
        financial_service,
        mock_cache_manager,
        mock_data_source_registry,
        mock_vci_adapter,
        sample_balance_sheet_data,
    ):
        """Test balance sheet retrieval with cache disabled."""
        # Setup successful adapter response
        mock_vci_adapter.get_balance_sheet.return_value = sample_balance_sheet_data
        mock_data_source_registry.get_adapter.return_value = mock_vci_adapter

        # Execute request with cache disabled
        result = await financial_service.get_balance_sheet(
            symbol="ACB",
            source=DataSource.VCI,
            period="year",
            language="vi",
            use_cache=False,
        )

        # Validate response
        assert isinstance(result, BalanceSheetResponse)
        assert result.metadata.from_cache is False

        # Verify cache was not checked
        mock_cache_manager.get.assert_not_called()

        # Verify cache was not updated
        mock_cache_manager.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_cache_specific_symbol(
        self, financial_service, mock_cache_manager
    ):
        """Test cache clearing for specific symbol."""
        # Setup mock response
        mock_cache_manager.delete_pattern.return_value = 5

        # Execute cache clearing
        result = await financial_service.clear_cache(symbol="ACB")

        # Validate result
        assert result.keys_removed == 5
        assert "ACB" in result.symbol_filter

        # Verify cache manager was called with correct pattern
        mock_cache_manager.delete_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_all(
        self, financial_service, mock_cache_manager
    ):
        """Test cache clearing for all data."""
        # Setup mock response
        mock_cache_manager.delete_pattern.return_value = 20

        # Execute cache clearing
        result = await financial_service.clear_cache()

        # Validate result
        assert result.keys_removed == 20
        assert result.symbol_filter is None

        # Verify cache manager was called
        mock_cache_manager.delete_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_service_metrics(
        self, financial_service, mock_cache_manager
    ):
        """Test service metrics retrieval."""
        # Setup mock metrics
        mock_cache_manager.get_metrics.return_value = {
            "hit_rate": 0.85,
            "total_keys": 100,
            "memory_usage": 1048576,
        }

        # Execute metrics request
        metrics = await financial_service.get_service_metrics()

        # Validate metrics structure
        assert "cache" in metrics
        assert "service_health" in metrics
        assert "performance" in metrics
        assert "data_sources" in metrics

        # Verify cache metrics were retrieved
        mock_cache_manager.get_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_comprehensive_financial_data_concurrent(
        self,
        financial_service,
        mock_cache_manager,
        mock_data_source_registry,
        mock_vci_adapter,
        sample_balance_sheet_data,
    ):
        """Test comprehensive financial data retrieval with concurrent execution."""
        # Setup cache miss and successful adapter responses
        mock_cache_manager.get.return_value = None
        mock_vci_adapter.get_balance_sheet.return_value = sample_balance_sheet_data
        mock_vci_adapter.get_income_statement.return_value = []
        mock_vci_adapter.get_cash_flow.return_value = []
        mock_vci_adapter.get_financial_ratios.return_value = []
        mock_data_source_registry.get_adapter.return_value = mock_vci_adapter

        # Execute concurrent request
        result = await financial_service.get_comprehensive_financial_data(
            symbol="ACB",
            source=DataSource.VCI,
            period="year",
            language="vi",
            use_cache=True,
        )

        # Validate response structure
        assert hasattr(result, 'balance_sheet')
        assert hasattr(result, 'income_statement')
        assert hasattr(result, 'cash_flow')
        assert hasattr(result, 'financial_ratios')
        assert hasattr(result, 'metadata')

        # Validate concurrent execution (all methods should be called)
        mock_vci_adapter.get_balance_sheet.assert_called_once()
        mock_vci_adapter.get_income_statement.assert_called_once()
        mock_vci_adapter.get_cash_flow.assert_called_once()
        mock_vci_adapter.get_financial_ratios.assert_called_once()

    def test_generate_cache_key(self, financial_service):
        """Test cache key generation."""
        key = financial_service._generate_cache_key(
            operation="balance_sheet",
            symbol="ACB",
            source=DataSource.VCI,
            period="year",
            language="vi",
        )

        # Validate key structure
        assert isinstance(key, str)
        assert "balance_sheet" in key
        assert "ACB" in key
        assert "VCI" in key

    def test_build_cache_key_pattern(self, financial_service):
        """Test cache key pattern building for clearing."""
        pattern = financial_service._build_cache_key_pattern(
            operation="balance_sheet",
            symbol="ACB",
            source=DataSource.VCI,
        )

        # Validate pattern structure
        assert isinstance(pattern, str)
        assert "*" in pattern  # Should be a wildcard pattern

    @pytest.mark.asyncio
    async def test_adapter_error_handling(
        self,
        financial_service,
        mock_cache_manager,
        mock_data_source_registry,
        mock_vci_adapter,
    ):
        """Test handling of adapter errors."""
        # Setup cache miss and generic adapter error
        mock_cache_manager.get.return_value = None
        mock_vci_adapter.get_balance_sheet.side_effect = Exception(
            "Unexpected adapter error"
        )
        mock_data_source_registry.get_adapter.return_value = mock_vci_adapter

        # Execute request and expect error
        with pytest.raises(DataSourceUnavailableError):
            await financial_service.get_balance_sheet(
                symbol="ACB",
                source=DataSource.VCI,
                period="year",
                language="vi",
                use_cache=True,
            )

    @pytest.mark.asyncio
    async def test_cache_error_handling(
        self, financial_service, mock_cache_manager, mock_vci_adapter
    ):
        """Test handling of cache errors."""
        # Setup cache error and successful adapter response
        mock_cache_manager.get.side_effect = Exception("Cache error")
        mock_cache_manager.set.side_effect = Exception("Cache set error")

        # Mock data source registry
        financial_service.data_source_registry.get_adapter.return_value = mock_vci_adapter
        mock_vci_adapter.get_balance_sheet.return_value = []

        # Execute request - should handle cache errors gracefully
        result = await financial_service.get_balance_sheet(
            symbol="ACB",
            source=DataSource.VCI,
            period="year",
            language="vi",
            use_cache=True,
        )

        # Should still get a response despite cache errors
        assert isinstance(result, BalanceSheetResponse)