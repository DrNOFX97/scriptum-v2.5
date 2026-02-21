import { state } from './state.js';
import { qs } from './dom.js';
import { t } from './i18n.js';
import { parseSrt, toTimestamp, entriesToSrt, downloadBlob, formatDuration, estimateEtaSeconds } from './utils.js';

let fsmService = null;
export function setFsmService(service) {
  fsmService = service;
}

export function updateProjectState(partial) {
  state.project.states = { ...state.project.states, ...partial };
  syncProjectStateFromData();
  renderProjectStates();
}

export function renderProjectStates() {
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

function stripTags(text) {
  return text.replace(/<[^>]*>/g, '');
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function updateOverlay() {
  const overlay = qs('#subtitleOverlay');
  const active = state.project.entries[state.project.activeIndex];
  if (!active) {
    overlay.textContent = '—';
    return;
  }
  const clean = stripTags(active.text);
  overlay.innerHTML = escapeHtml(clean).replace(/\n/g, '<br>');
}

function showPlayerIdle() {
  qs('#playerScreen')?.classList.remove('hidden');
  qs('#playerLoading')?.classList.add('hidden');
}

function showPlayerLoading() {
  qs('#playerScreen')?.classList.add('hidden');
  qs('#playerLoading')?.classList.remove('hidden');
}

function hidePlayerOverlays() {
  qs('#playerScreen')?.classList.add('hidden');
  qs('#playerLoading')?.classList.add('hidden');
}

function reflowText(text, maxLines, maxChars) {
  const clean = protectPhrases(
    text
      .replace(/\s+/g, ' ')
      .replace(/\s*\.\s*\.\s*\./g, '...')
      .replace(/…/g, '...')
      .replace(/\s+([,.;:!?])/g, '$1')
      .replace(/([,.;:!?])(?!\s|$)/g, '$1 ')
      .trim()
  );
  if (!clean) return text;
  const preferredSplit = clean.split(/([,.;:!?])/).reduce((acc, part, idx) => {
    if (idx % 2 === 0) acc.push(part);
    else acc[acc.length - 1] += part;
    return acc;
  }, []);

  const rawWords = preferredSplit.join(' ').split(' ');
  const words = [];
  const abbreviations = new Set(['sr.', 'sra.', 'dr.', 'dra.', 'srª.', 'sraª.', 'p.ex.', 'etc.']);
  const nonBreakingUnits = new Set(['%','°c','°f','km','m','cm','mm','kg','g','mg','l','ml','h','min','s']);

  rawWords.forEach((word) => {
    const lower = word.toLowerCase();
    if (word === '...') {
      if (words.length) {
        words[words.length - 1] += '...';
      } else {
        words.push('...');
      }
      return;
    }
    if (abbreviations.has(lower) && words.length) {
      words[words.length - 1] += ` ${word}`;
      return;
    }
    if (nonBreakingUnits.has(lower) && words.length) {
      words[words.length - 1] += ` ${word}`;
      return;
    }
    if (word.includes('‑') || word.includes('-')) {
      words.push(word.replace(/\s*-\s*/g, '-'));
      return;
    }
    words.push(word.replace(/__NB__/g, ' '));
  });

  const lines = [];
  let current = '';
  words.forEach((word) => {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length <= maxChars) {
      current = candidate;
    } else {
      if (current) lines.push(current);
      current = word;
    }
  });
  if (current) lines.push(current);

  if (lines.length <= maxLines) {
    return fixLineBeginnings(lines).map((line) => line.replace(/__NB__/g, ' ')).join('\n');
  }

  // If too many lines, rebalance into maxLines
  const allWords = clean.split(' ');
  const perLine = Math.ceil(allWords.length / maxLines);
  const rebalanced = [];
  for (let i = 0; i < maxLines; i += 1) {
    const slice = allWords.slice(i * perLine, (i + 1) * perLine);
    if (slice.length) rebalanced.push(slice.join(' '));
  }
  return fixLineBeginnings(rebalanced).map((line) => line.replace(/__NB__/g, ' ')).join('\n');
}

function fixLineBeginnings(lines) {
  const badStart = /^[,.;:!?)/\]”"—]/;
  const weakStart = /^(que|não|nao|se|me|te|lhe|vos|nos|a|à|ao|às|aos|da|do|dos|das)\b/i;
  const fixed = [...lines];
  for (let i = 1; i < fixed.length; i += 1) {
    const line = fixed[i].trim();
    if (!line) continue;
    if (badStart.test(line) || weakStart.test(line) || line.length <= 2) {
      fixed[i - 1] = `${fixed[i - 1]} ${line}`.trim();
      fixed[i] = '';
    }
  }
  return fixed.filter((line) => line && line.trim().length);
}

function protectPhrases(text) {
  const pairs = [
    'por favor',
    'de facto',
    'ainda assim',
    'de repente',
  ];
  let output = text;
  pairs.forEach((pair) => {
    const pattern = new RegExp(`\\b${pair}\\b`, 'gi');
    output = output.replace(pattern, (match) => match.replace(' ', '__NB__'));
  });
  return output;
}

function getLineLimits() {
  const maxLines = Number(qs('#projectMaxLines')?.value || 2);
  const maxChars = Number(qs('#projectMaxChars')?.value || 42);
  return { maxLines, maxChars };
}

function enforceLineLimits(entries) {
  const { maxLines, maxChars } = getLineLimits();
  return entries.map((entry) => {
    const normalized = entry.text.replace(/\n+/g, ' ').trim();
    const updated = reflowText(normalized, maxLines, maxChars);
    if (updated === entry.text) return entry;
    return {
      ...entry,
      text: updated,
      history: [...entry.history, updated],
      future: [],
    };
  });
}

function reflowAllEntries(maxLines, maxChars) {
  state.project.entries.forEach((entry) => {
    const updated = reflowText(entry.text, maxLines, maxChars);
    if (updated !== entry.text) {
      entry.text = updated;
      entry.history.push(updated);
      entry.future = [];
    }
  });
  renderEditorList();
  updateOverlay();
  updateProjectState({ subtitleEditing: true });
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

async function remuxForPlayback(file) {
  showPlayerLoading();
  const form = new FormData();
  form.append('video', file);
  try {
    const res = await fetch(`${state.apiBase}/remux-mkv-to-mp4`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Remux failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    state.project.videoUrl = url;
    qs('#projectVideo').src = url;
    hidePlayerOverlays();
  } catch (err) {
    console.error(err);
    showPlayerIdle();
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
      const posterHtml = movie.poster
        ? `<img src="${movie.poster}" alt="${movie.title}" />`
        : `<div class="muted">${t('Sem cartaz', 'No poster')}</div>`;
      const rating = movie.rating ? `${movie.rating}/10` : t('Sem rating', 'No rating');
      qs('#movieInfoBlock').innerHTML = `
        <div class="movie-poster">
          ${posterHtml}
        </div>
        <div class="movie-meta">
          <div class="movie-title">${movie.title} ${movie.year ? `(${movie.year})` : ''}</div>
          <div class="movie-rating">${t('Rating', 'Rating')}: ${rating}</div>
          <div class="muted">${movie.overview || ''}</div>
        </div>
      `;
    }
  } catch (err) {
    qs('#movieInfoBlock').innerHTML = `<p class="muted">${t('TMDB nao encontrado.', 'TMDB not found.')}</p>`;
  }
}

async function loadVideoFile(file) {
  if (fsmService) fsmService.send({ type: 'UPLOAD_MKV' });
  state.project.videoFile = file;
  updateProjectState({ videoLoaded: true });
  const video = qs('#projectVideo');

  if (file.name.toLowerCase().endsWith('.mkv')) {
    await remuxForPlayback(file);
  } else {
    const url = URL.createObjectURL(file);
    state.project.videoUrl = url;
    video.src = url;
    hidePlayerOverlays();
  }

  analyzeVideoForProject(file);
  recognizeMovieForProject(file.name);
  if (fsmService) {
    fsmService.send({ type: 'VIDEO_READY' });
    fsmService.send({ type: 'CHECK_SUBTITLES' });
  }
}

async function loadSubtitleFile(file) {
  state.project.subtitleFile = file;
  const text = await file.text();
  state.project.entries = enforceLineLimits(parseSrt(text));
  state.project.activeIndex = 0;
  updateOverlay();
  renderEditorList();
  updateProjectState({ subtitleMissing: false, subtitleActive: true });
  if (fsmService) fsmService.send({ type: 'SUBTITLE_AVAILABLE' });
  addVersion('original', state.project.entries, { source: 'upload', language: 'n/a' });
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
        state.project.entries = enforceLineLimits(parseSrt(sub.content));
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
    const entries = enforceLineLimits(parseSrt(translated));
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

export function setupProjectFlow() {
  showPlayerIdle();
  qs('#projectVideoPick').addEventListener('click', () => {
    qs('#projectVideoFile').click();
  });
  qs('#projectSubtitlePick').addEventListener('click', () => {
    qs('#projectSubtitleFile').click();
  });
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
      import('./search.js').then(({ searchSubtitles }) => searchSubtitles());
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

  qs('#projectOffsetSlider').addEventListener('input', (e) => {
    qs('#projectOffset').value = e.target.value;
  });

  qs('#projectOffset').addEventListener('input', (e) => {
    qs('#projectOffsetSlider').value = e.target.value;
  });

  qs('#projectReflow').addEventListener('click', () => {
    const maxLines = Number(qs('#projectMaxLines').value || 2);
    const maxChars = Number(qs('#projectMaxChars').value || 42);
    reflowAllEntries(maxLines, maxChars);
  });
  qs('#projectReflowDownload').addEventListener('click', () => {
    const maxLines = Number(qs('#projectMaxLines').value || 2);
    const maxChars = Number(qs('#projectMaxChars').value || 42);
    reflowAllEntries(maxLines, maxChars);
    const srt = entriesToSrt(state.project.entries);
    const baseName = state.project.subtitleFile?.name?.replace(/\.[^/.]+$/, '') || 'subtitle_fixed';
    downloadBlob(new Blob([srt], { type: 'text/plain' }), `${baseName}_fixed.srt`);
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
