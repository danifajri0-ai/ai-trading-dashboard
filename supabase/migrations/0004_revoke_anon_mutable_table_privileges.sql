revoke all on table public.analysis_logs from anon;
revoke all on table public.watchlists from anon;
revoke all on table public.user_profiles from anon;
revoke all on table public.user_usage_events from anon;
revoke all on table public.tier_limits from anon;

grant select on public.tier_limits to anon;
