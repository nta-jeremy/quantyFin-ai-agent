"""
Financial data transformer for converting vnstock DataFrames to domain models.

This module provides transformation utilities for converting vnstock library
DataFrame outputs to typed domain models following the project's data model.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from ..domain.financial_reports import (
    BalanceSheetRow, IncomeStatementRow, CashFlowRow, FinancialRatioRow
)
from ..domain.enums import VnstockDataSource


class FinancialDataTransformer:
    """Transform vnstock DataFrame data to typed domain models."""

    @staticmethod
    def transform_balance_sheet(
        df: pd.DataFrame,
        symbol: str,
        source: VnstockDataSource,
        language: str = "vi"
    ) -> List[BalanceSheetRow]:
        """Transform balance sheet DataFrame to typed models."""
        if df.empty:
            return []

        # Column name mapping for vnstock balance sheet data
        column_mapping = {
            # Vietnamese column names
            'Tổng tài sản': 'total_assets',
            'Tài sản ngắn hạn': 'current_assets',
            'Tiền và tương đương tiền': 'cash_and_equivalents',
            'Đầu tư tài chính ngắn hạn': 'short_term_investments',
            'Các khoản phải thu ngắn hạn': 'accounts_receivable',
            'Hàng tồn kho': 'inventory',
            'Tài sản ngắn hạn khác': 'other_current_assets',
            'Tài sản dài hạn': 'non_current_assets',
            'Tài sản cố định': 'property_plant_equipment',
            'Tài sản vô hình': 'intangible_assets',
            'Đầu tư tài chính dài hạn': 'long_term_investments',
            'Tài sản dài hạn khác': 'other_non_current_assets',
            'Nợ phải trả': 'total_liabilities',
            'Nợ ngắn hạn': 'current_liabilities',
            'Phải trả người bán ngắn hạn': 'accounts_payable',
            'Vay ngắn hạn': 'short_term_debt',
            'Chi phí phải trả ngắn hạn': 'accrued_expenses',
            'Nợ ngắn hạn khác': 'other_current_liabilities',
            'Nợ dài hạn': 'non_current_liabilities',
            'Vay dài hạn': 'long_term_debt',
            'Nợ dài hạn khác': 'other_non_current_liabilities',
            'Vốn chủ sở hữu': 'total_equity',
            'Lợi nhuận sau thuế chưa phân phối': 'retained_earnings',
            'Vốn góp của chủ sở hữu': 'share_capital',
            'Vốn chủ sở hữu khác': 'other_equity',

            # English column names
            'Total Assets': 'total_assets',
            'Current Assets': 'current_assets',
            'Cash and Equivalents': 'cash_and_equivalents',
            'Short-term Investments': 'short_term_investments',
            'Accounts Receivable': 'accounts_receivable',
            'Inventory': 'inventory',
            'Other Current Assets': 'other_current_assets',
            'Non-current Assets': 'non_current_assets',
            'Property, Plant and Equipment': 'property_plant_equipment',
            'Intangible Assets': 'intangible_assets',
            'Long-term Investments': 'long_term_investments',
            'Other Non-current Assets': 'other_non_current_assets',
            'Total Liabilities': 'total_liabilities',
            'Current Liabilities': 'current_liabilities',
            'Accounts Payable': 'accounts_payable',
            'Short-term Debt': 'short_term_debt',
            'Accrued Expenses': 'accrued_expenses',
            'Other Current Liabilities': 'other_current_liabilities',
            'Non-current Liabilities': 'non_current_liabilities',
            'Long-term Debt': 'long_term_debt',
            'Other Non-current Liabilities': 'other_non_current_liabilities',
            'Total Equity': 'total_equity',
            'Retained Earnings': 'retained_earnings',
            'Share Capital': 'share_capital',
            'Other Equity': 'other_equity',
        }

        # Standardize column names
        df_standardized = df.rename(columns=column_mapping)

        # Convert period_end column to datetime
        if 'period_end' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['period_end'])
        elif 'Period End' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['Period End'])

        # Ensure symbol and source are set
        df_standardized['symbol'] = symbol.upper()
        df_standardized['source'] = source
        df_standardized['language'] = language

        # Transform to model objects
        balance_sheets = []
        for _, row in df_standardized.iterrows():
            try:
                balance_sheet = BalanceSheetRow(
                    period_end=row.get('period_end', datetime.now()),
                    symbol=row.get('symbol', symbol.upper()),
                    source=row.get('source', source),
                    language=row.get('language', language),
                    current_assets=row.get('current_assets'),
                    cash_and_equivalents=row.get('cash_and_equivalents'),
                    short_term_investments=row.get('short_term_investments'),
                    accounts_receivable=row.get('accounts_receivable'),
                    inventory=row.get('inventory'),
                    other_current_assets=row.get('other_current_assets'),
                    non_current_assets=row.get('non_current_assets'),
                    property_plant_equipment=row.get('property_plant_equipment'),
                    intangible_assets=row.get('intangible_assets'),
                    long_term_investments=row.get('long_term_investments'),
                    other_non_current_assets=row.get('other_non_current_assets'),
                    total_assets=row.get('total_assets'),
                    current_liabilities=row.get('current_liabilities'),
                    accounts_payable=row.get('accounts_payable'),
                    short_term_debt=row.get('short_term_debt'),
                    accrued_expenses=row.get('accrued_expenses'),
                    other_current_liabilities=row.get('other_current_liabilities'),
                    non_current_liabilities=row.get('non_current_liabilities'),
                    long_term_debt=row.get('long_term_debt'),
                    other_non_current_liabilities=row.get('other_non_current_liabilities'),
                    total_liabilities=row.get('total_liabilities'),
                    shareholders_equity=row.get('shareholders_equity'),
                    retained_earnings=row.get('retained_earnings'),
                    share_capital=row.get('share_capital'),
                    other_equity=row.get('other_equity'),
                    total_equity=row.get('total_equity')
                )
                balance_sheets.append(balance_sheet)
            except Exception as e:
                # Skip invalid rows but continue processing
                continue

        return balance_sheets

    @staticmethod
    def transform_income_statement(
        df: pd.DataFrame,
        symbol: str,
        source: VnstockDataSource,
        language: str = "vi"
    ) -> List[IncomeStatementRow]:
        """Transform income statement DataFrame to typed models."""
        if df.empty:
            return []

        # Column name mapping for income statement data
        column_mapping = {
            # Vietnamese column names
            'Doanh thu thuần': 'total_revenue',
            'Giá vốn hàng bán': 'cost_of_goods_sold',
            'Lợi nhuận gộp': 'gross_profit',
            'Doanh thu hoạt động kinh doanh': 'operating_revenue',
            'Chi phí bán hàng': 'selling_expenses',
            'Chi phí quản lý doanh nghiệp': 'administrative_expenses',
            'Chi phí tài chính': 'interest_expense',
            'Thu nhập khác': 'other_income',
            'Lợi nhuận thuần từ hoạt động kinh doanh': 'operating_income',
            'Tổng lợi nhuận kế toán trước thuế': 'pre_tax_income',
            'Chi phí thuế TNDN': 'tax_expense',
            'Lợi nhuận sau thuế': 'net_income',
            'Lợi nhuận cơ bản trên cổ phiếu': 'earnings_per_share',
            'Lợi nhuận suy giảm trên cổ phiếu': 'diluted_earnings_per_share',

            # English column names
            'Total Revenue': 'total_revenue',
            'Cost of Goods Sold': 'cost_of_goods_sold',
            'Gross Profit': 'gross_profit',
            'Operating Revenue': 'operating_revenue',
            'Selling Expenses': 'selling_expenses',
            'Administrative Expenses': 'administrative_expenses',
            'Financial Expenses': 'interest_expense',
            'Other Income': 'other_income',
            'Operating Income': 'operating_income',
            'Pre-tax Income': 'pre_tax_income',
            'Tax Expense': 'tax_expense',
            'Net Income': 'net_income',
            'Earnings Per Share': 'earnings_per_share',
            'Diluted Earnings Per Share': 'diluted_earnings_per_share',
        }

        # Standardize column names
        df_standardized = df.rename(columns=column_mapping)

        # Convert period_end column to datetime
        if 'period_end' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['period_end'])
        elif 'Period End' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['Period End'])

        # Ensure symbol and source are set
        df_standardized['symbol'] = symbol.upper()
        df_standardized['source'] = source
        df_standardized['language'] = language

        # Transform to model objects
        income_statements = []
        for _, row in df_standardized.iterrows():
            try:
                income_statement = IncomeStatementRow(
                    period_end=row.get('period_end', datetime.now()),
                    symbol=row.get('symbol', symbol.upper()),
                    source=row.get('source', source),
                    language=row.get('language', language),
                    total_revenue=row.get('total_revenue'),
                    operating_revenue=row.get('operating_revenue'),
                    other_revenue=row.get('other_revenue'),
                    cost_of_goods_sold=row.get('cost_of_goods_sold'),
                    gross_profit=row.get('gross_profit'),
                    operating_expenses=row.get('operating_expenses'),
                    selling_expenses=row.get('selling_expenses'),
                    administrative_expenses=row.get('administrative_expenses'),
                    research_development=row.get('research_development'),
                    operating_income=row.get('operating_income'),
                    interest_income=row.get('interest_income'),
                    interest_expense=row.get('interest_expense'),
                    other_income=row.get('other_income'),
                    pre_tax_income=row.get('pre_tax_income'),
                    tax_expense=row.get('tax_expense'),
                    net_income=row.get('net_income'),
                    earnings_per_share=row.get('earnings_per_share'),
                    diluted_earnings_per_share=row.get('diluted_earnings_per_share')
                )
                income_statements.append(income_statement)
            except Exception as e:
                # Skip invalid rows but continue processing
                continue

        return income_statements

    @staticmethod
    def transform_cash_flow(
        df: pd.DataFrame,
        symbol: str,
        source: VnstockDataSource
    ) -> List[CashFlowRow]:
        """Transform cash flow DataFrame to typed models."""
        if df.empty:
            return []

        # Column name mapping for cash flow data
        column_mapping = {
            # Vietnamese column names
            'Lợi nhuận sau thuế': 'net_income',
            'Khấu hao': 'depreciation_amortization',
            'Thay đổi vốn lưu động': 'changes_working_capital',
            'Dòng tiền từ hoạt động kinh doanh': 'net_cash_from_operations',
            'Mua sắm TSCĐ': 'capital_expenditures',
            'Mua đầu tư': 'investments',
            'Dòng tiền từ hoạt động đầu tư': 'net_cash_from_investing',
            'Vay và nợ trả': 'debt_proceeds',
            'Trả nợ vay': 'debt_repayments',
            'Chi trả cổ tức': 'dividends_paid',
            'Dòng tiền từ hoạt động tài chính': 'net_cash_from_financing',
            'Thay đổi tiền và tương đương tiền': 'net_change_in_cash',

            # English column names
            'Net Income': 'net_income',
            'Depreciation and Amortization': 'depreciation_amortization',
            'Changes in Working Capital': 'changes_working_capital',
            'Net Cash from Operations': 'net_cash_from_operations',
            'Capital Expenditures': 'capital_expenditures',
            'Investments': 'investments',
            'Net Cash from Investing': 'net_cash_from_investing',
            'Debt Proceeds': 'debt_proceeds',
            'Debt Repayments': 'debt_repayments',
            'Dividends Paid': 'dividends_paid',
            'Net Cash from Financing': 'net_cash_from_financing',
            'Net Change in Cash': 'net_change_in_cash',
        }

        # Standardize column names
        df_standardized = df.rename(columns=column_mapping)

        # Convert period_end column to datetime
        if 'period_end' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['period_end'])
        elif 'Period End' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['Period End'])

        # Ensure symbol and source are set
        df_standardized['symbol'] = symbol.upper()
        df_standardized['source'] = source

        # Calculate free cash flow if possible
        if 'net_cash_from_operations' in df_standardized.columns and 'capital_expenditures' in df_standardized.columns:
            df_standardized['free_cash_flow'] = (
                df_standardized['net_cash_from_operations'] - df_standardized['capital_expenditures']
            )

        # Transform to model objects
        cash_flows = []
        for _, row in df_standardized.iterrows():
            try:
                cash_flow = CashFlowRow(
                    period_end=row.get('period_end', datetime.now()),
                    symbol=row.get('symbol', symbol.upper()),
                    source=row.get('source', source),
                    net_income=row.get('net_income'),
                    depreciation_amortization=row.get('depreciation_amortization'),
                    changes_working_capital=row.get('changes_working_capital'),
                    other_operating_activities=row.get('other_operating_activities'),
                    net_cash_from_operations=row.get('net_cash_from_operations'),
                    capital_expenditures=row.get('capital_expenditures'),
                    acquisitions=row.get('acquisitions'),
                    investments=row.get('investments'),
                    other_investing_activities=row.get('other_investing_activities'),
                    net_cash_from_investing=row.get('net_cash_from_investing'),
                    debt_proceeds=row.get('debt_proceeds'),
                    debt_repayments=row.get('debt_repayments'),
                    equity_proceeds=row.get('equity_proceeds'),
                    dividends_paid=row.get('dividends_paid'),
                    other_financing_activities=row.get('other_financing_activities'),
                    net_cash_from_financing=row.get('net_cash_from_financing'),
                    net_change_in_cash=row.get('net_change_in_cash'),
                    beginning_cash=row.get('beginning_cash'),
                    ending_cash=row.get('ending_cash'),
                    free_cash_flow=row.get('free_cash_flow')
                )
                cash_flows.append(cash_flow)
            except Exception as e:
                # Skip invalid rows but continue processing
                continue

        return cash_flows

    @staticmethod
    def transform_financial_ratios(
        df: pd.DataFrame,
        symbol: str,
        source: VnstockDataSource,
        language: str = "vi"
    ) -> List[FinancialRatioRow]:
        """Transform financial ratios DataFrame to typed models."""
        if df.empty:
            return []

        # Column name mapping for financial ratios
        column_mapping = {
            # Vietnamese column names
            'P/E': 'price_to_earnings',
            'P/B': 'price_to_book',
            'P/S': 'price_to_sales',
            'ROE': 'return_on_equity',
            'ROA': 'return_on_assets',
            'Biên lợi nhuận gộp': 'gross_margin',
            'Biên lợi nhuận hoạt động': 'operating_margin',
            'Biên lợi nhuận ròng': 'net_margin',
            'Hệ số thanh toán hiện hành': 'current_ratio',
            'Hệ số thanh toán nhanh': 'quick_ratio',
            'Nợ/Vốn chủ sở hữu': 'debt_to_equity',
            'EPS': 'earnings_per_share',
            'Tăng trưởng doanh thu': 'revenue_growth',
            'Tăng trưởng lợi nhuận': 'earnings_growth',
            'Lợi nhuận cổ tức': 'dividend_yield',

            # English column names
            'Price to Earnings': 'price_to_earnings',
            'Price to Book': 'price_to_book',
            'Price to Sales': 'price_to_sales',
            'Return on Equity': 'return_on_equity',
            'Return on Assets': 'return_on_assets',
            'Gross Margin': 'gross_margin',
            'Operating Margin': 'operating_margin',
            'Net Margin': 'net_margin',
            'Current Ratio': 'current_ratio',
            'Quick Ratio': 'quick_ratio',
            'Debt to Equity': 'debt_to_equity',
            'Earnings Per Share': 'earnings_per_share',
            'Revenue Growth': 'revenue_growth',
            'Earnings Growth': 'earnings_growth',
            'Dividend Yield': 'dividend_yield',
        }

        # Standardize column names
        df_standardized = df.rename(columns=column_mapping)

        # Convert period_end column to datetime
        if 'period_end' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['period_end'])
        elif 'Period End' in df_standardized.columns:
            df_standardized['period_end'] = pd.to_datetime(df_standardized['Period End'])

        # Ensure symbol and source are set
        df_standardized['symbol'] = symbol.upper()
        df_standardized['source'] = source
        df_standardized['language'] = language

        # Transform to model objects
        ratios = []
        for _, row in df_standardized.iterrows():
            try:
                ratio = FinancialRatioRow(
                    period_end=row.get('period_end', datetime.now()),
                    symbol=row.get('symbol', symbol.upper()),
                    source=row.get('source', source),
                    language=row.get('language', language),
                    price_to_earnings=row.get('price_to_earnings'),
                    price_to_book=row.get('price_to_book'),
                    price_to_sales=row.get('price_to_sales'),
                    enterprise_value_ebitda=row.get('enterprise_value_ebitda'),
                    return_on_equity=row.get('return_on_equity'),
                    return_on_assets=row.get('return_on_assets'),
                    gross_margin=row.get('gross_margin'),
                    operating_margin=row.get('operating_margin'),
                    net_margin=row.get('net_margin'),
                    current_ratio=row.get('current_ratio'),
                    quick_ratio=row.get('quick_ratio'),
                    cash_ratio=row.get('cash_ratio'),
                    debt_to_equity=row.get('debt_to_equity'),
                    debt_to_assets=row.get('debt_to_assets'),
                    interest_coverage=row.get('interest_coverage'),
                    asset_turnover=row.get('asset_turnover'),
                    inventory_turnover=row.get('inventory_turnover'),
                    receivables_turnover=row.get('receivables_turnover'),
                    revenue_growth=row.get('revenue_growth'),
                    earnings_growth=row.get('earnings_growth'),
                    dividend_yield=row.get('dividend_yield')
                )
                ratios.append(ratio)
            except Exception as e:
                # Skip invalid rows but continue processing
                continue

        return ratios