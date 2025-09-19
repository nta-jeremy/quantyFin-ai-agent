-- Migration: 002_financial_data.sql
-- Description: Create financial data tables for reports and stock data
-- Created: 2024-01-01
-- Author: QuantyFinAI Team

-- Create financial_reports table
CREATE TABLE financial_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL CHECK (report_type IN ('Annual', 'Quarterly', 'Semi-Annual', 'Monthly')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    filing_date DATE NOT NULL,
    document_url TEXT NOT NULL,
    summary TEXT,
    file_size BIGINT,
    file_type VARCHAR(10),
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create stock_data table
CREATE TABLE stock_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open_price NUMERIC(10, 2) NOT NULL CHECK (open_price > 0),
    close_price NUMERIC(10, 2) NOT NULL CHECK (close_price > 0),
    high_price NUMERIC(10, 2) NOT NULL CHECK (high_price > 0),
    low_price NUMERIC(10, 2) NOT NULL CHECK (low_price > 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    adjusted_close NUMERIC(10, 2),
    dividend_amount NUMERIC(10, 4) DEFAULT 0,
    split_coefficient NUMERIC(10, 4) DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create market_indicators table for broader market data
CREATE TABLE market_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_name VARCHAR(100) NOT NULL,
    indicator_type VARCHAR(50) NOT NULL CHECK (indicator_type IN ('Index', 'Currency', 'Commodity', 'Bond')),
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    value NUMERIC(15, 4) NOT NULL,
    change_percent NUMERIC(8, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_financial_reports_company_id ON financial_reports(company_id);
CREATE INDEX idx_financial_reports_period ON financial_reports(period_start, period_end);
CREATE INDEX idx_financial_reports_type ON financial_reports(report_type);
CREATE INDEX idx_financial_reports_filing_date ON financial_reports(filing_date);

CREATE INDEX idx_stock_data_company_id ON stock_data(company_id);
CREATE INDEX idx_stock_data_date ON stock_data(date);
CREATE INDEX idx_stock_data_company_date ON stock_data(company_id, date);

CREATE INDEX idx_market_indicators_symbol ON market_indicators(symbol);
CREATE INDEX idx_market_indicators_date ON market_indicators(date);
CREATE INDEX idx_market_indicators_type ON market_indicators(indicator_type);

-- Create unique constraints to prevent duplicate data
CREATE UNIQUE INDEX idx_stock_data_unique ON stock_data(company_id, date);
CREATE UNIQUE INDEX idx_market_indicators_unique ON market_indicators(symbol, date);

-- Create triggers for updated_at
CREATE TRIGGER update_financial_reports_updated_at BEFORE UPDATE ON financial_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stock_data_updated_at BEFORE UPDATE ON stock_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to validate date ranges
CREATE OR REPLACE FUNCTION validate_financial_report_dates()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.period_start >= NEW.period_end THEN
        RAISE EXCEPTION 'period_start must be before period_end';
    END IF;
    
    IF NEW.filing_date < NEW.period_end THEN
        RAISE EXCEPTION 'filing_date must be on or after period_end';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for date validation
CREATE TRIGGER validate_financial_report_dates_trigger
    BEFORE INSERT OR UPDATE ON financial_reports
    FOR EACH ROW EXECUTE FUNCTION validate_financial_report_dates();

-- Create function to calculate stock price change
CREATE OR REPLACE FUNCTION calculate_price_change()
RETURNS TRIGGER AS $$
BEGIN
    -- This function can be extended to calculate various technical indicators
    -- For now, it's a placeholder for future enhancements
    RETURN NEW;
END;
$$ language 'plpgsql';
