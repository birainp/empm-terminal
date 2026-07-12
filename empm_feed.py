#!/usr/bin/env python3
"""
EMPM feed  ---------------------------------------------------------------
Pulls daily OHLCV bars for the Tier-1 AI/semis universe + benchmarks and
writes `empm_data.js` next to your dashboard. The dashboard auto-loads it
on open, so you never paste prices again -- just schedule this script.

ONE-TIME SETUP (on your machine, not shared with anyone):
  1. Get free Alpaca API keys: https://alpaca.markets  ->  Paper account is fine.
     (The free "IEX" data feed covers everything this model needs.)
  2. Either set environment variables ALPACA_KEY_ID / ALPACA_SECRET,
     or paste them into the two lines just below.
  3. Put this file in the SAME folder as empm_terminal.html and run it once:
         python empm_feed.py
  4. Schedule it (see the README section printed at the bottom) so it
     refreshes on its own every day.

No third-party packages required -- standard library only.
"""

import os, json, sys, time, datetime as dt
from urllib import request, parse, error

# --- credentials: env vars take precedence; otherwise paste here -----------
API_KEY_ID = os.environ.get("ALPACA_KEY_ID", "PASTE_YOUR_ALPACA_KEY_ID")
API_SECRET = os.environ.get("ALPACA_SECRET", "PASTE_YOUR_ALPACA_SECRET")

# --- universe --------------------------------------------------------------
UNIVERSE = ["NVDA","META","AVGO","AMD","MU","MRVL","TSM","ANET",
            "VRT","ARM","ASML","AMAT","AAPL","TSLA","CRWV"]

# Benchmarks: tradable ETF proxies (free IEX feed carries these).
# Stored under SPX / SOX so the dashboard's relative-strength logic is unchanged.
BENCH = {"SPY": "SPX", "SOXX": "SOX"}     # S&P 500 proxy, semis proxy

LOOKBACK_DAYS = 420          # calendar days -> ~280 trading bars (need 200 for SMA200)
FEED          = "iex"        # free feed; use "sip" only if you pay for it
DATA_HOST     = "https://data.sandbox.alpaca.markets"
OUT_FILE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "empm_data.js")


def fetch_symbol(symbol, start_iso):
    """Fetch daily bars for one symbol, following pagination.
    Returns (bars, last_session_date) where last_session_date is 'YYYY-MM-DD'."""
    bars, page_token, last_t = [], None, None
    while True:
        q = {
            "timeframe": "1Day",
            "start": start_iso,
            "limit": "1000",
            "adjustment": "all",     # split/dividend adjusted
            "feed": FEED,
        }
        if page_token:
            q["page_token"] = page_token
        url = f"{DATA_HOST}/v2/stocks/{parse.quote(symbol)}/bars?{parse.urlencode(q)}"
        req = request.Request(url, headers={
            "APCA-API-KEY-ID": API_KEY_ID,
            "APCA-API-SECRET-KEY": API_SECRET,
            "accept": "application/json",
        })
        with request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode())
        for b in payload.get("bars", []) or []:
            last_t = b.get("t", last_t)
            bars.append({
                "o": round(b["o"], 4), "h": round(b["h"], 4),
                "l": round(b["l"], 4), "c": round(b["c"], 4),
                "v": int(b["v"]),
            })
        page_token = payload.get("next_page_token")
        if not page_token:
            break
    return bars, (last_t[:10] if last_t else None)


def main():
    if "PASTE_YOUR" in API_KEY_ID or "PASTE_YOUR" in API_SECRET:
        sys.exit("!! Add your Alpaca keys first (env vars ALPACA_KEY_ID / "
                 "ALPACA_SECRET, or edit the two lines near the top).")

    start = (dt.datetime.utcnow() - dt.timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    out_bars, failures, asof = {}, [], None

    all_syms = [(s, s) for s in UNIVERSE] + list(BENCH.items())
    for symbol, store_as in all_syms:
        try:
            data, last_date = fetch_symbol(symbol, start)
            if len(data) < 40:
                failures.append(f"{symbol} (only {len(data)} bars)")
            else:
                out_bars[store_as] = data
                if last_date and (asof is None or last_date > asof):
                    asof = last_date
                print(f"  {symbol:6s} -> {len(data)} bars (latest {last_date})")
            time.sleep(0.15)   # gentle on the free rate limit
        except error.HTTPError as e:
            body = e.read().decode()[:180]
            if e.code in (401, 403):
                sys.exit(f"!! Auth failed for {symbol} ({e.code}). Check your keys "
                         f"and that the data feed is enabled.\n{body}")
            failures.append(f"{symbol} (HTTP {e.code})")
        except Exception as e:
            failures.append(f"{symbol} ({e})")

    if "SPX" not in out_bars or "SOX" not in out_bars:
        sys.exit("!! Missing benchmark data (SPY/SOXX). Cannot compute relative "
                 "strength -- aborting so the dashboard keeps its last good data.")

    doc = {
        "updated": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "asof": asof,          # latest trading session present in the data (YYYY-MM-DD)
        "feed": FEED,
        "bars": out_bars,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("window.EMPM_DATA = " + json.dumps(doc, separators=(",", ":")) + ";\n")

    print(f"\nWrote {OUT_FILE}")
    print(f"Universe symbols fetched: {len([k for k in out_bars if k not in ('SPX','SOX')])}/{len(UNIVERSE)}")
    if failures:
        print("Skipped:", ", ".join(failures))
    print("Done. Open empm_terminal.html -- it will show LIVE + this timestamp.")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# SCHEDULING (so it refreshes with no button and no manual runs)
#
# Windows (Task Scheduler, one line in an admin PowerShell/cmd):
#   Daily after the close:
#     schtasks /create /tn "EMPM Feed" /tr "python C:\path\to\empm_feed.py" /sc daily /st 16:20
#   Or every 30 min (updates today's bar through the day):
#     schtasks /create /tn "EMPM Feed" /tr "python C:\path\to\empm_feed.py" /sc minute /mo 30
#   Delete it later with:  schtasks /delete /tn "EMPM Feed" /f
#
# macOS / Linux (cron -- run `crontab -e` and add):
#   Weekdays at 16:20 local:   20 16 * * 1-5  /usr/bin/python3 /path/to/empm_feed.py
# ---------------------------------------------------------------------------
