import { state } from './state.js';
import { qs } from './dom.js';
import { t } from './i18n.js';

export async function loadDiagnostics() {
  const diagText = qs('#diagText');
  const list = qs('#diagnosticsList');
  if (!list) return;

  try {
    const res = await fetch(`${state.apiBase}/diagnostics`);
    if (!res.ok) throw new Error('Diagnostics failed');
    const data = await res.json();
    const keys = data.keys || {};
    state.diagnostics = {
      tmdb: Boolean(keys.tmdb),
      opensubtitles: Boolean(keys.opensubtitles),
      gemini: Boolean(keys.gemini),
    };

    const messages = [];
    if (!state.diagnostics.tmdb) messages.push(t('TMDB_API_KEY em falta (reconhecimento desativado).', 'TMDB_API_KEY missing (recognition disabled).'));
    if (!state.diagnostics.opensubtitles) messages.push(t('OPENSUBTITLES_API_KEY em falta (pesquisa desativada).', 'OPENSUBTITLES_API_KEY missing (search disabled).'));
    if (!state.diagnostics.gemini) messages.push(t('GEMINI_API_KEY em falta (traducao desativada).', 'GEMINI_API_KEY missing (translation disabled).'));

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

export async function checkHealth() {
  const dot = qs('#healthDot');
  const text = qs('#healthText');
  const diagText = qs('#diagText');
  try {
    const res = await fetch(`${state.apiBase}/health`);
    if (!res.ok) throw new Error('Offline');
    dot.style.background = 'var(--accent)';
    text.textContent = t('Online', 'Online');
    if (diagText) diagText.textContent = '';
    await loadDiagnostics();
  } catch {
    dot.style.background = 'var(--danger)';
    text.textContent = t('Offline', 'Offline');
    if (diagText) diagText.textContent = t('Backend indisponivel.', 'Backend unavailable.');
  }
}
