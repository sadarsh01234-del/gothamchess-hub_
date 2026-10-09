const log = document.getElementById('log'), inp = document.getElementById('m');
function add(cls, text) { const p = document.createElement('p'); p.className = cls; p.textContent = text; log.appendChild(p); log.scrollTop = log.scrollHeight; }
async function ask(q) {
  add('me', q);
  try {
    const r = await fetch('/api/coach', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: q }) });
    add('bot', (await r.json()).reply);
  } catch { add('bot', 'The Bat-line is down. Try again.'); }
}
document.getElementById('cf').addEventListener('submit', e => { e.preventDefault(); if (inp.value.trim()) { ask(inp.value.trim()); inp.value = ''; } });
document.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => ask(b.textContent)));
