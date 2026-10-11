"""Top up official intervals using the installed upstream parser, unchanged.

Run from the project root with PYTHONPATH=src:
  python -m airalerts.collect.topup_official diagnose
  python -m airalerts.collect.topup_official collect

TG_API_ID, TG_API_HASH, TG_SESSION and UPSTREAM_DIR must come from the
environment. Diagnose writes nothing unless --summary reports/name.json is
supplied. Both modes diagnose before collection and enforce the hard stops.
The upstream active-alert pickle is copied into memory; its last-id sidecar is
read separately. Our checkpoint combines those two parts in a local pickle.
No upstream constructor, process(), write(), or dump method is called.
"""

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timedelta, timezone
import importlib
import json
import logging
import os
from pathlib import Path
import pickle
import sys
import tempfile
from types import ModuleType
from typing import Any, Awaitable, Callable

import pandas as pd

CHANNEL = "air_alert_ua"
BASELINE_ID = 338380
COLUMNS = ["oblast", "raion", "hromada", "level", "started_at", "finished_at", "source"]
STATE_PATH = Path("data/processed/official_state.pkl")
CSV_PATH = Path("data/processed/official_topup.csv")
RAW_PATH = Path("data/raw/official_data_en.csv")


class TopupError(Exception):
    """An error whose message is safe to display (no raw exception text)."""


def credentials() -> tuple[int, str, str]:
    """Read only required environment variables; never serialize credentials."""
    values = []
    for name in ("TG_API_ID", "TG_API_HASH", "TG_SESSION"):
        value = os.environ.get(name)
        if not value:
            raise TopupError(f"Missing environment variable: {name}")
        values.append(value)
    try:
        api_id = int(values[0])
    except ValueError:
        raise TopupError("TG_API_ID must be an integer") from None
    if api_id <= 0:
        raise TopupError("TG_API_ID must be positive")
    return api_id, values[1], values[2]


def import_upstream(root: Path) -> ModuleType:
    """Import the supplied clone without generating bytecode inside it."""
    root = root.resolve()
    if not (root / "processors/official_channel_processor.py").is_file():
        raise TopupError("UPSTREAM_DIR does not contain the official parser")
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    try:
        module = importlib.import_module("processors.official_channel_processor")
        if not Path(module.__file__).resolve().is_relative_to(root):
            raise TopupError("A different processors package is already imported")
        return module
    finally:
        sys.path.pop(0)
        sys.dont_write_bytecode = previous


def make_processor(module: ModuleType, state: dict[str, Any]) -> Any:
    """Isolate mutable upstream class state and reuse its own parsing methods."""
    processor = module.OfficialAirAlertProcessor.__new__(module.OfficialAirAlertProcessor)
    processor.client = None
    processor.hash_states_by_name = {}
    processor.active_alerts_by_location = pickle.loads(pickle.dumps(state["active_alerts_by_location"]))
    processor.completed_alerts = []
    processor.last_processed_id = int(state["last_processed_id"])
    processor.load_states()
    return processor


def load_state(module: ModuleType, state_path: Path = STATE_PATH) -> dict[str, Any]:
    """Load a local checkpoint or an in-memory copy of the upstream pickle."""
    if state_path.exists():
        state = pickle.loads(state_path.read_bytes())
        if state.get("format_version") != 1:
            raise TopupError("Unsupported local state format")
    else:
        active = pickle.loads(Path(module.pkl_file_path).read_bytes())
        last_id = int(Path(module.last_processed_id_path).read_text().strip())
        state = {"format_version": 1, "active_alerts_by_location": active,
                 "last_processed_id": last_id}
    if not isinstance(state["active_alerts_by_location"], dict) or int(state["last_processed_id"]) < 0:
        raise TopupError("Invalid parser checkpoint")
    return state


def ordered_messages(messages: list[Any], min_id: int) -> list[Any]:
    """Order by id, ignoring replayed ids and duplicate fetch results."""
    unique = {message.id: message for message in messages if message.id > min_id}
    return [unique[key] for key in sorted(unique)]


async def fetch_messages(client: Any, min_id: int, flood_error: type[Exception],
                         limit: int | None = None, max_id: int = 0) -> list[Any]:
    """Retry FloodWait from the last yielded id, pacing Telegram requests."""
    messages = []
    cursor = min_id
    while limit is None or len(messages) < limit:
        try:
            remaining = None if limit is None else limit - len(messages)
            async for message in client.iter_messages(
                CHANNEL, min_id=cursor, max_id=max_id, reverse=True,
                limit=remaining, wait_time=1,
            ):
                if message.id <= cursor:
                    continue
                messages.append(message)
                cursor = message.id
            break
        except flood_error as error:
            seconds = max(1, int(error.seconds))
            print(f"VERIFIED: FloodWait received; waiting {seconds} seconds")
            await asyncio.sleep(seconds)
    return ordered_messages(messages, min_id)


async def flood_retry(call: Callable[[], Awaitable[Any]], flood_error: type[Exception]) -> Any:
    """Retry individual read requests without logging their exception details."""
    while True:
        try:
            return await call()
        except flood_error as error:
            seconds = max(1, int(error.seconds))
            print(f"VERIFIED: FloodWait received; waiting {seconds} seconds")
            await asyncio.sleep(seconds)


def accepts(processor: Any, message: Any) -> bool:
    if not message.message:
        return False
    locations, activated, deactivated = processor.parse_message(message)
    return bool(locations and (activated or deactivated))


def diagnostic(processor: Any, messages: list[Any], first_five: list[Any],
               now: datetime) -> dict[str, Any]:
    """Describe fetched messages without advancing or persisting parser state."""
    messages = ordered_messages(messages, processor.last_processed_id)
    accepted = sum(accepts(processor, message) for message in messages)
    days = Counter(message.date.astimezone(timezone.utc).date() for message in messages)
    def sample(message: Any) -> dict[str, Any]:
        return {"id": message.id, "date": message.date.astimezone(timezone.utc).isoformat(),
                "text": (message.message or "")[:300]}
    first_day = now.astimezone(timezone.utc).date() - timedelta(days=59)
    return {
        "channel": CHANNEL, "as_of_utc": now.isoformat(), "min_id_exclusive": processor.last_processed_id,
        "new_messages": len(messages), "min_message_id": messages[0].id if messages else None,
        "max_message_id": messages[-1].id if messages else None,
        "first_message_date_utc": min(message.date for message in messages).isoformat() if messages else None,
        "last_message_date_utc": max(message.date for message in messages).isoformat() if messages else None,
        "accepted": accepted, "rejected": len(messages) - accepted,
        "new_messages_per_day_last_60_days": {
            (first_day + timedelta(days=i)).isoformat(): days[first_day + timedelta(days=i)] for i in range(60)
        },
        "rejected_samples": [sample(message) for message in messages if not accepts(processor, message)][:10],
        "first_five_after_338380": [sample(message) for message in first_five[:5]],
    }


def hard_stop(summary: dict[str, Any]) -> str | None:
    if summary["new_messages"] == 0:
        if summary["min_id_exclusive"] == BASELINE_ID:
            return "VERIFIED: No messages found after id 338380; channel is silent after that id. Collection stopped."
        return f"VERIFIED: No new messages after checkpoint id {summary['min_id_exclusive']}; collection stopped."
    if summary["rejected"] > summary["new_messages"] / 2:
        return ("VERIFIED: The upstream parser rejects most new messages; collection stopped. "
                "HYPOTHESIS: The public channel format or location vocabulary may have changed; review rejected samples.")
    return None


def process_messages(processor: Any, messages: list[Any]) -> list[dict[str, Any]]:
    """Use upstream transitions in id order; advance even for rejected messages."""
    processor.completed_alerts = []
    for message in ordered_messages(messages, processor.last_processed_id):
        if message.message:
            processor.process_message(message)
        processor.last_processed_id = message.id
    return [record.dict(lang="en") for record in processor.completed_alerts]


def canonical(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize serialization for dedupe without changing interval semantics."""
    frame = frame[COLUMNS].copy().fillna("")
    for column in ("started_at", "finished_at"):
        frame[column] = pd.to_datetime(frame[column], utc=True, format="ISO8601", errors="raise").map(str)
    return frame


def merge_new_rows(existing: pd.DataFrame, rows: list[dict[str, Any]],
                   history: pd.DataFrame) -> pd.DataFrame:
    """Retain topup only, removing exact raw matches and crash-replay rows."""
    candidate = canonical(pd.concat([existing, pd.DataFrame(rows, columns=COLUMNS)], ignore_index=True))
    candidate = candidate.drop_duplicates()
    raw_index = pd.MultiIndex.from_frame(canonical(history).drop_duplicates())
    candidate = candidate.loc[~pd.MultiIndex.from_frame(candidate).isin(raw_index)]
    return candidate.sort_values(["started_at", "finished_at", "oblast", "level"]).reset_index(drop=True)


def atomic_write(path: Path, content: bytes) -> None:
    """Replace one output atomically; clean up temporary files on failure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def save_collection(processor: Any, rows: list[dict[str, Any]], history: pd.DataFrame,
                    csv_path: Path = CSV_PATH, state_path: Path = STATE_PATH) -> pd.DataFrame:
    """CSV commits before state: an interrupted run replays and exact-dedupes.

    Never run two collectors concurrently. A checkpoint without its companion
    CSV is refused rather than silently losing previously collected intervals.
    """
    if state_path.exists() and not csv_path.exists():
        raise TopupError("Local state exists but official_topup.csv is missing")
    existing = pd.read_csv(csv_path) if csv_path.exists() else pd.DataFrame(columns=COLUMNS)
    result = merge_new_rows(existing, rows, history)
    atomic_write(csv_path, result.to_csv(index=False).encode())
    state = {"format_version": 1, "last_processed_id": processor.last_processed_id,
             "active_alerts_by_location": processor.active_alerts_by_location}
    atomic_write(state_path, pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL))
    return result


def collection_metrics(topup: pd.DataFrame, history: pd.DataFrame) -> dict[str, Any]:
    """Report untrimmed topup and a descriptive level-share comparison."""
    frame, raw = canonical(topup), canonical(history).drop_duplicates()
    for data in (frame, raw):
        for column in ("started_at", "finished_at"):
            data[column] = pd.to_datetime(data[column], utc=True, format="ISO8601")
    duration = (frame.finished_at - frame.started_at).dt.total_seconds()
    end = raw.finished_at.max()
    baseline = raw.loc[raw.started_at.ge(end - pd.DateOffset(months=2)) & raw.started_at.le(end)]
    levels = ["oblast", "raion", "hromada"]
    share = frame.level.value_counts(normalize=True).reindex(levels, fill_value=0)
    old_share = baseline.level.value_counts(normalize=True).reindex(levels, fill_value=0)
    duplicates = int(pd.MultiIndex.from_frame(canonical(topup)).isin(pd.MultiIndex.from_frame(canonical(history))).sum())
    longest = frame.assign(duration_days=duration / 86400).nlargest(5, "duration_days")
    longest = longest.astype({"started_at": str, "finished_at": str})
    return {
        "rows": len(frame), "started_at_min_utc": str(frame.started_at.min()) if len(frame) else None,
        "started_at_max_utc": str(frame.started_at.max()) if len(frame) else None,
        "finished_at_min_utc": str(frame.finished_at.min()) if len(frame) else None,
        "finished_at_max_utc": str(frame.finished_at.max()) if len(frame) else None,
        "level_share": share.to_dict(), "history_last_two_months_level_share": old_share.to_dict(),
        "history_comparison_start_utc": str(end - pd.DateOffset(months=2)),
        "history_comparison_end_utc": str(end), "duplicates_vs_raw": duplicates,
        "five_longest": longest.to_dict(orient="records"),
        "share_duration_3600s": float(duration.eq(3600).mean()) if len(frame) else None,
        "level_share_absolute_difference": (share - old_share).abs().to_dict(),
        "level_share_mismatch_gt10_percentage_points": bool(len(frame) and (share - old_share).abs().gt(.10).any()),
    }


def safe_json(value: Any, secrets: tuple[str, ...]) -> str:
    """Redact environment credential values before printing or optional JSON."""
    def redact(item: Any) -> Any:
        if isinstance(item, str):
            for secret in sorted(set(secrets), key=len, reverse=True):
                if secret:
                    item = item.replace(secret, "[REDACTED]")
            return item
        if isinstance(item, dict):
            return {redact(key): redact(val) for key, val in item.items()}
        if isinstance(item, list):
            return [redact(val) for val in item]
        if isinstance(item, int) and str(item) in secrets:
            return "[REDACTED]"
        return item
    return json.dumps(redact(value), ensure_ascii=False, indent=2, allow_nan=False)


async def run(args: argparse.Namespace, auth: tuple[int, str, str], root: Path) -> int:
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError
    from telethon.sessions import StringSession

    # Do not allow library exceptions or message logging to expose credentials.
    logging.disable(logging.CRITICAL)
    secrets = tuple(os.environ[name] for name in ("TG_API_ID", "TG_API_HASH", "TG_SESSION"))
    module = import_upstream(root)
    state = load_state(module)
    processor = make_processor(module, state)
    if STATE_PATH.exists() and not CSV_PATH.exists():
        raise TopupError("Local state exists but official_topup.csv is missing")
    client = TelegramClient(StringSession(auth[2]), auth[0], auth[1], receive_updates=False,
                            flood_sleep_threshold=0, connection_retries=2, request_retries=3)
    try:
        await flood_retry(client.connect, FloodWaitError)
        if not await flood_retry(client.is_user_authorized, FloodWaitError):
            raise TopupError("TG_SESSION is not authorized; no interactive login attempted")
        now = datetime.now(timezone.utc)
        latest = await flood_retry(lambda: client.get_messages(CHANNEL, limit=1), FloodWaitError)
        max_id = latest[0].id + 1 if latest else 0
        messages = await fetch_messages(client, processor.last_processed_id, FloodWaitError, max_id=max_id)
        first_five = messages[:5] if processor.last_processed_id == BASELINE_ID else await fetch_messages(
            client, BASELINE_ID, FloodWaitError, limit=5, max_id=max_id)
    finally:
        await client.disconnect()
    summary = diagnostic(processor, messages, first_five, now)
    print("VERIFIED: Telegram diagnostic (daily counts refer only to fetched new messages):")
    print(safe_json(summary, secrets))
    stop = hard_stop(summary)
    if stop:
        print(stop)
    if args.summary:
        atomic_write(args.summary, safe_json(summary, secrets).encode())
    if stop:
        return 2
    if args.mode == "diagnose":
        return 0
    history = pd.read_csv(RAW_PATH)
    rows = process_messages(processor, messages)
    topup = save_collection(processor, rows, history)
    metrics = collection_metrics(topup, history)
    print("VERIFIED: Collection metrics (no 48 h trim applied):")
    print(safe_json(metrics, secrets))
    if metrics["level_share_mismatch_gt10_percentage_points"]:
        print("VERIFIED: Level-share mismatch exceeds the descriptive 10 percentage point threshold. "
              "HYPOTHESIS: Recent geography, message format or censoring may contribute; no exclusion applied.")
    open_alerts = [{"location": key, "started_at": str(alert.started_at)}
                   for key, alert in sorted(processor.active_alerts_by_location.items())]
    print("VERIFIED: Still-open alerts:")
    print(safe_json(open_alerts, secrets))
    print(f"VERIFIED: Stored last message id: {processor.last_processed_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["diagnose", "collect"])
    parser.add_argument("--summary", type=Path, help="Optional diagnostic JSON under reports/")
    args = parser.parse_args()
    try:
        auth = credentials()
        upstream = os.environ.get("UPSTREAM_DIR")
        if not upstream:
            raise TopupError("Missing environment variable: UPSTREAM_DIR")
        root = Path(upstream).resolve()
        for path in (CSV_PATH, STATE_PATH, args.summary):
            if path is not None and path.resolve().is_relative_to(root):
                raise TopupError("Outputs must not be inside UPSTREAM_DIR")
        if args.summary and (args.summary.suffix != ".json" or not args.summary.resolve().is_relative_to(Path("reports").resolve())):
            raise TopupError("--summary must be a JSON path under reports/")
        return asyncio.run(run(args, auth, root))
    except TopupError as error:
        print(f"VERIFIED: {error}", file=sys.stderr)
        return 1
    except ModuleNotFoundError:
        print("VERIFIED: A required dependency or upstream parser module is unavailable; install requirements.txt and check UPSTREAM_DIR.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("VERIFIED: Interrupted; resume from the saved checkpoint.", file=sys.stderr)
        return 130
    except Exception:
        # Never display arbitrary exceptions/tracebacks containing auth material.
        print("VERIFIED: Collection failed; no exception details are displayed to protect credentials. Check network access, session validity, parser compatibility and input/output files.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
