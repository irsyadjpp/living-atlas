-- Identity Service Indexes
-- Living Atlas of Indonesian Mystery Culture

-- ============================================================
-- TENANT INDEXES
-- ============================================================
CREATE INDEX idx_tenants_created_at ON tenant.tenants(created_at DESC);
CREATE INDEX idx_tenants_status ON tenant.tenants(status);
CREATE INDEX idx_tenants_metadata ON tenant.tenants USING GIN(metadata);
CREATE UNIQUE INDEX uq_workspace_slug ON tenant.workspaces(tenant_id, slug);

-- ============================================================
-- AUTH INDEXES
-- ============================================================
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_users_status ON auth.users(status);

-- ============================================================
-- GOVERNANCE INDEXES
-- ============================================================
CREATE INDEX idx_audit_actor ON governance.audit_logs(actor_id);
CREATE INDEX idx_audit_resource ON governance.audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created_at ON governance.audit_logs(created_at DESC);
CREATE INDEX idx_lineage_target ON governance.lineage(target_type, target_id);
CREATE INDEX idx_lineage_source ON governance.lineage(source_type, source_id);