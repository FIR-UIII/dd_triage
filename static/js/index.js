/* Экран ввода: вкладки, счётчик ID, загрузка файла.
   Вкладки реализованы локально — внешних библиотек нет. */

/* ---------- Вкладки ---------- */

const tabButtons = Array.from(document.querySelectorAll('[data-tab-target]'));

function showTab(btn) {
  const pane = document.querySelector(btn.dataset.tabTarget);
  if (!pane) return;

  tabButtons.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('show', 'active'));
  pane.classList.add('active');
  // show ставим следующим кадром, чтобы сработал transition у .fade
  requestAnimationFrame(() => pane.classList.add('show'));
}

tabButtons.forEach(btn => btn.addEventListener('click', () => showTab(btn)));

/* ---------- Счётчик ID ---------- */

const ta = document.getElementById('finding_ids');
const btnIds = document.getElementById('btn-ids');

ta.addEventListener('input', () => {
  const ids = ta.value.split('\n').filter(l => l.trim().match(/^\d+$/));
  btnIds.textContent = ids.length
    ? `Загрузить ${ids.length} сработок →`
    : 'Загрузить сработки →';
});

/* ---------- Загрузка файла ---------- */

const fileInput = document.getElementById('jsonl_file');
const fileName = document.getElementById('file-name');
const btnUpload = document.getElementById('btn-upload');
const uploadZone = document.getElementById('upload-zone');

uploadZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) {
    fileName.textContent = fileInput.files[0].name;
    btnUpload.disabled = false;
  }
});

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag');
  const dt = e.dataTransfer;
  if (dt.files.length) {
    fileInput.files = dt.files;
    fileName.textContent = dt.files[0].name;
    btnUpload.disabled = false;
  }
});
