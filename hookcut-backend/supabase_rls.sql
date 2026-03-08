-- Run this in the Supabase SQL Editor:
-- https://supabase.com/dashboard/project/hetfjabbzxzhjyztlwoe/sql/new
--
-- Purpose: Enable Row Level Security (RLS) on all application tables and
-- restrict access to the service_role (used by the FastAPI backend).
-- Anonymous and authenticated Supabase roles are denied by default because
-- the backend is the sole data accessor — no direct client-to-Supabase queries.
--
-- Run once after the initial schema migration. Safe to re-run (IF NOT EXISTS guards).

-- ── Core application tables (001_initial_schema) ──────────────────────────────

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON users;
CREATE POLICY "service_only" ON users TO service_role USING (true) WITH CHECK (true);

ALTER TABLE credit_balances ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON credit_balances;
CREATE POLICY "service_only" ON credit_balances TO service_role USING (true) WITH CHECK (true);

ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON subscriptions;
CREATE POLICY "service_only" ON subscriptions TO service_role USING (true) WITH CHECK (true);

ALTER TABLE analysis_sessions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON analysis_sessions;
CREATE POLICY "service_only" ON analysis_sessions TO service_role USING (true) WITH CHECK (true);

ALTER TABLE hooks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON hooks;
CREATE POLICY "service_only" ON hooks TO service_role USING (true) WITH CHECK (true);

ALTER TABLE shorts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON shorts;
CREATE POLICY "service_only" ON shorts TO service_role USING (true) WITH CHECK (true);

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON transactions;
CREATE POLICY "service_only" ON transactions TO service_role USING (true) WITH CHECK (true);

ALTER TABLE learning_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON learning_logs;
CREATE POLICY "service_only" ON learning_logs TO service_role USING (true) WITH CHECK (true);

-- ── Admin tables (007_add_admin_tables) ───────────────────────────────────────

ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON admin_audit_logs;
CREATE POLICY "service_only" ON admin_audit_logs TO service_role USING (true) WITH CHECK (true);

ALTER TABLE prompt_rules ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON prompt_rules;
CREATE POLICY "service_only" ON prompt_rules TO service_role USING (true) WITH CHECK (true);

ALTER TABLE provider_configs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON provider_configs;
CREATE POLICY "service_only" ON provider_configs TO service_role USING (true) WITH CHECK (true);

ALTER TABLE narm_insights ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON narm_insights;
CREATE POLICY "service_only" ON narm_insights TO service_role USING (true) WITH CHECK (true);

-- ── Webhook idempotency table (009_add_processed_webhooks) ────────────────────

ALTER TABLE processed_webhooks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_only" ON processed_webhooks;
CREATE POLICY "service_only" ON processed_webhooks TO service_role USING (true) WITH CHECK (true);
