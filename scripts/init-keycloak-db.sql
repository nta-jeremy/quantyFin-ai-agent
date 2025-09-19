-- Keycloak database initialization script
-- This script ensures proper database setup for Keycloak

-- Set timezone to UTC
SET TIMEZONE = 'UTC';

-- Create extension if not exists (for UUID generation)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify database connection
SELECT current_database() as database_name, current_user as user_name, version() as postgres_version;

-- Set proper permissions for the keycloak user
-- This ensures the user has necessary permissions for Keycloak operations
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
GRANT ALL ON SCHEMA public TO keycloak;
GRANT ALL ON ALL TABLES IN SCHEMA public TO keycloak;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO keycloak;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO keycloak;

-- Set default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO keycloak;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO keycloak;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO keycloak;

-- Verify permissions
SELECT
    'Database permissions' as check_type,
    has_database_privilege('keycloak', 'keycloak', 'CREATE') as can_create,
    has_database_privilege('keycloak', 'keycloak', 'CONNECT') as can_connect,
    has_database_privilege('keycloak', 'keycloak', 'TEMPORARY') as can_temp
UNION ALL
SELECT
    'Schema permissions' as check_type,
    has_schema_privilege('keycloak', 'public', 'CREATE') as can_create,
    has_schema_privilege('keycloak', 'public', 'USAGE') as can_connect,
    NULL as can_temp
UNION ALL
SELECT
    'Role information' as check_type,
    use rolname as user_name,
    usecreaterole as can_create_role,
    usecreatedb as can_create_db,
    usesuper as is_superuser
FROM
    pg_user
WHERE
    usename = 'keycloak';

-- Create a test table to verify write permissions (will be dropped by Keycloak)
CREATE TABLE IF NOT EXISTS keycloak_connection_test (
    id SERIAL PRIMARY KEY,
    test_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    connection_status VARCHAR(50) DEFAULT 'successful'
);

-- Insert test record
INSERT INTO keycloak_connection_test (connection_status) VALUES ('database_ready')
ON CONFLICT (id) DO UPDATE SET test_timestamp = CURRENT_TIMESTAMP;

-- Verify the test record
SELECT * FROM keycloak_connection_test LIMIT 1;

-- Note: Keycloak will drop and recreate this table during initialization
-- This is just to verify database connectivity and permissions