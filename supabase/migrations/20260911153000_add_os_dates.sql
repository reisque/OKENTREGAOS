alter table public.okentrega_consultations
  add column if not exists integration_date timestamptz,
  add column if not exists cte_detected_at timestamptz;
