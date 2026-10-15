-- ============================================================================
-- TB Request Form — Supabase setup (one-time)
-- Project: arogya-sevak (Mumbai region) — same project as the ASHA app
--
-- HOW TO RUN:
--   1. Open https://supabase.com/dashboard -> project "arogya-sevak"
--      -> SQL Editor -> New query
--   2. Paste this entire file -> click "Run"
--   3. Done. Facilities can now Register / Login in the TB Request Form app.
--
-- SECURITY: Row Level Security makes sure every facility can ONLY see
-- and change its OWN rows. No facility can ever see another facility's data.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Facility profiles (one row per registered facility login)
-- ----------------------------------------------------------------------------
create table if not exists public.tb_facilities (
  user_id uuid primary key references auth.users(id) on delete cascade,
  facility_name text not null,
  facility_type text not null default '',
  created_at timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- 2. TB request forms (one row per saved form; id matches the app's record id)
-- ----------------------------------------------------------------------------
create table if not exists public.tb_request_forms (
  id text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  data jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_tb_forms_user
  on public.tb_request_forms(user_id);

-- ----------------------------------------------------------------------------
-- 3. Row Level Security — each facility sees ONLY its own data
-- ----------------------------------------------------------------------------
alter table public.tb_facilities enable row level security;
alter table public.tb_request_forms enable row level security;

drop policy if exists "facilities_own" on public.tb_facilities;
create policy "facilities_own"
  on public.tb_facilities for all
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "forms_own" on public.tb_request_forms;
create policy "forms_own"
  on public.tb_request_forms for all
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ----------------------------------------------------------------------------
-- 4. Explicit grants (Supabase stops auto-granting new tables in `public`
--    on 2026-10-30 — without these, fresh installs fail with 42501.
--    Re-running this file is safe.)
-- ----------------------------------------------------------------------------
grant select, insert, update, delete on public.tb_facilities to authenticated;
grant select, insert, update, delete on public.tb_request_forms to authenticated;
