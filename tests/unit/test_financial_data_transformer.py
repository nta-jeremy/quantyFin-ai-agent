"""
Unit tests for FinancialDataTransformer.

This module tests the data transformation functionality from vnstock
DataFrames to domain models following TDD principles.
"""

import pytest
from datetime import datetime
from typing import List

import pandas as pd

from app.core.application.financial_data_transformer import FinancialDataTransformer
from app.core.domain.data_source_models import VnstockDataSource
from app.core.domain.financial_reports import (
    BalanceSheetRow,
    CashFlowRow,
    FinancialRatioRow,
    IncomeStatementRow,
)


class TestFinancialDataTransformer:
    """Test suite for FinancialDataTransformer."""

    def test_transform_balance_sheet_vietnamese(self):
        """Test balance sheet transformation with Vietnamese data."""
        # Create test DataFrame similar to vnstock output
        test_data = {
            "Tổng tài sản": [1000000, 1200000],
            "Tài sản ngắn hạn": [600000, 700000],
            "Tiền và tương đương tiền": [100000, 150000],
            "Tài sản dài hạn": [400000, 500000],
            "Tổng Nợ phải trả": [500000, 600000],
            "Nợ ngắn hạn": [300000, 350000],
            "Nợ dài hạn": [200000, 250000],
            "Vốn chủ sở hữu": [500000, 600000],
            "Nguồn vốn kinh doanh": [1000000, 1200000],
        }
        df = pd.DataFrame(test_data)
        df.index = pd.to_datetime(["2023-12-31", "2022-12-31"])
        df.index.name = "period_end"

        # Transform data
        result = FinancialDataTransformer.transform_balance_sheet(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
            language="vi",
        )

        # Validate structure
        assert isinstance(result, list)
        assert len(result) == 2

        # Validate first record
        record = result[0]
        assert isinstance(record, BalanceSheetRow)
        assert record.symbol == "ACB"
        assert record.source == VnstockDataSource.VCI
        assert record.language == "vi"
        assert record.period_end == datetime(2023, 12, 31)
        assert record.total_assets == 1000000
        assert record.current_assets == 600000
        assert record.cash_and_equivalents == 100000
        assert record.non_current_assets == 400000
        assert record.total_liabilities == 500000
        assert record.current_liabilities == 300000
        assert record.non_current_liabilities == 200000
        assert record.total_equity == 500000

    def test_transform_balance_sheet_english(self):
        """Test balance sheet transformation with English data."""
        test_data = {
            "Total Assets": [1000000, 1200000],
            "Current Assets": [600000, 700000],
            "Cash and Cash Equivalents": [100000, 150000],
            "Non-Current Assets": [400000, 500000],
            "Total Liabilities": [500000, 600000],
            "Current Liabilities": [300000, 350000],
            "Non-Current Liabilities": [200000, 250000],
            "Total Equity": [500000, 600000],
        }
        df = pd.DataFrame(test_data)
        df.index = pd.to_datetime(["2023-12-31", "2022-12-31"])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_balance_sheet(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.TCBS,
            language="en",
        )

        # Validate first record
        record = result[0]
        assert record.language == "en"
        assert record.total_assets == 1000000
        assert record.current_assets == 600000
        assert record.cash_and_equivalents == 100000

    def test_transform_balance_sheet_empty_data(self):
        """Test balance sheet transformation with empty DataFrame."""
        df = pd.DataFrame()
        df.index = pd.to_datetime([])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_balance_sheet(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
        )

        assert result == []

    def test_transform_income_statement(self):
        """Test income statement transformation."""
        test_data = {
            "Doanh thu thuần": [1000000, 900000],
            "Giá vốn hàng bán": [600000, 550000],
            "Lợi nhuận gộp": [400000, 350000],
            "Doanh thu hoạt động kinh doanh": [350000, 300000],
            "Lợi nhuận thuần từ HĐKD": [250000, 200000],
            "Lợi nhuận sau thuế": [200000, 150000],
            "EPS": [5000, 4000],
        }
        df = pd.DataFrame(test_data)
        df.index = pd.to_datetime(["2023-12-31", "2022-12-31"])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_income_statement(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
            language="vi",
        )

        assert len(result) == 2
        record = result[0]
        assert isinstance(record, IncomeStatementRow)
        assert record.symbol == "ACB"
        assert record.total_revenue == 1000000
        assert record.cost_of_goods_sold == 600000
        assert record.gross_profit == 400000
        assert record.operating_income == 350000
        assert record.net_income == 200000
        assert record.eps == 5000

    def test_transform_cash_flow(self):
        """Test cash flow statement transformation."""
        test_data = {
            "Dòng tiền từ hoạt động kinh doanh": [300000, 250000],
            "Dòng tiền từ hoạt động đầu tư": [-100000, -80000],
            "Dòng tiền từ hoạt động tài chính": [-150000, -120000],
            "Dòng tiền thuần trong kỳ": [50000, 50000],
            "Tiền và tương đương tiền đầu kỳ": [100000, 50000],
            "Tiền và tương đương tiền cuối kỳ": [150000, 100000],
        }
        df = pd.DataFrame(test_data)
        df.index = pd.to_datetime(["2023-12-31", "2022-12-31"])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_cash_flow(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
            language="vi",
        )

        assert len(result) == 2
        record = result[0]
        assert isinstance(record, CashFlowRow)
        assert record.symbol == "ACB"
        assert record.operating_cash_flow == 300000
        assert record.investing_cash_flow == -100000
        assert record.financing_cash_flow == -150000
        assert record.net_cash_flow == 50000
        assert record.cash_beginning_period == 100000
        assert record.cash_end_period == 150000

    def test_transform_financial_ratios(self):
        """Test financial ratios transformation."""
        test_data = {
            "P/E": [15.5, 12.3],
            "P/B": [2.1, 1.8],
            "ROE": [0.18, 0.15],
            "ROA": [0.12, 0.10],
            "Current Ratio": [1.5, 1.3],
            "Quick Ratio": [1.2, 1.0],
            "Debt to Equity": [0.8, 0.9],
            "Interest Coverage": [5.5, 4.2],
        }
        df = pd.DataFrame(test_data)
        df.index = pd.to_datetime(["2023-12-31", "2022-12-31"])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_financial_ratios(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
            language="vi",
        )

        assert len(result) == 2
        record = result[0]
        assert isinstance(record, FinancialRatioRow)
        assert record.symbol == "ACB"
        assert record.pe_ratio == 15.5
        assert record.pb_ratio == 2.1
        assert record.roe == 0.18
        assert record.roa == 0.12
        assert record.current_ratio == 1.5
        assert record.quick_ratio == 1.2
        assert record.debt_to_equity == 0.8
        assert record.interest_coverage == 5.5

    def test_column_mapping_comprehensive(self):
        """Test that column mapping handles all expected variations."""
        # Test with mixed Vietnamese/English columns
        test_data = {
            "Tổng tài sản": [1000000],  # Vietnamese
            "Total Liabilities": [500000],  # English
            "Vốn chủ sở hữu": [500000],  # Vietnamese
            "ROE": [0.18],  # English acronym
        }
        df = pd.DataFrame(test_data)
        df.index = pd.to_datetime(["2023-12-31"])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_balance_sheet(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
            language="vi",
        )

        assert len(result) == 1
        record = result[0]
        assert record.total_assets == 1000000
        assert record.total_liabilities == 500000
        assert record.total_equity == 500000

    def test_invalid_numeric_data_handling(self):
        """Test handling of invalid numeric data."""
        test_data = {
            "Tổng tài sản": ["1,000,000", "invalid", 500000],  # Mixed formats
            "Vốn chủ sở hữu": [500000, 400000, 300000],
        }
        df = pd.DataFrame(test_data)
        df.index = pd.to_datetime(["2023-12-31", "2022-12-31", "2021-12-31"])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_balance_sheet(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
        )

        # Should handle gracefully, potentially filtering invalid data
        assert isinstance(result, list)
        # Note: The actual behavior depends on the implementation's error handling

    def test_datetime_index_validation(self):
        """Test proper handling of datetime index."""
        test_data = {"Tổng tài sản": [1000000, 1200000]}
        df = pd.DataFrame(test_data, index=["2023-12-31", "2022-12-31"])
        df.index.name = "period_end"

        result = FinancialDataTransformer.transform_balance_sheet(
            df=df,
            symbol="ACB",
            source=VnstockDataSource.VCI,
        )

        assert len(result) == 2
        assert all(
            isinstance(record.period_end, datetime) for record in result
        )