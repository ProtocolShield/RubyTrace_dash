-- OSINT Platform Database Initialization Script
-- This script sets up the initial database schema and user permissions

-- Create the osint_user if it doesn't exist
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'osint_user') THEN
      CREATE USER osint_user WITH PASSWORD 'secure_password_2024';
   END IF;
END
$$;

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE osint_db OWNER osint_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'osint_db')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE osint_db TO osint_user;

-- Connect to the database and set up permissions
\c osint_db;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO osint_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO osint_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO osint_user;

-- Allow user to create databases (for testing)
ALTER USER osint_user CREATEDB;

-- Create indexes for better performance (these will be created by SQLAlchemy models)
-- but we can add some basic ones here if needed

-- Create a health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TEXT AS $$
BEGIN
    RETURN 'Database is healthy - ' || now()::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION health_check() TO osint_user;

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'OSINT Database initialized successfully at %', now();
END
$$;
