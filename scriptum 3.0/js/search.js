import { state } from './state.js';
import { qs, setStatus } from './dom.js';
import { t } from './i18n.js';
import { downloadBlob, isSearchEnabled } from './utils.js';

export async function searchSubtitles() {
  const query = qs('#searchQuery').value.trim();
  const language = qs('#searchLanguage').value;
  if (!query) {
    setStatus('#searchStatus', t('Introduza uma pesquisa.', 'Enter a search query.'), true);
    return;
  }
  if (!isSearchEnabled()) {
    setStatus('#searchStatus', t('OPENSUBTITLES_API_KEY em falta. Pesquisa indisponível.', 'OPENSUBTITLES_API_KEY missing. Search unavailable.'), true);
    return;
  }

  setStatus('#searchStatus', t('A pesquisar...', 'Searching...'));
  const res = await fetch(`${state.apiBase}/search-subtitles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, language, limit: 20 }),
  });

  if (!res.ok) {
    setStatus('#searchStatus', t('Erro na pesquisa.', 'Search error.'), true);
    return;
  }
  const data = await res.json();
  renderSearchResults(data.subtitles || []);
  setStatus('#searchStatus', t(`Encontrados ${data.count || data.subtitles?.length || 0} resultados.`, `Found ${data.count || data.subtitles?.length || 0} results.`));
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
  const res = await fetch(`${state.apiBase}/download-subtitle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId }),
  });

  if (!res.ok) {
    setStatus('#searchStatus', t('Erro no download.', 'Download error.'), true);
    return;
  }
  const blob = await res.blob();
  downloadBlob(blob, name || `subtitle_${fileId}.srt`);
  setStatus('#searchStatus', t('Download concluido.', 'Download complete.'));
}

export function setupSearch() {
  qs('#searchStart').addEventListener('click', searchSubtitles);
}
