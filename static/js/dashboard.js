async function loadMatches() {
  const { matches } = await api('/api/dashboard');
  const tbody = document.querySelector('#matches tbody');
  tbody.replaceChildren();
  document.getElementById('empty').hidden = matches.length > 0;
  for (const m of matches) {
    const tr = el('tr');
    tr.append(el('td', m.id), el('td', (m.date || '').slice(0, 16)),
      el('td', `${m.team1} - ${m.team2}`), el('td', m.processed ? 'İşlendi' : 'Bekliyor'));
    const actions = el('td');
    if (m.processed) {
      actions.append(el('a', 'Detay', { href: `/match/${m.id}` }));
    } else {
      const btn = el('button', 'İşle');
      btn.onclick = async () => {
        btn.disabled = true; btn.textContent = 'İşleniyor...';
        try { await api('/api/process-match', jsonPost({ match_id: m.id })); }
        catch (e) { alert(e.message); }
        loadMatches();
      };
      actions.append(btn);
    }
    tr.append(actions);
    tbody.append(tr);
  }
}

function jsonPost(body) {
  return { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
}

async function loadMatchDetail(id) {
  const [match, players] = await Promise.all([api(`/api/match/${id}`), api(`/api/match/${id}/players`)]);
  document.getElementById('match-title').textContent = `${match.team1} - ${match.team2}`;
  document.getElementById('match-meta').textContent = [match.venue, (match.date || '').slice(0, 16)].filter(Boolean).join(' · ');
  document.getElementById('empty').hidden = players.length > 0;
  const tbody = document.querySelector('#players tbody');
  for (const p of players) {
    const tr = el('tr');
    const name = el('td'); name.append(el('a', p.player_name, { href: `/player/${p.player_id}` }));
    tr.append(name, el('td', p.rating ?? '--'), el('td', Math.round(p.distance_covered ?? 0)),
      el('td', p.coverage == null ? '--' : `${Math.round(p.coverage * 100)}%`));
    tbody.append(tr);
  }
  if (players.length && window.Chart) {
    new Chart(document.getElementById('ratings-chart'), {
      type: 'bar',
      data: { labels: players.map(p => p.player_name),
        datasets: [{ label: 'Puan', data: players.map(p => p.rating ?? 0), backgroundColor: '#d9a82c' }] },
      options: { scales: { y: { min: 0, max: 99 } } },
    });
  }
}

const form = document.getElementById('upload-form');
if (form) {
  form.onsubmit = async (e) => {
    e.preventDefault();
    const msg = document.getElementById('upload-msg');
    msg.textContent = 'Yükleniyor...';
    try {
      await api('/api/upload-video', { method: 'POST', body: new FormData(form) });
      msg.textContent = 'Yüklendi.'; form.reset(); loadMatches();
    } catch (err) { msg.textContent = err.message; }
  };
  loadMatches();
}
if (window.MATCH_ID) loadMatchDetail(window.MATCH_ID).catch(e => { document.getElementById('empty').hidden = false; document.getElementById('empty').textContent = e.message; });
