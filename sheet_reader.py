"""Read a Google Sheet's published/viewer-accessible CSV, no Google Cloud or service account.

The app is READ-ONLY. An anonymous web app cannot access a private Sheet: the
owner must enable link viewing, or publish only Rates_Log as CSV and paste its URL.
"""
from __future__ import annotations

import csv
import io
import re
from urllib.parse import urlencode, urlparse

import requests

SPREADSHEET_ID = "1xckakJWtevb91dqlpbW504SbLg2irhhxlIRHIuTF3Ow"
RATES_GID = 982784865  # Rates_Log; observed in the actual user's Google Sheet
EXPECTED_COLUMN = "نوع مسیر"
MAX_DOWNLOAD_BYTES = 5_000_000


class SheetAccessError(RuntimeError):
    pass


def standard_urls(spreadsheet_id: str = SPREADSHEET_ID, gid: int = RATES_GID) -> list[str]:
    """Both methods work for Sheets shared as anyone-with-the-link / Viewer."""
    if not re.fullmatch(r"[a-zA-Z0-9_-]{10,150}", spreadsheet_id):
        raise ValueError("شناسه Google Sheets معتبر نیست.")
    base = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    return [
        f"{base}/export?{urlencode({'format': 'csv', 'gid': str(gid)})}",
        f"{base}/gviz/tq?{urlencode({'tqx': 'out:csv', 'sheet': 'Rates_Log'})}",
    ]


def validate_published_url(url: str) -> str:
    """Only accept public Google Sheets CSV endpoints to avoid arbitrary URL fetches."""
    url = url.strip()
    p = urlparse(url)
    if p.scheme != "https" or p.hostname != "docs.google.com":
        raise ValueError("آدرس CSV باید لینک HTTPS خود Google Sheets از docs.google.com باشد.")
    if not p.path.startswith("/spreadsheets/d/"):
        raise ValueError("لینک منتشرشده Google Sheets معتبر نیست.")
    return url


def parse_google_csv(raw: bytes) -> list[list[object]]:
    if len(raw) > MAX_DOWNLOAD_BYTES:
        raise SheetAccessError("حجم خروجی شیت بیش از ۵ مگابایت است.")
    # Google serves a login/consent page as HTTP 200 in some restricted cases.
    prefix = raw.lstrip()[:500].lower()
    if prefix.startswith((b"<!doctype html", b"<html", b"<script")) or b"<html" in prefix:
        raise SheetAccessError("به جای CSV، صفحه ورود Google دریافت شد؛ دسترسی ناشناس به شیت فعال نیست.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as err:
        raise SheetAccessError("فرمت خروجی UTF-8 CSV نیست.") from err
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 5 or EXPECTED_COLUMN not in rows[0][1].strip():
        raise SheetAccessError("فایل دریافتی تب Rates_Log نیست؛ سطر اول باید شامل ستون «نوع مسیر» باشد.")
    return rows


def download_public_sheet(spreadsheet_id: str = SPREADSHEET_ID, gid: int = RATES_GID, published_csv_url: str = "") -> tuple[list[list[object]], str]:
    """Return (rows, used_url); try both standard endpoints unless URL overridden."""
    urls = [validate_published_url(published_csv_url)] if published_csv_url.strip() else standard_urls(spreadsheet_id, gid)
    errors: list[str] = []
    for url in urls:
        try:
            response = requests.get(
                url, timeout=(5, 20), headers={"User-Agent": "Helios-FX-Dashboard/2.0"},
                allow_redirects=True,
            )
            if response.status_code in (401, 403):
                raise SheetAccessError("دسترسی Google Sheets عمومی نیست (HTTP 403/401).")
            response.raise_for_status()
            rows = parse_google_csv(response.content)
            return rows, url
        except (requests.RequestException, SheetAccessError) as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    raise SheetAccessError(
        "نرخ‌ها از Google Sheets دریافت نشدند. در شیت Share → General access → "
        "Anyone with the link → Viewer را فعال کن، یا فقط تب Rates_Log را "
        "از File → Share → Publish to web → CSV منتشر و لینکش را در داشبورد وارد کن. "
        "(با این کار داده‌های منتشرشده بدون ورود قابل خواندن خواهند بود.) "
        "جزئیات: " + " | ".join(errors)[:700]
    )
