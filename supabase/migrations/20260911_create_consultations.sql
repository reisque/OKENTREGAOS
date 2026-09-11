create table if not exists public.okentrega_consultations (
  id bigint generated always as identity primary key,
  os_number text not null,
  found boolean not null,
  queried_at timestamptz not null default now()
);

alter table public.okentrega_consultations enable row level security;
