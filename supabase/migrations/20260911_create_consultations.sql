create table if not exists public.okentrega_consultations (
  id bigint generated always as identity primary key,
  os_number text not null,
  found boolean not null,
  status text,
  booking text,
  container text,
  contractor text,
  depot text,
  has_xml boolean not null default false,
  queried_at timestamptz not null default now()
);

create unique index if not exists okentrega_consultations_os_number_idx
  on public.okentrega_consultations (os_number);

alter table public.okentrega_consultations enable row level security;
