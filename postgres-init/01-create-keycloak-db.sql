-- Create dedicated database for Keycloak
CREATE DATABASE keycloak_db;

-- Create a dedicated user for Keycloak (optional but recommended for production)
-- The Keycloak service will use these credentials
DO
$do$
BEGIN
  IF NOT EXISTS (
    SELECT FROM pg_catalog.pg_roles
    WHERE rolname = 'keycloak') THEN
    CREATE ROLE keycloak LOGIN PASSWORD 'keycloak_password';
  END IF;
END
$do$;

-- Grant privileges on the keycloak_db to the keycloak user
GRANT ALL PRIVILEGES ON DATABASE keycloak_db TO keycloak;

-- Connect to keycloak_db and grant schema privileges
\c keycloak_db

GRANT ALL ON SCHEMA public TO keycloak;
