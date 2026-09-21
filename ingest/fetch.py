import json
import os
import time
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


def now() -> str:
    return f"{datetime.now(TPE):%Y-%m-%d %H:%M:%S}"


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TPE)


def fetch_with_retry(url: str, attempts: int = 4) -> list:
    delays = [10, 30, 60]
    for i in range(attempts):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if i == attempts - 1:
                raise
            wait = delays[i]
            print(f"{now()} retry {i + 1} in {wait}s: {type(e).__name__}")
            time.sleep(wait)


def main() -> None:
    stations = fetch_with_retry(URL)

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
                print(f"{now()} skip {s.get('sno')}: {e}")

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

    print(f"{now()} fetched={len(stations)} changed={len(rows)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{now()} FAILED {type(e).__name__}: {e}")
        raise SystemExit(1)
