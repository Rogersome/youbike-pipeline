import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg
import requests
from dotenv import load_dotenv

URL = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
TPE = ZoneInfo("Asia/Taipei")

load_dotenv()

DSN = (
    f"host=localhost port=5432 dbname={os.environ['POSTGRES_DB']} "
    f"user={os.environ['POSTGRES_USER']} password={os.environ['POSTGRES_PASSWORD']}"
)


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TPE)


def main() -> None:
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()
    stations = resp.json()

    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(
            """
            select distinct on (sno)
                   sno,
                   (payload->>'available_rent_bikes')::int,
                   (payload->>'available_return_bikes')::int
            from raw.station_snapshot
            order by sno, info_time desc
            """
        )
        latest = {sno: (rent, ret) for sno, rent, ret in cur.fetchall()}

        rows = []
        for s in stations:
            try:
                current = (
                    int(s["available_rent_bikes"]),
                    int(s["available_return_bikes"]),
                )
                if latest.get(s["sno"]) == current:
                    continue
                rows.append(
                    (
                        s["sno"],
                        parse_time(s["mday"]),
                        parse_time(s["srcUpdateTime"]),
                        json.dumps(s, ensure_ascii=False),
                    )
                )
            except (KeyError, ValueError) as e:
                print(f"skip {s.get('sno')}: {e}")

        if rows:
            cur.executemany(
                """
                insert into raw.station_snapshot
                    (sno, info_time, src_update_time, payload)
                values (%s, %s, %s, %s)
                on conflict (sno, info_time) do nothing
                """,
                rows,
            )

    print(f"fetched={len(stations)} changed={len(rows)}")

if __name__ == "__main__":
    main()
