-- WisdomTwin outbound voice: durable state for eligibility, suppression, concurrency, and webhook idempotency.
-- All tables: RLS on, no policies, no grants to anon/authenticated. Only the edge function (service role) touches them.

create table if not exists public.wt_voice_dial_decisions (
  id               bigint generated always as identity primary key,
  decided_at       timestamptz not null default now(),
  hubspot_contact_id text not null,
  to_number_sha256 text not null,              -- hash only; the number stays in HubSpot
  dial_mode        text not null,
  eligible         boolean not null,
  gate_ok          boolean not null,
  failures         jsonb not null,
  checked          jsonb not null,
  policy           jsonb not null,
  consent_snapshot jsonb not null,             -- the evidence fields as they were at decision time
  agent_id         text not null,
  agent_version_id text,
  conversation_id  text unique,                -- filled once the call is accepted
  call_sid         text
);

-- Decisions are immutable except for the one-time attachment of conversation_id / call_sid.
create or replace function public.wt_voice_decisions_guard() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then raise exception 'wt_voice_dial_decisions is append-only'; end if;
  if (old.conversation_id is not null or old.call_sid is not null)
     or new.id <> old.id or new.decided_at <> old.decided_at
     or new.hubspot_contact_id <> old.hubspot_contact_id or new.to_number_sha256 <> old.to_number_sha256
     or new.dial_mode <> old.dial_mode or new.eligible <> old.eligible or new.gate_ok <> old.gate_ok
     or new.failures <> old.failures or new.checked <> old.checked or new.policy <> old.policy
     or new.consent_snapshot <> old.consent_snapshot or new.agent_id <> old.agent_id
     or new.agent_version_id is distinct from old.agent_version_id then
    raise exception 'wt_voice_dial_decisions rows are immutable';
  end if;
  return new;
end $$;
drop trigger if exists wt_voice_decisions_guard on public.wt_voice_dial_decisions;
create trigger wt_voice_decisions_guard before update or delete on public.wt_voice_dial_decisions
  for each row execute function public.wt_voice_decisions_guard();

create table if not exists public.wt_voice_suppression (
  id               bigint generated always as identity primary key,
  created_at       timestamptz not null default now(),
  number_sha256    text,
  hubspot_contact_id text,
  source           text not null,              -- in_call | post_call | inbound_line | manual
  conversation_id  text,
  check (number_sha256 is not null or hubspot_contact_id is not null)
);
create index if not exists wt_voice_suppression_num on public.wt_voice_suppression (number_sha256);
create index if not exists wt_voice_suppression_contact on public.wt_voice_suppression (hubspot_contact_id);

-- Global one-call lock: a single row. Survives restarts, retries and concurrent invocations.
create table if not exists public.wt_voice_dial_lock (
  id          int primary key check (id = 1),
  acquired_at timestamptz not null default now(),
  decision_id bigint references public.wt_voice_dial_decisions(id),
  conversation_id text
);

-- Webhook idempotency / replay protection.
create table if not exists public.wt_voice_webhook_events (
  event_key   text primary key,
  received_at timestamptz not null default now(),
  event_type  text not null,
  conversation_id text
);

create table if not exists public.wt_voice_ledger (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  event       text not null,
  hubspot_contact_id text,
  conversation_id text,
  call_sid    text,
  outcome     text,
  opted_out   boolean,
  detail      jsonb
);

alter table public.wt_voice_dial_decisions enable row level security;
alter table public.wt_voice_suppression    enable row level security;
alter table public.wt_voice_dial_lock      enable row level security;
alter table public.wt_voice_webhook_events enable row level security;
alter table public.wt_voice_ledger         enable row level security;
revoke all on public.wt_voice_dial_decisions, public.wt_voice_suppression, public.wt_voice_dial_lock,
              public.wt_voice_webhook_events, public.wt_voice_ledger from anon, authenticated;

-- Atomic lock acquire: clears a stale lock (no webhook after 10 minutes), then tries to take it.
create or replace function public.wt_voice_try_lock(p_decision_id bigint) returns boolean
language plpgsql security definer set search_path = public as $$
begin
  delete from wt_voice_dial_lock where acquired_at < now() - interval '10 minutes';
  insert into wt_voice_dial_lock (id, decision_id) values (1, p_decision_id);
  return true;
exception when unique_violation then
  return false;
end $$;
revoke all on function public.wt_voice_try_lock(bigint) from public, anon, authenticated;
grant execute on function public.wt_voice_try_lock(bigint) to service_role;

-- Single-use test grants. Test mode dials only if it can atomically consume one unused, unexpired grant
-- for the exact destination number. One grant = one call attempt, ever. Grants are created by an operator
-- in the SQL editor, e.g.:
-- insert into wt_voice_test_grants (number_sha256, expires_at, authorized_by, note)
-- values (encode(sha256('+14162205314'::bytea), 'hex'), now() + interval '1 hour', 'Roman', 'first owner test');
create table if not exists public.wt_voice_test_grants (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  number_sha256 text not null,
  expires_at timestamptz not null,
  authorized_by text not null,
  note text,
  used_at timestamptz,
  used_decision_id bigint references public.wt_voice_dial_decisions(id)
);
alter table public.wt_voice_test_grants enable row level security;
revoke all on public.wt_voice_test_grants from anon, authenticated;

create or replace function public.wt_voice_consume_test_grant(p_number_sha256 text, p_decision_id bigint) returns bigint
language plpgsql security definer set search_path = public as $$
declare g bigint;
begin
  update wt_voice_test_grants set used_at = now(), used_decision_id = p_decision_id
  where id = (select id from wt_voice_test_grants
    where number_sha256 = p_number_sha256 and used_at is null and expires_at > now()
    order by id limit 1 for update skip locked)
  returning id into g;
  return g; -- null when no grant was available
end $$;
revoke all on function public.wt_voice_consume_test_grant(text, bigint) from public, anon, authenticated;
grant execute on function public.wt_voice_consume_test_grant(text, bigint) to service_role;
