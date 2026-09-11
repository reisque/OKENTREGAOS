alter table public.okentrega_consultations
  add column if not exists xml_notified_at timestamptz;

update public.okentrega_consultations
set xml_notified_at = cte_detected_at
where has_xml = true
  and xml_notified_at is null
  and cte_detected_at is not null;
