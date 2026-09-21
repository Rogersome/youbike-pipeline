{{ config(materialized='table') }}

select
    d.station_id,
    d.station_name,
    d.district,
    d.capacity,
    case when f.day_of_week in (0, 6) then 'weekend' else 'weekday' end as day_type,
    count(*)                                                              as hours_observed,
    round(avg(f.avg_fill_rate) * 100, 1)                                  as avg_fill_pct,
    round(sum(f.empty_minutes) / nullif(sum(f.observed_minutes), 0) * 100, 1) as empty_pct
from {{ ref('fct_station_hourly') }} f
join {{ ref('dim_station') }} d using (station_id)
join {{ ref('dim_fetch_hour') }} h using (hour_local)
where h.is_complete
  and f.observed_minutes >= 50
  and f.hour_of_day between 7 and 21
  and d.capacity >= 20
group by 1, 2, 3, 4, 5
having count(*) >= 10
