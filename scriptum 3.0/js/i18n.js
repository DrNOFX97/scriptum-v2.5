import { state } from './state.js';
import { qs } from './dom.js';

export function t(pt, en) {
  return state.language === 'pt' ? pt : en;
}

export function applyLanguage() {
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
