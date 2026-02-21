import { state } from './state.js';
import { qs } from './dom.js';
import { t } from './i18n.js';
import { downloadBlob, entriesToSrt } from './utils.js';

export function setupSync() {
  qs('#syncStart').addEventListener('click', syncSubtitles);
  qs('#syncDownload').addEventListener('click', () => {
    if (!state.syncBlob) return;
    const subtitle = qs('#syncSubtitle').files[0];
    const filename = subtitle ? subtitle.name.replace(/\.[^/.]+$/, '') + '_synced.srt' : 'synced.srt';
    downloadBlob(state.syncBlob, filename);
  });
}

async function syncSubtitles() {
  const video = qs('#syncVideo').files[0] || state.project.videoFile;
  let subtitle = qs('#syncSubtitle').files[0];
  if (!subtitle && state.project.entries.length) {
    const content = entriesToSrt(state.project.entries);
    subtitle = new File([content], state.project.subtitleFile?.name || 'project_subtitles.srt', { type: 'text/plain' });
  }
  if (!video || !subtitle) return;

  const form = new FormData();
  form.append('video', video);
  form.append('subtitle', subtitle);

  const progressBar = qs('#syncProgress .progress-bar');
  progressBar.style.width = '10%';
  qs('#syncStatus').textContent = t('A sincronizar...', 'Syncing...');

  let progress = 10;
  const timer = setInterval(() => {
    progress = Math.min(progress + 8, 90);
    progressBar.style.width = `${progress}%`;
  }, 1200);

  try {
    const res = await fetch(`${state.apiBase}/sync`, { method: 'POST', body: form });
    clearInterval(timer);
    progressBar.style.width = '100%';

    if (!res.ok) throw new Error('Sync failed');

    const blob = await res.blob();
    state.syncBlob = blob;
    qs('#syncOutput').innerHTML = `<p>${t('Sync concluido para', 'Sync completed for')} ${subtitle.name}</p>`;
    qs('#syncDownload').disabled = false;

    if (state.autoDownload) {
      downloadBlob(blob, subtitle.name.replace(/\.[^/.]+$/, '') + '_synced.srt');
    }

    qs('#syncStatus').textContent = t('Sync concluido.', 'Sync completed.');
  } catch (err) {
    clearInterval(timer);
    progressBar.style.width = '0%';
    qs('#syncStatus').textContent = t('Erro no sync.', 'Sync error.');
  }
}
