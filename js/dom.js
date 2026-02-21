export const qs = (selector) => document.querySelector(selector);
export const qsa = (selector) => Array.from(document.querySelectorAll(selector));

export function setStatus(id, message, isError = false) {
  const el = qs(id);
  if (!el) return;
  el.textContent = message;
  el.style.color = isError ? 'var(--danger)' : 'var(--text-muted)';
}
