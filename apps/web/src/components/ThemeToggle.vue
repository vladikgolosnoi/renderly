<template>
  <button class="theme-toggle" type="button" @click="toggle">
    <span v-if="theme === 'light'">🌞 Светлая тема</span>
    <span v-else>🌙 Тёмная тема</span>
  </button>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

const STORAGE_KEY = "renderly_theme";
const storedTheme =
  (typeof window !== "undefined"
    ? (localStorage.getItem(STORAGE_KEY) as "light" | "dark" | null)
    : null) ?? "light";

const theme = ref<"light" | "dark">(storedTheme);

function applyTheme(value: "light" | "dark") {
  if (typeof document === "undefined") {
    return;
  }
  const root = document.documentElement;
  if (value === "dark") {
    root.classList.add("theme-dark");
  } else {
    root.classList.remove("theme-dark");
  }
}

watch(
  theme,
  (value) => {
    applyTheme(value);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, value);
    }
  },
  { immediate: true }
);

function toggle() {
  theme.value = theme.value === "light" ? "dark" : "light";
}
</script>

<style scoped>
.theme-toggle {
  border: 1px solid var(--stroke);
  background: transparent;
  color: var(--text-primary);
  border-radius: 999px;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 0.85rem;
}
</style>
