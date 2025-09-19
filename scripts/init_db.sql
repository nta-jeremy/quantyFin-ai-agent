-- =============================================
-- QuantyFinAI Agent - Database Initialization
-- =============================================

-- This script initializes the PostgreSQL database with pgvector extension
-- and creates basic schema for the financial AI agent system.

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS "vector";

-- Enable uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm extension for text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================
-- Core Tables
-- =============================================

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles table for RBAC
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User roles association
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Sessions table for authentication
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Financial Data Tables
-- =============================================

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    description TEXT,
    market_cap DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock data table
CREATE TABLE IF NOT EXISTS stock_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    adjusted_close DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial reports table
CREATE TABLE IF NOT EXISTS financial_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL, -- 'annual', 'quarterly'
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER,
    revenue DECIMAL(20, 2),
    net_income DECIMAL(20, 2),
    earnings_per_share DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Vector Database Tables
-- =============================================

-- Document embeddings table for RAG system
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL, -- OpenAI embedding size
    metadata JSONB,
    source_type VARCHAR(50) NOT NULL, -- 'news', 'report', 'analysis', etc.
    source_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create HNSW index for efficient vector similarity search
CREATE INDEX IF NOT EXISTS idx_document_embeddings_hnsw ON document_embeddings
USING hnsw (embedding vector_cosine_ops);

-- Vector search queries table
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_embedding VECTOR(1536),
    search_type VARCHAR(50) NOT NULL, -- 'similarity', 'semantic', 'hybrid'
    results_count INTEGER DEFAULT 10,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query results table
CREATE TABLE IF NOT EXISTS query_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID REFERENCES search_queries(id) ON DELETE CASCADE,
    document_id UUID REFERENCES document_embeddings(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5, 4) NOT NULL,
    rank_position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- AI Agent Tables
-- =============================================

-- Agent execution logs
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(50) NOT NULL, -- 'guard', 'embedding', 'retriever', 'search', 'analyze', 'predict', 'aggregator'
    execution_id UUID NOT NULL,
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'timeout'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ML predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    prediction_type VARCHAR(50) NOT NULL, -- 'price', 'sentiment', 'trend'
    prediction_date DATE NOT NULL,
    predicted_value DECIMAL(20, 2),
    confidence_score DECIMAL(5, 4),
    model_version VARCHAR(50) NOT NULL,
    actual_value DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sentiment analysis results
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES document_embeddings(id) ON DELETE CASCADE,
    sentiment_score DECIMAL(5, 4) NOT NULL, -- -1.0 to 1.0
    sentiment_category VARCHAR(20) NOT NULL, -- 'positive', 'negative', 'neutral'
    confidence_score DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Analytics and Monitoring Tables
-- =============================================

-- User analytics table
CREATE TABLE IF NOT EXISTS user_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query_count INTEGER DEFAULT 0,
    total_execution_time_ms INTEGER DEFAULT 0,
    last_query_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System performance metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- =============================================
-- Indexes for Performance
-- =============================================

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);
CREATE INDEX IF NOT EXISTS idx_stock_data_company_date ON stock_data(company_id, date);
CREATE INDEX IF NOT EXISTS idx_document_embeddings_source_type ON document_embeddings(source_type);
CREATE INDEX IF NOT EXISTS idx_document_embeddings_created_at ON document_embeddings(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_logs_execution_id ON agent_logs(execution_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON agent_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_company_date ON predictions(company_id, prediction_date);
CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_document_id ON sentiment_analysis(document_id);

-- =============================================
-- Initialize with Default Data
-- =============================================

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
('admin', 'System administrator with full access', '{"read": true, "write": true, "delete": true, "manage_users": true}'),
('analyst', 'Financial analyst with read and analysis access', '{"read": true, "analyze": true}'),
('user', 'Regular user with basic access', '{"read": true}')
ON CONFLICT (name) DO NOTHING;

-- Insert sample companies for testing
INSERT INTO companies (ticker, name, sector, industry) VALUES
('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics'),
('GOOGL', 'Alphabet Inc.', 'Technology', 'Internet Services'),
('MSFT', 'Microsoft Corporation', 'Technology', 'Software'),
('AMZN', 'Amazon.com Inc.', 'Consumer Cyclical', 'E-Commerce')
ON CONFLICT (ticker) DO NOTHING;

-- =============================================
-- Verification
-- =============================================

-- Verify pgvector installation
SELECT 'pgvector extension installed successfully' as status
WHERE EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');

-- Verify database initialization
SELECT 'Database initialized successfully' as status,
       (SELECT COUNT(*) FROM users) as user_count,
       (SELECT COUNT(*) FROM companies) as company_count,
       (SELECT COUNT(*) FROM roles) as role_count;