-- Fix Governance Audit Logs Table
-- Living Atlas of Indonesian Mystery Culture
-- Recreate governance.audit_logs table with partitions

-- Drop existing table if it exists (in case of partial creation)
DROP TABLE IF EXISTS governance.audit_logs CASCADE;

-- Create audit_logs table with partitioning
CREATE TABLE governance.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID,
    tenant_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Create initial partitions for current and next months
CREATE TABLE governance.audit_logs_2026_06
PARTITION OF governance.audit_logs
FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE governance.audit_logs_2026_07
PARTITION OF governance.audit_logs
FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE governance.audit_logs_2026_08
PARTITION OF governance.audit_logs
FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

-- Create indexes
CREATE INDEX idx_audit_actor ON governance.audit_logs(actor_id);
CREATE INDEX idx_audit_resource ON governance.audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created_at ON governance.audit_logs(created_at DESC);
