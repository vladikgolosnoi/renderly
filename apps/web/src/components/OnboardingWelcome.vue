<template>
  <transition name="fade">
    <div v-if="visible" class="welcome-overlay" role="dialog" aria-modal="true">
      <div class="welcome-card">
        <p class="eyebrow">Добро пожаловать в Renderly Studio</p>
        <h2>Соберите первый лендинг за 3 шага</h2>
        <ol>
          <li>
            Создайте проект — задайте название и цель, чтобы мы подготовили для вас каркас.
          </li>
          <li>
            Перетащите блоки из библиотеки и настройте контент прямо в редакторе.
          </li>
          <li>Откройте предпросмотр, убедитесь, что всё хорошо, и опубликуйте.</li>
        </ol>
        <div class="actions">
          <button @click="startTour">Начать тур</button>
          <button class="ghost" @click="dismiss">Не сейчас</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useOnboardingStore } from "@/stores/onboarding";

const onboarding = useOnboardingStore();
const visible = computed(() => onboarding.shouldShowWelcome);

function startTour() {
  onboarding.startTour();
}

function dismiss() {
  onboarding.skipTour();
}
</script>

<style scoped>
.welcome-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 40;
  padding: 16px;
}

.welcome-card {
  max-width: 520px;
  background: #fff;
  border-radius: 28px;
  padding: 32px;
  box-shadow: 0 40px 120px rgba(15, 23, 42, 0.25);
}

.eyebrow {
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6366f1;
  margin-bottom: 8px;
}

h2 {
  margin: 0 0 16px;
  font-size: 1.8rem;
}

ol {
  margin: 0 0 24px 20px;
  color: #475569;
  line-height: 1.5;
}

.actions {
  display: flex;
  gap: 12px;
}

button {
  border: none;
  border-radius: 999px;
  padding: 12px 20px;
  font-size: 1rem;
  cursor: pointer;
}

button:not(.ghost) {
  background: linear-gradient(120deg, #6366f1, #8b5cf6);
  color: #fff;
  box-shadow: 0 12px 30px rgba(99, 102, 241, 0.35);
}

.ghost {
  background: transparent;
  border: 1px solid #cbd5f5;
  color: #1e293b;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
