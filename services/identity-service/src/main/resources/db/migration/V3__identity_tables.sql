-- Identity Service Tables
-- Living Atlas of Indonesian Mystery Culture

-- ============================================================
-- TENANT DOMAIN
-- ============================================================

CREATE TABLE tenant.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    tenant_type tenant.tenant_type NOT NULL,
    status tenant.tenant_status NOT NULL DEFAULT 'active',
    subscription_plan VARCHAR(100),
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    version BIGINT NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE tenant.workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    slug VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    workspace_type VARCHAR(100) NOT NULL,
    visibility VARCHAR(50) NOT NULL DEFAULT 'private',
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    version BIGINT NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_workspaces_tenant FOREIGN KEY (tenant_id) REFERENCES tenant.tenants(id)
);

-- ============================================================
-- AUTH DOMAIN
-- ============================================================

CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email CITEXT NOT NULL UNIQUE,
    username CITEXT NOT NULL UNIQUE,
    display_name VARCHAR(255),
    avatar_url TEXT,
    status auth.user_status NOT NULL DEFAULT 'pending',
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    password_hash TEXT NOT NULL,
    last_login_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    version BIGINT NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- ============================================================
-- IAM DOMAIN
-- ============================================================

CREATE TABLE iam.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE iam.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(255) NOT NULL UNIQUE,
    resource_type VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE iam.role_permissions (
    role_id UUID NOT NULL,
    permission_id UUID NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES iam.roles(id),
    CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES iam.permissions(id)
);

CREATE TABLE iam.user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    tenant_id UUID,
    workspace_id UUID,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_by UUID,
    PRIMARY KEY (user_id, role_id, tenant_id, workspace_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES auth.users(id),
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES iam.roles(id)
);

-- ============================================================
-- ABAC DOMAIN
-- ============================================================

CREATE TABLE iam.policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    effect VARCHAR(20) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE iam.policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL,
    rule_order INTEGER NOT NULL,
    rule_expression JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_policy_rules_policy FOREIGN KEY (policy_id) REFERENCES iam.policies(id)
);

-- ============================================================
-- GOVERNANCE DOMAIN
-- ============================================================

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

-- Create initial partition
CREATE TABLE governance.audit_logs_2026_07
PARTITION OF governance.audit_logs
FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE governance.audit_logs_2026_08
PARTITION OF governance.audit_logs
FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

CREATE TABLE governance.lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);