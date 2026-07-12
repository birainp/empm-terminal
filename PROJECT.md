# EMPM Terminal — Project Brief & Design Notes

The single source of truth for this project. Read this first — it captures **why** the
code is the way it is, not just what it does.

---

## What this is
A personal screening + exit-discipline dashboard for a concentrated AI/semiconductor
options book. It ranks a fixed universe for the probability of an *outsized* move (the
**Explosive Move Probability Model, EMPM**), places each name in its momentum lifecycle,
and — most importantly — flags when a move is decaying so positions are exited before
gains are handed back.

## Investment philosophy (the constitution)
- **Goal:** capture rare, large moves, expressed through options — mostly 3–6 months out,
  occasionally 12 months, rarely ~2-week snapbacks on names that have corrected hard.
  Holding period is incidental; the *move* is the point.
- **The exit is as important as the entry.** Documented failure mode: catching the move but
  giving back 60–70% by not exiting in time. The system therefore treats exit as a
  first-class engine, not an afterthought.
- Not a traditional momentum strategy — not trying to be right 55% of the time, but to catch
  the tails and keep a meaningful share of the gain.

## Universe
Tier 1 (15): NVDA, META, AVGO, AMD, MU, MRVL, TSM, ANET, VRT, ARM, ASML, AMAT, AAPL, TSLA,
CRWV. Benchmarks: **SPY** (stored as SPX) and **SOXX** (stored as SOX). Change it by editing
`UNIVERSE` in `empm_feed.py`.

## The EMPM score
Six factors, each mapped to 0–100 on its own scale, then blended by weights. Defaults
(tunable live via the sliders in the app):

| Factor | Weight | Notes |
|---|---|---|
| Relative Strength | 25% | vs SPX **and** SOX, weighted 45/55 toward SOX (sector-relative is the edge in an all-AI book); percentile-ranked across the universe |
| Volume | 15% | RVOL, up/down volume ratio, OBV slope |
| Trend / ADX | 15% | strength + rising-slope bonus; direction-penalized when −DI dominates |
| MACD | 15% | histogram sign + acceleration |
| MA Structure | 15% | price vs 20EMA/50/200 and stacking; penalized when over-extended |
| ATR Expansion | 15% | *change* in ATR (ratio vs 90d ago + percentile), **not** raw level; blow-off cap when volatility is extreme and price extended |

Design principle from the start: normalize each indicator to comparable scales, and don't
double-count correlated momentum oscillators (RSI/MACD/ROC measure the same thing) — hence
grouping and capping rather than naive summation.

## Why ADX and ATR are treated the way they are
- **ADX = trend *strength*, not direction** (a speedometer, not a compass). A high ADX alone
  is not a buy — it can accompany a strong *downtrend*, so it's direction-filtered.
- **ATR = volatility.** For an options book only the *transition* matters — expansion off a
  quiet base precedes the moves we want, while a very high ATR is often a blow-off top. Hence
  an **ATR Expansion Score**, not raw ATR, and a deliberately low weight.

## Lifecycle stages (the "where is the move" engine)
Six stages, assigned by a scored decision model (argmax over feature signals):
**Accumulation → Breakout → Markup → Acceleration → Climax → Distribution.** Placement uses
MA structure, ADX + slope, ATR expansion/percentile, extension vs the 50-MA, relative
strength, and MACD acceleration.

## Exit engine (the point of the whole thing)
- **Momentum Health / decay (0–100):** is the move still strengthening or leaking quality?
  Combines ADX rising, MACD accelerating, RS improving, volume confirming, and *not*
  over-extended vs the 20-EMA.
- **Exit Signal (a rule, not a number to stare at):** SCALE OUT at Climax; EXIT at
  Distribution or on a close below the 20-EMA while ADX is falling; TRIM when Health < 40;
  WATCH < 60; otherwise HOLD. The rules are meant to act on the trader rather than wait to be
  noticed — the direct countermeasure to the give-back problem.

## AI Cycle Score (context, not a factor)
A universe-level gauge (0–100): breadth (share of names above a rising 50/200 structure) +
benchmark strength (SOX) + average relative strength. Sits on top for context; it does not
feed the per-name EMPM.

## Data & hosting architecture
- `empm_feed.py` pulls **daily bars** from Alpaca (free IEX feed) for the universe +
  benchmarks and writes `empm_data.js` as `window.EMPM_DATA = { updated, asof, bars }`.
- `index.html` loads that file on open; falls back to clearly-labelled SAMPLE data if it's
  absent or invalid.
- `.github/workflows/feed.yml` runs the fetcher on a schedule (weekdays post-close) and
  commits the data — **this replaces an always-on computer.**
- GitHub Pages serves the page; it installs as a **PWA** (manifest + service worker + icons)
  on any device.
- The whole model is daily-bar based, so a scheduled end-of-day pull is sufficient — no
  tick/streaming infrastructure needed.

## Data staleness indicator
The badge keys off **weekdays behind the latest session in the data** (weekends ignored),
with last-successful-fetch time as a backstop for a stuck scheduler: green **LIVE** (current)
· amber **CHECK DATA** (~2 weekdays behind — a missed fetch or a market holiday) · red
**DATA STALE** (further behind — the fetch is failing).

## File map
- `index.html` — the dashboard (installable app)
- `empm_feed.py` — data fetcher (Alpaca; keys via env vars / GitHub Secrets)
- `empm_data.js` — data written by the fetcher (placeholder until the first run)
- `.github/workflows/feed.yml` — scheduled fetch + commit
- `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` — PWA
- `README.md` — setup / click-path
- `CLAUDE.md` — quick operational guidance for Claude Code
- `PROJECT.md` — this file (design + rationale)

## Roadmap
1. **Options / IV layer (v2):** IV rank, expected-move vs realized ATR, term structure → a
   "would I buy options today" **Conviction** score. Needs an options data source (Polygon
   options, ORATS/CBOE, or IBKR).
2. **Catalysts:** earnings/event dates folded into the model (Aiera connector or an earnings
   API), scoring time-to-catalyst within the 3–6-month option window.
3. **Alerts:** a daily email/push when a name flips to EXIT/SCALE OUT or a new leader crosses
   the EMPM threshold.
4. **Charts:** real date axis + longer history (optionally per-bar dates in the feed).
5. **Backtest harness:** tune weights/thresholds against past outsized moves.

## History note
Built collaboratively in a Claude chat: philosophy → scoring model → dashboard → Alpaca feed
→ GitHub Pages hosting with a scheduled Action → PWA install → data-staleness indicator. The
data is deliberately daily-bar based to keep the pipeline simple and free.

## Not investment advice
A screening/analysis tool; not buy/sell recommendations.
