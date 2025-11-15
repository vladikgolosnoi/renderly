import { describe, it, expect, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useOnboardingStore } from "../onboarding";

describe("useOnboardingStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.localStorage.clear();
  });

  it("shows welcome screen by default", () => {
    const store = useOnboardingStore();
    expect(store.shouldShowWelcome).toBe(true);
    expect(store.allStepsDone).toBe(false);
  });

  it("marks steps and persists state", () => {
    const store = useOnboardingStore();
    store.startTour();
    store.markProjectCreated();
    store.markBlockAdded();
    store.markPreviewed();
    expect(store.allStepsDone).toBe(true);
    store.completeTour();

    const persisted = window.localStorage.getItem("renderly_onboarding_v1");
    expect(persisted).toBeTruthy();

    // Hydrate new store instance from storage
    const secondStore = useOnboardingStore();
    expect(secondStore.allStepsDone).toBe(true);
    expect(secondStore.shouldShowWelcome).toBe(false);
    expect(secondStore.tourActive).toBe(false);
  });
});
