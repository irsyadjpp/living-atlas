-- Identity Service Enums
-- Living Atlas of Indonesian Mystery Culture

CREATE TYPE tenant.tenant_type AS ENUM (
    'individual',
    'research',
    'publisher',
    'production_house',
    'university',
    'government'
);

CREATE TYPE tenant.tenant_status AS ENUM (
    'active',
    'suspended',
    'archived'
);

CREATE TYPE auth.user_status AS ENUM (
    'pending',
    'active',
    'blocked',
    'deleted'
);