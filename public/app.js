/* ============================================================
   Industry Risk Radar — app logic
   ============================================================ */
const DATA = window.__RISK_DATA__;

const BAND = {
  low:      { fill: '#82DCBE', text: 'var(--low)',  label: 'Low' },
  moderate: { fill: '#FFC864', text: 'var(--mod)',  label: 'Moderate' },
  elevated: { fill: '#FF705A', text: 'var(--elev)', label: 'Elevated' },
  high:     { fill: '#FF585D', text: 'var(--high)', label: 'High' },
};
// short axis labels for the radar
const SHORT = {
  regulatory: 'Regulatory', financial: 'Financial', operational: 'Operational',
  cyber: 'Cyber & data', environmental: 'Environmental', governance: 'Governance',
  product: 'Product & safety', labor: 'Labour',
};

let current = null, selMonth = DATA.current_month, regWin = '3-6m', radar = null, trendChart = null;

const bandFromScore = (s) => s >= 80 ? 'high' : s >= 60 ? 'elevated' : s >= 40 ? 'moderate' : 'low';
const ctx = () => DATA.months[selMonth];
const isCurrentMonth = () => selMonth === DATA.current_month;
function ensureBands() { ctx().industries.forEach(i => { i.band = i.band || bandFromScore(i.risk_score); }); }

const fmt = (n) => n.toLocaleString('en-US');
const compact = (n) => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'k' : '' + n;
// event magnitude: always 1 decimal for thousands -> "13.2k", "5.6k", "980"
const magfmt = (n) => n >= 1000 ? (n / 1000).toFixed(1) + 'k' : '' + n;
const ind = () => ctx().industries.find(i => i.key === current);
const ranked = () => [...ctx().industries].sort((a, b) => b.risk_score - a.risk_score);

/* ---- tiny inline sparkline ---- */
function sparkline(values, color) {
  const w = 54, h = 22, p = 2;
  const min = Math.min(...values), max = Math.max(...values), span = (max - min) || 1;
  const pts = values.map((v, i) => {
    const x = p + (i / (values.length - 1)) * (w - p * 2);
    const y = h - p - ((v - min) / span) * (h - p * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const lastX = w - p, lastY = h - p - ((values.at(-1) - min) / span) * (h - p * 2);
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" fill="none">
    <polyline points="${pts}" stroke="${color}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" opacity=".85"/>
    <circle cx="${lastX}" cy="${lastY.toFixed(1)}" r="2" fill="${color}"/></svg>`;
}

function deltaHTML(d, mono) {
  if (d === null || d === undefined) return '';
  const flat = d === 0, up = d > 0;
  const arrow = flat ? '±' : (up ? '▲' : '▼');
  const col = flat ? 'var(--ink-3)' : (up ? 'var(--high)' : 'var(--low)');
  return `<span style="color:${col}">${arrow} ${up ? '+' : ''}${d}</span>`;
}

/* ============ RISK INDEX RAIL ============ */
function buildRail() {
  const el = document.getElementById('rail');
  document.getElementById('railCount').textContent = ctx().industries.length + ' industries';
  el.innerHTML = '';
  ranked().forEach((i, n) => {
    const b = BAND[i.band];
    const row = document.createElement('div');
    row.className = 'rrow' + (i.key === current ? ' on' : '');
    row.innerHTML = `
      <span class="rank">${String(n + 1).padStart(2, '0')}</span>
      <div>
        <div class="nm">${i.label}</div>
        <div class="sub">${i.sector_note}</div>
      </div>
      <div class="met">
        ${sparkline(i.trend.values, b.fill)}
        <div class="scwrap">
          <span class="sc" style="color:${b.text}">${i.risk_score}</span>
          <span class="dl">${deltaHTML(i.delta)}</span>
        </div>
      </div>`;
    row.onclick = () => { current = i.key; buildRail(); renderDetail(); };
    el.appendChild(row);
  });
}

/* ============ HERO / DETAIL ============ */
function renderDetail() {
  const d = ind(), b = BAND[d.band];

  document.getElementById('hName').textContent = d.label;
  document.getElementById('hSub').textContent = d.sector_note;

  // provenance — quiet, brand-forward, no daily timestamp
  const prov = document.getElementById('prov');
  const ls = ctx().live_sector, cur = isCurrentMonth();
  if (d.seed) {
    prov.className = 'prov sample';
    prov.innerHTML = `<span class="d" style="background:var(--mod)"></span>${cur ? 'Sample sector · live on next refresh' : 'Sample sector'}`;
  } else if (d.key === ls && cur) {
    prov.className = 'prov livep';
    prov.innerHTML = `<span class="d" style="background:var(--low)"></span>Live · Signal AI data`;
  } else {
    prov.className = 'prov livep';
    prov.innerHTML = `<span class="d" style="background:var(--low)"></span>Signal AI data${cur ? '' : ' · ' + ctx().label}`;
  }

  // score (animated count-up) + band + delta
  animateNumber(document.getElementById('score'), d.risk_score, b.text);
  const band = document.getElementById('band');
  band.textContent = b.label + ' risk'; band.style.color = b.text;
  document.getElementById('delta').innerHTML = deltaHTML(d.delta) + ' <span style="color:var(--ink-3)">vs last month</span>';

  // mini stats
  document.getElementById('ministats').innerHTML = `
    <div class="ms"><div class="v">${compact(d.volume_total)}</div><div class="k">Risk mentions, 30 days</div></div>
    <div class="ms"><div class="v" style="color:var(--high)">${Math.round(d.sentiment_neg * 100)}%</div><div class="k">Negative coverage share</div></div>
    <div class="ms"><div class="v">${d.events.length}</div><div class="k">Standout events</div></div>`;

  renderRadar(d);
  renderBars(d, b);
  renderTrend(d);
  renderEvents(d);
  renderReg();
}

function animateNumber(el, to, color) {
  el.style.color = color;
  const from = parseInt(el.textContent) || 0;
  el.textContent = to;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || from === to) return;
  const steps = 30, dt = 18; let n = 0;
  const id = setInterval(() => {
    n++; const k = n / steps, e = 1 - Math.pow(1 - k, 3);
    el.textContent = Math.round(from + (to - from) * e);
    if (n >= steps) { el.textContent = to; clearInterval(id); }
  }, dt);
}

/* ============ RADAR ============ */
function renderRadar(d) {
  const ctx = document.getElementById('radar');
  const labels = d.categories.map(c => SHORT[c.key] || c.label);
  const values = d.categories.map(c => c.score);
  if (radar) radar.destroy();
  radar = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        data: values,
        fill: true,
        backgroundColor: 'rgba(255,88,93,.13)',
        borderColor: '#FF585D',
        borderWidth: 2,
        pointBackgroundColor: '#FF585D',
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
        pointRadius: 3.5,
        pointHoverRadius: 5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      animation: { duration: 650, easing: 'easeOutCubic' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#2F2F2F', padding: 10, cornerRadius: 8, displayColors: false,
          titleFont: { family: 'Poppins', weight: '600', size: 12 },
          bodyFont: { family: 'JetBrains Mono', size: 12 },
          callbacks: { label: (c) => `Intensity ${c.raw} / 100` },
        },
      },
      scales: {
        r: {
          min: 0, max: 100,
          angleLines: { color: 'rgba(47,47,47,.08)' },
          grid: { color: 'rgba(47,47,47,.09)' },
          ticks: {
            stepSize: 25, backdropColor: 'transparent', color: '#A9A69C',
            font: { family: 'JetBrains Mono', size: 9 }, showLabelBackdrop: false,
          },
          pointLabels: {
            color: '#5A5853', font: { family: 'Poppins', size: 11.5, weight: '500' },
          },
        },
      },
    },
  });
}

/* ============ CATEGORY BARS ============ */
function renderBars(d, b) {
  const el = document.getElementById('bars');
  el.innerHTML = '';
  [...d.categories].sort((a, c) => c.score - a.score).forEach(c => {
    const cb = BAND[c.band];
    const row = document.createElement('div');
    row.className = 'crow';
    row.innerHTML = `
      <div class="ct"><span class="cl">${c.label}</span><span class="cv">${compact(c.volume)} · ${c.score}</span></div>
      <div class="ctrack"><div class="cfill" style="background:${cb.fill};width:${c.score}%"></div></div>`;
    el.appendChild(row);
  });
}

/* ============ TREND ============ */
function renderTrend(d) {
  const ctx = document.getElementById('trend');
  if (trendChart) trendChart.destroy();
  const grd = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
  grd.addColorStop(0, 'rgba(255,88,93,.18)');
  grd.addColorStop(1, 'rgba(255,88,93,0)');
  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: d.trend.weeks.map(w => w.slice(5).replace('-', '/')),
      datasets: [{
        data: d.trend.values, borderColor: '#FF585D', backgroundColor: grd,
        fill: true, tension: .38, borderWidth: 2.4,
        pointRadius: 0, pointHoverRadius: 4, pointHoverBackgroundColor: '#FF585D', pointHoverBorderColor: '#fff',
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 700, easing: 'easeOutCubic' },
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#2F2F2F', padding: 10, cornerRadius: 8, displayColors: false,
          titleFont: { family: 'JetBrains Mono', size: 11 }, bodyFont: { family: 'JetBrains Mono', size: 12 },
          callbacks: { label: (c) => `${c.raw} risk events` },
        },
      },
      scales: {
        y: {
          beginAtZero: true, border: { display: false },
          grid: { color: 'rgba(47,47,47,.07)' },
          ticks: { color: '#A9A69C', font: { family: 'JetBrains Mono', size: 10 }, maxTicksLimit: 5 },
        },
        x: {
          border: { display: false }, grid: { display: false },
          ticks: { color: '#A9A69C', font: { family: 'JetBrains Mono', size: 10 }, maxRotation: 0, autoSkipPadding: 14 },
        },
      },
    },
  });
}

/* ============ EVENTS ============ */
function renderEvents(d) {
  const el = document.getElementById('events');
  el.innerHTML = '';
  if (!d.events || !d.events.length) { el.innerHTML = '<div class="empty">No standout risk events this period.</div>'; return; }
  d.events.forEach(e => {
    const cats = (e.categories || []).map(k => (d.categories.find(x => x.key === k) || {}).label || k);
    const link = e.article_id ? `https://article.signal-ai.com/${e.article_id}` : null;
    const row = document.createElement('div');
    row.className = 'ev';
    row.innerHTML = `
      <div class="mag"><b>${magfmt(e.magnitude)}×</b><s>spike</s></div>
      <div>
        <div class="et">${link ? `<a href="${link}" target="_blank" rel="noopener">${e.title}</a>` : e.title}</div>
        <div class="emeta">${e.date} · ${fmt(e.sources)} sources · ${fmt(e.stories)} stories</div>
        <div class="chips">
          ${(e.entities || []).map(x => `<span class="chip">${x}</span>`).join('')}
          ${cats.map(x => `<span class="chip cat">${x}</span>`).join('')}
        </div>
      </div>`;
    el.appendChild(row);
  });
}

/* ============ REGULATION ============ */
function renderReg() {
  const el = document.getElementById('regList');
  el.innerHTML = '';
  const items = (ctx().regulatory[current] || []).filter(r => r.window === regWin);
  if (!items.length) {
    el.innerHTML = `<div class="empty">No tracked items in this window for ${ind().label}.<br>Added during the monthly review.</div>`;
    return;
  }
  items.forEach(r => {
    const row = document.createElement('div');
    row.className = 'reg';
    row.innerHTML = `
      <div class="rt">${r.name}</div>
      <div class="rmeta">
        <span class="jur">${r.jurisdiction}</span>
        <span class="rdate">${r.window === '3-6m' ? 'Effective' : 'Deadline'} ${r.effective_date}</span>
      </div>
      <div class="rsum">${r.summary} ${r.source ? `<a href="${r.source}">Source →</a>` : ''}</div>`;
    el.appendChild(row);
  });
}
document.querySelectorAll('.seg').forEach(btn => {
  btn.onclick = () => {
    regWin = btn.dataset.win;
    document.querySelectorAll('.seg').forEach(s => s.classList.toggle('on', s === btn));
    renderReg();
  };
});

/* ============ ENTRANCE REVEAL ============ */
function reveal() {
  const items = [...document.querySelectorAll('.reveal')];
  items.forEach((el, i) => { el.style.animationDelay = Math.min(i * 70, 420) + 'ms'; });
}

/* ============ MONTH PICKER ============ */
function buildMonthSelect() {
  const sel = document.getElementById('period');
  sel.innerHTML = '';
  Object.keys(DATA.months).sort().reverse().forEach(k => {
    const o = document.createElement('option');
    o.value = k; o.textContent = DATA.months[k].label;
    if (k === selMonth) o.selected = true;
    sel.appendChild(o);
  });
  sel.onchange = () => {
    selMonth = sel.value;
    ensureBands();
    if (!ind()) current = ctx().live_sector || ranked()[0].key;
    updateMasthead(); buildRail(); renderDetail();
  };
}

function updateMasthead() {
  const li = document.getElementById('liveInd');
  li.innerHTML = isCurrentMonth()
    ? '<span class="pulse"></span>Live feed'
    : '<span class="dot-static"></span>Archived snapshot';
  document.getElementById('footAsOf').textContent = 'Snapshot · ' + ctx().label;
}

/* ============ BOOT ============ */
function boot() {
  if (!DATA) { document.body.innerHTML = '<p style="padding:40px;font-family:sans-serif">Could not load data.js.</p>'; return; }
  ensureBands();
  current = ctx().live_sector || ranked()[0].key;
  buildMonthSelect();
  updateMasthead();
  buildRail();
  renderDetail();
  reveal();
}
boot();
