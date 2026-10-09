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
- **Hosting:** Render with Gunicorn

## Run locally

Requires Python 3.10 or newer.

```bash
git clone https://github.com/YOUR-USERNAME/gothamchess-hub.git
cd gothamchess-hub

python -m venv venv
# Windows:    venv\Scripts\activate
# Mac/Linux:  source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The play page needs an internet connection to load the chess libraries.

## Configuration

Set these as environment variables (never commit them):

| Variable | Default | Purpose |
|---|---|---|
| `ADMIN_USER` | `admin` | Admin login username |
| `ADMIN_PASSWORD` | `gotham` | Admin login password. **Change this in production** |
| `SECRET_KEY` | `dev-change-me` | Flask session key. **Change this in production** |
| `DB_PATH` | `gotham.db` | Location of the SQLite file |

## Admin backend

Go to `/admin` and sign in. You can view every Guess the Elo submission and newsletter signup, open each PGN, delete entries, and download everything at `/admin/export.csv`.

Submissions are stored in the `submissions` table: `id`, `game_url`, `pgn`, `gothamsub_color`, `submitter`, `created_at`.

## Deploy on Render

1. Push this repo to GitHub.
2. On [render.com](https://render.com), create a **New Web Service** from the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add the environment variables above.

**Note:** On Render's free plan the SQLite file is erased on each redeploy, and the app sleeps after about 15 minutes of inactivity. Download the CSV regularly, or attach a persistent disk and set `DB_PATH=/var/data/gotham.db`.

## Project structure

```
app.py              Flask app, routes, database, coach knowledge base
requirements.txt    Python dependencies
Procfile            Gunicorn start command
templates/          Jinja HTML templates
static/             CSS, JavaScript, chess piece SVGs
```

## Notes

- Chess.com offers no public engine API, so the bot uses Stockfish with a skill level mapped from the Elo slider. Elo values are approximate.
- The coach is a keyword-based knowledge base, not an AI model.

## Credits

- Chess pieces: cburnett set by Colin M.L. Burnett, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- Fonts: Cinzel and Manrope via Google Fonts
- Creator: [GothamChess on YouTube](https://www.youtube.com/@GothamChess)
