do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'user_profiles'
      and column_name = 'display_name'
  ) and not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'user_profiles'
      and column_name = 'full_name'
  ) then
    alter table public.user_profiles
      rename column display_name to full_name;
  end if;
end $$;

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'user_profiles'
      and column_name = 'tier'
  ) and not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'user_profiles'
      and column_name = 'role'
  ) then
    alter table public.user_profiles
      rename column tier to role;
  end if;
end $$;

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'user_profiles'
      and column_name = 'role'
  ) then
    alter table public.user_profiles
      alter column role type text using role::text,
      alter column role set default 'free';
  end if;
end $$;

alter table public.user_profiles
  alter column email drop not null;

alter table public.user_profiles
  alter column full_name set default '';

alter table public.user_profiles
  alter column full_name drop not null;

alter table public.user_profiles
  alter column created_at set default now();

alter table public.user_profiles
  drop column if exists is_active,
  drop column if exists updated_at;

drop trigger if exists trg_user_profiles_set_updated_at on public.user_profiles;

grant select on public.tier_limits to anon, authenticated;
grant select, insert, update on public.user_profiles to authenticated;
