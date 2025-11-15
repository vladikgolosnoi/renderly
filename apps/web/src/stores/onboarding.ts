import { defineStore } from "pinia";
import type { Project, ProjectDetail } from "@/types/blocks";

type OnboardingSteps = {
  projectCreated: boolean;
  blockAdded: boolean;
  previewOpened: boolean;
};

interface PersistedState {
  welcomeCompleted: boolean;
  tourActive: boolean;
  steps: OnboardingSteps;
  editorHintsTriggered: boolean;
  editorHintsDismissed: boolean;
}

const STORAGE_KEY = "renderly_onboarding_v1";
const defaultSteps: OnboardingSteps = {
  projectCreated: false,
  blockAdded: false,
  previewOpened: false
};

function loadPersisted(): PersistedState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as PersistedState) : null;
  } catch {
    return null;
  }
}

function persist(state: PersistedState) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export const useOnboardingStore = defineStore("onboarding", {
  state: () => {
    const persisted = loadPersisted();
    return {
      welcomeCompleted: persisted?.welcomeCompleted ?? false,
      tourActive: persisted?.tourActive ?? false,
      steps: { ...defaultSteps, ...(persisted?.steps ?? {}) },
      editorHintsTriggered: persisted?.editorHintsTriggered ?? false,
      editorHintsDismissed: persisted?.editorHintsDismissed ?? false
    };
  },
  getters: {
    shouldShowWelcome: (state) => !state.welcomeCompleted,
    allStepsDone: (state) =>
      state.steps.projectCreated && state.steps.blockAdded && state.steps.previewOpened,
    showEditorHints: (state) => state.editorHintsTriggered && !state.editorHintsDismissed
  },
  actions: {
    save() {
      persist({
        welcomeCompleted: this.welcomeCompleted,
        tourActive: this.tourActive,
        steps: this.steps,
        editorHintsTriggered: this.editorHintsTriggered,
        editorHintsDismissed: this.editorHintsDismissed
      });
    },
    startTour() {
      this.welcomeCompleted = true;
      this.tourActive = true;
      this.save();
    },
    skipTour() {
      this.welcomeCompleted = true;
      this.tourActive = false;
      this.save();
    },
    completeTour() {
      this.tourActive = false;
      this.save();
    },
    markProjectCreated() {
      if (!this.steps.projectCreated) {
        this.steps.projectCreated = true;
        this.save();
      }
    },
    markBlockAdded() {
      if (!this.steps.blockAdded) {
        this.steps.blockAdded = true;
        this.save();
      }
    },
    markPreviewed() {
      if (!this.steps.previewOpened) {
        this.steps.previewOpened = true;
        this.save();
      }
    },
    triggerEditorHints() {
      if (!this.editorHintsDismissed) {
        this.editorHintsTriggered = true;
        this.save();
      }
    },
    dismissEditorHints() {
      this.editorHintsDismissed = true;
      this.editorHintsTriggered = false;
      this.save();
    },
    syncProjects(projects: Project[]) {
      if (projects.length > 0) {
        this.markProjectCreated();
      }
    },
    syncProjectDetail(detail: ProjectDetail | null) {
      if (!detail) return;
      if (detail.blocks.length > 0) {
        this.markBlockAdded();
      }
    }
  }
});
