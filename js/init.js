import { applyLanguage } from './i18n.js';
import { initNavigation, setupTopbar } from './navigation.js';
import { setupSettings } from './settings.js';
import { setupTranslationPage } from './translation.js';
import { setupSearch } from './search.js';
import { setupVideoTools } from './video-tools.js';
import { setupSync } from './sync.js';
import { setupProjectFlow, updateProjectState, renderProjectStates, setFsmService } from './project.js';
import { initFsm, deriveUiStates } from './fsm.js';
import { checkHealth } from './diagnostics.js';
import { qs } from './dom.js';

function init() {
  initNavigation();
  setupSettings();
  setupTranslationPage();
  setupSync();
  setupSearch();
  setupVideoTools();
  setupProjectFlow();
  setupTopbar();
  applyLanguage();
  checkHealth();

  const service = initFsm((snapshot) => {
    const derived = deriveUiStates(snapshot);
    updateProjectState(derived);
    const debug = qs('#fsmDebug');
    if (debug) {
      debug.textContent = JSON.stringify({ state: snapshot.value, context: snapshot.context }, null, 2);
    }
  });
  setFsmService(service);
  renderProjectStates();
}

init();
