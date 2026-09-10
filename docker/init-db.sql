CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id VARCHAR(64) UNIQUE NOT NULL,
    data_hash VARCHAR(64) NOT NULL,
    source_platforms TEXT[] NOT NULL,
    query_context JSONB,
    record_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    insight_hash VARCHAR(64) NOT NULL,
    user_query TEXT NOT NULL,
    response_text TEXT NOT NULL,
    evidence JSONB,
    confidence_scores JSONB,
    model_version VARCHAR(64),
    analysis_version VARCHAR(64),
    blockchain_tx_id VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(128),
    title VARCHAR(256),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS provenance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_hash VARCHAR(64) NOT NULL,
    insight_hash VARCHAR(64) NOT NULL,
    evidence_hash VARCHAR(64) NOT NULL,
    model_version VARCHAR(64),
    analysis_version VARCHAR(64),
    blockchain_record JSONB,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_insights_dataset ON insights(dataset_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
