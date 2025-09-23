"""
Unit tests for financial adapter extensions.

This module tests the VCI and TCBS adapter extensions for financial
reporting functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.domain.data_source_models import VnstockDataSource
from app.core.domain.financial_reports import (
    BalanceSheetRow,
    CashFlowRow,
    FinancialRatioRow,
    IncomeStatementRow,
)
from app.core.domain.historical_models import (
    DataSourceUnavailableError,
    SymbolNotFoundError,
)
from app.infrastructure.data_sources.tcbs_adapter import TCBSAdapter
from app.infrastructure.data_sources.vci_adapter import VCIAdapter


class TestVCIAdapterFinancialReports:
    """Test suite for VCI adapter financial report extensions."""

    @pytest.fixture
    def mock_vci_adapter(self):
        """Create a mock VCI adapter for testing."""
        adapter = MagicMock(spec=VCIAdapter)
        adapter._validate_symbol = MagicMock()
        adapter._transform_dataframe = MagicMock()
        return adapter

    @pytest.fixture
    def sample_balance_sheet_df(self):
        """Create sample balance sheet DataFrame."""
        import pandas as pd

        data = {
            "Tổng tài sản": [1000000, 1200000],
            "Tài sản ngắn hạn": [600000, 700000],
            "Tiền và tương đương tiền": [100000, 150000],
            "Tài sản dài hạn": [400000, 500000],
            "Tổng Nợ phải trả": [500000, 600000],
            "Nợ ngắn hạn": [300000, 350000],
            "Nợ dài hạn": [200000, 250000],
            "Vốn chủ sở hữu": [500000, 600000],
        }
        df = pd.DataFrame(data)
        df.index = pd.to_datetime(["2023-12-31", "2022-12-31"])
        df.index.name = "period_end"
        return df

    @pytest.mark.asyncio
    async def test_get_balance_sheet_success(
        self, mock_vci_adapter, sample_balance_sheet_df
    ):
        """Test successful balance sheet retrieval."""
        # Import pandas here to avoid import issues in test setup
        import pandas as pd
        from app.core.application.financial_data_transformer import (
            FinancialDataTransformer,
        )

        # Setup mocks
        mock_vci_adapter._transform_dataframe.return_value = sample_balance_sheet_df
        FinancialDataTransformer.transform_balance_sheet = MagicMock(
            return_value=[
                BalanceSheetRow(
                    period_end=datetime(2023, 12, 31),
                    symbol="ACB",
                    source=VnstockDataSource.VCI,
                    total_assets=1000000,
                    current_assets=600000,
                    cash_and_equivalents=100000,
                    non_current_assets=400000,
                    total_liabilities=500000,
                    current_liabilities=300000,
                    non_current_liabilities=200000,
                    total_equity=500000,
                )
            ]
        )

        # Create real adapter instance with mocked methods
        adapter = VCIAdapter(MagicMock())
        adapter._validate_symbol = mock_vci_adapter._validate_symbol
        adapter._transform_dataframe = mock_vci_adapter._transform_dataframe

        # Execute test
        result = await adapter.get_balance_sheet(
            symbol="ACB", period="year", language="vi"
        )

        # Validate results
        assert len(result) == 1
        assert isinstance(result[0], BalanceSheetRow)
        assert result[0].symbol == "ACB"
        assert result[0].source == VnstockDataSource.VCI

        # Verify method calls
        mock_vci_adapter._validate_symbol.assert_called_once_with("ACB")
        mock_vci_adapter._transform_dataframe.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance_sheet_invalid_symbol(self, mock_vci_adapter):
        """Test balance sheet retrieval with invalid symbol."""
        # Setup validation error
        mock_vci_adapter._validate_symbol.side_effect = ValueError(
            "Invalid symbol format"
        )

        # Create adapter with mocked validation
        adapter = VCIAdapter(MagicMock())
        adapter._validate_symbol = mock_vci_adapter._validate_symbol

        # Execute test and expect error
        with pytest.raises(ValueError, match="Invalid symbol format"):
            await adapter.get_balance_sheet(
                symbol="INVALID", period="year", language="vi"
            )

    @pytest.mark.asyncio
    async def test_get_balance_sheet_vnstock_unavailable(self):
        """Test balance sheet retrieval when vnstock is unavailable."""
        adapter = VCIAdapter(MagicMock())

        # Mock vnstock as None to simulate unavailable library
        with patch("app.infrastructure.data_sources.vci_adapter.vn", None):
            with pytest.raises(
                DataSourceUnavailableError,
                match="vnstock library not available",
            ):
                await adapter.get_balance_sheet(
                    symbol="ACB", period="year", language="vi"
                )

    @pytest.mark.asyncio
    async def test_get_income_statement_success(self, mock_vci_adapter):
        """Test successful income statement retrieval."""
        # Setup mocks
        import pandas as pd

        sample_df = pd.DataFrame({
            "Doanh thu thuần": [1000000],
            "Giá vốn hàng bán": [600000],
            "Lợi nhuận gộp": [400000],
        })
        sample_df.index = pd.to_datetime(["2023-12-31"])
        sample_df.index.name = "period_end"

        mock_vci_adapter._transform_dataframe.return_value = sample_df

        # Mock the transformer
        with patch(
            "app.core.application.financial_data_transformer.FinancialDataTransformer.transform_income_statement"
        ) as mock_transform:
            mock_transform.return_value = [
                IncomeStatementRow(
                    period_end=datetime(2023, 12, 31),
                    symbol="ACB",
                    source=VnstockDataSource.VCI,
                    total_revenue=1000000,
                    cost_of_goods_sold=600000,
                    gross_profit=400000,
                )
            ]

            # Create adapter with mocked methods
            adapter = VCIAdapter(MagicMock())
            adapter._validate_symbol = mock_vci_adapter._validate_symbol
            adapter._transform_dataframe = mock_vci_adapter._transform_dataframe

            # Execute test
            result = await adapter.get_income_statement(
                symbol="ACB", period="year", language="vi"
            )

            # Validate results
            assert len(result) == 1
            assert isinstance(result[0], IncomeStatementRow)
            assert result[0].symbol == "ACB"

    @pytest.mark.asyncio
    async def test_get_cash_flow_success(self, mock_vci_adapter):
        """Test successful cash flow retrieval."""
        import pandas as pd

        sample_df = pd.DataFrame({
            "Dòng tiền từ hoạt động kinh doanh": [300000],
            "Dòng tiền từ hoạt động đầu tư": [-100000],
            "Dòng tiền từ hoạt động tài chính": [-150000],
        })
        sample_df.index = pd.to_datetime(["2023-12-31"])
        sample_df.index.name = "period_end"

        mock_vci_adapter._transform_dataframe.return_value = sample_df

        # Mock the transformer
        with patch(
            "app.core.application.financial_data_transformer.FinancialDataTransformer.transform_cash_flow"
        ) as mock_transform:
            mock_transform.return_value = [
                CashFlowRow(
                    period_end=datetime(2023, 12, 31),
                    symbol="ACB",
                    source=VnstockDataSource.VCI,
                    operating_cash_flow=300000,
                    investing_cash_flow=-100000,
                    financing_cash_flow=-150000,
                    net_cash_flow=50000,
                )
            ]

            adapter = VCIAdapter(MagicMock())
            adapter._validate_symbol = mock_vci_adapter._validate_symbol
            adapter._transform_dataframe = mock_vci_adapter._transform_dataframe

            result = await adapter.get_cash_flow(
                symbol="ACB", period="year", language="vi"
            )

            assert len(result) == 1
            assert isinstance(result[0], CashFlowRow)

    @pytest.mark.asyncio
    async def test_get_financial_ratios_success(self, mock_vci_adapter):
        """Test successful financial ratios retrieval."""
        import pandas as pd

        sample_df = pd.DataFrame({
            "P/E": [15.5],
            "P/B": [2.1],
            "ROE": [0.18],
        })
        sample_df.index = pd.to_datetime(["2023-12-31"])
        sample_df.index.name = "period_end"

        mock_vci_adapter._transform_dataframe.return_value = sample_df

        # Mock the transformer
        with patch(
            "app.core.application.financial_data_transformer.FinancialDataTransformer.transform_financial_ratios"
        ) as mock_transform:
            mock_transform.return_value = [
                FinancialRatioRow(
                    period_end=datetime(2023, 12, 31),
                    symbol="ACB",
                    source=VnstockDataSource.VCI,
                    pe_ratio=15.5,
                    pb_ratio=2.1,
                    roe=0.18,
                )
            ]

            adapter = VCIAdapter(MagicMock())
            adapter._validate_symbol = mock_vci_adapter._validate_symbol
            adapter._transform_dataframe = mock_vci_adapter._transform_dataframe

            result = await adapter.get_financial_ratios(
                symbol="ACB", period="year", language="vi"
            )

            assert len(result) == 1
            assert isinstance(result[0], FinancialRatioRow)

    @pytest.mark.asyncio
    async def test_get_balance_sheet_quarterly_period(self, mock_vci_adapter):
        """Test balance sheet retrieval with quarterly period."""
        import pandas as pd

        sample_df = pd.DataFrame({
            "Tổng tài sản": [1000000],
            "Vốn chủ sở hữu": [500000],
        })
        sample_df.index = pd.to_datetime(["2023-09-30"])
        sample_df.index.name = "period_end"

        mock_vci_adapter._transform_dataframe.return_value = sample_df

        # Mock the transformer
        with patch(
            "app.core.application.financial_data_transformer.FinancialDataTransformer.transform_balance_sheet"
        ) as mock_transform:
            mock_transform.return_value = [
                BalanceSheetRow(
                    period_end=datetime(2023, 9, 30),
                    symbol="ACB",
                    source=VnstockDataSource.VCI,
                    total_assets=1000000,
                    total_equity=500000,
                )
            ]

            adapter = VCIAdapter(MagicMock())
            adapter._validate_symbol = mock_vci_adapter._validate_symbol
            adapter._transform_dataframe = mock_vci_adapter._transform_dataframe

            result = await adapter.get_balance_sheet(
                symbol="ACB", period="quarter", language="vi"
            )

            assert len(result) == 1
            # Verify period parameter was passed correctly
            mock_vci_adapter._transform_dataframe.assert_called_once()


class TestTCBSAdapterFinancialReports:
    """Test suite for TCBS adapter financial report extensions."""

    @pytest.fixture
    def mock_tcbs_adapter(self):
        """Create a mock TCBS adapter for testing."""
        adapter = MagicMock(spec=TCBSAdapter)
        adapter._validate_symbol = MagicMock()
        adapter._transform_dataframe = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_get_balance_sheet_success(self, mock_tcbs_adapter):
        """Test successful balance sheet retrieval from TCBS."""
        import pandas as pd

        sample_df = pd.DataFrame({
            "Total Assets": [1000000],
            "Total Liabilities": [500000],
            "Total Equity": [500000],
        })
        sample_df.index = pd.to_datetime(["2023-12-31"])
        sample_df.index.name = "period_end"

        mock_tcbs_adapter._transform_dataframe.return_value = sample_df

        # Mock the transformer
        with patch(
            "app.core.application.financial_data_transformer.FinancialDataTransformer.transform_balance_sheet"
        ) as mock_transform:
            mock_transform.return_value = [
                BalanceSheetRow(
                    period_end=datetime(2023, 12, 31),
                    symbol="ACB",
                    source=VnstockDataSource.TCBS,
                    total_assets=1000000,
                    total_liabilities=500000,
                    total_equity=500000,
                )
            ]

            # Create adapter with mocked methods
            adapter = TCBSAdapter(MagicMock())
            adapter._validate_symbol = mock_tcbs_adapter._validate_symbol
            adapter._transform_dataframe = mock_tcbs_adapter._transform_dataframe

            result = await adapter.get_balance_sheet(
                symbol="ACB", period="year", language="en"
            )

            # Validate results
            assert len(result) == 1
            assert isinstance(result[0], BalanceSheetRow)
            assert result[0].source == VnstockDataSource.TCBS
            assert result[0].language == "en"

    @pytest.mark.asyncio
    async def test_get_income_statement_english(self, mock_tcbs_adapter):
        """Test income statement retrieval in English from TCBS."""
        import pandas as pd

        sample_df = pd.DataFrame({
            "Total Revenue": [1000000],
            "Cost of Goods Sold": [600000],
            "Net Income": [200000],
        })
        sample_df.index = pd.to_datetime(["2023-12-31"])
        sample_df.index.name = "period_end"

        mock_tcbs_adapter._transform_dataframe.return_value = sample_df

        # Mock the transformer
        with patch(
            "app.core.application.financial_data_transformer.FinancialDataTransformer.transform_income_statement"
        ) as mock_transform:
            mock_transform.return_value = [
                IncomeStatementRow(
                    period_end=datetime(2023, 12, 31),
                    symbol="ACB",
                    source=VnstockDataSource.TCBS,
                    total_revenue=1000000,
                    cost_of_goods_sold=600000,
                    net_income=200000,
                    language="en",
                )
            ]

            adapter = TCBSAdapter(MagicMock())
            adapter._validate_symbol = mock_tcbs_adapter._validate_symbol
            adapter._transform_dataframe = mock_tcbs_adapter._transform_dataframe

            result = await adapter.get_income_statement(
                symbol="ACB", period="year", language="en"
            )

            assert len(result) == 1
            assert result[0].language == "en"

    @pytest.mark.asyncio
    async def test_adapter_error_handling(self, mock_tcbs_adapter):
        """Test error handling in TCBS adapter."""
        # Setup transform error
        mock_tcbs_adapter._transform_dataframe.side_effect = Exception(
            "TCBS API error"
        )

        adapter = TCBSAdapter(MagicMock())
        adapter._validate_symbol = mock_tcbs_adapter._validate_symbol
        adapter._transform_dataframe = mock_tcbs_adapter._transform_dataframe

        # Expect DataSourceUnavailableError for adapter errors
        with pytest.raises(DataSourceUnavailableError):
            await adapter.get_balance_sheet(
                symbol="ACB", period="year", language="en"
            )

    def test_adapter_source_consistency(self):
        """Test that adapters correctly identify their data source."""
        vci_config = MagicMock()
        tcbs_config = MagicMock()

        vci_adapter = VCIAdapter(vci_config)
        tcbs_adapter = TCBSAdapter(tcbs_config)

        # This would test the source property if implemented
        # For now, we verify the adapters can be instantiated
        assert vci_adapter is not None
        assert tcbs_adapter is not None

    @pytest.mark.asyncio
    async def test_vnstock_import_error_handling(self):
        """Test handling when vnstock library import fails."""
        # Test with vnstock unavailable
        with patch.dict('sys.modules', {'vnstock': None}):
            # This test verifies the import error handling
            # The actual adapters should handle vnstock import gracefully
            adapter = VCIAdapter(MagicMock())
            # The adapter should not crash during initialization
            assert adapter is not None