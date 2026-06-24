-- Identity Service Seed Data
-- Living Atlas of Indonesian Mystery Culture

-- ============================================================
-- DEFAULT ROLES
-- ============================================================
INSERT INTO iam.roles (id, code, name, description) VALUES
    (gen_random_uuid(), 'super_admin', 'Super Admin', 'Full system access across all tenants'),
    (gen_random_uuid(), 'tenant_admin', 'Tenant Admin', 'Administrative access within a tenant'),
    (gen_random_uuid(), 'researcher', 'Researcher', 'Research and annotation access'),
    (gen_random_uuid(), 'creator', 'Creator', 'Content creation and publishing'),
    (gen_random_uuid(), 'viewer', 'Viewer', 'Read-only access to published content')
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- DEFAULT PERMISSIONS
-- ============================================================
-- User permissions
INSERT INTO iam.permissions (id, code, resource_type, action, description) VALUES
    (gen_random_uuid(), 'user.read', 'user', 'read', 'View user profiles'),
    (gen_random_uuid(), 'user.write', 'user', 'write', 'Create and update users'),
    (gen_random_uuid(), 'user.delete', 'user', 'delete', 'Delete users'),
    (gen_random_uuid(), 'user.admin', 'user', 'admin', 'Full user administration')
ON CONFLICT (code) DO NOTHING;

-- Tenant permissions
INSERT INTO iam.permissions (id, code, resource_type, action, description) VALUES
    (gen_random_uuid(), 'tenant.read', 'tenant', 'read', 'View tenant details'),
    (gen_random_uuid(), 'tenant.write', 'tenant', 'write', 'Update tenant settings'),
    (gen_random_uuid(), 'tenant.admin', 'tenant', 'admin', 'Full tenant administration'),
    (gen_random_uuid(), 'workspace.read', 'workspace', 'read', 'View workspaces'),
    (gen_random_uuid(), 'workspace.write', 'workspace', 'write', 'Create and update workspaces'),
    (gen_random_uuid(), 'workspace.delete', 'workspace', 'delete', 'Delete workspaces')
ON CONFLICT (code) DO NOTHING;

-- Content permissions
INSERT INTO iam.permissions (id, code, resource_type, action, description) VALUES
    (gen_random_uuid(), 'story.read', 'story', 'read', 'View stories'),
    (gen_random_uuid(), 'story.write', 'story', 'write', 'Create and update stories'),
    (gen_random_uuid(), 'story.publish', 'story', 'publish', 'Publish stories'),
    (gen_random_uuid(), 'story.delete', 'story', 'delete', 'Delete stories'),
    (gen_random_uuid(), 'article.read', 'article', 'read', 'View articles'),
    (gen_random_uuid(), 'article.write', 'article', 'write', 'Create and update articles'),
    (gen_random_uuid(), 'article.publish', 'article', 'publish', 'Publish articles'),
    (gen_random_uuid(), 'article.delete', 'article', 'delete', 'Delete articles')
ON CONFLICT (code) DO NOTHING;

-- Knowledge permissions
INSERT INTO iam.permissions (id, code, resource_type, action, description) VALUES
    (gen_random_uuid(), 'knowledge.read', 'knowledge', 'read', 'View knowledge objects'),
    (gen_random_uuid(), 'knowledge.write', 'knowledge', 'write', 'Create and update knowledge'),
    (gen_random_uuid(), 'knowledge.admin', 'knowledge', 'admin', 'Full knowledge administration'),
    (gen_random_uuid(), 'research.read', 'research', 'read', 'View research data'),
    (gen_random_uuid(), 'research.write', 'research', 'write', 'Create and update research'),
    (gen_random_uuid(), 'research.delete', 'research', 'delete', 'Delete research data')
ON CONFLICT (code) DO NOTHING;

-- Admin permissions
INSERT INTO iam.permissions (id, code, resource_type, action, description) VALUES
    (gen_random_uuid(), 'admin.access', 'admin', 'access', 'Access admin panel'),
    (gen_random_uuid(), 'admin.audit', 'admin', 'audit', 'View audit logs'),
    (gen_random_uuid(), 'admin.settings', 'admin', 'settings', 'Modify system settings'),
    (gen_random_uuid(), 'admin.roles', 'admin', 'roles', 'Manage roles and permissions')
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- ASSIGN PERMISSIONS TO ROLES
-- ============================================================
-- Super Admin: all permissions
INSERT INTO iam.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM iam.roles r, iam.permissions p
WHERE r.code = 'super_admin'
ON CONFLICT DO NOTHING;

-- Tenant Admin: tenant + workspace + user read + content + knowledge
INSERT INTO iam.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM iam.roles r, iam.permissions p
WHERE r.code = 'tenant_admin'
  AND p.code IN (
      'tenant.read', 'tenant.write', 'tenant.admin',
      'workspace.read', 'workspace.write', 'workspace.delete',
      'user.read',
      'story.read', 'story.write', 'story.publish', 'story.delete',
      'article.read', 'article.write', 'article.publish', 'article.delete',
      'knowledge.read', 'knowledge.write',
      'research.read',
      'admin.access', 'admin.audit'
  )
ON CONFLICT DO NOTHING;

-- Researcher: read + research write
INSERT INTO iam.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM iam.roles r, iam.permissions p
WHERE r.code = 'researcher'
  AND p.code IN (
      'story.read', 'article.read', 'knowledge.read',
      'research.read', 'research.write',
      'user.read'
  )
ON CONFLICT DO NOTHING;

-- Creator: content creation
INSERT INTO iam.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM iam.roles r, iam.permissions p
WHERE r.code = 'creator'
  AND p.code IN (
      'story.read', 'story.write',
      'article.read', 'article.write',
      'knowledge.read',
      'user.read'
  )
ON CONFLICT DO NOTHING;

-- Viewer: read-only
INSERT INTO iam.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM iam.roles r, iam.permissions p
WHERE r.code = 'viewer'
  AND p.code IN (
      'story.read', 'article.read', 'knowledge.read',
      'user.read'
  )
ON CONFLICT DO NOTHING;