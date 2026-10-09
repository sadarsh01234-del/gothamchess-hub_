# GothamChess Hub

An unofficial fan hub for chess creator **GothamChess (Levy Rozman)**, built with Python, Flask and SQLite. It has a dark Gotham City theme: a skyline and chessboard backdrop with rain, fog, a bat-signal and lightning.

> Fan project, not affiliated with Levy Rozman, GothamChess, Chess.com or DC.

**Live site:** _add your Render URL here_

## Features

| Page | Route | What it does |
|---|---|---|
| Home | `/` | Live GothamChess ratings and the daily puzzle from the Chess.com public API |
| Guess the Elo | `/guess` | Submit a game (URL, PGN, your colour as GothamSub). Saved to SQLite with validation |
| Play Gotham Bot | `/play` | Play a Stockfish bot with an adjustable Elo (400 to 2800) and themed opponents |
| Gotham Coach | `/coach` | Chat bot answering chess rules, theory and strategy questions |
| Connect | `/connect` | Links to YouTube, Twitch, Chess.com, Instagram and Chessly |
| Admin | `/admin` | Password-protected view of submissions and subscribers, delete, CSV export |

The footer on every page has a newsletter signup.

## Tech stack

- **Backend:** Python 3, Flask, SQLite
- **Frontend:** Jinja templates, plain CSS and JavaScript
- **Chess:** [chess.js](https://github.com/jhlywa/chess.js) for rules, [stockfish.js](https://github.com/nmrugg/stockfish.js) as the bot engine (loaded in the browser)
- **Data:** Chess.com public API (ratings and daily puzzle, cached)
- **Hosting:** Vercel (serverless) with Postgres, or Render with Gunicorn

## Run locally

Requires Python 3.10 or newer.

```bash
git clone https://github.com/YOUR-USERNAME/gothamchess-hub.git
cd gothamchess-hub

python -m venv venv
# Windows:    venv\Scripts\activate
# Mac/Linux:  source venv/bin/activate

pip install -r requirements.txt
python src/app.py
```

Open http://127.0.0.1:5000. The play page needs an internet connection to load the chess libraries.

## Configuration

Set these as environment variables (never commit them):

| Variable | Default | Purpose |
|---|---|---|
| `ADMIN_USER` | `admin` | Admin login username |
| `ADMIN_PASSWORD` | `gotham` | Admin login password. **Change this in production** |
| `SECRET_KEY` | `dev-change-me` | Flask session key. **Change this in production** |
| `DATABASE_URL` | empty | Postgres connection string. If set, Postgres is used instead of SQLite (required on Vercel) |
| `DB_PATH` | `gotham.db` | Location of the SQLite file (local use) |

## Admin backend

Go to `/admin` and sign in. You can view every Guess the Elo submission and newsletter signup, open each PGN, delete entries, and download everything at `/admin/export.csv`.

Submissions are stored in the `submissions` table: `id`, `game_url`, `pgn`, `gothamsub_color`, `submitter`, `created_at`.

## Deploy on Vercel

Vercel's filesystem is temporary, so submissions need an external Postgres database.

1. Push this repo to GitHub.
2. On [vercel.com](https://vercel.com), click **Add New, Project** and import the repo. Leave the framework preset as detected (Flask) and deploy.
3. In the project, open **Storage** and create a **Neon Postgres** database from the Marketplace. Connect it to the project so `DATABASE_URL` is added automatically.
4. Under **Settings, Environment Variables**, add `ADMIN_PASSWORD` and `SECRET_KEY` (and optionally `ADMIN_USER`).
5. **Redeploy** so the variables take effect. Tables are created automatically on first load.

## Deploy on Render (alternative)

Build command `pip install -r requirements.txt`, start command `gunicorn src.app:app`. On the free plan SQLite is erased on redeploy, so set `DATABASE_URL` to a Postgres database to keep data.

## Project structure

```
src/app.py          Flask app, routes, database, coach knowledge base
src/templates/      Jinja HTML templates
public/static/      CSS, JavaScript, chess piece SVGs (served by Vercel's CDN)
requirements.txt    Python dependencies
vercel.json         Vercel config
Procfile            Gunicorn start command (Render)
.env.example        Environment variable template
```

## Notes

- Chess.com offers no public engine API, so the bot uses Stockfish with a skill level mapped from the Elo slider. Elo values are approximate.
- The coach is a keyword-based knowledge base, not an AI model.

## Credits

- Chess pieces: cburnett set by Colin M.L. Burnett, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- Fonts: Cinzel and Manrope via Google Fonts
- Creator: [GothamChess on YouTube](https://www.youtube.com/@GothamChess)
