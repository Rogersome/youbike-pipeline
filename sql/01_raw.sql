create schema if not exists raw;

create table if not exists raw.station_snapshot (
    sno              text        not null,
    info_time        timestamptz not null,
    src_update_time  timestamptz not null,
    fetched_at       timestamptz not null default now(),
    payload          jsonb       not null,
    primary key (sno, info_time)
);

create index if not exists idx_station_snapshot_fetched
    on raw.station_snapshot (fetched_at);
