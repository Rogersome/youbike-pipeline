{{ config(materialized='table') }}

select
    station_id,
    date_trunc('hour', event_time at time zone 'Asia/Taipei') as hour_local,
    extract(dow  from event_time at time zone 'Asia/Taipei')::int as day_of_week,
    extract(hour from event_time at time zone 'Asia/Taipei')::int as hour_of_day,
    count(*)                                                  as event_count,
    round(avg(bikes_available), 2)                            as avg_bikes,
    min(bikes_available)                                      as min_bikes,
    max(bikes_available)                                      as max_bikes,
    round(avg(bikes_available::numeric / capacity), 4)        as avg_fill_rate,
    count(*) filter (where bikes_available = 0)               as empty_events,
    count(*) filter (where docks_available = 0)               as full_events
from {{ ref('stg_station_events') }}
group by 1, 2, 3, 4
