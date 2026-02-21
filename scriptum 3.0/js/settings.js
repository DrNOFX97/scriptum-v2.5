import { state } from './state.js';
import { qs } from './dom.js';
import { checkHealth } from './diagnostics.js';
import { t } from './i18n.js';

export function setupSettings() {
  qs('#apiBase').value = state.apiBase;
  qs('#autoDownload').checked = state.autoDownload;

  qs('#saveSettings').addEventListener('click', () => {
    state.apiBase = qs('#apiBase').value.trim();
    state.autoDownload = qs('#autoDownload').checked;
    localStorage.setItem('scriptum.apiBase', state.apiBase);
    localStorage.setItem('scriptum.autoDownload', String(state.autoDownload));
    const status = qs('#settingsStatus');
    if (status) status.textContent = t('Guardado.', 'Saved.');
    checkHealth();
  });
}
