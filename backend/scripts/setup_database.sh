#!/bin/bash

# Database setup script for AI Health Records Application
# This script creates the PostgreSQL database and user

set -e  # Exit on error

echo "Setting up PostgreSQL database for AI Health Records..."

# Default values
DB_NAME="health_records_dev"
DB_USER="healthapp"
DB_PASSWORD="password"
DB_HOST="localhost"
DB_PORT="5432"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL is not installed. Please install PostgreSQL first."
    echo "On macOS: brew install postgresql"
    echo "On Ubuntu: sudo apt-get install postgresql"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
    echo "Error: PostgreSQL is not running. Please start PostgreSQL first."
    echo "On macOS: brew services start postgresql"
    echo "On Ubuntu: sudo systemctl start postgresql"
    exit 1
fi

echo "PostgreSQL is running..."

# Create database and user
echo "Creating database and user..."

# Connect as superuser (postgres) to create database and user
psql -h $DB_HOST -p $DB_PORT -U postgres <<EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Enable required extensions in the database
\c $DB_NAME
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOF

echo "Database setup complete!"
echo ""
echo "Database connection details:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo "Connection string: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?schema=public"
echo ""
echo "Next steps:"
echo "1. Update .env file with the connection string if needed"
echo "2. Run 'prisma db push' to create the schema"
echo "3. Start the application with 'uvicorn main:app --reload'"