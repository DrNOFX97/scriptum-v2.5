import { state } from './state.js';
import { qs, setStatus } from './dom.js';
import { t } from './i18n.js';
import { parseSrt, estimateEtaSeconds, formatDuration, downloadBlob, isTranslationEnabled, entriesToSrt } from './utils.js';

export async function translateSubtitle() {
  let file = qs('#translateFile').files[0];
  if (!file && state.project.entries.length) {
    const srt = entriesToSrt(state.project.entries);
    const name = state.project.subtitleFile?.name || 'project_subtitles.srt';
    file = new File([srt], name, { type: 'text/plain' });
  }
  if (!file) {
    setStatus('#translateStatus', t('Escolha um ficheiro de legendas.', 'Select a subtitle file.'), true);
    return;
  }
  if (!isTranslationEnabled()) {
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
      setStatus('#translateStatus', t('Erro na tradução.', 'Translation error.'), true);
      return;
    }

    const blob = await res.blob();
    state.translateBlob = blob;
    qs('#translateDownload').disabled = false;
    setStatus('#translateStatus', t('Traducao concluida.', 'Translation completed.'));
    const output = qs('#translateOutput');
    if (output) output.innerHTML = `<p>${t('Traducao pronta', 'Translation ready')}: ${file.name}</p>`;

    if (state.autoDownload) {
      downloadBlob(blob, file.name.replace(/\.[^/.]+$/, '') + `_${target}.srt`);
    }

    if (statsEl) {
      const elapsed = Math.round((Date.now() - startedAt) / 1000);
      const batches = Math.max(1, Math.ceil(entriesCount / 10));
      const avg = Math.max(1, elapsed / batches);
      localStorage.setItem('scriptum.avgBatchSec', String(Math.round(avg)));
      statsEl.textContent = `${t('Entradas', 'Entries')}: ${entriesCount} · ${t('Tempo total', 'Total time')}: ${formatDuration(elapsed)}`;
    }
    if (progressBar) progressBar.style.width = '100%';
  } finally {
    if (timer) clearInterval(timer);
  }
}

export function setupTranslationPage() {
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
    qs('#translateDownload').disabled = true;
    state.translateBlob = null;
    setStatus('#translateStatus', t('Pronto.', 'Ready.'));
    const statsEl = qs('#translateStats');
    if (statsEl) statsEl.textContent = '';
    const progressBar = qs('#translateProgressBar');
    if (progressBar) progressBar.style.width = '0%';
    const output = qs('#translateOutput');
    if (output) output.innerHTML = `<p>${t('O ficheiro traduzido fica pronto aqui.', 'Translated file will be ready for download here.')}</p>`;
  });
}
