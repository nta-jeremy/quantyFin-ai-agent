-- Migration: 004_analytics_tables.sql
-- Description: Create analytics and monitoring tables for system insights
-- Created: 2024-01-01
-- Author: QuantyFinAI Team

-- Create system_metrics table for monitoring
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'summary')),
    value NUMERIC(15, 4) NOT NULL,
    labels JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create agent_performance table for tracking AI agent performance
CREATE TABLE agent_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC(10, 6),
    confidence_score NUMERIC(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create user_activity table for tracking user interactions
CREATE TABLE user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN ('login', 'logout', 'query', 'analysis', 'prediction', 'download')),
    activity_data JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create api_usage table for tracking API usage
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create data_quality_metrics table for monitoring data quality
CREATE TABLE data_quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data_source VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(15, 4) NOT NULL,
    threshold_value NUMERIC(15, 4),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pass', 'warning', 'fail')),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_system_metrics_type ON system_metrics(metric_type);

CREATE INDEX idx_agent_performance_agent ON agent_performance(agent_name);
CREATE INDEX idx_agent_performance_task ON agent_performance(task_type);
CREATE INDEX idx_agent_performance_created_at ON agent_performance(created_at);
CREATE INDEX idx_agent_performance_success ON agent_performance(success);

CREATE INDEX idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX idx_user_activity_created_at ON user_activity(created_at);
CREATE INDEX idx_user_activity_session ON user_activity(session_id);

CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX idx_api_usage_created_at ON api_usage(created_at);
CREATE INDEX idx_api_usage_status ON api_usage(status_code);

CREATE INDEX idx_data_quality_source ON data_quality_metrics(data_source);
CREATE INDEX idx_data_quality_metric ON data_quality_metrics(metric_name);
CREATE INDEX idx_data_quality_status ON data_quality_metrics(status);
CREATE INDEX idx_data_quality_created_at ON data_quality_metrics(created_at);

-- Create function to clean up old metrics data
CREATE OR REPLACE FUNCTION cleanup_old_metrics(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up system_metrics older than retention period
    DELETE FROM system_metrics 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up agent_performance older than retention period
    DELETE FROM agent_performance 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Clean up user_activity older than retention period (keep longer for analytics)
    DELETE FROM user_activity 
    WHERE created_at < NOW() - INTERVAL '1 day' * (retention_days * 3);
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Clean up api_usage older than retention period
    DELETE FROM api_usage 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get system health status
CREATE OR REPLACE FUNCTION get_system_health()
RETURNS TABLE (
    metric_name VARCHAR(100),
    current_value NUMERIC(15, 4),
    status VARCHAR(20),
    last_updated TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sm.metric_name,
        sm.value as current_value,
        CASE 
            WHEN sm.value > 0.9 THEN 'critical'
            WHEN sm.value > 0.7 THEN 'warning'
            ELSE 'healthy'
        END as status,
        sm.timestamp as last_updated
    FROM system_metrics sm
    WHERE sm.timestamp > NOW() - INTERVAL '1 hour'
    ORDER BY sm.metric_name;
END;
$$ LANGUAGE plpgsql;

-- Create function to get agent performance summary
CREATE OR REPLACE FUNCTION get_agent_performance_summary(
    agent_name_filter VARCHAR(100) DEFAULT NULL,
    hours_back INTEGER DEFAULT 24
)
RETURNS TABLE (
    agent_name VARCHAR(100),
    total_tasks BIGINT,
    success_rate NUMERIC(5, 2),
    avg_execution_time NUMERIC(10, 2),
    avg_confidence NUMERIC(3, 2),
    total_cost NUMERIC(10, 2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ap.agent_name,
        COUNT(*) as total_tasks,
        ROUND(AVG(CASE WHEN ap.success THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate,
        ROUND(AVG(ap.execution_time_ms), 2) as avg_execution_time,
        ROUND(AVG(ap.confidence_score), 2) as avg_confidence,
        ROUND(SUM(COALESCE(ap.cost_usd, 0)), 2) as total_cost
    FROM agent_performance ap
    WHERE ap.created_at > NOW() - INTERVAL '1 hour' * hours_back
      AND (agent_name_filter IS NULL OR ap.agent_name = agent_name_filter)
    GROUP BY ap.agent_name
    ORDER BY total_tasks DESC;
END;
$$ LANGUAGE plpgsql;

-- Create view for recent user activity
CREATE VIEW recent_user_activity AS
SELECT 
    ua.id,
    u.username,
    ua.activity_type,
    ua.activity_data,
    ua.ip_address,
    ua.created_at
FROM user_activity ua
LEFT JOIN users u ON ua.user_id = u.id
WHERE ua.created_at > NOW() - INTERVAL '24 hours'
ORDER BY ua.created_at DESC;

-- Create view for API usage statistics
CREATE VIEW api_usage_stats AS
SELECT 
    endpoint,
    method,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN status_code < 400 THEN 1 END) as successful_requests,
    ROUND(AVG(response_time_ms), 2) as avg_response_time,
    ROUND(COUNT(CASE WHEN status_code < 400 THEN 1 END)::NUMERIC / COUNT(*) * 100, 2) as success_rate
FROM api_usage
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY endpoint, method
ORDER BY total_requests DESC;
