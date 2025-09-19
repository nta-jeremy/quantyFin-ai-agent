-- Migration 005: Vietnamese Market Data Tables
-- This migration creates tables for Vietnamese market data integration

-- Create enum types for Vietnamese market data
CREATE TYPE vietnamese_exchange AS ENUM ('HOSE', 'HNX', 'UPCOM');
CREATE TYPE vnstock_data_source AS ENUM ('VCI', 'TCBS', 'MSN');
CREATE TYPE vietnamese_market_group AS ENUM ('VN30', 'VNMIDCAP', 'VNSMALLCAP', 'ETF', 'CW', 'BOND');

-- Vietnamese Stock Data Table
CREATE TABLE vietnamese_stocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    vnstock_symbol VARCHAR(10) NOT NULL,
    exchange vietnamese_exchange NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(15,4) NOT NULL CHECK (open_price > 0),
    close_price DECIMAL(15,4) NOT NULL CHECK (close_price > 0),
    high_price DECIMAL(15,4) NOT NULL CHECK (high_price > 0),
    low_price DECIMAL(15,4) NOT NULL CHECK (low_price > 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    market_cap DECIMAL(20,2),
    free_float DECIMAL(5,2) CHECK (free_float >= 0 AND free_float <= 100),
    listing_date TIMESTAMP WITH TIME ZONE,
    sector VARCHAR(100),
    industry VARCHAR(100),
    industry_icb_code VARCHAR(20),
    market_group vietnamese_market_group,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_high_low CHECK (high_price >= low_price),
    CONSTRAINT chk_high_open CHECK (high_price >= open_price),
    CONSTRAINT chk_high_close CHECK (high_price >= close_price),
    CONSTRAINT chk_low_open CHECK (low_price <= open_price),
    CONSTRAINT chk_low_close CHECK (low_price <= close_price)
);

-- Vietnamese Companies Table
CREATE TABLE vietnamese_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vnstock_symbol VARCHAR(10) NOT NULL UNIQUE,
    exchange vietnamese_exchange NOT NULL,
    name VARCHAR(255) NOT NULL,
    ticker_symbol VARCHAR(10) NOT NULL,
    industry VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Vietnam',
    founded_date TIMESTAMP WITH TIME ZONE,
    industry_icb_code VARCHAR(20),
    market_cap DECIMAL(20,2),
    free_float DECIMAL(5,2) CHECK (free_float >= 0 AND free_float <= 100),
    listing_date TIMESTAMP WITH TIME ZONE,
    market_group vietnamese_market_group,
    is_active BOOLEAN DEFAULT TRUE,
    website VARCHAR(255),
    address VARCHAR(500),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vietnamese Financial Reports Table
CREATE TABLE vietnamese_financial_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    vnstock_symbol VARCHAR(10) NOT NULL,
    exchange vietnamese_exchange NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    filing_date TIMESTAMP WITH TIME ZONE NOT NULL,
    document_url TEXT NOT NULL,
    summary TEXT,
    report_language VARCHAR(5) DEFAULT 'vi',
    is_audited BOOLEAN DEFAULT FALSE,
    auditor_name VARCHAR(255),
    filing_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_period_range CHECK (period_start < period_end)
);

-- Vietnamese Financial Metrics Table
CREATE TABLE vietnamese_financial_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    vnstock_symbol VARCHAR(10) NOT NULL,
    exchange vietnamese_exchange NOT NULL,
    revenue DECIMAL(20,2) CHECK (revenue >= 0),
    net_income DECIMAL(20,2),
    total_assets DECIMAL(20,2) CHECK (total_assets >= 0),
    total_liabilities DECIMAL(20,2) CHECK (total_liabilities >= 0),
    cash_flow DECIMAL(20,2),
    pe_ratio DECIMAL(10,4) CHECK (pe_ratio >= 0),
    roe DECIMAL(10,4),
    roa DECIMAL(10,4),
    debt_to_equity DECIMAL(10,4) CHECK (debt_to_equity >= 0),
    current_ratio DECIMAL(10,4) CHECK (current_ratio >= 0),
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Vietnamese specific metrics
    eps DECIMAL(10,4),
    book_value_per_share DECIMAL(10,4) CHECK (book_value_per_share >= 0),
    dividend_yield DECIMAL(10,4) CHECK (dividend_yield >= 0),
    price_to_book DECIMAL(10,4) CHECK (price_to_book >= 0),
    price_to_sales DECIMAL(10,4) CHECK (price_to_sales >= 0),
    ev_to_ebitda DECIMAL(10,4),
    debt_to_assets DECIMAL(10,4) CHECK (debt_to_assets >= 0),
    interest_coverage DECIMAL(10,4) CHECK (interest_coverage >= 0),
    return_on_equity DECIMAL(10,4),
    return_on_assets DECIMAL(10,4),
    gross_margin DECIMAL(5,2) CHECK (gross_margin >= 0 AND gross_margin <= 100),
    operating_margin DECIMAL(5,2) CHECK (operating_margin >= 0 AND operating_margin <= 100),
    net_margin DECIMAL(5,2) CHECK (net_margin >= 0 AND net_margin <= 100),
    quick_ratio DECIMAL(10,4) CHECK (quick_ratio >= 0),
    cash_ratio DECIMAL(10,4) CHECK (cash_ratio >= 0),
    inventory_turnover DECIMAL(10,4) CHECK (inventory_turnover >= 0),
    receivables_turnover DECIMAL(10,4) CHECK (receivables_turnover >= 0),
    asset_turnover DECIMAL(10,4) CHECK (asset_turnover >= 0),
    equity_multiplier DECIMAL(10,4) CHECK (equity_multiplier >= 0)
);

-- Vietnamese Market Data Table
CREATE TABLE vietnamese_market_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange vietnamese_exchange NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    index_value DECIMAL(10,2) CHECK (index_value >= 0),
    index_change DECIMAL(10,2),
    index_change_percent DECIMAL(8,4),
    total_volume BIGINT CHECK (total_volume >= 0),
    total_value DECIMAL(20,2) CHECK (total_value >= 0),
    advancing_stocks INTEGER CHECK (advancing_stocks >= 0),
    declining_stocks INTEGER CHECK (declining_stocks >= 0),
    unchanged_stocks INTEGER CHECK (unchanged_stocks >= 0),
    foreign_buy_value DECIMAL(20,2) CHECK (foreign_buy_value >= 0),
    foreign_sell_value DECIMAL(20,2) CHECK (foreign_sell_value >= 0),
    net_foreign_value DECIMAL(20,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint for exchange and date
    UNIQUE(exchange, date)
);

-- Vietnamese News Table
CREATE TABLE vietnamese_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vnstock_symbol VARCHAR(10),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    url VARCHAR(500),
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    language VARCHAR(5) DEFAULT 'vi',
    sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    sentiment_label VARCHAR(20),
    tags TEXT[], -- Array of tags
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vietnamese Events Table
CREATE TABLE vietnamese_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vnstock_symbol VARCHAR(10) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_date TIMESTAMP WITH TIME ZONE NOT NULL,
    record_date TIMESTAMP WITH TIME ZONE,
    ex_date TIMESTAMP WITH TIME ZONE,
    payment_date TIMESTAMP WITH TIME ZONE,
    value DECIMAL(15,4),
    currency VARCHAR(10) DEFAULT 'VND',
    status VARCHAR(20) DEFAULT 'upcoming',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_event_status CHECK (status IN ('upcoming', 'completed', 'cancelled'))
);

-- Vietnamese Dividends Table
CREATE TABLE vietnamese_dividends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vnstock_symbol VARCHAR(10) NOT NULL,
    dividend_type VARCHAR(20) NOT NULL,
    amount_per_share DECIMAL(15,4) NOT NULL CHECK (amount_per_share >= 0),
    currency VARCHAR(10) DEFAULT 'VND',
    ex_date TIMESTAMP WITH TIME ZONE NOT NULL,
    record_date TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_date TIMESTAMP WITH TIME ZONE NOT NULL,
    announcement_date TIMESTAMP WITH TIME ZONE,
    fiscal_year INTEGER NOT NULL CHECK (fiscal_year >= 2000 AND fiscal_year <= 2100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_dividend_type CHECK (dividend_type IN ('cash', 'stock', 'special')),
    CONSTRAINT chk_dividend_dates CHECK (ex_date <= record_date AND record_date <= payment_date)
);

-- Vietnamese Shareholders Table
CREATE TABLE vietnamese_shareholders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vnstock_symbol VARCHAR(10) NOT NULL,
    shareholder_name VARCHAR(255) NOT NULL,
    shareholder_type VARCHAR(50) NOT NULL,
    shares_held BIGINT NOT NULL CHECK (shares_held >= 0),
    ownership_percentage DECIMAL(5,2) NOT NULL CHECK (ownership_percentage >= 0 AND ownership_percentage <= 100),
    is_major_shareholder BOOLEAN DEFAULT FALSE,
    report_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_shareholder_type CHECK (shareholder_type IN ('individual', 'institutional', 'foreign'))
);

-- Create indexes for better performance
CREATE INDEX idx_vietnamese_stocks_symbol_date ON vietnamese_stocks(vnstock_symbol, date);
CREATE INDEX idx_vietnamese_stocks_exchange_date ON vietnamese_stocks(exchange, date);
CREATE INDEX idx_vietnamese_stocks_company_id ON vietnamese_stocks(company_id);

CREATE INDEX idx_vietnamese_companies_symbol ON vietnamese_companies(vnstock_symbol);
CREATE INDEX idx_vietnamese_companies_exchange ON vietnamese_companies(exchange);
CREATE INDEX idx_vietnamese_companies_industry ON vietnamese_companies(industry);

CREATE INDEX idx_vietnamese_financial_reports_symbol ON vietnamese_financial_reports(vnstock_symbol);
CREATE INDEX idx_vietnamese_financial_reports_company_id ON vietnamese_financial_reports(company_id);
CREATE INDEX idx_vietnamese_financial_reports_period ON vietnamese_financial_reports(period_start, period_end);

CREATE INDEX idx_vietnamese_financial_metrics_symbol ON vietnamese_financial_metrics(vnstock_symbol);
CREATE INDEX idx_vietnamese_financial_metrics_company_id ON vietnamese_financial_metrics(company_id);
CREATE INDEX idx_vietnamese_financial_metrics_period ON vietnamese_financial_metrics(period_end);

CREATE INDEX idx_vietnamese_market_data_exchange_date ON vietnamese_market_data(exchange, date);

CREATE INDEX idx_vietnamese_news_symbol ON vietnamese_news(vnstock_symbol);
CREATE INDEX idx_vietnamese_news_published_at ON vietnamese_news(published_at);
CREATE INDEX idx_vietnamese_news_sentiment ON vietnamese_news(sentiment_score);

CREATE INDEX idx_vietnamese_events_symbol ON vietnamese_events(vnstock_symbol);
CREATE INDEX idx_vietnamese_events_event_date ON vietnamese_events(event_date);
CREATE INDEX idx_vietnamese_events_status ON vietnamese_events(status);

CREATE INDEX idx_vietnamese_dividends_symbol ON vietnamese_dividends(vnstock_symbol);
CREATE INDEX idx_vietnamese_dividends_ex_date ON vietnamese_dividends(ex_date);
CREATE INDEX idx_vietnamese_dividends_fiscal_year ON vietnamese_dividends(fiscal_year);

CREATE INDEX idx_vietnamese_shareholders_symbol ON vietnamese_shareholders(vnstock_symbol);
CREATE INDEX idx_vietnamese_shareholders_report_date ON vietnamese_shareholders(report_date);
CREATE INDEX idx_vietnamese_shareholders_type ON vietnamese_shareholders(shareholder_type);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vietnamese_stocks_updated_at
    BEFORE UPDATE ON vietnamese_stocks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vietnamese_companies_updated_at
    BEFORE UPDATE ON vietnamese_companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE vietnamese_stocks IS 'Historical and real-time Vietnamese stock data';
COMMENT ON TABLE vietnamese_companies IS 'Vietnamese company information and profiles';
COMMENT ON TABLE vietnamese_financial_reports IS 'Vietnamese company financial reports (balance sheet, income statement, cash flow)';
COMMENT ON TABLE vietnamese_financial_metrics IS 'Vietnamese company financial metrics and ratios';
COMMENT ON TABLE vietnamese_market_data IS 'Vietnamese market-wide data and indices';
COMMENT ON TABLE vietnamese_news IS 'Vietnamese financial news and market updates';
COMMENT ON TABLE vietnamese_events IS 'Vietnamese corporate events and announcements';
COMMENT ON TABLE vietnamese_dividends IS 'Vietnamese dividend information and payments';
COMMENT ON TABLE vietnamese_shareholders IS 'Vietnamese company shareholder information';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO quantyfin;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO quantyfin;
