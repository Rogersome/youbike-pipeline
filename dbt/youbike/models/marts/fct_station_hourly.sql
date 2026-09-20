{{ config(materialized='table') }}

with bounded as (
    select
        station_id,
        capacity,
        bikes_available,
        docks_available,
        event_time,
        least(
            coalesce(next_event_time, event_time + interval '1 hour'),
            date_trunc('hour', event_time at time zone 'Asia/Taipei')
                at time zone 'Asia/Taipei' + interval '1 hour'
        ) as state_end
    from {{ ref('stg_station_events') }}
),

weighted as (
    select
        *,
        greatest(extract(epoch from (state_end - event_time)) / 60.0, 0) as duration_min
    from bounded
)

select
    station_id,
    date_trunc('hour', event_time at time zone 'Asia/Taipei')         as hour_local,
    extract(dow  from event_time at time zone 'Asia/Taipei')::int     as day_of_week,
    extract(hour from event_time at time zone 'Asia/Taipei')::int     as hour_of_day,
    count(*)                                                          as event_count,
    round(sum(duration_min), 1)                                       as observed_minutes,
    round(sum(bikes_available * duration_min) / nullif(sum(duration_min), 0), 2) as avg_bikes,
    min(bikes_available)                                              as min_bikes,
    max(bikes_available)                                              as max_bikes,
    round(
        sum((bikes_available::numeric / capacity) * duration_min)
        / nullif(sum(duration_min), 0), 4
    )                                                                 as avg_fill_rate,
    round(coalesce(sum(duration_min) filter (where bikes_available = 0), 0), 1) as empty_minutes,
    round(coalesce(sum(duration_min) filter (where docks_available = 0), 0), 1) as full_minutes
from weighted
group by 1, 2, 3, 4
