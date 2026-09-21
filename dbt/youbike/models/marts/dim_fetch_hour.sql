{{ config(materialized='table') }}

select
    date_trunc('hour', fetched_at at time zone 'Asia/Taipei') as hour_local,
    count(distinct fetched_at)                                as runs,
    count(distinct fetched_at) >= 11                          as is_complete
from raw.station_snapshot
group by 1
