#!/usr/bin/env python3
"""
currency_report.py
==================
Trail Project – Scripting & Automation Task

Fetches today's and yesterday's USD exchange rates from the
Frankfurter (api.frankfurter.app) free public API, calculates
percentage change, flags significant moves (> 0.5 %), and
writes both a CSV report and a run log.

Usage
-----
    python currency_report.py

Scheduling
----------
Linux/Mac – add to crontab (runs every morning at 07:00):
    0 7 * * * /usr/bin/python3 /path/to/currency_report.py

Windows Task Scheduler – create a Basic Task:
    Program : python.exe
    Arguments: "C:\\path\\to\\currency_report.py"
    Trigger  : Daily at 07:00
"""

import csv
import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests                     # pip install requests


# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

# Currencies we care about (base is always USD)
# NOTE: AED is not supported by Frankfurter API (UAE Dirham is pegged,
#       not included in their dataset). It is tracked separately below.
TARGET_CURRENCIES = ["INR", "USD", "EUR", "GBP", "BRL", "MXN"]

# AED is always pegged to USD at a fixed rate — we add it manually
AED_FIXED_RATE = 3.6725      # 1 USD = 3.6725 AED (official peg, never changes)

# A move larger than this is flagged "Significant"
SIGNIFICANCE_THRESHOLD = 0.5       # percent

# Free API – no key required
BASE_URL = "https://api.frankfurter.app"

# Output paths (same directory as this script by default)
SCRIPT_DIR   = Path(__file__).parent
OUTPUT_DIR   = SCRIPT_DIR                  # change if needed
CSV_REPORT   = OUTPUT_DIR / "currency_report.csv"
LOG_FILE     = OUTPUT_DIR / "currency_report.log"


# ──────────────────────────────────────────────────────────────
# LOGGING SETUP
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt  = "%Y-%m-%d %H:%M:%S",
    handlers = [
        logging.FileHandler(LOG_FILE, encoding="utf-8"),   # → .log file
        logging.StreamHandler(sys.stdout),                 # → console
    ],
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def fetch_rates(rate_date: date, use_latest: bool = False) -> dict:
    """
    Fetch USD-based exchange rates for a specific date from
    the Frankfurter API.

    - use_latest=True  → hits /latest  (always works, fastest)
    - use_latest=False → hits /YYYY-MM-DD (for historical/yesterday)

    If the date falls on a weekend or holiday, Frankfurter
    automatically returns the most recent available rates.

    Returns a dict like {"INR": 83.45, "EUR": 0.92, ...}
    AED is added separately as a fixed peg (3.6725).

    Raises requests.HTTPError on any non-2xx response.
    """
    symbols = ",".join(c for c in TARGET_CURRENCIES if c != "USD")

    if use_latest:
        url = f"{BASE_URL}/latest?from=USD&to={symbols}"
    else:
        url = f"{BASE_URL}/{rate_date}?from=USD&to={symbols}"

    log.info("Fetching rates for %s → %s", rate_date, url)

    # Retry up to 3 times with a short wait (handles slow connections)
    for attempt in range(1, 4):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            break                               # success — exit retry loop
        except requests.exceptions.Timeout:
            log.warning("Attempt %d timed out, retrying...", attempt)
            if attempt == 3:
                raise
        except requests.exceptions.RequestException:
            raise

    data  = response.json()
    rates = data.get("rates", {})

    # USD/USD is always 1.0 — add explicitly
    rates["USD"] = 1.0

    # AED is pegged — add at fixed official rate
    rates["AED"] = AED_FIXED_RATE

    # Keep only our full target list (API may return extras)
    full_list = TARGET_CURRENCIES + ["AED"]
    filtered  = {c: rates[c] for c in full_list if c in rates}
    log.info("Rates received for: %s", list(filtered.keys()))
    return filtered


def pct_change(today_rate: float, yesterday_rate: float) -> float:
    """
    Calculate percentage change between two rates.
    Returns 0.0 if yesterday_rate is zero (avoid divide-by-zero).
    """
    if yesterday_rate == 0:
        return 0.0
    return ((today_rate - yesterday_rate) / yesterday_rate) * 100


def flag_significant(change_pct: float) -> str:
    """Return 'Yes' if the absolute change exceeds the threshold."""
    return "Yes" if abs(change_pct) > SIGNIFICANCE_THRESHOLD else "No"


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Currency Report – run started")
    log.info("Target currencies : %s", TARGET_CURRENCIES)

    today     = date.today()
    yesterday = today - timedelta(days=1)

    errors_encountered = []

    # ── 1. Fetch rates ────────────────────────────────────────
    try:
        # use_latest=True is faster and always returns current rates
        today_rates = fetch_rates(today, use_latest=True)
    except Exception as exc:
        log.error("Failed to fetch TODAY's rates: %s", exc)
        errors_encountered.append(f"Today fetch error: {exc}")
        today_rates = {}

    try:
        # Fetch yesterday by date; Frankfurter handles weekends automatically
        yesterday_rates = fetch_rates(yesterday, use_latest=False)
    except Exception as exc:
        log.error("Failed to fetch YESTERDAY's rates: %s", exc)
        errors_encountered.append(f"Yesterday fetch error: {exc}")
        yesterday_rates = {}

    if not today_rates or not yesterday_rates:
        log.error("Aborting: insufficient data to build report.")
        log.info("Errors this run: %s", errors_encountered or "None")
        sys.exit(1)

    # ── 2. Build report rows ──────────────────────────────────
    ALL_CURRENCIES = TARGET_CURRENCIES + ["AED"]   # AED added via fixed peg
    rows = []
    for currency in ALL_CURRENCIES:
        t_rate = today_rates.get(currency)
        y_rate = yesterday_rates.get(currency)

        if t_rate is None or y_rate is None:
            log.warning("Missing data for %s – skipping.", currency)
            errors_encountered.append(f"Missing data for {currency}")
            continue

        change = pct_change(t_rate, y_rate)
        rows.append({
            "Currency"         : currency,
            "Today_Rate_USD"   : round(t_rate,  6),
            "Yesterday_Rate_USD": round(y_rate, 6),
            "Pct_Change"       : round(change,  4),
            "Significant"      : flag_significant(change),
        })

    # ── 3. Write CSV ──────────────────────────────────────────
    fieldnames = [
        "Currency",
        "Today_Rate_USD",
        "Yesterday_Rate_USD",
        "Pct_Change",
        "Significant",
    ]

    with open(CSV_REPORT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    log.info("CSV report written → %s  (%d rows)", CSV_REPORT, len(rows))

    # ── 4. Pretty-print to console ────────────────────────────
    print("\n" + "─" * 70)
    print(f"  USD Exchange Rate Report  |  {today}  vs  {yesterday}")
    print("─" * 70)
    header = f"{'Currency':<10} {'Today':>12} {'Yesterday':>12} {'% Change':>10} {'Significant':>12}"
    print(header)
    print("─" * 70)
    for row in rows:
        line = (
            f"{row['Currency']:<10}"
            f"{row['Today_Rate_USD']:>12.4f}"
            f"{row['Yesterday_Rate_USD']:>12.4f}"
            f"{row['Pct_Change']:>10.4f}%"
            f"{'  *** ' + row['Significant'] if row['Significant'] == 'Yes' else row['Significant']:>12}"
        )
        print(line)
    print("─" * 70 + "\n")

    # ── 5. Final log summary ──────────────────────────────────
    log.info("Currencies in report : %s", [r["Currency"] for r in rows])
    log.info("Significant moves    : %s",
             [r["Currency"] for r in rows if r["Significant"] == "Yes"] or "None")
    log.info("Errors this run      : %s", errors_encountered or "None")
    log.info("Currency Report – run complete")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
