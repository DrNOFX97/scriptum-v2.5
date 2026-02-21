import { state } from './state.js';
import { qs } from './dom.js';
import { t } from './i18n.js';
import { downloadBlob } from './utils.js';

async function analyzeVideo() {
  const file = qs('#analyzeVideo').files[0] || state.project.videoFile;
  if (!file) return;

  const form = new FormData();
  form.append('video', file);

  qs('#analyzeOutput').innerHTML = `<p>${t('A analisar...', 'Analyzing...')}</p>`;

  try {
    const res = await fetch(`${state.apiBase}/analyze-video`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) throw new Error('Analyze failed');

    const data = await res.json();
    const info = data.video_info || {};
    qs('#analyzeOutput').innerHTML = `
      <p><strong>${t('Formato', 'Format')}:</strong> ${info.format || 'n/a'}</p>
      <p><strong>${t('Resolucao', 'Resolution')}:</strong> ${info.resolution || 'n/a'}</p>
      <p><strong>${t('Duracao', 'Duration')}:</strong> ${info.duration_formatted || 'n/a'}</p>
      <p><strong>Codec:</strong> ${info.codec || 'n/a'}</p>
    `;
  } catch (err) {
    qs('#analyzeOutput').innerHTML = `<p style="color: var(--danger)">${t('Falha na analise.', 'Analysis failed.')}</p>`;
  }
}

async function remuxVideo() {
  const file = qs('#toolVideo').files[0] || state.project.videoFile;
  if (!file) return;
  const form = new FormData();
  form.append('video', file);

  try {
    const res = await fetch(`${state.apiBase}/remux-mkv-to-mp4`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) throw new Error('Remux failed');

    const blob = await res.blob();
    downloadBlob(blob, file.name.replace(/\.[^/.]+$/, '') + '.mp4');
  } catch (err) {
    qs('#extractOutput').innerHTML = `<p style="color: var(--danger)">${t('Falha no remux.', 'Remux failed.')}</p>`;
  }
}

async function convertVideo() {
  const file = qs('#toolVideo').files[0] || state.project.videoFile;
  if (!file) return;
  const form = new FormData();
  form.append('video', file);
  form.append('quality', qs('#convertQuality').value);

  try {
    const res = await fetch(`${state.apiBase}/convert-to-mp4`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) throw new Error('Convert failed');

    const blob = await res.blob();
    downloadBlob(blob, file.name.replace(/\.[^/.]+$/, '') + '.mp4');
  } catch (err) {
    qs('#extractOutput').innerHTML = `<p style="color: var(--danger)">${t('Falha na conversao.', 'Conversion failed.')}</p>`;
  }
}

async function extractSubtitles() {
  const file = qs('#toolVideo').files[0] || state.project.videoFile;
  if (!file) return;
  const form = new FormData();
  form.append('video', file);

  qs('#extractOutput').innerHTML = `<p>${t('A extrair legendas...', 'Extracting subtitles...')}</p>`;

  try {
    const res = await fetch(`${state.apiBase}/extract-mkv-subtitles`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) throw new Error('Extraction failed');

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
    qs('#extractOutput').innerHTML = `<p style="color: var(--danger)">${t('Falha ao extrair.', 'Extraction failed.')}</p>`;
  }
}

export function setupVideoTools() {
  qs('#analyzeStart').addEventListener('click', analyzeVideo);
  qs('#remuxStart').addEventListener('click', remuxVideo);
  qs('#convertStart').addEventListener('click', convertVideo);
  qs('#extractStart').addEventListener('click', extractSubtitles);
}
