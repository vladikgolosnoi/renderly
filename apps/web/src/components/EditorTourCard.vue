<template>
  <aside v-if="active" class="tour-card">
    <header>
      <h3>Пошаговый тур</h3>
      <span>{{ progressLabel }}</span>
    </header>
    <ol>
      <li :class="{ done: steps.projectCreated }">
        <strong>1. Создайте проект</strong>
        <p>На главной нажмите «Новый проект» — так появится заготовка.</p>
      </li>
      <li :class="{ done: steps.blockAdded }">
        <strong>2. Добавьте блок</strong>
        <p>Перетащите карточку из библиотеки слева или кликните по ней.</p>
      </li>
      <li :class="{ done: steps.previewOpened }">
        <strong>3. Посмотрите предпросмотр</strong>
        <p>
          Обновите блок «Live Preview», чтобы увидеть итоговую страницу
          <button type="button" class="link" @click="scrollToPreview">Перейти к предпросмотру</button>
        </p>
      </li>
    </ol>
    <div class="buttons">
      <button class="ghost" @click="skip">Пропустить</button>
      <button :disabled="!allDone" @click="finish">Готово</button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useOnboardingStore } from "@/stores/onboarding";

const onboarding = useOnboardingStore();
const active = computed(() => onboarding.tourActive);
const steps = computed(() => onboarding.steps);
const allDone = computed(() => onboarding.allStepsDone);
const progressLabel = computed(() => {
  const doneCount = Object.values(steps.value).filter(Boolean).length;
  return `${doneCount}/3`;
});

function skip() {
  onboarding.completeTour();
}

function finish() {
  onboarding.completeTour();
}

function scrollToPreview() {
  if (typeof window === "undefined") return;
  document.getElementById("live-preview")?.scrollIntoView({ behavior: "smooth", block: "center" });
}
</script>

<style scoped>
.tour-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 20px;
  border: 1px solid rgba(99, 102, 241, 0.25);
  box-shadow: 0 20px 80px rgba(15, 23, 42, 0.12);
  max-width: 320px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}

header h3 {
  margin: 0;
  font-size: 1.1rem;
}

header span {
  font-size: 0.85rem;
  color: #6366f1;
}

ol {
  list-style: none;
  padding: 0;
  margin: 0 0 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

li {
  padding-left: 0;
  border-left: 4px solid #e2e8f0;
  padding: 0 0 0 12px;
}

li.done {
  border-left-color: #22c55e;
}

li strong {
  display: block;
  margin-bottom: 4px;
}

li p {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
}

.buttons {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

button {
  border-radius: 12px;
  border: none;
  padding: 8px 12px;
  font-size: 0.95rem;
  cursor: pointer;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

button:not(.ghost) {
  background: #2563eb;
  color: #fff;
}

.ghost {
  background: transparent;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}

.link {
  border: none;
  background: none;
  color: #6366f1;
  font-size: 0.85rem;
  padding: 0 4px;
  cursor: pointer;
}
</style>
