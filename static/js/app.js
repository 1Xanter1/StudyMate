const API = {
  tasks: '/api/tasks',
  sessions: '/api/sessions',
  flashcards: '/api/flashcards',
  review: '/api/flashcards/review',
  progress: '/api/progress',
};

let currentSort = 'deadline';
let reviewQueue = [];
let reviewIndex = 0;
let cardFlipped = false;
let timerSeconds = 25 * 60;
let timerTotal = 25 * 60;
let timerInterval = null;
let timerRunning = false;
let sessionStartTime = null;
const CIRCUMFERENCE = 2 * Math.PI * 70;

document.addEventListener('DOMContentLoaded', () => {
  initTasks();
  initTimer();
  initFlashcards();
  loadProgress();
  loadTasks();
  loadSessions();
  loadFlashcards();
});

function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2200);
}

async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) throw new Error('API error');
  return res.json();
}

async function loadProgress() {
  try {
    const p = await api(API.progress);
    document.getElementById('statCompleted').textContent = p.completed_tasks;
    document.getElementById('statMinutes').textContent = p.total_focus_minutes;
    document.getElementById('statSessions').textContent = p.total_sessions;
    document.getElementById('statReviews').textContent = p.total_reviews;
    document.getElementById('pendingCount').textContent = p.pending_tasks;
    document.getElementById('dueCount').textContent = p.flashcards_due;
    document.getElementById('totalCardsCount').textContent = p.total_flashcards;
    document.getElementById('taskProgressBar').style.width = `${p.progress_percent || 0}%`;
  } catch (_) {}
}

function initTasks() {
  document.getElementById('taskForm').addEventListener('submit', async e => {
    e.preventDefault();
    const title = document.getElementById('taskTitle').value.trim();
    if (!title) return;
    await api(API.tasks, {
      method: 'POST',
      body: JSON.stringify({
        title,
        priority: document.getElementById('taskPriority').value,
        deadline: document.getElementById('taskDeadline').value || null,
      }),
    });
    e.target.reset();
    toast('Задача добавлена');
    loadTasks();
    loadProgress();
  });

  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSort = btn.dataset.sort;
      loadTasks();
    });
  });

  document.getElementById('editForm').addEventListener('submit', async e => {
    e.preventDefault();
    const id = document.getElementById('editId').value;
    await api(`${API.tasks}/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: document.getElementById('editTitle').value,
        priority: document.getElementById('editPriority').value,
        deadline: document.getElementById('editDeadline').value || null,
      }),
    });
    closeEditModal();
    loadTasks();
  });

  document.getElementById('editCancel').addEventListener('click', closeEditModal);
  document.querySelector('.modal-backdrop')?.addEventListener('click', closeEditModal);
}

async function loadTasks() {
  try {
    const tasks = await api(`${API.tasks}?sort=${currentSort}`);
    const list = document.getElementById('taskList');
    const empty = document.getElementById('emptyTasks');
    list.innerHTML = '';
    if (!tasks.length) {
      empty.classList.remove('hidden');
      return;
    }
    empty.classList.add('hidden');
    const labels = { high: 'Выс', medium: 'Ср', low: 'Низ' };
    const today = new Date().toISOString().slice(0, 10);
    tasks.forEach(task => {
      const li = document.createElement('li');
      li.className = `task-item${task.completed ? ' completed' : ''}`;
      const overdue = task.deadline && task.deadline < today && !task.completed;
      li.innerHTML = `
        <div class="task-check" data-id="${task.id}">${task.completed ? '✓' : ''}</div>
        <div class="task-body">
          <div class="task-title">${escapeHtml(task.title)}</div>
          <div class="task-meta">
            <span class="priority-badge priority-${task.priority}">${labels[task.priority]}</span>
            ${task.deadline ? `<span class="deadline-badge${overdue ? ' deadline-overdue' : ''}">${formatDate(task.deadline)}</span>` : ''}
          </div>
        </div>
        <div class="task-actions">
          <button type="button" data-edit="${task.id}">✎</button>
          <button type="button" data-del="${task.id}">✕</button>
        </div>
      `;
      list.appendChild(li);
    });
    list.querySelectorAll('.task-check').forEach(el => {
      el.addEventListener('click', async () => {
        await api(`${API.tasks}/${el.dataset.id}/toggle`, { method: 'POST' });
        loadTasks();
        loadProgress();
      });
    });
    list.querySelectorAll('[data-edit]').forEach(btn => {
      btn.addEventListener('click', () => openEditModal(tasks.find(t => t.id == btn.dataset.edit)));
    });
    list.querySelectorAll('[data-del]').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (confirm('Удалить?')) {
          await api(`${API.tasks}/${btn.dataset.del}`, { method: 'DELETE' });
          loadTasks();
          loadProgress();
        }
      });
    });
  } catch (_) {}
}

function openEditModal(task) {
  document.getElementById('editId').value = task.id;
  document.getElementById('editTitle').value = task.title;
  document.getElementById('editPriority').value = task.priority;
  document.getElementById('editDeadline').value = task.deadline || '';
  document.getElementById('editModal').classList.remove('hidden');
}

function closeEditModal() {
  document.getElementById('editModal').classList.add('hidden');
}

function getTimerMinutes() {
  const val = parseInt(document.getElementById('timerMinutes').value, 10);
  return Math.min(180, Math.max(1, val || 25));
}

function initTimer() {
  const ring = document.getElementById('ringProgress');
  if (ring) {
    ring.style.stroke = 'var(--primary)';
    ring.style.strokeDasharray = CIRCUMFERENCE;
    ring.style.strokeDashoffset = '0';
  }

  document.getElementById('timerForm').addEventListener('submit', e => {
    e.preventDefault();
    if (timerRunning) return;
    applyTimerFromInput();
    startTimer();
  });

  document.getElementById('timerMinutes').addEventListener('input', () => {
    if (!timerRunning) applyTimerFromInput();
  });

  document.getElementById('timerPause').addEventListener('click', pauseTimer);
  document.getElementById('timerReset').addEventListener('click', () => {
    pauseTimer();
    applyTimerFromInput();
    sessionStartTime = null;
  });

  applyTimerFromInput();
}

function applyTimerFromInput() {
  const mins = getTimerMinutes();
  timerSeconds = mins * 60;
  timerTotal = timerSeconds;
  updateTimerUI();
}

function updateTimerUI() {
  const m = Math.floor(timerSeconds / 60);
  const s = timerSeconds % 60;
  document.getElementById('timerDisplay').textContent =
    `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  const ring = document.getElementById('ringProgress');
  if (ring && timerTotal > 0) {
    ring.style.strokeDashoffset = CIRCUMFERENCE * (1 - timerSeconds / timerTotal);
    ring.style.stroke = 'var(--primary)';
  }
}

function startTimer() {
  if (timerRunning) return;
  timerRunning = true;
  if (!sessionStartTime) sessionStartTime = new Date().toISOString();
  document.getElementById('timerStart').disabled = true;
  document.getElementById('timerPause').disabled = false;
  document.getElementById('timerMinutes').disabled = true;
  timerInterval = setInterval(() => {
    if (timerSeconds <= 0) {
      onTimerComplete();
      return;
    }
    timerSeconds--;
    updateTimerUI();
  }, 1000);
}

function pauseTimer() {
  timerRunning = false;
  clearInterval(timerInterval);
  document.getElementById('timerStart').disabled = false;
  document.getElementById('timerPause').disabled = true;
  document.getElementById('timerMinutes').disabled = false;
}

async function onTimerComplete() {
  pauseTimer();
  const mins = getTimerMinutes();
  try {
    await api(API.sessions, {
      method: 'POST',
      body: JSON.stringify({
        duration_seconds: mins * 60,
        session_type: 'focus',
        started_at: sessionStartTime || new Date().toISOString(),
      }),
    });
    toast('Сессия завершена');
    loadSessions();
    loadProgress();
  } catch (_) {}
  sessionStartTime = null;
  applyTimerFromInput();
}

async function loadSessions() {
  try {
    const sessions = await api(`${API.sessions}?limit=8`);
    ['sessionHistory', 'recentSessions'].forEach(elId => {
      const el = document.getElementById(elId);
      if (!el) return;
      el.innerHTML = '';
      if (!sessions.length) return;
      sessions.forEach(s => {
        const li = document.createElement('li');
        const mins = Math.round(s.duration_seconds / 60);
        li.innerHTML = `<span>${mins} мин</span><span>${formatDateTime(s.completed_at)}</span>`;
        el.appendChild(li);
      });
    });
  } catch (_) {}
}

function initFlashcards() {
  document.getElementById('cardForm').addEventListener('submit', async e => {
    e.preventDefault();
    const front = document.getElementById('cardFront').value.trim();
    const back = document.getElementById('cardBack').value.trim();
    if (!front || !back) return;
    try {
      await api(API.flashcards, { method: 'POST', body: JSON.stringify({ front, back }) });
      e.target.reset();
      toast('Карточка добавлена');
      endReview();
      await loadFlashcards();
      loadProgress();
    } catch (_) {
      toast('Ошибка при создании');
    }
  });

  document.getElementById('startReview').addEventListener('click', startReview);
  document.getElementById('flashcard').addEventListener('click', flipCard);
  document.getElementById('btnCorrect').addEventListener('click', () => answerCard(true));
  document.getElementById('btnWrong').addEventListener('click', () => answerCard(false));
}

function setReviewUI(state) {
  const idle = document.getElementById('reviewIdle');
  const area = document.getElementById('reviewArea');
  const done = document.getElementById('reviewDone');
  idle.classList.add('hidden');
  area.classList.add('hidden');
  done.classList.add('hidden');
  if (state === 'idle') idle.classList.remove('hidden');
  if (state === 'active') area.classList.remove('hidden');
  if (state === 'done') done.classList.remove('hidden');
}

function endReview() {
  reviewQueue = [];
  reviewIndex = 0;
  cardFlipped = false;
  setReviewUI('idle');
}

async function loadFlashcards() {
  try {
    const [cards, due] = await Promise.all([api(API.flashcards), api(API.review)]);
    document.getElementById('libraryCount').textContent = cards.length;
    document.getElementById('reviewStatus').textContent = `К повторению: ${due.length}`;
    document.getElementById('startReview').disabled = due.length === 0;

    const lib = document.getElementById('cardLibrary');
    const libEmpty = document.getElementById('libraryEmpty');
    lib.innerHTML = '';
    if (!cards.length) {
      libEmpty.classList.remove('hidden');
    } else {
      libEmpty.classList.add('hidden');
      cards.forEach(c => {
        const li = document.createElement('li');
        const dueMark = due.some(d => d.id === c.id) ? '<span class="due-dot" title="К повторению"></span>' : '';
        li.innerHTML = `
          ${dueMark}
          <span class="lib-text" title="${escapeHtml(c.front)}">${escapeHtml(c.front)}</span>
          <span class="lib-box">ур.${c.box}</span>
          <button type="button" data-del-card="${c.id}">✕</button>
        `;
        li.addEventListener('click', e => {
          if (e.target.closest('[data-del-card]')) return;
          previewCard(c);
        });
        lib.appendChild(li);
      });
      lib.querySelectorAll('[data-del-card]').forEach(btn => {
        btn.addEventListener('click', async e => {
          e.stopPropagation();
          if (confirm('Удалить карточку?')) {
            await api(`${API.flashcards}/${btn.dataset.delCard}`, { method: 'DELETE' });
            toast('Удалено');
            endReview();
            loadFlashcards();
            loadProgress();
          }
        });
      });
    }

    if (reviewQueue.length === 0) {
      setReviewUI(due.length ? 'idle' : 'idle');
      if (!cards.length) {
        document.getElementById('reviewIdle').querySelector('p').textContent =
          'Создайте карточку и нажмите «Повторить»';
      } else if (!due.length) {
        document.getElementById('reviewIdle').querySelector('p').textContent =
          'Все карточки повторены. Загляните позже.';
      } else {
        document.getElementById('reviewIdle').querySelector('p').textContent =
          'Нажмите «Повторить», чтобы начать';
      }
    }
  } catch (_) {
    toast('Ошибка загрузки карточек');
  }
}

function previewCard(card) {
  setReviewUI('active');
  cardFlipped = false;
  document.getElementById('cardFaceFront').textContent = card.front;
  document.getElementById('cardFaceBack').innerHTML =
    escapeHtml(card.back) + `<div class="box-tag">Уровень ${card.box}/5</div>`;
  document.getElementById('cardFaceBack').classList.add('hidden');
  document.getElementById('cardFaceFront').classList.remove('hidden');
  document.getElementById('flipHint').classList.remove('hidden');
  document.getElementById('reviewActions').classList.add('hidden');
  document.getElementById('reviewProgress').textContent = 'Просмотр';
}

async function startReview() {
  try {
    reviewQueue = await api(API.review);
    reviewIndex = 0;
    cardFlipped = false;
    if (!reviewQueue.length) {
      toast('Нет карточек к повторению');
      setReviewUI('idle');
      return;
    }
    document.getElementById('reviewDone').classList.add('hidden');
    setReviewUI('active');
    showCurrentCard();
    toast(`Начато: ${reviewQueue.length} карточек`);
  } catch (_) {
    toast('Ошибка запуска повторения');
  }
}

function showCurrentCard() {
  if (reviewIndex >= reviewQueue.length) {
    setReviewUI('done');
    toast('Повторение завершено');
    loadFlashcards();
    loadProgress();
    return;
  }
  const card = reviewQueue[reviewIndex];
  cardFlipped = false;
  document.getElementById('cardFaceFront').textContent = card.front;
  document.getElementById('cardFaceBack').innerHTML =
    escapeHtml(card.back) + `<div class="box-tag">Уровень ${card.box}/5</div>`;
  document.getElementById('cardFaceBack').classList.add('hidden');
  document.getElementById('cardFaceFront').classList.remove('hidden');
  document.getElementById('flipHint').classList.remove('hidden');
  document.getElementById('reviewActions').classList.add('hidden');
  document.getElementById('reviewProgress').textContent =
    `${reviewIndex + 1} / ${reviewQueue.length}`;
}

function flipCard() {
  if (!document.getElementById('reviewArea').classList.contains('hidden')) {
    if (document.getElementById('reviewProgress').textContent === 'Просмотр') {
      cardFlipped = !cardFlipped;
      document.getElementById('cardFaceFront').classList.toggle('hidden', cardFlipped);
      document.getElementById('cardFaceBack').classList.toggle('hidden', !cardFlipped);
      return;
    }
  }
  if (!reviewQueue.length || reviewIndex >= reviewQueue.length) return;
  cardFlipped = !cardFlipped;
  document.getElementById('cardFaceFront').classList.toggle('hidden', cardFlipped);
  document.getElementById('cardFaceBack').classList.toggle('hidden', !cardFlipped);
  if (cardFlipped) {
    document.getElementById('flipHint').classList.add('hidden');
    document.getElementById('reviewActions').classList.remove('hidden');
  } else {
    document.getElementById('flipHint').classList.remove('hidden');
    document.getElementById('reviewActions').classList.add('hidden');
  }
}

async function answerCard(correct) {
  if (!reviewQueue.length || reviewIndex >= reviewQueue.length) return;
  const card = reviewQueue[reviewIndex];
  try {
    await api(`${API.flashcards}/${card.id}/review`, {
      method: 'POST',
      body: JSON.stringify({ correct }),
    });
    if (!correct) reviewQueue.push({ ...card });
    reviewIndex++;
    showCurrentCard();
  } catch (_) {
    toast('Ошибка сохранения');
  }
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}.${m}`;
}

function formatDateTime(iso) {
  if (!iso) return '';
  const dt = new Date(iso);
  return dt.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
