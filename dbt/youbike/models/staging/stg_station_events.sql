{{ config(materialized='view') }}

with base as (
    select
        sno                                        as station_id,
        payload->>'sna'                            as station_name,
        payload->>'sarea'                          as district,
        payload->>'ar'                             as address,
        (payload->>'latitude')::numeric            as latitude,
        (payload->>'longitude')::numeric           as longitude,
        (payload->>'Quantity')::int                as capacity,
        (payload->>'available_rent_bikes')::int    as bikes_available,
        (payload->>'available_return_bikes')::int  as docks_available,
        (payload->>'act') = '1'                    as is_active,
        info_time                                  as event_time,
        fetched_at
    from raw.station_snapshot
    where (payload->>'Quantity')::int > 0
)

select
    *,
    lead(event_time) over (
        partition by station_id order by event_time
    ) as next_event_time
from base
