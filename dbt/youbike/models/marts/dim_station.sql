{{ config(materialized='table') }}

select distinct on (station_id)
    station_id,
    station_name,
    district,
    address,
    latitude,
    longitude,
    capacity,
    is_active,
    event_time as last_seen_at
from {{ ref('stg_station_events') }}
order by station_id, event_time desc
