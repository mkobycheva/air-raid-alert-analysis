"""Fetch the last month of alert history from alerts.in.ua and normalise it.

The history endpoint only supports `month_ago` and has a separate limit of
2 requests per minute, so a full run over all oblasts takes ~13 minutes.

Usage:
    export ALERTS_IN_UA_TOKEN=...      # secret: never commit it or paste it into chats/logs
    PYTHONPATH=src python -m airalerts.collect.alerts_in_ua --uids 27 8
    PYTHONPATH=src python -m airalerts.collect.alerts_in_ua

Outputs (in --out, default ./alerts_in_ua):
    raw/<uid>_<fetched_at>.json   raw API responses (keep out of git: .gitignore)
    alerts_month.csv              normalised table, one row per alert
"""
import argparse
import json
import os
import sys
import time
from typing import Any
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://api.alerts.in.ua/v1"
HISTORY_SLEEP_S = 31  # history limit: 2 requests / minute

# Oblast UIDs from the API documentation (Crimea 29 and Sevastopol 30 left out:
# no data in the other datasets either).
OBLAST_UIDS = {
    3: "Khmelnytska", 4: "Vinnytska", 5: "Rivnenska", 8: "Volynska",
    9: "Dnipropetrovska", 10: "Zhytomyrska", 11: "Zakarpatska", 12: "Zaporizka",
    13: "Ivano-Frankivska", 14: "Kyivska", 15: "Kirovohradska", 16: "Luhanska",
    17: "Mykolaivska", 18: "Odeska", 19: "Poltavska", 20: "Sumska",
    21: "Ternopilska", 22: "Kharkivska", 23: "Khersonska", 24: "Cherkaska",
    25: "Chernihivska", 26: "Chernivetska", 27: "Lvivska", 28: "Donetska",
    31: "Kyiv City",
}
OBLAST_UK = dict(zip(OBLAST_UIDS, [
    "Хмельницька область", "Вінницька область", "Рівненська область", "Волинська область",
    "Дніпропетровська область", "Житомирська область", "Закарпатська область", "Запорізька область",
    "Івано-Франківська область", "Київська область", "Кіровоградська область", "Луганська область",
    "Миколаївська область", "Одеська область", "Полтавська область", "Сумська область",
    "Тернопільська область", "Харківська область", "Херсонська область", "Черкаська область",
    "Чернігівська область", "Чернівецька область", "Львівська область", "Донецька область", "м. Київ",
]))
NORMALISED_COLUMNS = ["id", "queried_uid", "location_uid", "location_oblast_uid", "oblast",
                      "location_title_en", "location_type", "alert_type", "alert_level",
                      "threat_types", "started_at", "finished_at", "notes", "is_open", "fetched_at"]


def resolve_oblast(uid: Any, queried_uid: Any = None, title: Any = None) -> tuple[str, str]:
    """Resolve UID, validating against the supplied name when available.

    Local API snapshots put raion/hromada ids in location_oblast_uid. Fall back
    to their named oblast or corroborated queried UID, recording the method.
    Neither the raw field nor the raw CSV is rewritten.
    """
    def number(value: Any) -> int | None:
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    raw, queried = number(uid), number(queried_uid)
    names = {uk: key for key, uk in OBLAST_UK.items()}
    names.update({name + ("" if name == "Kyiv City" else " oblast"): key for key, name in OBLAST_UIDS.items()})
    names.update({"Київ": 31, "Київ місто": 31, "Автономна Республіка Крим": 29,
                  "Crimea": 29, "м. Севастополь": 30})
    named = names.get(str(title))
    if named in (29, 30) or raw in (29, 30) and named is None and queried in (None, raw):
        return ("Crimea" if (named or raw) == 29 else "Sevastopol"), "excluded_region"
    if raw in OBLAST_UIDS and (named is None or named == raw) and (queried not in OBLAST_UIDS or queried == raw or named == raw):
        chosen, method = raw, "location_oblast_uid"
    elif named in OBLAST_UIDS:
        chosen, method = named, "location_oblast_name_fallback"
        if queried in OBLAST_UIDS and queried != named:
            raise ValueError("API oblast name disagrees with queried oblast UID")
    elif queried in OBLAST_UIDS:
        chosen, method = queried, "queried_uid_fallback"
    else:
        raise ValueError("Unknown API oblast UID with no usable name or query UID")
    name = OBLAST_UIDS[chosen]
    return name + ("" if name == "Kyiv City" else " oblast"), method


def fetch_history(uid: int, token: str, period: str = "month_ago", retries: int = 3) -> Any:
    """GET /v1/regions/{uid}/alerts/{period}.json. The token goes in a header, not the URL."""
    url = f"{BASE}/regions/{uid}/alerts/{period}.json"
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(1, retries + 1):
        r = requests.get(url, headers=headers, timeout=60)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            try:
                pause = max(65, float(r.headers.get("Retry-After", "65")))
            except ValueError:
                pause = 65
            print(f"  uid={uid}: 429 (rate limit), sleeping {pause:g}s (attempt {attempt}/{retries})")
            time.sleep(pause)
            continue
        if r.status_code == 401:
            sys.exit("401: token missing, wrong, revoked or expired")
        if r.status_code == 403:
            sys.exit("403: IP blocked or API unavailable in your country (try without VPN or from another network)")
        r.raise_for_status()
    raise RuntimeError(f"uid={uid}: gave up after {retries} attempts")


def _alerts_list(payload: Any) -> list[dict[str, Any]]:
    """Accept {"alerts": [...]} or a bare list."""
    if isinstance(payload, dict):
        payload = payload.get("alerts") or []
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise ValueError("API alerts payload must be a list")
    return payload


def normalise(payloads: dict, fetched_at: datetime) -> pd.DataFrame:
    """payloads: {queried_uid: parsed JSON}. Returns one row per alert id."""
    rows = []
    for queried_uid, payload in payloads.items():
        for a in _alerts_list(payload):
            threats = a.get("threats") or []
            rows.append({
                "id": a.get("id"),
                "queried_uid": queried_uid,
                "location_uid": a.get("location_uid"),
                "location_oblast_uid": a.get("location_oblast_uid"),
                "oblast": a.get("location_oblast"),
                "location_title_en": a.get("location_title_en"),
                "location_type": a.get("location_type"),
                "alert_type": a.get("alert_type"),
                "alert_level": a.get("alert_level"),  # may be absent in history responses
                "threat_types": ",".join(sorted({t["threat_type"] for t in threats
                                                if isinstance(t, dict) and isinstance(t.get("threat_type"), str)
                                                and t["threat_type"]})),
                "started_at": a.get("started_at"),
                "finished_at": a.get("finished_at"),
                "notes": a.get("notes"),
            })
    df = pd.DataFrame(rows, columns=NORMALISED_COLUMNS[:-2])
    if not df.empty and df["id"].isna().any():
        raise ValueError("API alert is missing id; refusing unsafe deduplication")
    df["started_at"] = pd.to_datetime(df["started_at"], utc=True, format="ISO8601")
    df["finished_at"] = pd.to_datetime(df["finished_at"], utc=True, format="ISO8601")
    df["is_open"] = df["finished_at"].isna()
    df["fetched_at"] = pd.to_datetime(fetched_at, utc=True)
    if df.empty:
        return df[NORMALISED_COLUMNS]
    # finished_at == null means the alert is still active at fetch time (right-censored):
    # keep it NaT, flag it, and do NOT treat it as a completed interval.
    if df["started_at"].isna().any() or (df["finished_at"] < df["started_at"]).any():
        raise ValueError("Invalid API interval timestamps")
    df["id"] = df["id"].map(str)
    # the same alert can come back from several queried uids
    # Later queries can observe the same alert after it has closed.
    df = df.drop_duplicates(subset="id", keep="last").sort_values("started_at").reset_index(drop=True)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uids", nargs="*", type=int, default=list(OBLAST_UIDS))
    ap.add_argument("--out", default="alerts_in_ua")
    args = ap.parse_args()

    token = os.environ.get("ALERTS_IN_UA_TOKEN")
    if not token:
        sys.exit("Set ALERTS_IN_UA_TOKEN in the environment first")

    out = Path(args.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc)
    stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")

    payloads = {}
    for i, uid in enumerate(args.uids):
        print(f"[{i + 1}/{len(args.uids)}] uid={uid} {OBLAST_UIDS.get(uid, '')}")
        payloads[uid] = fetch_history(uid, token)
        (out / "raw" / f"{uid}_{stamp}.json").write_text(
            json.dumps(payloads[uid], ensure_ascii=False), encoding="utf-8")
        print(f"  alerts returned: {len(_alerts_list(payloads[uid]))}")
        if i < len(args.uids) - 1:
            time.sleep(HISTORY_SLEEP_S)

    # A full fetch takes minutes; use completion time, not the pre-request time.
    df = normalise(payloads, datetime.now(timezone.utc))
    df.to_csv(out / "alerts_month.csv", index=False)
    print(f"\nSaved {len(df)} alerts -> {out / 'alerts_month.csv'}")
    if not df.empty:
        print("\nlocation_type:\n", df.location_type.value_counts().to_string())
        print("\nalert_type:\n", df.alert_type.value_counts().to_string())
        print("\nalert_level:\n", df.alert_level.value_counts(dropna=False).to_string())
        print("\nstarted_at range:", df.started_at.min(), "->", df.started_at.max())


if __name__ == "__main__":
    main()
