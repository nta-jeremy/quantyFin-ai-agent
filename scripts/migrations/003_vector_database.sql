-- Migration: 003_vector_database.sql
-- Description: Setup vector database for RAG system with pgvector extension
-- Created: 2024-01-01
-- Author: QuantyFinAI Team

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_embeddings table for storing vector embeddings
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('news', 'report', 'legal', 'earnings_call', 'sec_filing', 'research', 'social_media')),
    source_id UUID, -- Optional: links to original source (e.g., financial_reports.id)
    content_chunk TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL, -- OpenAI text-embedding-ada-002 dimension
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chunk_size INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL DEFAULT 1,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create document_sources table to track original documents
CREATE TABLE document_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    title TEXT,
    author VARCHAR(255),
    published_date TIMESTAMP,
    file_path TEXT,
    file_size BIGINT,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create user_queries table to track user interactions for analytics
CREATE TABLE user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) CHECK (query_type IN ('analysis', 'prediction', 'search', 'general')),
    response_text TEXT,
    confidence_score NUMERIC(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    processing_time_ms INTEGER,
    retrieved_documents INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create query_embeddings table to store query vectors for similarity search
CREATE TABLE query_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID NOT NULL REFERENCES user_queries(id) ON DELETE CASCADE,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for vector operations and performance
CREATE INDEX idx_document_embeddings_source_type ON document_embeddings(source_type);
CREATE INDEX idx_document_embeddings_source_id ON document_embeddings(source_id);
CREATE INDEX idx_document_embeddings_created_at ON document_embeddings(created_at);

-- Create vector similarity search index using HNSW algorithm
CREATE INDEX idx_document_embeddings_vector_cosine ON document_embeddings 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Create additional vector indexes for different distance metrics
CREATE INDEX idx_document_embeddings_vector_l2 ON document_embeddings 
USING hnsw (embedding vector_l2_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_document_embeddings_vector_ip ON document_embeddings 
USING hnsw (embedding vector_ip_ops) WITH (m = 16, ef_construction = 64);

-- Create indexes for document_sources
CREATE INDEX idx_document_sources_type ON document_sources(source_type);
CREATE INDEX idx_document_sources_status ON document_sources(processing_status);
CREATE INDEX idx_document_sources_published_date ON document_sources(published_date);

-- Create indexes for user_queries
CREATE INDEX idx_user_queries_user_id ON user_queries(user_id);
CREATE INDEX idx_user_queries_type ON user_queries(query_type);
CREATE INDEX idx_user_queries_created_at ON user_queries(created_at);

-- Create indexes for query_embeddings
CREATE INDEX idx_query_embeddings_query_id ON query_embeddings(query_id);
CREATE INDEX idx_query_embeddings_vector_cosine ON query_embeddings 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Create triggers for updated_at
CREATE TRIGGER update_document_embeddings_updated_at BEFORE UPDATE ON document_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_sources_updated_at BEFORE UPDATE ON document_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding VECTOR(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    source_type VARCHAR(50),
    source_id UUID,
    content_chunk TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.id,
        de.source_type,
        de.source_id,
        de.content_chunk,
        1 - (de.embedding <=> query_embedding) AS similarity,
        de.metadata
    FROM document_embeddings de
    WHERE 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Create function for hybrid search (vector + text)
CREATE OR REPLACE FUNCTION hybrid_search_documents(
    query_embedding VECTOR(1536),
    query_text TEXT,
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    source_type VARCHAR(50),
    source_id UUID,
    content_chunk TEXT,
    similarity FLOAT,
    text_rank FLOAT,
    combined_score FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.id,
        de.source_type,
        de.source_id,
        de.content_chunk,
        1 - (de.embedding <=> query_embedding) AS similarity,
        ts_rank(to_tsvector('english', de.content_chunk), plainto_tsquery('english', query_text)) AS text_rank,
        (1 - (de.embedding <=> query_embedding)) * 0.7 + 
        ts_rank(to_tsvector('english', de.content_chunk), plainto_tsquery('english', query_text)) * 0.3 AS combined_score,
        de.metadata
    FROM document_embeddings de
    WHERE 1 - (de.embedding <=> query_embedding) > similarity_threshold
       OR to_tsvector('english', de.content_chunk) @@ plainto_tsquery('english', query_text)
    ORDER BY combined_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Create function to clean up old embeddings
CREATE OR REPLACE FUNCTION cleanup_old_embeddings(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM document_embeddings 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
