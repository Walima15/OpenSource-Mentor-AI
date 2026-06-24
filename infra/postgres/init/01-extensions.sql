-- Extensions used by the application (for fully-local Postgres mode).
-- On Supabase these are already available.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Supabase exposes auth.users; for local dev we create a minimal stand-in
-- schema so foreign keys referencing user ids do not fail. The application
-- only ever references the user id (uuid), never the full auth schema.
CREATE SCHEMA IF NOT EXISTS auth;

CREATE TABLE IF NOT EXISTS auth.users (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    email text,
    created_at timestamptz NOT NULL DEFAULT now()
);
