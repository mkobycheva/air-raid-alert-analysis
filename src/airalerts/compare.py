"""Deterministic offline descriptive comparisons. No targets or model inputs."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from airalerts.grid import episodes, exact_share, time_grid
from airalerts.plot_comparison import plot_reports
from airalerts.io import load_alerts_in_ua, load_official, load_volunteer, official_variant, trim_tail, valid_end

EXCLUDED = {"Luhanska oblast", "Crimea", "Sevastopol"}
# User-supplied external reference, not fetched by this offline program:
# https://www.slovoidilo.ua/2026/03/24/infografika/suspilstvo/yakyx-oblastyax-prolunalo-najbilshe-najmenshe-povitryanyx-tryvoh-pochatku-roku
REFERENCE_HOURS = {"Dnipropetrovska oblast": 1780, "Kyiv City": 122, "Kyivska oblast": 375,
                   "Poltavska oblast": 532, "Kirovohradska oblast": 302}
FACT3 = {
    "2026": {"Dnipropetrovska oblast": (.999, .905, .952), "Donetska oblast": (.962, .913, .744),
             "Kharkivska oblast": (.882, .881, .862), "Zaporizka oblast": (.833, .832, .782),
             "Odeska oblast": (.208, .208, .208), "Kyiv City": (.066, .066, .066),
             "Lvivska oblast": (.011, .011, .011)},
    "2024": {"Dnipropetrovska oblast": (.911, .220, .856), "Donetska oblast": (.612, .452, .608),
             "Kharkivska oblast": (.748, .451, .431)},
}


def utc(value: str | pd.Timestamp) -> pd.Timestamp:
    value = pd.Timestamp(value)
    return value.tz_localize("UTC") if value.tzinfo is None else value.tz_convert("UTC")


def closed(df: pd.DataFrame) -> pd.DataFrame:
    mask = df.finished_at.notna() & df.finished_at.gt(df.started_at)
    if "is_open" in df:
        mask &= ~df.is_open
    return df.loc[mask].copy()


def window_rows(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    rows = closed(df)
    return rows.loc[rows.started_at.lt(end) & rows.finished_at.gt(start)].copy()


def without_exclusions(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[~df.oblast.isin(EXCLUDED)].copy()


@dataclass
class Source:
    name: str
    full: pd.DataFrame
    end: pd.Timestamp
    rows: pd.DataFrame

    @classmethod
    def prepare(cls, name: str, full: pd.DataFrame) -> "Source":
        return cls(name, full, valid_end(full), closed(without_exclusions(trim_tail(full))))


def daily_presence(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp,
                   oblasts: list[str]) -> pd.DataFrame:
    """Touch of Europe/Kyiv calendar days, including partial boundary days.

    Midnight boundaries follow Kyiv DST (23/25-hour days), never fixed UTC days.
    """
    first = start.tz_convert("Europe/Kyiv").floor("D")
    last = end.tz_convert("Europe/Kyiv").ceil("D")
    index = pd.date_range(first, last, freq="D", inclusive="left")
    result = pd.DataFrame(False, index=index, columns=oblasts)
    for oblast, rows in window_rows(df, start, end).groupby("oblast"):
        if oblast not in result:
            continue
        left = index.searchsorted(rows.started_at.clip(lower=start), side="right") - 1
        right = index.searchsorted(rows.finished_at.clip(upper=end), side="left")
        changes = np.zeros(len(index) + 1, dtype=int)
        np.add.at(changes, left, 1)
        np.add.at(changes, right, -1)
        result[oblast] = np.cumsum(changes[:-1]) > 0
    return result


def source_metrics(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp,
                   oblasts: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid60 = time_grid(df, start, end).reindex(columns=oblasts, fill_value=False)
    grid30 = time_grid(df, start, end, "30min").reindex(columns=oblasts, fill_value=False)
    daily = daily_presence(df, start, end, oblasts)
    shares = exact_share(df, start, end).reindex(oblasts, fill_value=0)
    output = []
    for oblast in oblasts:
        merged = episodes(df, oblast, start, end)
        minutes = (merged.finished_at - merged.started_at).dt.total_seconds() / 60
        output.append({"oblast": oblast, "exact_share": shares[oblast],
                       "touch60_share": grid60[oblast].mean(), "touch30_share": grid30[oblast].mean(),
                       "kyiv_days_present": int(daily[oblast].sum()), "kyiv_days": len(daily),
                       "kyiv_daily_presence_share": daily[oblast].mean(), "episodes": len(merged),
                       "median_episode_minutes": minutes.median(), "total_hours": minutes.sum() / 60})
    return pd.DataFrame(output).set_index("oblast"), grid60


def pair_table(a: pd.DataFrame, b: pd.DataFrame, name_a: str, name_b: str,
               start: pd.Timestamp, end: pd.Timestamp, period: str,
               oblasts: list[str], cache: dict | None = None) -> pd.DataFrame:
    """Exact unions first; conditional touch probabilities are descriptive."""
    if end <= start or not oblasts:
        return pd.DataFrame()
    def metrics(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        key = (id(frame), start, end, tuple(oblasts))
        if cache is None:
            return source_metrics(frame, start, end, oblasts)
        if key not in cache:
            cache[key] = source_metrics(frame, start, end, oblasts)
        return cache[key]
    ma, ga = metrics(a)
    mb, gb = metrics(b)
    together = (ga & gb).sum()
    result = ma.add_prefix("a_").join(mb.add_prefix("b_"))
    result["p_a_given_b_60min"] = together / gb.sum().replace(0, np.nan)
    result["p_b_given_a_60min"] = together / ga.sum().replace(0, np.nan)
    result["source_a"], result["source_b"] = name_a, name_b
    result["period"], result["start_utc"], result["end_utc"] = period, start.isoformat(), end.isoformat()
    return result.reset_index()


def official_periods(end: pd.Timestamp, start: pd.Timestamp) -> list[tuple[str, pd.Timestamp, pd.Timestamp]]:
    bounds = [("full", start, end), ("2023", utc("2023-01-01"), utc("2024-01-01")),
              ("2024", utc("2024-01-01"), utc("2025-01-01")),
              ("2025-01..06", utc("2025-01-01"), utc("2025-07-01")),
              ("2025-12..2026-01", utc("2025-12-01"), utc("2026-02-01")),
              ("2026-02..valid_end", utc("2026-02-01"), end)]
    return [(label, max(a, start), min(b, end)) for label, a, b in bounds if min(b, end) > max(a, start)]


def month_windows(start: pd.Timestamp, end: pd.Timestamp) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    first = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    boundaries = pd.date_range(first, end, freq="MS")
    return [(max(a, start), min(a + pd.offsets.MonthBegin(), end)) for a in boundaries
            if min(a + pd.offsets.MonthBegin(), end) > max(a, start)]


def monthly_shares(sources: dict[str, pd.DataFrame], start: pd.Timestamp,
                   end: pd.Timestamp, oblasts: list[str]) -> pd.DataFrame:
    output = []
    for a, b in month_windows(start, end):
        shares = {name: exact_share(df, a, b).reindex(oblasts, fill_value=0) for name, df in sources.items()}
        for oblast in oblasts:
            row = {"oblast": oblast, "month": a.strftime("%Y-%m"), "start_utc": a.isoformat(), "end_utc": b.isoformat()}
            row.update({name: values[oblast] for name, values in shares.items()})
            row["B_minus_volunteer"] = row["official_B"] - row["volunteer"]
            output.append(row)
    return pd.DataFrame(output)


def variant_table(official: pd.DataFrame, end: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for label, start, stop in [("2024", utc("2024-01-01"), utc("2025-01-01")),
                               ("2026-02..valid_end", utc("2026-02-01"), end)]:
        stop = min(stop, end)
        if stop <= start:
            continue
        values = {v: exact_share(official_variant(official, v), start, stop) for v in "ABCD"}
        for oblast in sorted(official.oblast.unique()):
            rows.append({"period": label, "oblast": oblast, "start_utc": start.isoformat(), "end_utc": stop.isoformat(),
                         **{v: shares.get(oblast, 0.0) for v, shares in values.items()}})
    return pd.DataFrame(rows)


def fact3_regression(official: pd.DataFrame) -> pd.DataFrame:
    """Explicit untrimmed windows reproduce the supplied regression definition."""
    rows = []
    for period, start, end in [("2024", utc("2024-01-01"), utc("2025-01-01")),
                               ("2026", utc("2026-02-01"), utc("2026-09-07"))]:
        values = {v: exact_share(official_variant(official, v), start, end) for v in "ABCD"}
        for oblast, expected in FACT3[period].items():
            actual = {v: values[v].get(oblast, 0.0) for v in "ABCD"}
            rows.append({"period": period, "oblast": oblast, "start_utc": start.isoformat(), "end_utc": end.isoformat(),
                         **actual, **{f"expected_{v}": n for v, n in zip("ABC", expected)},
                         "discrepancy_gt002": any(abs(actual[v] - n) > .002 for v, n in zip("ABC", expected))})
    return pd.DataFrame(rows)


def hromada_drivers(official: pd.DataFrame, end: pd.Timestamp) -> pd.DataFrame:
    rows = official.loc[official.level.eq("hromada")].copy()
    keys = ["oblast", "raion", "hromada"]
    first = rows.groupby(keys, dropna=False).started_at.min()
    output = []
    for label, start, stop in [("2023-06..2024-01", utc("2023-06-01"), utc("2024-02-01")),
                               ("2024-02..2024-12", utc("2024-02-01"), utc("2025-01-01")),
                               ("2026-02..valid_end", utc("2026-02-01"), end)]:
        if min(stop, end) <= start:
            continue
        records = []
        for key, group in window_rows(rows, start, min(stop, end)).groupby(keys, dropna=False):
            merged = episodes(group, key[0], start, min(stop, end))
            hours = (merged.finished_at - merged.started_at).dt.total_seconds().sum() / 3600
            records.append(dict(zip(keys, key), row_count=len(group), union_hours=hours, first_appearance=str(first.loc[key])))
        frame = pd.DataFrame(records)
        if frame.empty:
            continue
        for ranking, metric in [("row_count", "row_count"), ("union_hours", "union_hours")]:
            top = frame.sort_values([metric, *keys], ascending=[False, True, True, True]).head(10)
            output.extend(top.assign(period=label, ranking=ranking, rank=range(1, len(top) + 1),
                                     start_utc=start.isoformat(), end_utc=min(stop, end).isoformat()).to_dict(orient="records"))
    return pd.DataFrame(output)


def long_tables(official: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rows = official.assign(duration_days=(official.finished_at - official.started_at).dt.total_seconds() / 86400)
    rows = rows.loc[rows.duration_days.gt(1)]
    counts = rows.groupby(["oblast", "level"]).size().rename("count").reset_index()
    locations = rows.fillna({"raion": "", "hromada": ""}).groupby(["oblast", "level", "raion", "hromada"])
    top = locations.agg(count=("duration_days", "size"), summed_interval_days=("duration_days", "sum")).reset_index()
    top = top.sort_values(["count", "oblast", "raion", "hromada"], ascending=[False, True, True, True]).head(20)
    return {"long_counts": counts, "long_top_locations": top,
            "longest_20": rows.sort_values(["duration_days", "started_at"], ascending=[False, True]).head(20)}


def template_group(template: str) -> str:
    text = template.casefold()
    if "повітряна тривога" in text or "відбій тривоги" in text:
        return "siren"
    if "артобстр" in text:
        return "artillery"
    if "бпла" in text or "дрон" in text:
        return "UAV"
    if "каб" in text:
        return "KAB"
    if "ракет" in text or "баліст" in text or "балист" in text:
        return "ballistic-missile"
    return "other"


def census_tables(paths: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = []
    for path in sorted(paths):
        frame = pd.read_csv(path)
        frame["file"] = path.name
        frame["template_group"] = frame.template.map(template_group)
        data.append(frame)
    if not data:
        return (pd.DataFrame(columns=["file", "upstream_class", "level", "template_group", "count"]),
                pd.DataFrame(columns=["file", "level", "activations", "siren_activations", "siren_share"]))
    combined = pd.concat(data, ignore_index=True)
    groups = combined.groupby(["file", "upstream_class", "level", "template_group"], as_index=False)["count"].sum()
    activated = combined.loc[combined.upstream_class.eq("activated")].copy()
    activated["siren_activations"] = activated["count"].where(activated.template_group.eq("siren"), 0)
    shares = activated.groupby(["file", "level"]).agg(activations=("count", "sum"), siren_activations=("siren_activations", "sum"))
    shares["siren_share"] = shares.siren_activations / shares.activations
    return groups, shares.reset_index()


def external_reference(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    start = pd.Timestamp("2026-01-01", tz="Europe/Kyiv").tz_convert("UTC")
    output = []
    for day in ("2026-03-24", "2026-03-25"):
        end = pd.Timestamp(day, tz="Europe/Kyiv").tz_convert("UTC")
        for source, df in sources.items():
            for oblast, reference in REFERENCE_HOURS.items():
                hours = exact_share(df, oblast, start, end) * (end - start).total_seconds() / 3600
                output.append({"source": source, "oblast": oblast, "start_utc": start.isoformat(), "end_utc": end.isoformat(),
                               "end_kyiv": end.tz_convert("Europe/Kyiv").isoformat(), "union_hours": hours,
                               "reference_hours": reference, "ratio_to_reference": hours / reference})
    return pd.DataFrame(output)


def intersection_hours(a: pd.DataFrame, b: pd.DataFrame, oblast: str,
                       start: pd.Timestamp, end: pd.Timestamp) -> float:
    aa, bb = episodes(a, oblast, start, end), episodes(b, oblast, start, end)
    left, right, seconds = 0, 0, 0.0
    while left < len(aa) and right < len(bb):
        a0, a1 = aa.iloc[left]
        b0, b1 = bb.iloc[right]
        seconds += max(0, (min(a1, b1) - max(a0, b0)).total_seconds())
        if a1 <= b1:
            left += 1
        else:
            right += 1
    return seconds / 3600


def overlap_flags(queries: pd.DataFrame, reference: pd.DataFrame, oblast: str,
                  start: pd.Timestamp, end: pd.Timestamp) -> np.ndarray:
    merged = episodes(reference, oblast, start, end)
    if merged.empty:
        return np.zeros(len(queries), dtype=bool)
    positions = pd.DatetimeIndex(merged.finished_at).searchsorted(queries.started_at.clip(lower=start), side="right")
    valid = positions < len(merged)
    positions = np.minimum(positions, len(merged) - 1)
    return valid & (pd.DatetimeIndex(merged.started_at).take(positions) < pd.DatetimeIndex(queries.finished_at.clip(upper=end)))


def api_overlap_tables(api: pd.DataFrame, volunteer: pd.DataFrame, start: pd.Timestamp,
                       end: pd.Timestamp, oblasts: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts, red_time = [], []
    for oblast in oblasts:
        volunteers = window_rows(volunteer.loc[volunteer.oblast.eq(oblast)], start, end)
        region = window_rows(api.loc[api.oblast.eq(oblast)], start, end)
        if oblast in {"Lvivska oblast", "Volynska oblast"}:
            for (level, threats), group in region.groupby(["alert_level", "threat_types"], dropna=False):
                number = int(overlap_flags(volunteers, group, oblast, start, end).sum())
                counts.append({"oblast": oblast, "api_alert_level": level or "none", "api_threat_types": threats or "none",
                               "volunteer_intervals": len(volunteers), "overlapping_volunteer_intervals": number,
                               "share": number / len(volunteers) if len(volunteers) else np.nan,
                               "start_utc": start.isoformat(), "end_utc": end.isoformat()})
        red = region.loc[region.alert_level.eq("red")]
        hours = exact_share(red, oblast, start, end) * (end - start).total_seconds() / 3600
        overlap = intersection_hours(red, volunteers, oblast, start, end)
        red_time.append({"oblast": oblast, "api_red_hours": hours, "red_hours_covered_by_volunteer": overlap,
                         "share_api_red_time_covered": overlap / hours if hours else np.nan,
                         "start_utc": start.isoformat(), "end_utc": end.isoformat()})
    return pd.DataFrame(counts), pd.DataFrame(red_time)


def api_counts(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for field in ("alert_type", "alert_level", "location_type", "oblast", "oblast_resolution"):
        for value, count in frame[field].fillna("none").replace("", "none").value_counts().sort_index().items():
            rows.append({"field": field, "value": value, "count": count})
    return pd.DataFrame(rows)


def write_tables(tables: dict[str, pd.DataFrame], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False, float_format="%.12g")


def markdown_table(frame: pd.DataFrame) -> str:
    """Render without an extra tabulate dependency."""
    if frame.empty:
        return "No rows."
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        cells = [f"{value:.6f}" if isinstance(value, float) else str(value) for value in row]
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    return "\n".join(lines)


def write_summary(tables: dict[str, pd.DataFrame], notes: list[str], out: Path) -> None:
    paragraphs = ["# Source comparison — descriptive only", *notes,
                  "All windows are half-open [start, end), in UTC unless marked Europe/Kyiv. "
                  "Exact shares use union time with second/subsecond precision. Sources are never merged or averaged. "
                  "All counts, conditional grid probabilities, differences, episode lengths and reference ratios are descriptive; "
                  "no targets, splits, features, models or forecast evaluation are created.",
                  "Tail rule: max(started_at) − 48 h per original source, bounded by max(fetched_at) for API. "
                  "Compute before definition/region/naive filters; clip intervals at each pair's earlier valid end. "
                  "Open API alerts are counted separately and excluded from every interval metric. "
                  "Touch shares weight bins equally, including a partial final bin. Daily presence uses Kyiv calendar boundaries "
                  "(time-grid bins are anchored at each pair's start) "
                  "with DST and includes partial boundary days. Episodes merge strict overlaps; abutting intervals remain separate. "
                  "An empty conditional denominator is blank/NaN, not zero.",
                  "Pair A/B labels in conditional columns refer to source_a/source_b, not official definition variants. "
                  "The API pairs use A=API-ALL or API-RED and B=volunteer. "
                  "API-level/threat overlap categories are non-exclusive: one volunteer interval can appear in several categories."]
    pairs = pd.concat([tables.get("official_volunteer", pd.DataFrame()), tables.get("api_volunteer", pd.DataFrame())], ignore_index=True)
    if not pairs.empty:
        columns = ["source_a", "source_b", "period", "start_utc", "end_utc"]
        paragraphs += ["## Explicit pairs and windows", markdown_table(pairs[columns].drop_duplicates())]
    paragraphs += ["## Excluded regions", markdown_table(tables["excluded_regions"]),
                   "## Input inventory and cheaply checked facts", markdown_table(tables["inventory"]),
                   "## Fact 3 regression (explicit untrimmed reference windows)", markdown_table(tables["fact3_regression"]),
                   "## External reference (user-supplied; not retrieved offline)",
                   "[Reference](https://www.slovoidilo.ua/2026/03/24/infografika/suspilstvo/yakyx-oblastyax-prolunalo-najbilshe-najmenshe-povitryanyx-tryvoh-pochatku-roku)",
                   markdown_table(tables["external_reference"]),
                   "## INDIRECT bridge — windows do not overlap", markdown_table(tables.get("indirect_bridge", pd.DataFrame())),
                   "## API snapshot and Fact 5 subset", markdown_table(tables.get("api_counts", pd.DataFrame())),
                   markdown_table(tables.get("api_fact5_regression", pd.DataFrame())),
                   "## API threat metadata", markdown_table(tables.get("api_threat_shares", pd.DataFrame())),
                   "## Open API alerts (not used in interval maths)", markdown_table(tables.get("api_open_counts", pd.DataFrame())),
                   "## CSV tables", "\n".join(f"- [{name}.csv]({name}.csv): {len(frame)} rows" for name, frame in tables.items())]
    (out / "source_comparison.md").write_text("\n\n".join(paragraphs) + "\n", encoding="utf-8")


def run_comparison(raw_dir: Path, api_path: Path, census_dir: Path, out: Path,
                   start: pd.Timestamp, end_cap: pd.Timestamp | None = None, plots: bool = True) -> dict[str, pd.DataFrame]:
    official = Source.prepare("official", load_official(raw_dir / "official_data_en.csv"))
    volunteer = Source.prepare("volunteer", load_volunteer(raw_dir / "volunteer_data_en.csv"))
    end = min(official.end, volunteer.end, end_cap or official.end)
    if end <= start:
        raise ValueError("Requested comparison start must precede the common trimmed end")
    oblasts = sorted(set(official.rows.oblast) & set(volunteer.rows.oblast))
    definitions = {"official_" + v: official_variant(official.rows, v) for v in "AB"}
    volunteers = {"volunteer": volunteer.rows, "volunteer_no_naive": volunteer.rows.loc[~volunteer.rows.naive]}
    notes = ["Existing components retained: official/volunteer loaders, UTC interval grid and exact unions, "
             "Telegram topup/census, API collector and their tests. "
             "The API collector is not run by this program.",
             "Official primary definition is B (oblast+raion); A and D are sensitivities. "
             "The official CSV has no alert-type field; variant B is a level-based definition, not a row-level siren label.",
             "Volunteer channel provenance is user-supplied UkraineAlarmSignal; the CSV has no channel field, so provenance "
             "cannot be independently verified from that file. Earlier documentation naming eTryvoga is superseded by this supplied fact."]
    notes.append("API collector review: Authorization: Bearer is retained, with 31-second request spacing and a 429 "
                 "Retry-After-aware backoff. Auth/header and endpoint limits were not tested against the live API. "
                 "Clear fixes are ISO8601 mixed-precision parsing, stable empty-output schema, null threat-type handling, "
                 "refusal of missing ids/invalid timestamps, latest-query duplicate-id resolution, and completion-time fetched_at. "
                 "Null finished_at remains open; missing alert_level is not inferred.")
    excluded = []
    inventory = []
    for source in (official, volunteer):
        inventory.append({"source": source.name, "rows": len(source.full), "min_started_at": str(source.full.started_at.min()),
                          "max_started_at": str(source.full.started_at.max()), "max_finished_at": str(source.full.finished_at.max()),
                          "valid_end": str(source.end), "oblasts": source.full.oblast.nunique(), "open_rows": 0})
        excluded.extend({"source": source.name, "oblast": name, "rows": count}
                        for name, count in source.full.loc[source.full.oblast.isin(EXCLUDED)].oblast.value_counts().items())
    if len(official.full) != 185430:
        notes.append(f"FACT discrepancy: official deduplicated row count is {len(official.full)}, expected 185430.")
    if official.full.finished_at.max().date().isoformat() != "2026-09-07":
        notes.append("FACT discrepancy: official does not end on 2026-09-07.")
    if volunteer.full.finished_at.max().date().isoformat() != "2026-10-10":
        notes.append("FACT discrepancy: volunteer does not end on 2026-10-10.")
    cache: dict = {}
    pair_frames = [pair_table(a, b, na, nb, low, high, label, oblasts, cache)
                   for label, low, high in official_periods(end, start)
                   for na, a in definitions.items() for nb, b in volunteers.items()]
    tables = {"official_volunteer": pd.concat(pair_frames, ignore_index=True),
              "monthly_exact_shares": monthly_shares({**definitions, **volunteers}, start, end, oblasts),
              "variants": variant_table(official.rows, min(official.end, end_cap or official.end)),
              "fact3_regression": fact3_regression(without_exclusions(official.full)),
              "hromada_drivers": hromada_drivers(official.rows, min(official.end, end_cap or official.end)),
              "external_reference": external_reference({**definitions, "volunteer": volunteer.rows}),
              **long_tables(official.rows)}
    if tables["fact3_regression"].discrepancy_gt002.any():
        notes.append("FACT discrepancy: Fact 3 differs by >.002 in rows flagged in fact3_regression.csv.")
    for source, lower, upper in [("official_B", 1762, 1784), ("official_A", 1968, 1992)]:
        values = tables["external_reference"].loc[(tables["external_reference"].source.eq(source)) &
                                                  tables["external_reference"].oblast.eq("Dnipropetrovska oblast"), "union_hours"]
        if ((values < lower - 1) | (values > upper + 1)).any():
            notes.append(f"FACT discrepancy: {source} Dnipropetrovska external-reference hours outside supplied range (±1 h rounding).")
    dated = sorted(census_dir.glob("census_message_templates_*.csv"))
    tables["census_groups"], tables["census_siren_shares"] = census_tables(dated)
    tables["legacy_census_groups"], tables["legacy_census_siren_shares"] = census_tables([])
    if not dated:
        notes.append("SKIPPED dated template aggregations: census_message_templates_*.csv is missing.")
    legacy = census_dir / "census_message_templates.csv"
    if legacy.exists():
        groups, shares = census_tables([legacy])
        messages = int(groups["count"].sum())
        notes.append(f"Existing undated census contains {messages} messages; it is inventoried separately, not relabelled or combined with dated censuses.")
        tables["legacy_census_groups"], tables["legacy_census_siren_shares"] = groups, shares
    notes.append("2026 census totals and the June 2026 break cannot be checked unless their date-ranged census files are present. "
                 "Telegram silence is supplied context; offline CSV endpoints cannot verify live channel silence.")
    # Write empty, labelled tables on skipped inputs, replacing any stale results
    # from a previous run into this output directory. Do not remove user files.
    optional_columns = {
        "api_counts": ["field", "value", "count"],
        "api_fact5_regression": ["metric", "actual", "expected_test_snapshot", "discrepancy"],
        "api_open_counts": ["oblast", "rows", "open_rows"],
        "api_threat_shares": ["alert_level", "rows", "nonempty_threat_rows", "nonempty_threat_share"],
        "api_alert_overlap": ["oblast", "api_alert_level", "api_threat_types", "volunteer_intervals",
                              "overlapping_volunteer_intervals", "share", "start_utc", "end_utc"],
        "api_red_time_coverage": ["oblast", "api_red_hours", "red_hours_covered_by_volunteer",
                                  "share_api_red_time_covered", "start_utc", "end_utc"],
        "indirect_bridge": ["label", "oblast", "official_start_utc", "official_end_utc", "api_start_utc",
                            "api_end_utc", "windows_do_not_overlap", "official_B", "volunteer_official_window",
                            "API_ALL", "API_RED", "volunteer_API_window"],
    }
    tables.update({name: pd.DataFrame(columns=columns) for name, columns in optional_columns.items()})
    tables["api_volunteer"] = tables["official_volunteer"].iloc[:0].copy()
    if api_path.exists():
        api_full = load_alerts_in_ua(api_path, air_raid_only=False)
        api = Source.prepare("alerts.in.ua", api_full)
        covered = sorted(set(without_exclusions(api_full).oblast))
        api_all = api.rows.loc[api.rows.alert_type.eq("air_raid")]
        api_red = api_all.loc[api_all.alert_level.eq("red")]
        names = sorted(set(covered) & set(volunteer.rows.oblast))
        # month_ago can contain long-lived alerts that started before the query
        # window. Their start does not extend archive coverage backwards.
        archive_start = (api_full.fetched_at.min() - pd.Timedelta(days=30)
                         if "fetched_at" in api_full and api_full.fetched_at.notna().any()
                         else api_full.started_at.min())
        low = max(archive_start, volunteer.full.started_at.min())
        high = min(api.end, volunteer.end, end_cap or api.end)
        notes.append(f"API file covers {len(covered)} non-excluded oblasts: {', '.join(covered)}. "
                     "Partial coverage is retained; absent oblasts are not treated as zero alerts. "
                     "The API archive is assumed to cover the 30 days preceding the earliest fetched_at timestamp; "
                     "long-lived alert starts do not extend this archive window backwards.")
        fallback = int(api_full.oblast_resolution.ne("location_oblast_uid").sum())
        if fallback:
            notes.append(f"FACT discrepancy in API UID schema: {fallback}/{len(api_full)} rows require an oblast name/query fallback; "
                         "location_oblast_uid does not identify their oblast. Resolution methods are in api_counts.csv.")
        if not api_full.location_type.eq("raion").all():
            notes.append("FACT discrepancy: the current API CSV also contains non-raion rows; API ALL/RED OR all its air_raid levels. See api_counts.csv.")
        inventory.append({"source": "alerts.in.ua", "rows": len(api_full), "min_started_at": str(api_full.started_at.min()),
                          "max_started_at": str(api_full.started_at.max()), "max_finished_at": str(api_full.finished_at.max()),
                          "valid_end": str(api.end), "oblasts": api_full.oblast.nunique(), "open_rows": int(api_full.is_open.sum()),
                          "min_fetched_at": str(api_full.fetched_at.min()), "max_fetched_at": str(api_full.fetched_at.max())})
        later_than_fetch = int(api_full.started_at.gt(api_full.fetched_at).sum())
        if later_than_fetch:
            notes.append(f"FACT discrepancy in API snapshot timestamp: {later_than_fetch} rows start after their fetched_at. "
                         "The existing collector recorded a pre-request timestamp; future runs now use fetch completion. "
                         "This comparison conservatively bounds the API end by the stored fetched_at as requested.")
        excluded.extend({"source": "alerts.in.ua", "oblast": name, "rows": count}
                        for name, count in api_full.loc[api_full.oblast.isin(EXCLUDED)].oblast.value_counts().items())
        tables["api_counts"] = api_counts(api_full)
        subset = api_full.loc[api_full.oblast.isin(["Lvivska oblast", "Volynska oblast"])]
        fact5 = [("Lvivska+Volynska rows", len(subset), 188),
                 ("raion rows", int(subset.location_type.eq("raion").sum()), 188),
                 ("air_raid rows", int(subset.alert_type.eq("air_raid").sum()), 188),
                 ("yellow rows", int(subset.alert_level.eq("yellow").sum()), 155),
                 ("red rows", int(subset.alert_level.eq("red").sum()), 33)]
        tables["api_fact5_regression"] = pd.DataFrame([
            {"metric": metric, "actual": actual, "expected_test_snapshot": expected,
             "discrepancy": actual != expected} for metric, actual, expected in fact5])
        if tables["api_fact5_regression"].discrepancy.any():
            notes.append("FACT discrepancy: current Lvivska+Volynska subset differs from the earlier 188-row test snapshot; see api_fact5_regression.csv.")
        threats = api_full.assign(nonempty_threats=api_full.threat_types.ne(""))
        tables["api_threat_shares"] = threats.groupby("alert_level", dropna=False).agg(
            rows=("id", "size"), nonempty_threat_rows=("nonempty_threats", "sum"),
            nonempty_threat_share=("nonempty_threats", "mean")).reset_index()
        tables["api_open_counts"] = api_full.groupby("oblast", as_index=False).agg(rows=("is_open", "size"), open_rows=("is_open", "sum"))
        if high > low and names:
            tables["api_volunteer"] = pd.concat([pair_table(a, b, na, nb, low, high, "API overlap", names, cache)
                                                 for na, a in {"API-ALL": api_all, "API-RED": api_red}.items()
                                                 for nb, b in volunteers.items()], ignore_index=True)
            tables["api_alert_overlap"], tables["api_red_time_coverage"] = api_overlap_tables(api_all, volunteer.rows, low, high, names)
            bridge = []
            earlier = utc("2026-08-01")
            earlier_end = min(official.end, volunteer.end, end_cap or official.end)
            for oblast in names:
                bridge.append({"label": "INDIRECT", "oblast": oblast, "official_start_utc": earlier.isoformat(),
                               "official_end_utc": earlier_end.isoformat(), "api_start_utc": low.isoformat(), "api_end_utc": high.isoformat(),
                               "windows_do_not_overlap": earlier_end <= low,
                               "official_B": exact_share(definitions["official_B"], oblast, earlier, earlier_end),
                               "volunteer_official_window": exact_share(volunteer.rows, oblast, earlier, earlier_end),
                               "API_ALL": exact_share(api_all, oblast, low, high), "API_RED": exact_share(api_red, oblast, low, high),
                               "volunteer_API_window": exact_share(volunteer.rows, oblast, low, high)})
            tables["indirect_bridge"] = pd.DataFrame(bridge)
            if not tables["indirect_bridge"].windows_do_not_overlap.all():
                notes.append("FACT discrepancy: some bridge windows overlap; INDIRECT label is a comparison of different windows, see boolean column.")
        else:
            notes.append("SKIPPED API comparison: no usable trimmed overlap or common covered oblasts.")
    else:
        notes.append(f"SKIPPED alerts.in.ua comparison: {api_path} is missing.")
    tables["inventory"] = pd.DataFrame(inventory)
    tables["excluded_regions"] = pd.DataFrame(excluded, columns=["source", "oblast", "rows"])
    notes.append("Configured exclusions: Luhanska oblast, Crimea and Sevastopol. Only actually present excluded regions appear below.")
    write_tables(tables, out)
    write_summary(tables, notes, out)
    if plots:
        plot_reports(out)
    for note in notes:
        print(note)
    print("Fact 3 regression:\n" + tables["fact3_regression"].to_string(index=False))
    print("External-reference union hours:\n" + tables["external_reference"].to_string(index=False))
    return tables
