-- WisdomTwin role layer.
-- The referenced scaffold schema was not present in this repository, so these
-- role tables are the MVP definition. Keep the role tables intact in later edits.
-- judgment_seeds is reserved for a later phase and has no writer in this build.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY,
    subject TEXT NOT NULL DEFAULT 'local',
    domain TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (subject, domain)
);

CREATE TABLE IF NOT EXISTS persons (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations (id),
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations (id),
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, title)
);

CREATE TABLE IF NOT EXISTS tenures (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES roles (id),
    person_id UUID NOT NULL REFERENCES persons (id),
    started_on DATE NOT NULL,
    ended_on DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS judgment_seeds (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES roles (id),
    body TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS tenures_one_open_per_role
ON tenures (role_id) WHERE ended_on IS NULL;

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES roles (id),
    tenure_id UUID NOT NULL REFERENCES tenures (id),
    author_person_id UUID NOT NULL REFERENCES persons (id),
    service TEXT NOT NULL,
    uri TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    embedding vector(1536),
    source_uri TEXT NOT NULL DEFAULT '',
    source_hash TEXT NOT NULL DEFAULT '',
    chunk_index INTEGER NOT NULL DEFAULT 0,
    keyword_hashes JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (role_id, uri)
);

CREATE INDEX IF NOT EXISTS chunks_role_id_idx ON chunks (role_id);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY,
    tool_name TEXT NOT NULL,
    error_code TEXT,
    organization_id UUID,
    role_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES roles (id),
    service TEXT NOT NULL,
    query TEXT NOT NULL,
    max_items INTEGER NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL,
    chunks_ingested INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES roles (id),
    service TEXT NOT NULL,
    domain TEXT NOT NULL,
    role_title TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT 'local',
    connected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (role_id, service)
);

CREATE TABLE IF NOT EXISTS active_role (
    subject TEXT PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES roles (id)
);

CREATE TABLE IF NOT EXISTS oauth_transactions (
    id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    role_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS connector_credentials (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES roles (id),
    service TEXT NOT NULL,
    token_ciphertext TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (role_id, service)
);
