delete from public.okentrega_consultations
where upper(regexp_replace(os_number, '\s', '', 'g')) not like '6SP%';
