-- Runs once, when the postgres data directory is first created.
-- PostGIS is required by the data model (docs/03-architecture/data-model.md).
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid() for UUID primary keys

-- Sanity output in the container log so a broken image is obvious at first start.
DO $$
BEGIN
    RAISE NOTICE 'PostGIS version: %', postgis_full_version();
END
$$;
