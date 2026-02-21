import { state } from './state.js';

export function formatDuration(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

export function estimateEtaSeconds(entries) {
  const batchSize = 10;
  const batches = Math.max(1, Math.ceil(entries / batchSize));
  const avg = Number(localStorage.getItem('scriptum.avgBatchSec') || '8');
  return Math.round(batches * avg);
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function toSeconds(timestamp) {
  const [time, ms] = timestamp.split(',');
  const [hh, mm, ss] = time.split(':').map(Number);
  return hh * 3600 + mm * 60 + ss + Number(ms) / 1000;
}

export function toTimestamp(seconds) {
  const clamped = Math.max(0, seconds);
  const h = String(Math.floor(clamped / 3600)).padStart(2, '0');
  const m = String(Math.floor((clamped % 3600) / 60)).padStart(2, '0');
  const s = String(Math.floor(clamped % 60)).padStart(2, '0');
  const ms = String(Math.round((clamped % 1) * 1000)).padStart(3, '0');
  return `${h}:${m}:${s},${ms}`;
}

export function parseSrt(text) {
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

export function entriesToSrt(entries) {
  return entries
    .map((e, idx) => `${idx + 1}\n${toTimestamp(e.start)} --> ${toTimestamp(e.end)}\n${e.text}\n`)
    .join('\n')
    .trim();
}

export function isTranslationEnabled() {
  return state.diagnostics.gemini;
}

export function isSearchEnabled() {
  return state.diagnostics.opensubtitles;
}

export function isTmdbEnabled() {
  return state.diagnostics.tmdb;
}
