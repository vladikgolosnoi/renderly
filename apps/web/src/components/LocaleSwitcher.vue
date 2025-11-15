<template>
  <section class="locale-switcher">
    <header>
      <div>
        <h3>Языки лендинга</h3>
        <p>Выберите активный язык и управляйте набором локалей.</p>
      </div>
      <span class="active-label">Текущий: {{ activeLocale.toUpperCase() }}</span>
    </header>

    <div class="locale-list">
      <article
        v-for="locale in locales"
        :key="locale"
        class="locale-chip"
        :class="{ active: locale === activeLocale }"
      >
        <button class="chip-main" type="button" @click="$emit('change-locale', locale)">
          {{ locale.toUpperCase() }}
          <small v-if="locale === defaultLocale">(default)</small>
        </button>
        <div class="chip-actions">
          <button
            v-if="locale !== defaultLocale"
            class="ghost"
            type="button"
            @click="$emit('set-default', locale)"
          >
            Сделать основным
          </button>
          <button
            v-if="locale !== defaultLocale && locales.length > 1"
            class="ghost"
            type="button"
            @click="$emit('remove-locale', locale)"
          >
            Удалить
          </button>
        </div>
      </article>
      <p v-if="!locales.length" class="empty">Языков пока нет.</p>
    </div>

    <form class="add-form" @submit.prevent="addLocale">
      <label>
        <span>Добавить язык (ISO-код, например en)</span>
        <input v-model="newLocale" placeholder="en" maxlength="5" />
      </label>
      <button type="submit">Добавить</button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  locales: string[];
  defaultLocale: string;
  activeLocale: string;
}>();

const emit = defineEmits<{
  (e: "change-locale", payload: string): void;
  (e: "add-locale", payload: string): void;
  (e: "set-default", payload: string): void;
  (e: "remove-locale", payload: string): void;
}>();

const newLocale = ref("");

function addLocale() {
  if (!newLocale.value.trim()) return;
  emit("add-locale", newLocale.value);
  newLocale.value = "";
}
</script>

<style scoped>
.locale-switcher {
  background: var(--panel-surface);
  border-radius: 18px;
  border: 1px solid var(--divider-color);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--panel-shadow);
}

header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.active-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  background: var(--panel-soft);
  padding: 6px 10px;
  border-radius: 999px;
}

.locale-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.locale-chip {
  border: 1px solid var(--divider-color);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: var(--panel-soft);
}

.locale-chip.active {
  border-color: var(--accent);
  background: var(--accent-muted);
}

.chip-main {
  border: none;
  background: transparent;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
}

.chip-main small {
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: 6px;
}

.chip-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.ghost {
  border: 1px solid var(--divider-color);
  background: transparent;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.85rem;
  cursor: pointer;
  color: var(--text-primary);
}

.add-form {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.add-form label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

input {
  border-radius: 12px;
  border: 1px solid var(--input-border);
  padding: 8px 12px;
  background: var(--input-bg);
  color: var(--input-text);
}

button[type="submit"] {
  border: none;
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: #fff;
  border-radius: 12px;
  padding: 10px 16px;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.2);
}

.empty {
  color: var(--text-secondary);
  font-size: 0.9rem;
}
</style>
