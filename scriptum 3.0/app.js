const state = {
  apiBase: localStorage.getItem('scriptum.apiBase') || 'http://localhost:5001',
  autoDownload: localStorage.getItem('scriptum.autoDownload') !== 'false',
  language: localStorage.getItem('scriptum.language') || 'pt',
  translateBlob: null,
  syncBlob: null,
  extractResults: [],
  diagnostics: {
    tmdb: true,
    opensubtitles: true,
    gemini: true,
  },
  project: {
    videoFile: null,
    videoUrl: null,
    subtitleFile: null,
    entries: [],
    embeddedSubtitles: [],
    versions: [],
    activeVersionId: null,
    activeIndex: null,
    movie: null,
    videoInfo: null,
    states: {
      videoLoaded: false,
      subtitleMissing: true,
      subtitleActive: false,
      subtitleTranslated: false,
      subtitleSynced: false,
      subtitleEditing: false,
    },
  },
};

const qs = (selector) => document.querySelector(selector);
const qsa = (selector) => Array.from(document.querySelectorAll(selector));

const { createMachine, createActor, assign } = window.XState;
let fsmService = null;

function setStatus(id, message, isError = false) {
  const el = qs(id);
  if (!el) return;
  el.textContent = message;
  el.style.color = isError ? 'var(--danger)' : 'var(--text-muted)';
}

function t(pt, en) {
  return state.language === 'pt' ? pt : en;
}

function formatDuration(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

function estimateEtaSeconds(entries) {
  const batchSize = 10;
  const batches = Math.max(1, Math.ceil(entries / batchSize));
  const avg = Number(localStorage.getItem('scriptum.avgBatchSec') || '8');
  return Math.round(batches * avg);
}

function applyLanguage() {
  const lang = state.language;
  document.documentElement.setAttribute('data-lang', lang);
  document.querySelectorAll('[data-pt][data-en]').forEach((el) => {
    el.textContent = lang === 'pt' ? el.dataset.pt : el.dataset.en;
  });
  document.querySelectorAll('[data-pt-placeholder][data-en-placeholder]').forEach((el) => {
    el.placeholder = lang === 'pt' ? el.dataset.ptPlaceholder : el.dataset.enPlaceholder;
  });
  const toggle = qs('#langToggle');
  if (toggle) toggle.textContent = lang.toUpperCase();
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function updateProjectState(partial) {
  state.project.states = { ...state.project.states, ...partial };
  syncProjectStateFromData();
  renderProjectStates();
}

function renderProjectStates() {
  const badges = qs('#stateBadges');
  const list = qs('#stateList');
  const label = qs('#projectStateLabel');
  const st = state.project.states;
  const stateMap = [
    { key: 'videoLoaded', pt: 'video carregado', en: 'video loaded' },
    { key: 'subtitleMissing', pt: 'legenda inexistente', en: 'subtitle missing' },
    { key: 'subtitleActive', pt: 'legenda ativa', en: 'subtitle active' },
    { key: 'subtitleTranslated', pt: 'legenda traduzida', en: 'subtitle translated' },
    { key: 'subtitleSynced', pt: 'legenda sincronizada', en: 'subtitle synced' },
    { key: 'subtitleEditing', pt: 'legenda em edicao', en: 'subtitle editing' },
  ];
  badges.innerHTML = '';
  list.innerHTML = '';
  stateMap.forEach((item) => {
    if (st[item.key]) {
      const badge = document.createElement('span');
      badge.className = 'badge';
      badge.textContent = t(item.pt, item.en);
      badges.appendChild(badge);
      const li = document.createElement('li');
      li.textContent = `• ${t(item.pt, item.en)}`;
      list.appendChild(li);
    }
  });
  label.textContent = t(
    st.videoLoaded ? 'Estado: video pronto' : 'Estado: video nao carregado',
    st.videoLoaded ? 'State: video ready' : 'State: video not loaded'
  );
}

function syncProjectStateFromData() {
  const hasSubtitle = state.project.entries.length > 0;
  if (!hasSubtitle) {
    state.project.states.subtitleMissing = true;
    state.project.states.subtitleActive = false;
  }
}

function createProjectMachine() {
  return createMachine({
    id: 'scriptum',
    initial: 'appIdle',
    context: {
      hasSubtitle: false,
      hasTranslated: false,
      hasSynced: false,
    },
    states: {
      appIdle: {
        on: {
          UPLOAD_MKV: {
            target: 'project',
            actions: assign({ hasSubtitle: false, hasTranslated: false, hasSynced: false }),
          },
          OPEN_PROJECT: 'project',
        },
      },
      project: {
        type: 'parallel',
        states: {
          video: {
            initial: 'loading',
            states: {
              loading: {
                on: {
                  VIDEO_READY: 'ready',
                  VIDEO_ERROR: 'error',
                },
              },
              ready: {
                on: {
                  CHECK_SUBTITLES: 'ready',
                },
              },
              error: {},
            },
          },
          subtitle: {
            initial: 'check',
            states: {
              check: {
                always: [
                  { target: 'missing', guard: 'subtitleMissing' },
                  { target: 'present' },
                ],
              },
              missing: {
                on: {
                  EXTRACT_FROM_MKV: 'available',
                  SEARCH_OPENSUBTITLES: 'available',
                  UPLOAD_SUBTITLE: 'available',
                  SUBTITLE_AVAILABLE: 'available',
                },
              },
              present: {
                on: {
                  CHOOSE_TRANSLATE: 'ready',
                  CHOOSE_SYNC: 'ready',
                  CHOOSE_EDIT: 'ready',
                },
              },
              available: {
                entry: assign({ hasSubtitle: true }),
                always: 'ready',
              },
              ready: {
                on: {
                  TRANSLATE: 'ready',
                  SYNC: 'ready',
                  EDIT: 'ready',
                },
              },
            },
          },
          translation: {
            initial: 'idle',
            states: {
              idle: { on: { TRANSLATE: 'running' } },
              running: {
                on: {
                  TRANSLATION_DONE: 'done',
                  TRANSLATION_ERROR: 'error',
                },
              },
              done: {
                entry: assign({ hasTranslated: true }),
                on: { ACK_TRANSLATION: 'idle' },
              },
              error: { on: { ACK_TRANSLATION: 'idle' } },
            },
          },
          sync: {
            initial: 'idle',
            states: {
              idle: { on: { SYNC: 'auto' } },
              auto: { on: { SYNC_PREVIEW: 'preview', SYNC_ERROR: 'error' } },
              preview: {
                entry: assign({ hasSynced: true }),
                on: { CONFIRM_SYNC: 'idle', CANCEL_SYNC: 'idle' },
              },
              manual: {},
              error: { on: { ACK_SYNC: 'idle' } },
            },
          },
          edit: {
            initial: 'active',
            states: { active: {} },
          },
        },
      },
    },
  }, {
    guards: {
      subtitleMissing: (ctx) => !ctx.hasSubtitle,
    },
  });
}

function deriveUiStates(machineState) {
  const ctx = machineState.context;
  return {
    videoLoaded: machineState.matches({ project: { video: 'ready' } }),
    subtitleMissing: machineState.matches({ project: { subtitle: 'missing' } }),
    subtitleActive: machineState.matches({ project: { subtitle: 'ready' } }),
    subtitleTranslated: ctx.hasTranslated,
    subtitleSynced: ctx.hasSynced,
  };
}

function parseSrt(text) {
  const blocks = text.replace(/\r\n/g, '\n').trim().split('\n\n');
  const entries = [];
  blocks.forEach((block, idx) => {
    const lines = block.split('\n');
    if (lines.length < 3) return;
    const time = lines[1].trim();
    const textLines = lines.slice(2).join('\n').trim();
    const [start, end] = time.split(' --> ').map((t) => toSeconds(t));
    entries.push({
      id: idx + 1,
      start,
      end,
      time,
      text: textLines,
      history: [textLines],
      future: [],
    });
  });
  return entries;
}

function toSeconds(timestamp) {
  const [time, ms] = timestamp.split(',');
  const [hh, mm, ss] = time.split(':').map(Number);
  return hh * 3600 + mm * 60 + ss + Number(ms) / 1000;
}

function toTimestamp(seconds) {
  const clamped = Math.max(0, seconds);
  const h = String(Math.floor(clamped / 3600)).padStart(2, '0');
  const m = String(Math.floor((clamped % 3600) / 60)).padStart(2, '0');
  const s = String(Math.floor(clamped % 60)).padStart(2, '0');
  const ms = String(Math.round((clamped % 1) * 1000)).padStart(3, '0');
  return `${h}:${m}:${s},${ms}`;
}

function renderEditorList() {
  const list = qs('#editorList');
  list.innerHTML = '';
  state.project.entries.forEach((entry, index) => {
    const row = document.createElement('div');
    row.className = 'editor-row' + (state.project.activeIndex === index ? ' active' : '');
    row.dataset.index = String(index);

    const time = document.createElement('div');
    time.className = 'editor-time';
    time.textContent = `${toTimestamp(entry.start)} → ${toTimestamp(entry.end)}`;

    const textWrap = document.createElement('div');
    const textarea = document.createElement('textarea');
    textarea.className = 'editor-text';
    textarea.value = entry.text;
    textarea.addEventListener('input', () => {
      entry.text = textarea.value;
      entry.history.push(entry.text);
      entry.future = [];
      updateOverlay();
      updateProjectState({ subtitleEditing: true });
    });

    const actions = document.createElement('div');
    actions.className = 'editor-actions-inline';
    const undo = document.createElement('button');
    undo.className = 'btn ghost';
    undo.textContent = t('Undo', 'Undo');
    undo.addEventListener('click', () => {
      if (entry.history.length > 1) {
        entry.future.push(entry.history.pop());
        entry.text = entry.history[entry.history.length - 1];
        textarea.value = entry.text;
        updateOverlay();
      }
    });
    const redo = document.createElement('button');
    redo.className = 'btn ghost';
    redo.textContent = t('Redo', 'Redo');
    redo.addEventListener('click', () => {
      if (entry.future.length) {
        const next = entry.future.pop();
        entry.history.push(next);
        entry.text = next;
        textarea.value = entry.text;
        updateOverlay();
      }
    });
    actions.appendChild(undo);
    actions.appendChild(redo);

    textWrap.appendChild(textarea);
    textWrap.appendChild(actions);
    row.appendChild(time);
    row.appendChild(textWrap);
    row.addEventListener('click', () => {
      state.project.activeIndex = index;
      const video = qs('#projectVideo');
      if (video && entry.start != null) {
        video.currentTime = Math.max(entry.start - 0.2, 0);
        video.play();
      }
      renderEditorList();
    });

    list.appendChild(row);
  });
}

function updateOverlay() {
  const overlay = qs('#subtitleOverlay');
  const active = state.project.entries[state.project.activeIndex];
  overlay.textContent = active ? active.text : '—';
}

function handleTimeUpdate() {
  const video = qs('#projectVideo');
  const current = video.currentTime;
  const idx = state.project.entries.findIndex((entry) => current >= entry.start && current <= entry.end);
  if (idx !== -1 && idx !== state.project.activeIndex) {
    state.project.activeIndex = idx;
    renderEditorList();
    updateOverlay();
  }
}

async function loadVideoFile(file) {
  if (fsmService) fsmService.send({ type: 'UPLOAD_MKV' });
  state.project.videoFile = file;
  state.project.states.videoLoaded = true;
  updateProjectState({ videoLoaded: true });
  const video = qs('#projectVideo');

  if (file.name.toLowerCase().endsWith('.mkv')) {
    await remuxForPlayback(file);
  } else {
    const url = URL.createObjectURL(file);
    state.project.videoUrl = url;
    video.src = url;
  }

  analyzeVideoForProject(file);
  recognizeMovieForProject(file.name);
  if (fsmService) {
    fsmService.send({ type: 'VIDEO_READY' });
    fsmService.send({ type: 'CHECK_SUBTITLES' });
  }
}

async function remuxForPlayback(file) {
  const form = new FormData();
  form.append('video', file);
  try {
    const res = await fetch(`${state.apiBase}/remux-mkv-to-mp4`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Remux failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    state.project.videoUrl = url;
    qs('#projectVideo').src = url;
  } catch (err) {
    console.error(err);
  }
}

async function analyzeVideoForProject(file) {
  const form = new FormData();
  form.append('video', file);
  try {
    const res = await fetch(`${state.apiBase}/analyze-video`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Analyze failed');
    const data = await res.json();
    state.project.videoInfo = data.video_info || {};
    const info = state.project.videoInfo;
    qs('#videoInfoBlock').innerHTML = `
      <p><strong>${t('Formato', 'Format')}:</strong> ${info.format || 'n/a'}</p>
      <p><strong>${t('Resolucao', 'Resolution')}:</strong> ${info.resolution || 'n/a'}</p>
      <p><strong>${t('Duracao', 'Duration')}:</strong> ${info.duration_formatted || 'n/a'}</p>
      <p><strong>FPS:</strong> ${info.fps || 'n/a'}</p>
    `;
  } catch (err) {
    qs('#videoInfoBlock').innerHTML = `<p class="muted">${t('Falha na analise.', 'Analysis failed.')}</p>`;
  }
}

async function recognizeMovieForProject(filename) {
  if (!state.diagnostics.tmdb) {
    qs('#movieInfoBlock').innerHTML = `<p class="muted">${t('TMDB_API_KEY em falta.', 'TMDB_API_KEY missing.')}</p>`;
    return;
  }
  try {
    const res = await fetch(`${state.apiBase}/recognize-movie`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename }),
    });
    if (!res.ok) throw new Error('TMDB failed');
    const data = await res.json();
    state.project.movie = data.movie;
    const movie = data.movie;
    if (movie) {
      qs('#movieInfoBlock').innerHTML = `
        <p><strong>${movie.title}</strong> (${movie.year})</p>
        <p class="muted">${movie.overview || ''}</p>
      `;
    }
  } catch (err) {
    qs('#movieInfoBlock').innerHTML = `<p class="muted">${t('TMDB nao encontrado.', 'TMDB not found.')}</p>`;
  }
}

async function loadSubtitleFile(file) {
  state.project.subtitleFile = file;
  const text = await file.text();
  state.project.entries = parseSrt(text);
  state.project.activeIndex = 0;
  updateOverlay();
  renderEditorList();
  updateProjectState({ subtitleMissing: false, subtitleActive: true });
  if (fsmService) fsmService.send({ type: 'SUBTITLE_AVAILABLE' });
  addVersion('original', state.project.entries);
}

function addVersion(label, entries, meta = {}) {
  const existing = state.project.versions.find((v) => v.label === label && v.source === meta.source && v.language === meta.language);
  if (existing) {
    existing.entries = entries.map((e) => ({ ...e, history: [...e.history], future: [...e.future] }));
    renderVersions();
    return;
  }
  const versionId = `${label}-${Date.now()}`;
  const copy = entries.map((e) => ({ ...e, history: [...e.history], future: [...e.future] }));
  state.project.versions.push({ id: versionId, label, entries: copy, ...meta });
  state.project.activeVersionId = versionId;
  renderVersions();
}

function renderVersions() {
  const container = qs('#subtitleVersions');
  container.innerHTML = '';
  state.project.versions.forEach((version) => {
    const item = document.createElement('div');
    item.className = 'version-item' + (version.id === state.project.activeVersionId ? ' active' : '');
    const meta = [version.language, version.variant, version.source].filter(Boolean).join(' · ');
    item.innerHTML = `<span>${version.label}${meta ? ` — ${meta}` : ''}</span>`;
    const btn = document.createElement('button');
    btn.className = 'btn ghost';
    btn.textContent = t('Abrir', 'Open');
    btn.addEventListener('click', () => {
    state.project.entries = version.entries.map((e) => ({ ...e, history: [...e.history], future: [...e.future] }));
    state.project.activeVersionId = version.id;
    state.project.activeIndex = 0;
    renderEditorList();
    updateOverlay();
    renderVersions();
    });
    item.appendChild(btn);
    container.appendChild(item);
  });
}

function renderEmbeddedSubtitles() {
  const list = qs('#embeddedList');
  if (!list) return;
  if (!state.project.embeddedSubtitles.length) {
    list.innerHTML = `<p class="muted">${t('Nenhuma legenda extraida.', 'No subtitles extracted.')}</p>`;
    return;
  }
  list.innerHTML = '';
  state.project.embeddedSubtitles.forEach((sub, idx) => {
    const item = document.createElement('div');
    item.className = 'embedded-item';
      const label = document.createElement('span');
      const lang = sub.language || sub.lang || 'n/a';
      const title = sub.title || sub.file_name || `Track ${idx + 1}`;
      label.textContent = `${title} · ${lang}`;
      const btn = document.createElement('button');
      btn.className = 'btn ghost';
      btn.textContent = t('Importar', 'Import');
      btn.addEventListener('click', () => {
        if (sub.content) {
          state.project.entries = parseSrt(sub.content);
          state.project.activeIndex = 0;
          updateOverlay();
          renderEditorList();
          updateProjectState({ subtitleMissing: false, subtitleActive: true });
          addVersion('extracted', state.project.entries, { source: 'mkv', language: lang, variant: sub.language || '' });
        }
      });
    item.appendChild(label);
    item.appendChild(btn);
    list.appendChild(item);
  });
}

async function extractProjectSubtitles() {
  if (!state.project.videoFile) return;
  const form = new FormData();
  form.append('video', state.project.videoFile);
  try {
    const res = await fetch(`${state.apiBase}/extract-mkv-subtitles`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) throw new Error('Extraction failed');
    const data = await res.json();
    state.project.embeddedSubtitles = data.subtitles || [];
    renderEmbeddedSubtitles();
  } catch (err) {
    qs('#embeddedList').innerHTML = `<p class="muted">${t('Falha ao extrair legendas.', 'Failed to extract subtitles.')}</p>`;
  }
}

function entriesToSrt(entries) {
  return entries
    .map((e, idx) => `${idx + 1}\n${toTimestamp(e.start)} --> ${toTimestamp(e.end)}\n${e.text}\n`)
    .join('\n')
    .trim();
}

async function translateProjectSubtitle() {
  if (!state.project.subtitleFile) return;
  if (fsmService) fsmService.send({ type: 'TRANSLATE' });
  const blob = new Blob([entriesToSrt(state.project.entries)], { type: 'text/plain' });
  const entriesCount = state.project.entries.length;
  const statsEl = qs('#projectTranslateStats');
  const progressBar = qs('#projectTranslateProgress');
  const startedAt = Date.now();
  const etaSec = estimateEtaSeconds(entriesCount);
  let timer = null;
  const form = new FormData();
  form.append('subtitle', blob, 'active.srt');
  const sourceLang = 'en';
  const targetLang = 'pt';
  form.append('source_lang', sourceLang);
  form.append('target_lang', targetLang);
  if (statsEl) {
    statsEl.textContent = `${t('Entradas', 'Entries')}: ${entriesCount} · ${t('ETA', 'ETA')}: ${formatDuration(etaSec)} · ${t('Decorrido', 'Elapsed')}: 0s`;
    timer = setInterval(() => {
      const elapsed = Math.round((Date.now() - startedAt) / 1000);
      const remaining = Math.max(0, etaSec - elapsed);
      statsEl.textContent = `${t('Entradas', 'Entries')}: ${entriesCount} · ${t('ETA', 'ETA')}: ${formatDuration(remaining)} · ${t('Decorrido', 'Elapsed')}: ${formatDuration(elapsed)}`;
      if (progressBar) {
        const pct = Math.min(95, Math.round((elapsed / Math.max(1, etaSec)) * 100));
        progressBar.style.width = `${pct}%`;
      }
    }, 1000);
  }

  try {
    const res = await fetch(`${state.apiBase}/translate`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Translation failed');
    const translated = await res.text();
    const entries = parseSrt(translated);
    addVersion('translated', entries, { source: 'translation', language: targetLang });
    updateProjectState({ subtitleTranslated: true });
    if (fsmService) {
      fsmService.send({ type: 'TRANSLATION_DONE' });
      fsmService.send({ type: 'ACK_TRANSLATION' });
    }
    if (statsEl) {
      const elapsed = Math.round((Date.now() - startedAt) / 1000);
      const batches = Math.max(1, Math.ceil(entriesCount / 10));
      const avg = Math.max(1, elapsed / batches);
      localStorage.setItem('scriptum.avgBatchSec', String(Math.round(avg)));
      statsEl.textContent = `${t('Entradas', 'Entries')}: ${entriesCount} · ${t('Tempo total', 'Total time')}: ${formatDuration(elapsed)}`;
    }
    if (progressBar) progressBar.style.width = '100%';
  } catch (err) {
    console.error(err);
    if (fsmService) fsmService.send({ type: 'TRANSLATION_ERROR' });
    if (statsEl) {
      statsEl.textContent = t('Erro na tradução.', 'Translation error.');
    }
  } finally {
    if (timer) clearInterval(timer);
    if (progressBar && statsEl?.textContent === '') {
      progressBar.style.width = '0%';
    }
  }
}

async function syncProjectSubtitle() {
  if (!state.project.videoFile || !state.project.subtitleFile) return;
  if (fsmService) fsmService.send({ type: 'SYNC' });
  const form = new FormData();
  form.append('video', state.project.videoFile);
  const blob = new Blob([entriesToSrt(state.project.entries)], { type: 'text/plain' });
  form.append('subtitle', blob, 'active.srt');
  try {
    const res = await fetch(`${state.apiBase}/sync`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Sync failed');
    const synced = await res.text();
    const entries = parseSrt(synced);
    addVersion('autosync', entries, { source: 'autosync' });
    updateProjectState({ subtitleSynced: true });
    if (fsmService) {
      fsmService.send({ type: 'SYNC_PREVIEW' });
      fsmService.send({ type: 'CONFIRM_SYNC' });
    }
  } catch (err) {
    console.error(err);
    if (fsmService) fsmService.send({ type: 'SYNC_ERROR' });
  }
}

function setupProjectFlow() {
  qs('#projectVideoFile').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    await loadVideoFile(file);
  });

  qs('#projectSubtitleFile').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    await loadSubtitleFile(file);
  });

  qs('#projectVideo').addEventListener('timeupdate', handleTimeUpdate);

  qs('#projectUpload').addEventListener('click', () => {
    qs('#projectSubtitleFile').click();
  });

  qs('#projectExtract').addEventListener('click', () => {
    if (!state.project.videoFile) return;
    if (fsmService) fsmService.send({ type: 'EXTRACT_FROM_MKV' });
    extractProjectSubtitles();
  });

  qs('#projectSearch').addEventListener('click', () => {
    const query = state.project.movie?.title || '';
    if (query) {
      if (fsmService) fsmService.send({ type: 'SEARCH_OPENSUBTITLES' });
      qs('#searchQuery').value = query;
      searchSubtitles();
    }
  });

  qs('#projectApplyOffset').addEventListener('click', () => {
    const offset = Number(qs('#projectOffset').value || 0);
    state.project.entries = state.project.entries.map((entry) => ({
      ...entry,
      start: entry.start + offset,
      end: entry.end + offset,
    }));
    renderEditorList();
    updateOverlay();
    updateProjectState({ subtitleEditing: true });
  });

  qs('#projectTranslate').addEventListener('click', translateProjectSubtitle);
  qs('#projectSync').addEventListener('click', syncProjectSubtitle);

  qs('#exportActive').addEventListener('click', () => {
    const srt = entriesToSrt(state.project.entries);
    downloadBlob(new Blob([srt], { type: 'text/plain' }), 'subtitle_active.srt');
  });

  qs('#exportAll').addEventListener('click', () => {
    state.project.versions.forEach((version) => {
      const srt = entriesToSrt(version.entries);
      downloadBlob(new Blob([srt], { type: 'text/plain' }), `subtitle_${version.label}.srt`);
    });
  });

  qs('#editorNormalizeAll').addEventListener('click', () => {
    state.project.entries = parseSrt(entriesToSrt(state.project.entries));
    renderEditorList();
    updateOverlay();
  });

  updateProjectState({});
}
async function checkHealth() {
  const dot = qs('#healthDot');
  const text = qs('#healthText');
  const diagText = qs('#diagText');
  try {
    const res = await fetch(`${state.apiBase}/health`);
    if (!res.ok) throw new Error('Offline');
    dot.style.background = 'var(--accent)';
    text.textContent = state.language === 'pt' ? 'Online' : 'Online';
    if (diagText) diagText.textContent = '';
    loadDiagnostics();
  } catch {
    dot.style.background = 'var(--danger)';
    text.textContent = state.language === 'pt' ? 'Offline' : 'Offline';
    if (diagText) {
      diagText.textContent = t('Backend indisponivel.', 'Backend unavailable.');
    }
  }
}

async function loadDiagnostics() {
  const diagText = qs('#diagText');
  const list = qs('#diagnosticsList');
  if (!list) return;

  try {
    const res = await fetch(`${state.apiBase}/diagnostics`);
    if (!res.ok) throw new Error('Diagnostics failed');
    const data = await res.json();
    const warnings = data.warnings || [];
    const keys = data.keys || {};
    state.diagnostics = {
      tmdb: Boolean(keys.tmdb),
      opensubtitles: Boolean(keys.opensubtitles),
      gemini: Boolean(keys.gemini),
    };

    const messages = [];
    if (!keys.tmdb) messages.push(t('TMDB_API_KEY em falta (reconhecimento desativado).', 'TMDB_API_KEY missing (recognition disabled).'));
    if (!keys.opensubtitles) messages.push(t('OPENSUBTITLES_API_KEY em falta (pesquisa desativada).', 'OPENSUBTITLES_API_KEY missing (search disabled).'));
    if (!keys.gemini) messages.push(t('GEMINI_API_KEY em falta (traducao desativada).', 'GEMINI_API_KEY missing (translation disabled).'));

    list.innerHTML = '';
    if (!messages.length) {
      list.innerHTML = `<div class="diagnostic-item">${t('Sem avisos. Backend pronto.', 'No warnings. Backend ready.')}</div>`;
      if (diagText) diagText.textContent = '';
      return;
    }

    messages.forEach((msg) => {
      const item = document.createElement('div');
      item.className = 'diagnostic-item';
      item.textContent = msg;
      list.appendChild(item);
    });
    if (diagText) diagText.textContent = t('Chaves em falta.', 'Missing keys.');
  } catch (err) {
    list.innerHTML = `<div class="diagnostic-item">${t('Nao foi possivel obter diagnosticos.', 'Unable to fetch diagnostics.')}</div>`;
  }
}

function initNavigation() {
  qsa('.nav-link').forEach((link) => {
    link.addEventListener('click', (e) => {
      qsa('.nav-link').forEach((item) => item.classList.remove('active'));
      link.classList.add('active');
    });
  });

  qsa('[data-jump]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const section = btn.dataset.jump;
      const target = qs(`#${section}`);
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
  });
}

function setupSettings() {
  qs('#apiBase').value = state.apiBase;
  qs('#autoDownload').checked = state.autoDownload;

  qs('#saveSettings').addEventListener('click', () => {
    state.apiBase = qs('#apiBase').value.trim();
    state.autoDownload = qs('#autoDownload').checked;
    localStorage.setItem('scriptum.apiBase', state.apiBase);
    localStorage.setItem('scriptum.autoDownload', String(state.autoDownload));
    setStatus('#settingsStatus', state.language === 'pt' ? 'Guardado.' : 'Saved.');
    checkHealth();
  });
}

async function translateSubtitle() {
  const file = qs('#translateFile').files[0];
  if (!file) {
    setStatus('#translateStatus', t('Escolha um ficheiro de legendas.', 'Select a subtitle file.'), true);
    return;
  }
  if (!state.diagnostics.gemini) {
    setStatus('#translateStatus', t('GEMINI_API_KEY em falta. Tradução indisponível.', 'GEMINI_API_KEY missing. Translation unavailable.'), true);
    return;
  }

  const source = qs('#translateSource').value;
  const target = qs('#translateTarget').value;
  const context = qs('#translateContext').value.trim();

  if (source === target) {
    setStatus('#translateStatus', t('Origem e destino devem ser diferentes.', 'Source and target must differ.'), true);
    return;
  }

  const content = await file.text();
  const entriesCount = parseSrt(content).length;
  const statsEl = qs('#translateStats');
  const progressBar = qs('#translateProgressBar');
  const startedAt = Date.now();
  const etaSec = estimateEtaSeconds(entriesCount);
  let timer = null;

  const form = new FormData();
  form.append('subtitle', file);
  form.append('source_lang', source);
  form.append('target_lang', target);
  if (context) form.append('movie_context', context);

  setStatus('#translateStatus', t('A traduzir...', 'Translating...'));
  if (statsEl) {
    statsEl.textContent = `${t('Entradas', 'Entries')}: ${entriesCount} · ${t('ETA', 'ETA')}: ${formatDuration(etaSec)} · ${t('Decorrido', 'Elapsed')}: 0s`;
    timer = setInterval(() => {
      const elapsed = Math.round((Date.now() - startedAt) / 1000);
      const remaining = Math.max(0, etaSec - elapsed);
      statsEl.textContent = `${t('Entradas', 'Entries')}: ${entriesCount} · ${t('ETA', 'ETA')}: ${formatDuration(remaining)} · ${t('Decorrido', 'Elapsed')}: ${formatDuration(elapsed)}`;
      if (progressBar) {
        const pct = Math.min(95, Math.round((elapsed / Math.max(1, etaSec)) * 100));
        progressBar.style.width = `${pct}%`;
      }
    }, 1000);
  }

  try {
    const res = await fetch(`${state.apiBase}/translate`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Translation failed' }));
      throw new Error(err.error || 'Translation failed');
    }

    const blob = await res.blob();
    state.translateBlob = blob;
    qs('#translateOutput').innerHTML = `<p>${t('Traducao pronta', 'Translation ready')}: ${file.name}</p>`;
    qs('#translateDownload').disabled = false;

    if (state.autoDownload) {
      downloadBlob(blob, file.name.replace(/\.[^/.]+$/, '') + `_${target}.srt`);
    }

    setStatus('#translateStatus', t('Traducao concluida.', 'Translation completed.'));
    if (statsEl) {
      const elapsed = Math.round((Date.now() - startedAt) / 1000);
      const batches = Math.max(1, Math.ceil(entriesCount / 10));
      const avg = Math.max(1, elapsed / batches);
      localStorage.setItem('scriptum.avgBatchSec', String(Math.round(avg)));
      statsEl.textContent = `${t('Entradas', 'Entries')}: ${entriesCount} · ${t('Tempo total', 'Total time')}: ${formatDuration(elapsed)}`;
    }
    if (progressBar) progressBar.style.width = '100%';
  } catch (err) {
    setStatus('#translateStatus', err.message, true);
  } finally {
    if (timer) clearInterval(timer);
    if (progressBar && statsEl?.textContent === '') {
      progressBar.style.width = '0%';
    }
  }
}

function setupTranslation() {
  qs('#translateStart').addEventListener('click', translateSubtitle);
  qs('#translateDownload').addEventListener('click', () => {
    if (!state.translateBlob) return;
    const file = qs('#translateFile').files[0];
    const target = qs('#translateTarget').value;
    const filename = file ? file.name.replace(/\.[^/.]+$/, '') + `_${target}.srt` : 'translation.srt';
    downloadBlob(state.translateBlob, filename);
  });
  qs('#translateReset').addEventListener('click', () => {
    qs('#translateFile').value = '';
    qs('#translateContext').value = '';
    qs('#translateOutput').innerHTML = `<p>${t('O ficheiro traduzido fica pronto aqui.', 'Translated file will be ready for download here.')}</p>`;
    qs('#translateDownload').disabled = true;
    state.translateBlob = null;
    setStatus('#translateStatus', t('Pronto.', 'Ready.'));
  });
}

function normalizeSrt(text) {
  return text.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}

function renumberSrt(text) {
  const blocks = normalizeSrt(text).split('\n\n');
  return blocks
    .map((block, index) => {
      const lines = block.split('\n');
      if (lines.length < 2) return block;
      lines[0] = String(index + 1);
      return lines.join('\n');
    })
    .join('\n\n');
}

function shiftTimestamp(timestamp, offsetSec) {
  const parts = timestamp.split(' --> ');
  if (parts.length !== 2) return timestamp;
  const shifted = parts.map((part) => {
    const [time, ms] = part.split(',');
    const [hh, mm, ss] = time.split(':').map(Number);
    const total = hh * 3600 + mm * 60 + ss + Number(`0.${ms}`) + offsetSec;
    const clamped = Math.max(0, total);
    const h = String(Math.floor(clamped / 3600)).padStart(2, '0');
    const m = String(Math.floor((clamped % 3600) / 60)).padStart(2, '0');
    const s = String(Math.floor(clamped % 60)).padStart(2, '0');
    const milli = String(Math.round((clamped % 1) * 1000)).padStart(3, '0');
    return `${h}:${m}:${s},${milli}`;
  });
  return shifted.join(' --> ');
}

function applyOffsetToSrt(text, offsetSec) {
  const blocks = normalizeSrt(text).split('\n\n');
  const updated = blocks.map((block) => {
    const lines = block.split('\n');
    if (lines.length < 2) return block;
    lines[1] = shiftTimestamp(lines[1], offsetSec);
    return lines.join('\n');
  });
  return updated.join('\n\n');
}

function setupEditor() {
  const editorArea = qs('#editorArea');

  qs('#editorFile').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const text = await file.text();
    editorArea.value = normalizeSrt(text);
    setStatus('#editorStatus', t('Carregado.', 'Loaded.'));
  });

  qs('#editorNormalize').addEventListener('click', () => {
    editorArea.value = normalizeSrt(editorArea.value);
    setStatus('#editorStatus', t('Normalizado.', 'Normalized.'));
  });

  qs('#editorRenumber').addEventListener('click', () => {
    editorArea.value = renumberSrt(editorArea.value);
    setStatus('#editorStatus', t('Renumeração aplicada.', 'Renumbered.'));
  });

  qs('#editorApplyOffset').addEventListener('click', () => {
    const offset = Number(qs('#editorOffset').value || 0);
    editorArea.value = applyOffsetToSrt(editorArea.value, offset);
    setStatus('#editorStatus', t(`Offset aplicado (${offset}s).`, `Offset applied (${offset}s).`));
  });

  qs('#editorFindReplace').addEventListener('click', () => {
    const find = qs('#editorFind').value;
    if (!find) return;
    const replace = qs('#editorReplace').value;
    editorArea.value = editorArea.value.split(find).join(replace);
    setStatus('#editorStatus', t('Procurar/substituir aplicado.', 'Find/replace applied.'));
  });

  qs('#editorDownload').addEventListener('click', () => {
    const blob = new Blob([editorArea.value], { type: 'text/plain' });
    downloadBlob(blob, 'edited.srt');
  });

  qs('#editorLoadDemo').addEventListener('click', () => {
    editorArea.value = '1\n00:00:01,000 --> 00:00:03,000\nExample line one.\n\n2\n00:00:04,000 --> 00:00:06,000\nExample line two.';
  });

  qs('#editorReset').addEventListener('click', () => {
    editorArea.value = '';
    qs('#editorFile').value = '';
    setStatus('#editorStatus', t('Pronto.', 'Ready.'));
  });
}

async function syncSubtitles() {
  const video = qs('#syncVideo').files[0];
  const subtitle = qs('#syncSubtitle').files[0];
  if (!video || !subtitle) {
    setStatus('#syncStatus', t('Escolha video e legenda.', 'Select video and subtitle files.'), true);
    return;
  }

  const form = new FormData();
  form.append('video', video);
  form.append('subtitle', subtitle);

  const progressBar = qs('#syncProgress .progress-bar');
  progressBar.style.width = '10%';
  setStatus('#syncStatus', t('A sincronizar...', 'Syncing...'));

  let progress = 10;
  const timer = setInterval(() => {
    progress = Math.min(progress + 8, 90);
    progressBar.style.width = `${progress}%`;
  }, 1200);

  try {
    const res = await fetch(`${state.apiBase}/sync`, {
      method: 'POST',
      body: form,
    });

    clearInterval(timer);
    progressBar.style.width = '100%';

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Sync failed' }));
      throw new Error(err.error || 'Sync failed');
    }

    const blob = await res.blob();
    state.syncBlob = blob;
    qs('#syncOutput').innerHTML = `<p>${t('Sync concluido para', 'Sync completed for')} ${subtitle.name}</p>`;
    qs('#syncDownload').disabled = false;

    if (state.autoDownload) {
      downloadBlob(blob, subtitle.name.replace(/\.[^/.]+$/, '') + '_synced.srt');
    }

    setStatus('#syncStatus', t('Sync concluido.', 'Sync completed.'));
  } catch (err) {
    clearInterval(timer);
    progressBar.style.width = '0%';
    setStatus('#syncStatus', err.message, true);
  }
}

function setupSync() {
  qs('#syncStart').addEventListener('click', syncSubtitles);
  qs('#syncDownload').addEventListener('click', () => {
    if (!state.syncBlob) return;
    const subtitle = qs('#syncSubtitle').files[0];
    const filename = subtitle ? subtitle.name.replace(/\.[^/.]+$/, '') + '_synced.srt' : 'synced.srt';
    downloadBlob(state.syncBlob, filename);
  });
}

async function searchSubtitles() {
  const query = qs('#searchQuery').value.trim();
  const language = qs('#searchLanguage').value;
  if (!query) {
    setStatus('#searchStatus', t('Introduza uma pesquisa.', 'Enter a search query.'), true);
    return;
  }
  if (!state.diagnostics.opensubtitles) {
    setStatus('#searchStatus', t('OPENSUBTITLES_API_KEY em falta. Pesquisa indisponível.', 'OPENSUBTITLES_API_KEY missing. Search unavailable.'), true);
    return;
  }

  setStatus('#searchStatus', t('A pesquisar...', 'Searching...'));

  try {
    const res = await fetch(`${state.apiBase}/search-subtitles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, language, limit: 20 }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Search failed' }));
      throw new Error(err.error || 'Search failed');
    }

    const data = await res.json();
    renderSearchResults(data.subtitles || []);
    setStatus('#searchStatus', t(`Encontrados ${data.count || data.subtitles?.length || 0} resultados.`, `Found ${data.count || data.subtitles?.length || 0} results.`));
  } catch (err) {
    setStatus('#searchStatus', err.message, true);
  }
}

function renderSearchResults(results) {
  const container = qs('#searchResults');
  if (!results.length) {
    container.innerHTML = `<p class="muted">${t('Sem resultados.', 'No results.')}</p>`;
    return;
  }

  container.innerHTML = '';
  results.forEach((item) => {
    const card = document.createElement('div');
    card.className = 'result-item';
    const meta = document.createElement('div');
    meta.className = 'result-meta';
    meta.innerHTML = `
      <strong>${item.name || 'Subtitle'}</strong>
      <span>${t('Idioma', 'Language')}: ${item.language || 'n/a'}</span>
      <span>${t('Downloads', 'Downloads')}: ${item.downloads || 0}</span>
    `;
    const button = document.createElement('button');
    button.className = 'btn ghost';
    button.textContent = t('Download', 'Download');
    button.addEventListener('click', () => downloadSubtitle(item.file_id, item.name));
    card.appendChild(meta);
    card.appendChild(button);
    container.appendChild(card);
  });
}

async function downloadSubtitle(fileId, name) {
  if (!fileId) return;
  setStatus('#searchStatus', t('A descarregar...', 'Downloading...'));

  try {
    const res = await fetch(`${state.apiBase}/download-subtitle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Download failed' }));
      throw new Error(err.error || 'Download failed');
    }

    const blob = await res.blob();
    downloadBlob(blob, name || `subtitle_${fileId}.srt`);
    setStatus('#searchStatus', t('Download concluido.', 'Download complete.'));
  } catch (err) {
    setStatus('#searchStatus', err.message, true);
  }
}

function setupSearch() {
  qs('#searchStart').addEventListener('click', searchSubtitles);
}

async function analyzeVideo() {
  const file = qs('#analyzeVideo').files[0];
  if (!file) return;

  const form = new FormData();
  form.append('video', file);

  qs('#analyzeOutput').innerHTML = `<p>${t('A analisar...', 'Analyzing...')}</p>`;

  try {
    const res = await fetch(`${state.apiBase}/analyze-video`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Analyze failed' }));
      throw new Error(err.error || 'Analyze failed');
    }

    const data = await res.json();
    const info = data.video_info || {};
    qs('#analyzeOutput').innerHTML = `
      <p><strong>${t('Formato', 'Format')}:</strong> ${info.format || 'n/a'}</p>
      <p><strong>${t('Resolucao', 'Resolution')}:</strong> ${info.resolution || 'n/a'}</p>
      <p><strong>${t('Duracao', 'Duration')}:</strong> ${info.duration_formatted || 'n/a'}</p>
      <p><strong>Codec:</strong> ${info.codec || 'n/a'}</p>
    `;
  } catch (err) {
    qs('#analyzeOutput').innerHTML = `<p style="color: var(--danger)">${err.message}</p>`;
  }
}

async function remuxVideo() {
  const file = qs('#toolVideo').files[0];
  if (!file) return;
  const form = new FormData();
  form.append('video', file);

  try {
    const res = await fetch(`${state.apiBase}/remux-mkv-to-mp4`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Remux failed' }));
      throw new Error(err.error || 'Remux failed');
    }

    const blob = await res.blob();
    downloadBlob(blob, file.name.replace(/\.[^/.]+$/, '') + '.mp4');
  } catch (err) {
    qs('#extractOutput').innerHTML = `<p style="color: var(--danger)">${err.message}</p>`;
  }
}

async function convertVideo() {
  const file = qs('#toolVideo').files[0];
  if (!file) return;
  const form = new FormData();
  form.append('video', file);
  form.append('quality', qs('#convertQuality').value);

  try {
    const res = await fetch(`${state.apiBase}/convert-to-mp4`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Convert failed' }));
      throw new Error(err.error || 'Convert failed');
    }

    const blob = await res.blob();
    downloadBlob(blob, file.name.replace(/\.[^/.]+$/, '') + '.mp4');
  } catch (err) {
    qs('#extractOutput').innerHTML = `<p style="color: var(--danger)">${err.message}</p>`;
  }
}

async function extractSubtitles() {
  const file = qs('#toolVideo').files[0];
  if (!file) return;
  const form = new FormData();
  form.append('video', file);

  qs('#extractOutput').innerHTML = `<p>${t('A extrair legendas...', 'Extracting subtitles...')}</p>`;

  try {
    const res = await fetch(`${state.apiBase}/extract-mkv-subtitles`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Extraction failed' }));
      throw new Error(err.error || 'Extraction failed');
    }

    const data = await res.json();
    const subtitles = data.subtitles || [];
    if (!subtitles.length) {
      qs('#extractOutput').innerHTML = `<p>${t('Sem legendas encontradas.', 'No subtitles found.')}</p>`;
      return;
    }

    qs('#extractOutput').innerHTML = subtitles
      .map((sub) => `<p>${sub.file_name || 'subtitle.srt'} (${sub.language || 'n/a'})</p>`)
      .join('');
  } catch (err) {
    qs('#extractOutput').innerHTML = `<p style="color: var(--danger)">${err.message}</p>`;
  }
}

function setupVideoTools() {
  qs('#analyzeStart').addEventListener('click', analyzeVideo);
  qs('#remuxStart').addEventListener('click', remuxVideo);
  qs('#convertStart').addEventListener('click', convertVideo);
  qs('#extractStart').addEventListener('click', extractSubtitles);
}

function setupTopbar() {
  qs('#newSession').addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  qs('#openDocs').addEventListener('click', () => {
    window.open('../README_REFACTORED.md', '_blank');
  });
  qs('#langToggle').addEventListener('click', () => {
    state.language = state.language === 'pt' ? 'en' : 'pt';
    localStorage.setItem('scriptum.language', state.language);
    applyLanguage();
    renderProjectStates();
  });
}

function init() {
  initNavigation();
  setupSettings();
  setupTranslation();
  setupEditor();
  setupSync();
  setupSearch();
  setupVideoTools();
  setupProjectFlow();
  setupTopbar();
  applyLanguage();
  checkHealth();
  const machine = createProjectMachine();
  fsmService = createActor(machine);
  fsmService.subscribe((snapshot) => {
    const derived = deriveUiStates(snapshot);
    updateProjectState(derived);
    const debug = qs('#fsmDebug');
    if (debug) {
      debug.textContent = JSON.stringify(
        { state: snapshot.value, context: snapshot.context },
        null,
        2
      );
    }
  });
  fsmService.start();
}

init();
