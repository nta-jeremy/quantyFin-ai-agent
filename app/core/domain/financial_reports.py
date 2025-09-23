"""
Financial report domain models for Vietnamese stock market data.

This module contains Pydantic models for financial reporting data including
balance sheets, income statements, cash flow statements, and financial ratios.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

from .enums import VnstockDataSource


class BalanceSheetRow(BaseModel):
    """Balance sheet line item model."""

    # Metadata
    period_end: datetime
    symbol: str
    source: VnstockDataSource
    language: str = "vi"

    # Assets
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    short_term_investments: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    other_current_assets: Optional[float] = None

    non_current_assets: Optional[float] = None
    property_plant_equipment: Optional[float] = None
    intangible_assets: Optional[float] = None
    long_term_investments: Optional[float] = None
    other_non_current_assets: Optional[float] = None

    total_assets: Optional[float] = None

    # Liabilities
    current_liabilities: Optional[float] = None
    accounts_payable: Optional[float] = None
    short_term_debt: Optional[float] = None
    accrued_expenses: Optional[float] = None
    other_current_liabilities: Optional[float] = None

    non_current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    other_non_current_liabilities: Optional[float] = None

    total_liabilities: Optional[float] = None

    # Equity
    shareholders_equity: Optional[float] = None
    retained_earnings: Optional[float] = None
    share_capital: Optional[float] = None
    other_equity: Optional[float] = None

    total_equity: Optional[float] = None

    # Validation
    @field_validator('symbol')
    def symbol_upper(cls, v):
        return v.upper()

    @field_validator('language')
    def language_validation(cls, v):
        if v not in ['vi', 'en']:
            raise ValueError('Language must be "vi" or "en"')
        return v


class IncomeStatementRow(BaseModel):
    """Income statement line item model."""

    # Metadata
    period_end: datetime
    symbol: str
    source: VnstockDataSource
    language: str = "vi"

    # Revenue
    total_revenue: Optional[float] = None
    operating_revenue: Optional[float] = None
    other_revenue: Optional[float] = None

    # Expenses
    cost_of_goods_sold: Optional[float] = None
    gross_profit: Optional[float] = None

    operating_expenses: Optional[float] = None
    selling_expenses: Optional[float] = None
    administrative_expenses: Optional[float] = None
    research_development: Optional[float] = None

    operating_income: Optional[float] = None

    # Non-operating items
    interest_income: Optional[float] = None
    interest_expense: Optional[float] = None
    other_income: Optional[float] = None

    # Taxes and net income
    pre_tax_income: Optional[float] = None
    tax_expense: Optional[float] = None
    net_income: Optional[float] = None

    # Per share data
    earnings_per_share: Optional[float] = None
    diluted_earnings_per_share: Optional[float] = None

    # Validation
    @field_validator('symbol')
    def symbol_upper(cls, v):
        return v.upper()

    @field_validator('language')
    def language_validation(cls, v):
        if v not in ['vi', 'en']:
            raise ValueError('Language must be "vi" or "en"')
        return v


class CashFlowRow(BaseModel):
    """Cash flow statement line item model."""

    # Metadata
    period_end: datetime
    symbol: str
    source: VnstockDataSource

    # Operating activities
    net_income: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    changes_working_capital: Optional[float] = None
    other_operating_activities: Optional[float] = None
    net_cash_from_operations: Optional[float] = None

    # Investing activities
    capital_expenditures: Optional[float] = None
    acquisitions: Optional[float] = None
    investments: Optional[float] = None
    other_investing_activities: Optional[float] = None
    net_cash_from_investing: Optional[float] = None

    # Financing activities
    debt_proceeds: Optional[float] = None
    debt_repayments: Optional[float] = None
    equity_proceeds: Optional[float] = None
    dividends_paid: Optional[float] = None
    other_financing_activities: Optional[float] = None
    net_cash_from_financing: Optional[float] = None

    # Net change in cash
    net_change_in_cash: Optional[float] = None
    beginning_cash: Optional[float] = None
    ending_cash: Optional[float] = None

    # Free cash flow
    free_cash_flow: Optional[float] = None

    # Validation
    @field_validator('symbol')
    def symbol_upper(cls, v):
        return v.upper()


class FinancialRatioRow(BaseModel):
    """Financial ratios line item model."""

    # Metadata
    period_end: datetime
    symbol: str
    source: VnstockDataSource
    language: str = "vi"

    # Valuation ratios
    price_to_earnings: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    enterprise_value_ebitda: Optional[float] = None

    # Profitability ratios
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None

    # Liquidity ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None

    # Leverage ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None

    # Efficiency ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None

    # Growth ratios
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    dividend_yield: Optional[float] = None

    # Validation
    @field_validator('symbol')
    def symbol_upper(cls, v):
        return v.upper()

    @field_validator('language')
    def language_validation(cls, v):
        if v not in ['vi', 'en']:
            raise ValueError('Language must be "vi" or "en"')
        return v


# Request/Response Models

class FinancialReportRequest(BaseModel):
    """Base request model for financial reports."""

    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    source: VnstockDataSource = Field(default=VnstockDataSource.VCI, description="Data source")
    period: str = Field(default="year", regex="^(year|quarter)$", description="Report period")
    language: str = Field(default="vi", regex="^(vi|en)$", description="Report language")
    use_cache: bool = Field(default=True, description="Use cached data if available")

    @field_validator('symbol')
    def symbol_upper(cls, v):
        return v.upper()


class BalanceSheetMetadata(BaseModel):
    """Balance sheet response metadata."""

    symbol: str
    source: str
    period: str
    language: str
    count: int
    generated_at: str
    cache_status: str  # "hit", "miss", "stale"


class BalanceSheetResponse(BaseModel):
    """Balance sheet API response."""

    data: List[BalanceSheetRow]
    metadata: BalanceSheetMetadata


class ComprehensiveFinancialMetadata(BaseModel):
    """Comprehensive financial response metadata."""

    symbol: str
    source: str
    period: str
    language: str
    generated_at: str
    data_quality: Dict[str, Any]  # Quality metrics for each report type
    processing_time_ms: float


class ComprehensiveFinancialResponse(BaseModel):
    """Comprehensive financial data API response."""

    balance_sheet: List[BalanceSheetRow]
    income_statement: List[IncomeStatementRow]
    cash_flow: List[CashFlowRow]
    financial_ratios: List[FinancialRatioRow]
    metadata: ComprehensiveFinancialMetadata