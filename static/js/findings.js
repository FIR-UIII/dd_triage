/* ---------- Индекс карточек (строится один раз, без сетевых вызовов) ---------- */

const cards = Array.from(document.querySelectorAll('.finding-card'));
const index = cards.map(el => ({
  el,
  id: el.dataset.id,
  title:  (el.dataset.title  || '').toLowerCase(),
  path:   (el.dataset.path   || '').toLowerCase(),
  notes:  (el.dataset.notes  || '').toLowerCase(),
  triage: (el.dataset.triage || '').toLowerCase(),
}));
const selected = new Set();   // id выбранных сработок
const doneIds  = new Set();   // id уже обработанных

let filtered = index.slice();
let page = 1;
let pageSize = 25;

/* ---------- Прогресс ---------- */

const totalCards = index.length;
let doneCount = 0;

function updateProgress() {
  const bar = document.getElementById('progress-bar');
  const label = document.getElementById('progress-label');
  const pct = totalCards ? Math.round(doneCount / totalCards * 100) : 0;
  bar.style.width = pct + '%';
  label.textContent = `${doneCount} / ${totalCards} обработано`;
}
updateProgress();

function markDone(id) {
  id = String(id);
  const card = document.getElementById('card-' + id);
  if (card && !card.classList.contains('done')) {
    card.classList.add('done');
    card.classList.remove('selected');
    doneIds.add(id);
    doneCount++;
    updateProgress();
  }
  if (selected.delete(id)) {
    const cb = card && card.querySelector('.card-check');
    if (cb) cb.checked = false;
    updateBulkBar();
  }
  syncSelectAll();
}

/* ---------- Фильтрация ---------- */

const qInput      = document.getElementById('filter-query');
const fieldChecks = Array.from(document.querySelectorAll('.field-check'));
const pageSelect  = document.getElementById('page-size');
const selectAllCb = document.getElementById('select-all');

function activeFields() {
  return fieldChecks.filter(c => c.checked).map(c => c.value);
}

function applyFilter() {
  const words  = qInput.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const fields = activeFields();

  if (!words.length) {
    filtered = index.slice();
  } else if (!fields.length) {
    filtered = [];
  } else {
    // OR: карточка подходит, если совпало хотя бы одно слово запроса
    filtered = index.filter(it => {
      const hay = fields.map(f => it[f]).join(' \n ');
      return words.some(w => hay.includes(w));
    });
  }
  page = 1;
  render();
}

let filterTimer = null;
qInput.addEventListener('input', () => {
  clearTimeout(filterTimer);
  filterTimer = setTimeout(applyFilter, 120);
});
fieldChecks.forEach(c => c.addEventListener('change', applyFilter));
document.getElementById('filter-clear').addEventListener('click', () => {
  qInput.value = '';
  fieldChecks.forEach(c => c.checked = true);
  applyFilter();
  qInput.focus();
});
pageSelect.addEventListener('change', () => {
  pageSize = parseInt(pageSelect.value, 10) || 0;
  page = 1;
  render();
});

/* ---------- Рендер списка + пагинация ---------- */

function pageCount() {
  if (!pageSize) return 1;
  return Math.max(1, Math.ceil(filtered.length / pageSize));
}

function render() {
  const pages = pageCount();
  if (page > pages) page = pages;

  const start = pageSize ? (page - 1) * pageSize : 0;
  const shown = pageSize ? filtered.slice(start, start + pageSize) : filtered;
  const visible = new Set(shown.map(it => it.el));

  index.forEach(it => { it.el.style.display = visible.has(it.el) ? '' : 'none'; });

  document.getElementById('empty-state').style.display = filtered.length ? 'none' : '';

  const from = filtered.length ? start + 1 : 0;
  const to   = start + shown.length;
  document.getElementById('filter-count').textContent =
    filtered.length === index.length
      ? `Показано ${from}–${to} из ${index.length}`
      : `Показано ${from}–${to} из ${filtered.length} найденных (всего ${index.length})`;

  renderPager(pages);
  syncSelectAll();
}

function renderPager(pages) {
  const pager = document.getElementById('pager');
  pager.innerHTML = '';
  if (!pageSize || pages <= 1) return;

  const mkBtn = (label, targetPage, opts = {}) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    if (opts.disabled) b.disabled = true;
    if (opts.active) b.classList.add('active');
    if (!opts.disabled && !opts.active) {
      b.addEventListener('click', () => {
        page = targetPage;
        render();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
    pager.appendChild(b);
  };
  const mkGap = () => {
    const s = document.createElement('span');
    s.className = 'gap';
    s.textContent = '…';
    pager.appendChild(s);
  };

  mkBtn('←', page - 1, { disabled: page === 1 });

  const nums = new Set([1, pages, page, page - 1, page + 1, page - 2, page + 2]);
  const list = [...nums].filter(n => n >= 1 && n <= pages).sort((a, b) => a - b);
  let prev = 0;
  list.forEach(n => {
    if (prev && n - prev > 1) mkGap();
    mkBtn(String(n), n, { active: n === page });
    prev = n;
  });

  mkBtn('→', page + 1, { disabled: page === pages });
}

/* ---------- Выделение ---------- */

document.addEventListener('change', e => {
  const cb = e.target.closest('.card-check');
  if (!cb) return;
  const id = cb.dataset.id;
  const card = document.getElementById('card-' + id);
  if (cb.checked) { selected.add(id); card && card.classList.add('selected'); }
  else            { selected.delete(id); card && card.classList.remove('selected'); }
  updateBulkBar();
  syncSelectAll();
});

function selectableFiltered() {
  return filtered.filter(it => !doneIds.has(it.id));
}

selectAllCb.addEventListener('change', () => {
  const targets = selectableFiltered();
  targets.forEach(it => {
    const cb = it.el.querySelector('.card-check');
    if (selectAllCb.checked) {
      selected.add(it.id);
      it.el.classList.add('selected');
      if (cb) cb.checked = true;
    } else {
      selected.delete(it.id);
      it.el.classList.remove('selected');
      if (cb) cb.checked = false;
    }
  });
  updateBulkBar();
  syncSelectAll();
});

document.getElementById('select-none').addEventListener('click', () => {
  selected.clear();
  index.forEach(it => {
    it.el.classList.remove('selected');
    const cb = it.el.querySelector('.card-check');
    if (cb) cb.checked = false;
  });
  updateBulkBar();
  syncSelectAll();
});

function syncSelectAll() {
  const targets = selectableFiltered();
  const picked = targets.filter(it => selected.has(it.id)).length;
  selectAllCb.checked = targets.length > 0 && picked === targets.length;
  selectAllCb.indeterminate = picked > 0 && picked < targets.length;
}

function updateBulkBar() {
  const bar = document.getElementById('bulk-bar');
  const n = selected.size;
  document.getElementById('bulk-count').textContent = `Выбрано: ${n}`;
  bar.classList.toggle('show', n > 0);
  if (!n) document.getElementById('bulk-progress').textContent = '';
}

function toast(msg, ok) {
  const el = document.createElement('div');
  el.className = 'toast-msg ' + (ok ? 'toast-ok' : 'toast-err');
  el.textContent = msg;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

async function apiCall(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return r.json();
}

async function doAccept(id) {
  const data = await apiCall(`/api/accept/${id}`, {});
  toast(data.message, data.status === 'ok');
  if (data.status === 'ok') markDone(id);
}

async function doReject(id) {
  const reason = document.getElementById('reject-reason-' + id).value.trim();
  if (!reason) {
    toast('Введите обоснование отклонения.', false);
    document.getElementById('reject-reason-' + id).focus();
    return;
  }
  const data = await apiCall(`/api/reject/${id}`, { reason });
  toast(data.message, data.status === 'ok');
  if (data.status === 'ok') markDone(id);
}

async function doCorrect(id) {
  const comment = document.getElementById('correct-comment-' + id).value.trim();
  if (!comment) {
    toast('Введите комментарий для DD.', false);
    document.getElementById('correct-comment-' + id).focus();
    return;
  }
  const data = await apiCall(`/api/correct/${id}`, { comment });
  toast(data.message, data.status === 'ok');
  if (data.status === 'ok') markDone(id);
}

/* ---------- Массовые действия ---------- */

const BULK_CONCURRENCY = 3;

async function bulkRun(kind) {
  const ids = [...selected].filter(id => !doneIds.has(id));
  if (!ids.length) { toast('Ничего не выбрано.', false); return; }

  let body = {};
  if (kind === 'reject') {
    const el = document.getElementById('bulk-reject-reason');
    const reason = el.value.trim();
    if (!reason) { toast('Введите обоснование отклонения.', false); el.focus(); return; }
    body = { reason };
  } else if (kind === 'correct') {
    const el = document.getElementById('bulk-correct-comment');
    const comment = el.value.trim();
    if (!comment) { toast('Введите комментарий для DD.', false); el.focus(); return; }
    body = { comment };
  }

  const labels = { accept: 'Accept', reject: 'Reject', correct: 'Correct' };
  if (!confirm(`Применить «${labels[kind]}» к ${ids.length} сработкам?`)) return;

  const bar = document.getElementById('bulk-bar');
  const progress = document.getElementById('bulk-progress');
  bar.classList.add('busy');

  const queue = ids.slice();
  let ok = 0, fail = 0, done = 0;
  const errors = [];

  const worker = async () => {
    while (queue.length) {
      const id = queue.shift();
      try {
        const data = await apiCall(`/api/${kind}/${id}`, body);
        if (data.status === 'ok') { ok++; markDone(id); }
        else { fail++; errors.push(`${id}: ${data.message || 'ошибка'}`); }
      } catch (e) {
        fail++; errors.push(`${id}: ${e}`);
      }
      done++;
      progress.textContent = `${done} / ${ids.length} — ok: ${ok}, ошибок: ${fail}`;
    }
  };

  await Promise.all(Array.from({ length: Math.min(BULK_CONCURRENCY, ids.length) }, worker));

  bar.classList.remove('busy');
  toast(`${labels[kind]}: успешно ${ok}, ошибок ${fail}.`, fail === 0);
  if (errors.length) console.warn('Ошибки массовой операции:', errors);
  syncSelectAll();
}

/* ---------- Старт ---------- */
pageSize = parseInt(pageSelect.value, 10) || 0;
render();
