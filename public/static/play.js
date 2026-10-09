const SF = 'https://cdnjs.cloudflare.com/ajax/libs/stockfish.js/10.0.2/stockfish.js';
const game = new Chess();
let me = 'w', flip = false, sel = null, busy = false, eng = null, ready = false;
const $ = id => document.getElementById(id);
const names = [[800, 'the Penguin'], [1200, 'the Riddler'], [1600, 'Two-Face'], [2000, 'the Scarecrow'], [2400, 'the Joker'], [2801, 'Bane']];
const botName = () => names.find(n => +$('elo').value < n[0])[1];
const skill = () => Math.max(0, Math.min(20, Math.round((+$('elo').value - 400) / 120)));

function render(last) {
  const b = $('board'); b.innerHTML = '';
  const legal = sel ? game.moves({ square: sel, verbose: true }).map(m => m.to) : [];
  for (let r = 0; r < 8; r++) for (let f = 0; f < 8; f++) {
    const rr = flip ? 7 - r : r, ff = flip ? 7 - f : f, sq = 'abcdefgh'[ff] + (8 - rr);
    const p = game.get(sq), d = document.createElement('button');
    d.className = 'sq ' + ((rr + ff) % 2 ? 'dk' : 'lt') + (sq === sel ? ' sel' : '') + (legal.includes(sq) ? ' dot' : '') + (last && (sq === last.from || sq === last.to) ? ' last' : '');
    d.setAttribute('aria-label', sq + (p ? ' ' + (p.color === 'w' ? 'white ' : 'black ') + p.type : ''));
    if (p) { const i = document.createElement('img'); i.src = '/static/pieces/' + p.color + p.type.toUpperCase() + '.svg'; i.alt = ''; i.draggable = false; d.appendChild(i); }
    d.onclick = () => click(sq); b.appendChild(d);
  }
  $('moves').textContent = game.pgn();
}
function status() {
  if (game.in_checkmate()) return game.turn() === me ? 'Checkmate. ' + botName() + ' wins.' : 'Checkmate! You win!';
  if (game.in_draw() || game.in_stalemate()) return 'Draw.';
  return (game.turn() === me ? 'Your move' : botName() + ' is thinking…') + (game.in_check() ? ' (check)' : '');
}
function after(m) { render(m); $('status').textContent = status(); if (!game.game_over() && game.turn() !== me) botMove(); }
function click(sq) {
  if (busy || game.game_over() || game.turn() !== me) return;
  if (sel) {
    const m = game.move({ from: sel, to: sq, promotion: 'q' });
    if (m) { sel = null; return after(m); }
  }
  const p = game.get(sq); sel = p && p.color === me ? sq : null; render();
}
function botMove() {
  busy = true;
  const done = uci => {
    busy = false; if (!uci) return;
    const m = game.move({ from: uci.slice(0, 2), to: uci.slice(2, 4), promotion: uci[4] || 'q' });
    if (m) after(m);
  };
  if (!ready) { const mv = game.moves({ verbose: true }); const m = mv[Math.floor(Math.random() * mv.length)]; return setTimeout(() => done(m.from + m.to), 400); }
  eng.onmessage = e => { const t = String(e.data); if (t.startsWith('bestmove')) done(t.split(' ')[1]); };
  eng.postMessage('setoption name Skill Level value ' + skill());
  eng.postMessage('position fen ' + game.fen());
  eng.postMessage('go depth ' + (2 + Math.round(skill() * .6)) + ' movetime 1200');
}
function newGame() {
  game.reset(); sel = null; busy = false;
  const s = $('side').value; me = s === 'r' ? (Math.random() < .5 ? 'w' : 'b') : s; flip = me === 'b';
  $('botname').textContent = botName(); render(); $('status').textContent = status();
  if (me === 'b') botMove();
}
async function initEngine() {
  try {
    const code = await (await fetch(SF)).text();
    eng = new Worker(URL.createObjectURL(new Blob([code], { type: 'text/javascript' })));
    eng.onmessage = e => { if (String(e.data) === 'readyok') { ready = true; $('status').textContent = status(); } };
    eng.postMessage('uci'); eng.postMessage('isready');
  } catch { $('status').textContent = 'Engine failed to load: the bot will play random moves.'; }
}
$('elo').oninput = () => { $('elov').textContent = $('elo').value; $('botname').textContent = botName(); };
$('new').onclick = newGame;
$('flip').onclick = () => { flip = !flip; render(); };
$('undo').onclick = () => { if (busy) return; game.undo(); if (game.turn() !== me) game.undo(); sel = null; render(); $('status').textContent = status(); };
$('submitpgn').onclick = () => { localStorage.setItem('gotham_pgn', game.pgn()); location.href = '/guess'; };
newGame(); initEngine();
