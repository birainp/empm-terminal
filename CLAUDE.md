# CLAUDE.md — EMPM Terminal

Operational guidance for Claude Code working in this repo. **Read `PROJECT.md` first**
for the full design rationale (philosophy, scoring model, weights, exit logic); this file
is the quick reference for how to work here.

## What this is
A self-updating momentum + exit-discipline dashboard for a concentrated AI/semiconductor
options book. It ranks a fixed universe with the **Explosive Move Probability Model
(EMPM)**, places each name in its lifecycle stage, and flags momentum decay so positions
are exited before gains are given back. It is a screening/analysis tool, **not investment
advice** — do not add buy/sell recommendations.

## Repo layout
- `index.html` — the entire dashboard: scoring engine + UI, **vanilla JS, no build step**.
  Loads `empm_data.js` on open; falls back to clearly-labelled SAMPLE data if it's absent.
- `empm_feed.py` — the data fetcher. Pulls **daily bars** from Alpaca (free IEX feed) for
  the universe + SPY/SOXX benchmarks and writes `empm_data.js`
  (`window.EMPM_DATA = {updated, asof, bars}`). **Standard library only** — no pip installs.
- `.github/workflows/feed.yml` — scheduled Action; runs the fetcher weekdays after the US
  close and commits `empm_data.js`. This is what keeps the hosted site fresh with no server.
- `manifest.webmanifest`, `sw.js`, `icon-*.png`, `apple-touch-icon.png` — PWA (installs to
  the home screen on iOS/desktop).
- `empm_data.js` — generated data. **Do not hand-edit.**

## Run / test locally
- **Fetcher:** set env vars `ALPACA_KEY_ID` and `ALPACA_SECRET`, then `python empm_feed.py`.
  It writes `empm_data.js` in the repo root.
- **Dashboard:** open `index.html` directly, or run `python -m http.server` and visit it.
  With no populated `empm_data.js` it shows SAMPLE data — that's expected, not a bug.
- **Validate before pushing:** `feed.yml` must be valid YAML; `manifest.webmanifest` valid JSON.

## Guardrails (important)
- **Never commit API keys or secrets.** Keys come only from env vars (local) or the GitHub
  repository Secrets `ALPACA_KEY_ID` / `ALPACA_SECRET` (in the Action). No keys in code, no
  keys in `empm_data.js`, no keys in commit messages.
- Keep the `loadLive()` → sample-data fallback intact so the page never hard-fails.
- The model is **daily-bar based** — do not introduce a hard dependency on intraday/tick data.
- If you change `index.html`, **bump `CACHE = 'empm-vN'` in `sw.js`** so installed PWAs pick
  up the new shell (they cache aggressively).
- Keep the fetcher **dependency-free (stdlib)** so GitHub Actions runs it with no install step.
- Benchmarks are stored under keys `SPX` (from SPY) and `SOX` (from SOXX); the dashboard's
  relative-strength code depends on those two keys existing.

## Deployment model
GitHub Pages serves the repo root (Settings → Pages → Deploy from branch → `main`/root). The
feed Action commits data → Pages redeploys automatically on the push. Don't restructure paths
in a way that breaks the root-served Pages site or the relative asset paths in `index.html`.

## Roadmap / likely next tasks
1. **Options/IV layer (v2):** IV rank, expected-move vs realized ATR, term structure → a
   "Conviction" (would-I-buy-options-today) score. Needs an options data source (Polygon
   options, ORATS/CBOE, or IBKR). Implement as new fields in the feed + a new sub-score +
   a drilldown section.
2. **Catalysts:** earnings/event dates folded in (Aiera connector or an earnings API); score
   time-to-catalyst within the 3–6-month option window.
3. **Alerts:** a daily email/push when a name flips to EXIT/SCALE OUT or a new leader crosses
   the EMPM threshold.
4. **Charts:** real date axis + more history (add per-bar dates to the feed).
5. **Backtest harness:** tune weights/thresholds against past outsized moves.

## Conventions
- Single-file dashboard, no framework, no bundler — keep it that way unless there's a strong
  reason. Match the existing code style in each file. Small, reviewable commits.
- The scoring math (Wilder ATR/ADX, MACD, relative strength, ATR-expansion, the stage
  classifier, the decay/exit logic) lives in `index.html`. If any of it is ported to the
  fetcher for server-side scoring, keep the two implementations in sync.
