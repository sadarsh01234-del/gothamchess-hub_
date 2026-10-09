"""GothamChess fan hub (unofficial). Flask + SQLite."""
import csv, hmac, io, json, os, random, re, sqlite3, time, urllib.request
from datetime import datetime, timezone
from functools import wraps
from flask import (Flask, Response, flash, g, jsonify, redirect,
                   render_template, request, url_for)
from markupsafe import Markup

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-change-me")
DB = os.environ.get("DB_PATH", "gotham.db")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "gotham")  # CHANGE in production

# ---------- database ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()

with sqlite3.connect(DB) as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS submissions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, game_url TEXT NOT NULL, pgn TEXT NOT NULL,
      gothamsub_color TEXT NOT NULL CHECK(gothamsub_color IN ('white','black')),
      submitter TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS subscribers(
      id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL);""")

now = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")

# ---------- admin (HTTP basic auth) ----------
def admin_only(f):
    @wraps(f)
    def wrap(*a, **k):
        au = request.authorization
        if not au or not (hmac.compare_digest(au.username, ADMIN_USER)
                          and hmac.compare_digest(au.password or "", ADMIN_PASS)):
            return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Gotham Admin"'})
        return f(*a, **k)
    return wrap

# ---------- chess.com public API (cached) ----------
_cache = {}
def chesscom(path, ttl=900):
    url = "https://api.chess.com/pub/" + path
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GothamFanHub/1.0"})
        data = json.load(urllib.request.urlopen(req, timeout=5))
    except Exception:
        data = hit[1] if hit else None
    _cache[url] = (time.time() - (ttl - 60 if data is None else 0), data)
    return data

# ---------- Gotham backdrop: skyline + perspective chessboard ----------
def build_bg():
    r = random.Random(7)
    s = ['<svg viewBox="0 0 1600 900" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">'
         '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05060a"/>'
         '<stop offset=".7" stop-color="#1a2233"/><stop offset="1" stop-color="#3a3320"/></linearGradient></defs>'
         '<rect width="1600" height="900" fill="url(#sky)"/>'
         '<polygon class="beam" points="1230,190 700,0 1500,0" fill="#f1e7b8"/>'
         '<circle class="moon" cx="1230" cy="190" r="95" fill="#f1e7b8" opacity=".9"/>'
         '<path d="M1230 150c-10 14-30 16-48 10 6 14 14 22 22 22 4-8 12-10 26-6 14-4 22-2 26 6 8 0 16-8 22-22-18 6-38 4-48-10z" fill="#0b0d12"/>']
    x = -20
    while x < 1620:
        w, h = r.randint(45, 115), r.randint(180, 470)
        top = 720 - h
        s.append(f'<rect x="{x}" y="{top}" width="{w}" height="{h+10}" fill="#0c101a"/>')
        if r.random() < .45:
            s.append(f'<polygon points="{x},{top} {x+w/2},{top-r.randint(40,110)} {x+w},{top}" fill="#0c101a"/>')
        for _ in range(int(w * h / 900)):
            if r.random() < .35:
                s.append(f'<rect x="{x+r.randint(5,w-12)}" y="{top+r.randint(8,h-10)}" width="5" height="7" fill="#f5c518" opacity="{r.choice((.35,.6,.9))}" class="tw t{r.randint(1,3)}"/>')
        x += w + r.randint(-8, 6)
    ys = [720 + 180 * (i / 8) ** 1.7 for i in range(9)]
    for i in range(8):
        t0, t1 = i / 8, (i + 1) / 8
        for c in range(16):
            xa = lambda t, cc: 800 + (cc - 8) * 100 * (.3 + .7 * t)
            pts = f"{xa(t0,c):.0f},{ys[i]:.0f} {xa(t0,c+1):.0f},{ys[i]:.0f} {xa(t1,c+1):.0f},{ys[i+1]:.0f} {xa(t1,c):.0f},{ys[i+1]:.0f}"
            s.append(f'<polygon points="{pts}" fill="{"#2c374d" if (i+c)%2 else "#10151f"}" opacity=".95"/>')
    for ch, px, py, fs in (("♜", 250, 760, 120), ("♞", 520, 800, 150), ("♚", 800, 780, 190),
                           ("♝", 1090, 810, 150), ("♛", 1340, 765, 130)):
        s.append(f'<text x="{px}" y="{py}" font-size="{fs}" text-anchor="middle" fill="#0b0d12" stroke="#f5c518" stroke-width="2">{ch}</text>')
    return Markup("".join(s) + "</svg>")
BG = build_bg()

@app.context_processor
def inject():
    return {"bg_svg": BG}

# ---------- pages ----------
@app.route("/")
def home():
    st = chesscom("player/gothamchess/stats") or {}
    rat = {k: st.get("chess_" + k, {}).get("last", {}).get("rating") for k in ("rapid", "blitz", "bullet")}
    return render_template("index.html", rat=rat, puzzle=chesscom("puzzle", 3600))

@app.route("/connect")
def connect():
    return render_template("connect.html")

@app.route("/play")
def play():
    return render_template("play.html")

@app.route("/coach")
def coach():
    return render_template("coach.html")

URL_RE = re.compile(r"^https?://(www\.)?(chess\.com|lichess\.org)/\S+$", re.I)

@app.route("/guess", methods=["GET", "POST"])
def guess():
    if request.method == "POST":
        url = request.form.get("game_url", "").strip()
        pgn = request.form.get("pgn", "").strip()
        col = request.form.get("gothamsub_color", "")
        who = request.form.get("submitter", "").strip()[:60]
        err = None
        if not URL_RE.match(url):
            err = "Enter a valid chess.com or lichess game URL."
        elif len(pgn) < 10 or not re.search(r"1\.\s*\S+", pgn) or len(pgn) > 20000:
            err = "Paste a valid PGN (it must contain moves, e.g. 1. e4 e5)."
        elif col not in ("white", "black"):
            err = "Choose GothamSub's colour."
        if err:
            flash(err, "error")
            return render_template("guess.html", f=request.form), 400
        db().execute("INSERT INTO submissions(game_url,pgn,gothamsub_color,submitter,created_at) VALUES(?,?,?,?,?)",
                     (url, pgn, col, who, now()))
        db().commit()
        flash("Game received! Levy may feature it in a Guess the Elo video.", "ok")
        return redirect(url_for("guess"))
    return render_template("guess.html", f={})

@app.post("/subscribe")
def subscribe():
    email = request.form.get("email", "").strip().lower()
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) and len(email) < 255:
        try:
            db().execute("INSERT INTO subscribers(email,created_at) VALUES(?,?)", (email, now()))
            db().commit()
        except sqlite3.IntegrityError:
            pass
        flash("You're on the Bat-list! Thanks for subscribing.", "ok")
    else:
        flash("Please enter a valid email.", "error")
    return redirect(request.referrer or url_for("home"))

# ---------- admin ----------
@app.route("/admin")
@admin_only
def admin():
    subs = db().execute("SELECT * FROM submissions ORDER BY id DESC").fetchall()
    news = db().execute("SELECT * FROM subscribers ORDER BY id DESC").fetchall()
    return render_template("admin.html", subs=subs, news=news)

@app.post("/admin/delete/<int:sid>")
@admin_only
def admin_delete(sid):
    db().execute("DELETE FROM submissions WHERE id=?", (sid,))
    db().commit()
    return redirect(url_for("admin"))

@app.route("/admin/export.csv")
@admin_only
def export():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "game_url", "gothamsub_color", "submitter", "created_at", "pgn"])
    for r in db().execute("SELECT * FROM submissions ORDER BY id"):
        w.writerow([r["id"], r["game_url"], r["gothamsub_color"], r["submitter"], r["created_at"], r["pgn"]])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=guess_the_elo.csv"})

# ---------- coach (rule-based knowledge base) ----------
KB = [
 (["en passant"], "En passant: if an enemy pawn jumps two squares and lands beside your pawn, you may capture it as if it had moved one square. You must do it immediately or lose the right."),
 (["castle", "castling"], "Castling: king moves two squares toward a rook, rook hops over. Legal only if neither piece has moved, no pieces between, the king isn't in check, and doesn't cross or land on an attacked square. Castle early, king safety first."),
 (["stalemate"], "Stalemate: the side to move has no legal move but is NOT in check. It's a draw. Always check it before you go chasing that last pawn when you're winning."),
 (["fork"], "A fork is one piece attacking two or more targets at once. Knights are the kings of forks because most pieces can't hit back at them."),
 (["pin", "skewer"], "A pin freezes a piece because moving it exposes something more valuable behind it. A skewer is the reverse: the valuable piece must move, exposing the one behind it."),
 (["opening", "principles"], "Opening principles: fight for the center, develop knights before bishops, castle early, don't move the same piece twice without reason, and don't bring the queen out too soon."),
 (["endgame", "opposition"], "Endgames: activate your king, create passed pawns, and learn the opposition (kings facing each other with one square between; the side NOT to move wins the fight). King and pawn endings are pure calculation."),
 (["lucena", "philidor", "rook endgame"], "Rook endgames: Lucena is the winning bridge-building technique. Philidor is the defensive setup, keeping your rook on the 3rd rank until the pawn advances. Rooks belong behind passed pawns."),
 (["london"], "The London System: d4, Bf4, e3, Nf3, c3, Bd3. A solid, low-theory setup that's easy to learn. Don't play it on autopilot, though; watch for early ...c5 and ...Qb6 ideas."),
 (["sicilian"], "The Sicilian (1.e4 c5) is Black's most ambitious reply: it unbalances the position and fights for d4. Expect sharp play and opposite-side attacks."),
 (["gambit"], "A gambit sacrifices material, usually a pawn, for development, space or initiative. The Queen's Gambit (1.d4 d5 2.c4) isn't a true gambit because White can win the pawn back."),
 (["piece value", "worth", "points"], "Rough values: pawn 1, knight 3, bishop 3, rook 5, queen 9. Two bishops are usually worth a little more than the sum, and activity can beat material."),
 (["threefold", "repetition", "draw", "fifty"], "Draws happen by stalemate, agreement, threefold repetition, the fifty-move rule (no capture or pawn move), or insufficient material."),
 (["tactic", "puzzle"], "Tactics are 90% of improvement below 1800. Do daily puzzles, and before every move ask: what are the checks, captures and threats for both sides?"),
 (["blunder"], "Cut blunders with a blunderchecking routine: before you move, ask 'what does this move leave undefended, and what does my opponent threaten?'"),
 (["pawn structure", "isolated", "doubled", "passed pawn"], "Pawns can't go back. Isolated and doubled pawns are weaknesses; passed pawns are assets; a pawn chain should be attacked at its base."),
 (["center", "centre"], "Control of the center gives your pieces more room. You can do it with pawns (e4/d4) or by hitting it from the side with pieces, as in hypermodern openings."),
 (["back rank", "mate", "checkmate"], "Classic mates: back-rank mate (rook or queen on the first rank behind unmoved pawns), smothered mate, Scholar's mate. Give your king luft (a pawn move) to avoid the back-rank trap."),
 (["rating", "improve", "better", "elo"], "To climb: 1) daily tactics, 2) analyze your losses, 3) learn 1 opening for each color, 4) study basic endgames, 5) play longer time controls. Consistency beats cramming."),
 (["bullet", "blitz", "rapid", "time control"], "Bullet < 3 min, blitz 3 to 10, rapid 10 to 60, classical longer. Learn in rapid, entertain yourself in blitz."),
 (["hello", "hi", "hey", "yo"], "Hello everybody! I'm Gotham's fan-made coach. Ask me about rules, openings, tactics, endgames or how to improve."),
]
def coach_reply(msg):
    m = msg.lower()
    best, score = None, 0
    for keys, ans in KB:
        sc = sum(1 for k in keys if re.search(r"\b" + re.escape(k), m))
        if sc > score:
            best, score = ans, sc
    return best or ("Hmm, that one's not in my notebook. Try asking about: castling, en passant, openings, "
                    "tactics (forks/pins), endgames, pawn structure, or how to improve.")

@app.post("/api/coach")
def api_coach():
    msg = (request.get_json(silent=True) or {}).get("message", "")[:500]
    return jsonify(reply=coach_reply(msg))

if __name__ == "__main__":
    app.run(debug=True)
