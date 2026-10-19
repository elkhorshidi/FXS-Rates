"""Data preparation and comparison for Helios FX obligation dashboard.

Rates: toman per USD. Declaration fee: percentage points (0.6 means 0.6%).
"""
from __future__ import annotations

from datetime import datetime, timedelta
import math
import re
import unicodedata
import pandas as pd

HEADERS = [
    "زمان استعلام (تهران)", "نوع مسیر", "نام منبع / بانک", "نرخ خام (تومان/دلار)",
    "کارمزد اظهار (%)", "نرخ مؤثر (تومان/دلار)", "مرجع استعلام", "توضیحات",
]
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
KINDS = ("بازار آزاد", "کوتاژ", "بانک")


def clean_string(value: object) -> str:
    if value is None:
        return ""
    value = unicodedata.normalize("NFKC", str(value)).translate(DIGITS)
    return " ".join(value.replace("ي", "ی").replace("ك", "ک").strip().split())


def as_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = float(value)
        return n if math.isfinite(n) else None
    s = clean_string(value).replace(",", "").replace("٬", "").replace("،", "").replace(" ", "")
    s = s.replace("٪", "").replace("%", "").replace("٫", ".")
    if s in ("", "—", "-", "nan", "None"):
        return None
    try:
        n = float(s)
    except ValueError:
        return None
    return n if math.isfinite(n) else None


def parse_timestamp(value: object) -> pd.Timestamp | None:
    # Sheets UNFORMATTED_VALUE returns a local date-time serial number.
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        if 20000 < float(value) < 100000:
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(float(value), unit="D")
        return None
    s = clean_string(value)
    if not s:
        return None
    try:
        # ISO year-first dates must not be interpreted as DD/MM/YYYY.
        year_first = bool(re.match(r"^\d{4}[-/]", s))
        ts = pd.to_datetime(s, dayfirst=not year_first, errors="coerce")
        if pd.isna(ts):
            return None
        if ts.tzinfo is not None:
            ts = ts.tz_convert("Asia/Tehran").tz_localize(None)
        return pd.Timestamp(ts)
    except (ValueError, TypeError, OverflowError):
        return None


def route_label(kind: str, source: str) -> str:
    source = clean_string(source)
    kind = clean_string(kind)
    if kind == "بانک":
        return source if source.startswith("بانک ") else "بانک " + source
    if kind == "کوتاژ":
        return "کوتاژ" if source in ("بازار", "کوتاژ", "کوتاژ صادراتی") else f"کوتاژ · {source}"
    return "بازار آزاد" if source in ("بازار", "آزاد", "بازار آزاد", "بازار آزاد تهران") else f"آزاد · {source}"


def parse_rates(values: list[list[object]]) -> tuple[pd.DataFrame, list[str]]:
    """Read A:H from Rates_Log; do not mutate source records."""
    cols = ["timestamp", "kind", "source", "raw_rate", "fee_pct", "effective_rate", "reference", "note", "sheet_row", "label"]
    errors: list[str] = []
    records = []
    for sheet_row, entry in enumerate(values[1:], start=2):
        cells = list(entry[:8]) + [None] * max(0, 8 - len(entry))
        if not any(clean_string(c) for c in cells):
            continue
        stamp, kind_raw, source_raw, rate_raw, fee_raw, _sheet_effective, ref, note = cells[:8]
        kind, source = clean_string(kind_raw), clean_string(source_raw)
        rate = as_number(rate_raw)
        fee = as_number(fee_raw)
        if kind not in KINDS or not source or rate is None or rate <= 0:
            errors.append(f"ردیف {sheet_row}: نوع مسیر، نام منبع یا نرخ خام نامعتبر است.")
            continue
        if kind == "بانک" and (fee is None or not (0 <= fee < 100)):
            errors.append(f"ردیف {sheet_row}: کارمزد بانک باید عددی از صفر تا کمتر از ۱۰۰ باشد.")
            continue
        # Fee is not applicable to free-market and qotaj rows.
        fee = fee if kind == "بانک" else 0.0
        ts = parse_timestamp(stamp)
        if ts is None:
            errors.append(f"ردیف {sheet_row}: تاریخ معتبر نیست؛ نرخ همچنان با ترتیب ثبت قابل نمایش است.")
        effective = rate * (1 - fee / 100)
        records.append({
            "timestamp": ts, "kind": kind, "source": source, "raw_rate": rate,
            "fee_pct": fee, "effective_rate": effective, "reference": clean_string(ref),
            "note": clean_string(note), "sheet_row": sheet_row, "label": route_label(kind, source),
        })
    return pd.DataFrame(records, columns=cols), errors


def latest_rates(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return data.copy()
    df = data.copy()
    # Prefer the most recent timestamp. Missing timestamps are sorted below dated entries.
    df["_sort_time"] = df["timestamp"].fillna(pd.Timestamp("1900-01-01"))
    df = df.sort_values(["_sort_time", "sheet_row"], kind="stable")
    df = df.drop_duplicates(["kind", "source"], keep="last")
    return df.drop(columns=["_sort_time"]).reset_index(drop=True)


def compare(latest: pd.DataFrame, reference_source: str, volume_usd: float) -> tuple[pd.DataFrame, float]:
    base = latest[(latest["kind"] == "بازار آزاد") & (latest["source"] == reference_source)]
    if base.empty:
        raise ValueError("نرخ مبنای بازار آزاد پیدا نشد.")
    market = float(base.iloc[0]["effective_rate"])
    if market <= 0:
        raise ValueError("نرخ بازار آزاد باید بزرگتر از صفر باشد.")
    result = latest[latest["kind"] != "بازار آزاد"].copy()
    result["gap_toman"] = market - result["effective_rate"]
    result["gap_pct"] = result["gap_toman"] / market * 100
    result["gap_total_toman"] = result["gap_toman"] * volume_usd
    result["gap_usd"] = result["gap_total_toman"] / market
    result = result.sort_values("effective_rate", ascending=False).reset_index(drop=True)
    return result, market


def fmt_toman(value: float) -> str:
    return f"{value:,.0f}"


def fmt_percent(value: float) -> str:
    return f"{value:,.2f}%"
