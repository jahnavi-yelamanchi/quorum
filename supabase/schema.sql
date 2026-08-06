create table if not exists public.saved_places (
  id bigint generated always as identity primary key,
  user_id text not null,
  address text not null,
  latitude double precision,
  longitude double precision,
  radius_meters integer not null check (radius_meters between 100 and 5000),
  created_at timestamptz not null default now()
);

create table if not exists public.monitor_state (
  place_id bigint not null references public.saved_places(id) on delete cascade,
  item_id text not null,
  status text not null,
  primary key (place_id, item_id)
);

create table if not exists public.alerts (
  id bigint generated always as identity primary key,
  place_id bigint not null references public.saved_places(id) on delete cascade,
  item_id text not null,
  status text not null,
  created_at timestamptz not null default now(),
  unique (place_id, item_id, status)
);

create index if not exists saved_places_user_id_created_at_idx on public.saved_places (user_id, created_at desc);
create index if not exists alerts_place_id_id_idx on public.alerts (place_id, id desc);

alter table public.saved_places enable row level security;
alter table public.monitor_state enable row level security;
alter table public.alerts enable row level security;
