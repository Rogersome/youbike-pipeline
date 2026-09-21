{{ config(materialized='table') }}

select
    d.district,
    case when f.day_of_week in (0, 6) then 'weekend' else 'weekday' end as day_type,
    count(distinct d.station_id)                                          as stations,
    count(*)                                                              as station_hours,
    round(avg(f.avg_fill_rate) * 100, 1)                                  as avg_fill_pct,
    round(sum(f.empty_minutes) / nullif(sum(f.observed_minutes), 0) * 100, 1) as empty_pct
from {{ ref('fct_station_hourly') }} f
join {{ ref('dim_station') }} d using (station_id)
join {{ ref('dim_fetch_hour') }} h using (hour_local)
where h.is_complete
  and f.observed_minutes >= 50
  and f.hour_of_day between 7 and 21
group by 1, 2
