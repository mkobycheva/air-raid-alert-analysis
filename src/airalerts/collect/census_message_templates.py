"""Read-only template census; run locally from the project root.

PYTHONPATH=src python -m airalerts.collect.census_message_templates \
    --from-date 2026-09-07 --to-date 2026-10-11 [--limit 1000]

Dates are inclusive UTC calendar dates. Credentials are read only from API_ID,
API_HASH, API_SESSION_STRING or the top-up aliases TG_API_ID, TG_API_HASH,
TG_SESSION; UPSTREAM_DIR supplies the unchanged parser.
Only the report CSV is written; no parser state or Telegram session is saved.
"""

import argparse
import asyncio
from datetime import date, datetime, time, timedelta, timezone
import logging
import os
from pathlib import Path
import re
import sys
from typing import Any, AsyncIterator, Iterable

import pandas as pd

from airalerts.collect.topup_official import (
    TopupError, flood_retry, import_upstream, make_processor,
)

CHANNEL = "air_alert_ua"
COLUMNS = ["template", "upstream_class", "level", "count", "first_seen", "last_seen",
           "example_1", "example_2", "example_3"]
ENV_NAMES = [("API_ID", "TG_API_ID"), ("API_HASH", "TG_API_HASH"),
             ("API_SESSION_STRING", "TG_SESSION")]


def report_path(from_date: date, to_date: date) -> Path:
    return Path("reports") / f"census_message_templates_{from_date}_{to_date}.csv"


def write_report(path: Path, frame: pd.DataFrame, overwrite: bool = False) -> None:
    """Exclusive creation also prevents races between simultaneous censuses."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w" if overwrite else "x", encoding="utf-8", newline="") as handle:
            frame.to_csv(handle, index=False)
    except FileExistsError:
        raise TopupError("Census report already exists; use --overwrite to replace it") from None


def template_first_line(text: str) -> str:
    """Normalize the first line only, preserving emojis and threat keywords."""
    line = text.split("\n")[0].strip()
    line = re.sub(r"(?<!\d)(?:[01]\d|2[0-3]):[0-5]\d(?!\d)", "{T}", line)
    line = re.sub(r"\s*•.*$", " {LOC}", line)
    # Parenthetical qualifiers stay visible, including 'тривога ще триває'.
    line = re.sub(r"(?<!\w)в\s+(?:м\.\s*)?[^()\n]+", "в {LOC} ", line, flags=re.IGNORECASE)
    line = re.sub(r"(?<!\w)в\s*$", "в {LOC}", line, flags=re.IGNORECASE)
    return " ".join(line.split())


def classify_message(processor: Any, message: Any) -> tuple[str, frozenset[str], str]:
    """Call upstream classification; use its loaded states for hashtag levels.

    Recognized messages use the upstream returned hashtags (including its
    aliases). On rejection, known literal last-line hashtags still contribute
    levels. Missing/unknown hashtags or several distinct levels yield mixed.
    Empty messages cannot be passed to the upstream string-based parser.
    """
    text = message.message or ""
    if text:
        ignored = processor.is_ignored_message(message)
        locations, activated, deactivated = processor.parse_message(message)
    else:
        ignored, locations, activated, deactivated = False, None, False, False
    upstream_class = ("ignored" if ignored else "activated" if activated else
                      "deactivated" if deactivated else "unparseable")
    hashtags = locations or re.findall(r"#[^\s#]+", text.split("\n")[-1].lower())
    mapping = processor.hash_states_by_name
    levels = frozenset(mapping[tag][3] for tag in hashtags if tag in mapping)
    unknown = any(tag not in mapping for tag in hashtags)
    level = next(iter(levels)) if len(levels) == 1 and not unknown else "mixed"
    return upstream_class, levels, level


def census(messages: Iterable[Any], processor: Any) -> pd.DataFrame:
    """Group templates, keeping three distinct raw first-line examples per row."""
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for message in messages:
        first_line = (message.message or "").split("\n")[0]
        upstream_class, _, level = classify_message(processor, message)
        key = (template_first_line(message.message or ""), upstream_class, level)
        timestamp = message.date.astimezone(timezone.utc).isoformat()
        if key not in groups:
            groups[key] = {"count": 0, "first_seen": timestamp, "last_seen": timestamp, "examples": []}
        group = groups[key]
        group["count"] += 1
        group["first_seen"] = min(group["first_seen"], timestamp)
        group["last_seen"] = max(group["last_seen"], timestamp)
        if first_line not in group["examples"] and len(group["examples"]) < 3:
            group["examples"].append(first_line)
    rows = []
    for (template, upstream_class, level), group in groups.items():
        examples = group["examples"] + [""] * (3 - len(group["examples"]))
        rows.append([template, upstream_class, level, group["count"], group["first_seen"],
                     group["last_seen"], *examples])
    return pd.DataFrame(rows, columns=COLUMNS).sort_values(
        ["count", "template", "upstream_class", "level"], ascending=[False, True, True, True],
    ).reset_index(drop=True)


async def iter_range(client: Any, start: datetime, end: datetime,
                     limit: int | None, flood_error: type[Exception]) -> AsyncIterator[Any]:
    """Read descending by id from exclusive end; stop below inclusive start.

    Resume FloodWait by offset_id, avoiding skips among equal-date messages.
    Limit counts messages in the requested range, including service messages.
    """
    cursor, emitted = 0, 0
    while True:
        try:
            async for message in client.iter_messages(
                CHANNEL, offset_date=end if not cursor else None, offset_id=cursor,
                reverse=False, limit=None, wait_time=1,
            ):
                if cursor and message.id >= cursor:
                    continue
                cursor = message.id
                timestamp = message.date.astimezone(timezone.utc)
                if timestamp < start:
                    return
                if timestamp >= end:
                    continue
                yield message
                emitted += 1
                if limit is not None and emitted >= limit:
                    return
            return
        except flood_error as error:
            await asyncio.sleep(max(1, int(error.seconds)))


def credential_values() -> tuple[str, ...]:
    """Prefer the requested API_* names, falling back to top-up aliases."""
    values = []
    for name, alias in ENV_NAMES:
        value = os.environ.get(name) or os.environ.get(alias)
        if not value:
            raise TopupError(f"Missing environment variable: {name} (or {alias})")
        values.append(value)
    return tuple(values)


def read_credentials() -> tuple[int, str, str]:
    values = credential_values()
    try:
        api_id = int(values[0])
    except ValueError:
        raise TopupError("API_ID must be a positive integer") from None
    if api_id <= 0:
        raise TopupError("API_ID must be a positive integer")
    return api_id, values[1], values[2]


def redact(text: str, secrets: tuple[str, ...]) -> str:
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text


async def run(args: argparse.Namespace, auth: tuple[int, str, str], root: Path) -> None:
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError
    from telethon.sessions import StringSession

    output = report_path(args.from_date, args.to_date)
    if output.exists() and not args.overwrite:
        raise TopupError("Census report already exists; use --overwrite to replace it")
    logging.disable(logging.CRITICAL)
    module = import_upstream(root)
    processor = make_processor(module, {"last_processed_id": 0, "active_alerts_by_location": {}})
    start = datetime.combine(args.from_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(args.to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    secrets = tuple(os.environ[name] for pair in ENV_NAMES for name in pair if os.environ.get(name))
    client = TelegramClient(StringSession(auth[2]), auth[0], auth[1], receive_updates=False,
                            flood_sleep_threshold=0, connection_retries=2, request_retries=3)
    try:
        await flood_retry(client.connect, FloodWaitError)
        if not await flood_retry(client.is_user_authorized, FloodWaitError):
            raise TopupError("API_SESSION_STRING is not authorized; no interactive login attempted")
        messages = [message async for message in iter_range(client, start, end, args.limit, FloodWaitError)]
    finally:
        await client.disconnect()
    result = census(messages, processor)
    # Redact cell strings before CSV serialization, keeping its quoting valid.
    for column in [column for column in COLUMNS if column != "count"]:
        result[column] = result[column].map(lambda value: redact(value, secrets) if isinstance(value, str) else value)
    write_report(output, result, args.overwrite)
    print(redact(result.head(40).to_string(index=False), secrets))
    print("Totals per (upstream_class, level):")
    totals = result.groupby(["upstream_class", "level"], dropna=False)["count"].sum()
    print(redact(totals.to_string(), secrets))
    print(f"Report written: {output}; messages counted: {len(messages)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", required=True, type=date.fromisoformat)
    parser.add_argument("--to-date", required=True, type=date.fromisoformat)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        if args.to_date < args.from_date:
            raise TopupError("--to-date must be on or after --from-date")
        if args.limit is not None and args.limit <= 0:
            raise TopupError("--limit must be positive")
        output = report_path(args.from_date, args.to_date)
        if output.exists() and not args.overwrite:
            raise TopupError("Census report already exists; use --overwrite to replace it")
        auth = read_credentials()
        upstream = os.environ.get("UPSTREAM_DIR")
        if not upstream:
            raise TopupError("Missing environment variable: UPSTREAM_DIR")
        root = Path(upstream).resolve()
        if output.resolve().is_relative_to(root):
            raise TopupError("Report output must not be inside UPSTREAM_DIR")
        asyncio.run(run(args, auth, root))
        return 0
    except TopupError as error:
        print(str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted; no credentials or exception details displayed", file=sys.stderr)
        return 130
    except Exception:
        print("Census failed; exception details suppressed to protect credentials. Check dependencies, upstream parser, network and session validity.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
