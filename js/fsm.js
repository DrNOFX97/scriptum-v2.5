import { state } from './state.js';

const { createMachine, createActor, assign } = window.XState;

export function createProjectMachine() {
  return createMachine({
    id: 'scriptum',
    initial: 'appIdle',
    context: {
      hasSubtitle: false,
      hasTranslated: false,
      hasSynced: false,
    },
    states: {
      appIdle: {
        on: {
          UPLOAD_MKV: {
            target: 'project',
            actions: assign({ hasSubtitle: false, hasTranslated: false, hasSynced: false }),
          },
          OPEN_PROJECT: 'project',
        },
      },
      project: {
        type: 'parallel',
        states: {
          video: {
            initial: 'loading',
            states: {
              loading: {
                on: {
                  VIDEO_READY: 'ready',
                  VIDEO_ERROR: 'error',
                },
              },
              ready: {
                on: {
                  CHECK_SUBTITLES: 'ready',
                },
              },
              error: {},
            },
          },
          subtitle: {
            initial: 'check',
            states: {
              check: {
                always: [
                  { target: 'missing', guard: 'subtitleMissing' },
                  { target: 'present' },
                ],
              },
              missing: {
                on: {
                  EXTRACT_FROM_MKV: 'available',
                  SEARCH_OPENSUBTITLES: 'available',
                  UPLOAD_SUBTITLE: 'available',
                  SUBTITLE_AVAILABLE: 'available',
                },
              },
              present: {
                on: {
                  CHOOSE_TRANSLATE: 'ready',
                  CHOOSE_SYNC: 'ready',
                  CHOOSE_EDIT: 'ready',
                },
              },
              available: {
                entry: assign({ hasSubtitle: true }),
                always: 'ready',
              },
              ready: {
                on: {
                  TRANSLATE: 'ready',
                  SYNC: 'ready',
                  EDIT: 'ready',
                },
              },
            },
          },
          translation: {
            initial: 'idle',
            states: {
              idle: { on: { TRANSLATE: 'running' } },
              running: {
                on: {
                  TRANSLATION_DONE: 'done',
                  TRANSLATION_ERROR: 'error',
                },
              },
              done: {
                entry: assign({ hasTranslated: true }),
                on: { ACK_TRANSLATION: 'idle' },
              },
              error: { on: { ACK_TRANSLATION: 'idle' } },
            },
          },
          sync: {
            initial: 'idle',
            states: {
              idle: { on: { SYNC: 'auto' } },
              auto: { on: { SYNC_PREVIEW: 'preview', SYNC_ERROR: 'error' } },
              preview: {
                entry: assign({ hasSynced: true }),
                on: { CONFIRM_SYNC: 'idle', CANCEL_SYNC: 'idle' },
              },
              manual: {},
              error: { on: { ACK_SYNC: 'idle' } },
            },
          },
          edit: {
            initial: 'active',
            states: { active: {} },
          },
        },
      },
    },
  }, {
    guards: {
      subtitleMissing: (ctx) => !ctx.hasSubtitle,
    },
  });
}

export function deriveUiStates(machineState) {
  const ctx = machineState.context;
  return {
    videoLoaded: machineState.matches({ project: { video: 'ready' } }),
    subtitleMissing: machineState.matches({ project: { subtitle: 'missing' } }),
    subtitleActive: machineState.matches({ project: { subtitle: 'ready' } }),
    subtitleTranslated: ctx.hasTranslated,
    subtitleSynced: ctx.hasSynced,
  };
}

export function initFsm(onChange) {
  const machine = createProjectMachine();
  const service = createActor(machine);
  service.subscribe((snapshot) => onChange(snapshot));
  service.start();
  return service;
}
