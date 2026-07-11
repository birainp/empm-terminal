# EMPM Terminal — always-on hosted setup

A self-updating momentum/exit dashboard for your Tier-1 AI/semis universe.
GitHub hosts the page and runs the data fetch on a schedule, so **no computer
needs to stay on** and you can open it from any device.

How the pieces fit:

- `index.html` — the dashboard (installs as an app; opens full-screen on iPhone/iPad).
- `empm_feed.py` — pulls daily bars from Alpaca and writes `empm_data.js`.
- `.github/workflows/feed.yml` — runs the fetcher on a schedule and commits the data.
- `manifest.webmanifest`, `sw.js`, icons — make it an installable, offline-capable app.

Your Alpaca key is **never in these files.** It lives as an encrypted GitHub
*Secret* that only the Action can read. You enter it yourself in GitHub's UI.

---

## One-time setup (~10 minutes)

### 1. Create the repo and add these files
- On GitHub: **New repository** → name it e.g. `empm-terminal` → **Public** is fine
  (nothing sensitive is committed — daily prices are public and your key is a Secret).
- Upload every file **keeping the folder structure** — the workflow must stay at
  `.github/workflows/feed.yml`. Easiest is Git:
  ```
  git init
  git add .
  git commit -m "EMPM terminal"
  git branch -M main
  git remote add origin https://github.com/<you>/empm-terminal.git
  git push -u origin main
  ```
  (Or use **Add file → Upload files** and drag everything in; if the web uploader
  flattens the workflow, create it manually via **Add file → Create new file** and
  type the path `.github/workflows/feed.yml`.)

### 2. Add your Alpaca keys as encrypted Secrets
- Get free keys at **alpaca.markets** (a paper account works; the free **IEX** feed
  covers everything this model needs).
- Repo → **Settings → Secrets and variables → Actions → New repository secret**.
  Add two secrets:
  - `ALPACA_KEY_ID` = your key id
  - `ALPACA_SECRET` = your secret
- These are encrypted and only exposed to the workflow at runtime.

### 3. Turn on GitHub Pages
- Repo → **Settings → Pages** → **Source: Deploy from a branch** →
  **Branch: `main` / `/ (root)`** → **Save**.
- After ~1 minute your URL is: `https://<you>.github.io/empm-terminal/`

### 4. Run the fetch once (so data appears now)
- Repo → **Actions** tab → if prompted, enable workflows →
  select **EMPM data feed** → **Run workflow**.
- It fetches, commits `empm_data.js`, and Pages redeploys. Refresh the URL — the
  badge flips from amber **SAMPLE DATA** to green **● LIVE** with a timestamp.
- From then on it runs on its own (weekdays after the close). No further action.

### 5. Install it as an app
- **iPhone / iPad:** open the URL in **Safari** → **Share** → **Add to Home Screen**.
  It installs as **EMPM** with the icon and opens full-screen.
- **Mac / Windows (Chrome/Edge):** open the URL → the **install** icon in the address
  bar → Install.
- Any number of devices — they all just open the same URL.

---

## Everyday use
- Nothing. It refreshes daily by itself; opening the app fetches the latest data,
  and it reloads hourly if you leave it open.
- **Data-status badge (top right):** green **● LIVE · as of &lt;date&gt;** when current;
  amber **◆ CHECK DATA** if the latest session is ~2 weekdays behind (a missed fetch or
  a market holiday); red **▲ DATA STALE** if it's further behind (the scheduled fetch is
  likely failing — check the Actions tab). Weekends are ignored, so a Friday close reads
  fresh all weekend. Tap the badge for the exact session date and last fetch time.

## Adjusting it
- **Change tickers:** edit `UNIVERSE` in `empm_feed.py`, commit. (The dashboard reads
  whatever symbols the feed provides.)
- **More frequent updates:** uncomment the intraday `cron` line in `feed.yml`.
- **Change the schedule:** edit the `cron` (UTC) in `feed.yml`.
- **After editing `index.html`:** bump `CACHE = 'empm-v1'` → `'empm-v2'` in `sw.js` so
  installed apps pick up the new version.

## Notes
- The free IEX feed is lightly delayed and skips after-hours. Since every score is
  built on **daily bars**, that doesn't affect the numbers — but it's not a real-time
  Level 1 quote.
- This is a screening/analysis tool, not investment advice.
