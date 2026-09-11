alter table public.okentrega_consultations
  add column if not exists status text,
  add column if not exists booking text,
  add column if not exists container text,
  add column if not exists contractor text,
  add column if not exists depot text,
  add column if not exists has_xml boolean not null default false;

create unique index if not exists okentrega_consultations_os_number_idx
  on public.okentrega_consultations (os_number);
