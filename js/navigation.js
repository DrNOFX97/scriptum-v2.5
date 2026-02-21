import { qsa, qs } from './dom.js';
import { state } from './state.js';
import { applyLanguage, t } from './i18n.js';
import { renderProjectStates } from './project.js';

function syncSidebarToggleLabel() {
  const btn = qs('#sidebarToggle');
  const shell = qs('.app-shell');
  if (!btn || !shell) return;
  const collapsed = shell.classList.contains('sidebar-collapsed');
  btn.textContent = collapsed ? t('Mostrar Menu', 'Show Menu') : t('Esconder Menu', 'Hide Menu');
}

export function initNavigation() {
  qsa('.nav-link').forEach((link) => {
    link.addEventListener('click', () => {
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

export function setupTopbar() {
  const shell = qs('.app-shell');
  const saved = localStorage.getItem('scriptum.sidebarCollapsed') === 'true';
  if (shell && saved) shell.classList.add('sidebar-collapsed');
  syncSidebarToggleLabel();

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
    syncSidebarToggleLabel();
  });
  qs('#sidebarToggle').addEventListener('click', () => {
    const app = qs('.app-shell');
    if (!app) return;
    app.classList.toggle('sidebar-collapsed');
    localStorage.setItem('scriptum.sidebarCollapsed', String(app.classList.contains('sidebar-collapsed')));
    syncSidebarToggleLabel();
  });
}
