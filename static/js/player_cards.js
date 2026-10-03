function drawHeatmap(canvas, grid) {
  const ctx = canvas.getContext('2d');
  const rows = grid.length, cols = grid[0].length;
  const max = Math.max(...grid.flat(), 1);
  const cw = canvas.width / cols, ch = canvas.height / rows;
  ctx.fillStyle = '#1f6b3a'; ctx.fillRect(0, 0, canvas.width, canvas.height);
  grid.forEach((row, j) => row.forEach((v, i) => {
    ctx.fillStyle = `rgba(255, 60, 30, ${(v / max) * 0.85})`;
    ctx.fillRect(i * cw, j * ch, cw, ch);
  }));
  ctx.strokeStyle = '#fff8'; ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);
  ctx.beginPath(); ctx.moveTo(canvas.width / 2, 0); ctx.lineTo(canvas.width / 2, canvas.height); ctx.stroke();
}

async function loadCard(id) {
  const s = await api(`/api/player/${id}/stats`);
  document.getElementById('c-rating').textContent = s.rating ?? '--';
  document.getElementById('c-pos').textContent = s.position || 'OYN';
  document.getElementById('c-name').textContent = s.player_name;
  const phy = Math.min(99, Math.round((s.distance_covered || 0) / 3000 * 99));
  const pos = s.coverage == null ? '--' : Math.round(s.coverage * 99);
  const stats = [['PHY', phy], ['POS', pos], ['PAS', '--'], ['SHO', '--'], ['DEF', '--'], ['DRI', '--']];
  const box = document.getElementById('c-stats');
  for (const [k, v] of stats) { const sp = el('span'); sp.append(el('b', v), k); box.append(sp); }
  document.getElementById('card').hidden = false;
  if (s.heatmap) drawHeatmap(document.getElementById('heatmap'), s.heatmap);
}

loadCard(window.PLAYER_ID).catch(e => {
  const err = document.getElementById('error'); err.hidden = false; err.textContent = e.message;
});
