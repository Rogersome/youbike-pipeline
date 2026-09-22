import os

import matplotlib.pyplot as plt
import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()
plt.rcParams["font.family"] = "Noto Sans CJK TC"

DSN = (
    f"host=localhost port=5432 dbname={os.environ['POSTGRES_DB']} "
    f"user={os.environ['POSTGRES_USER']} password={os.environ['POSTGRES_PASSWORD']}"
)

SQL = """
select d.district,
       case when f.day_of_week in (0, 6) then 'weekend' else 'weekday' end as day_type,
       f.hour_of_day,
       sum(f.empty_minutes) / nullif(sum(f.observed_minutes), 0) * 100 as empty_pct,
       count(distinct f.hour_local) as n_hours
from mart.fct_station_hourly f
join mart.dim_station d using (station_id)
join mart.dim_fetch_hour h using (hour_local)
where h.is_complete
  and f.observed_minutes >= 50
group by 1, 2, 3
"""

with psycopg.connect(DSN) as conn:
    df = pd.read_sql(SQL, conn)

order = (
    df[df.day_type == "weekday"]
    .groupby("district")["empty_pct"].mean()
    .sort_values(ascending=False).index
)

fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
vmax = df["empty_pct"].quantile(0.98)

for ax, day_type, title in zip(axes, ["weekday", "weekend"], ["平日", "週末"]):
    pivot = (
        df[df.day_type == day_type]
        .assign(empty_pct=lambda d: d.empty_pct.where(d.n_hours >= 1))
        .pivot(index="district", columns="hour_of_day", values="empty_pct")
        .reindex(index=order, columns=range(6, 24))
    )
    im = ax.imshow(pivot.values, aspect="auto", cmap="Reds", vmin=0, vmax=vmax)
    ax.set_title(f"{title}：各行政區每小時空車時間比例 (%)", fontsize=13)
    ax.set_xticks(range(0, 18, 2))
    ax.set_xticklabels([f"{h:02d}" for h in range(6, 24, 2)])
    ax.set_xlabel("時段（台北時間）")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)

fig.colorbar(im, ax=axes, shrink=0.8, label="空車時間比例 (%)")
fig.savefig("docs/heatmap_district_hour.png", dpi=150, bbox_inches="tight")
print("saved docs/heatmap_district_hour.png")
