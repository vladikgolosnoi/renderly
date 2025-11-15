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
  background: #fff;
  border-radius: 18px;
  border: 1px solid #e2e8f0;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  color: #475569;
  background: #f1f5f9;
  padding: 6px 10px;
  border-radius: 999px;
}

.locale-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.locale-chip {
  border: 1px solid #cbd5f5;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.locale-chip.active {
  border-color: #2563eb;
  background: #f0f4ff;
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
  color: #475569;
  margin-left: 6px;
}

.chip-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.ghost {
  border: 1px solid #cbd5f5;
  background: transparent;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.85rem;
  cursor: pointer;
  color: #0f172a;
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
  color: #475569;
}

input {
  border-radius: 12px;
  border: 1px solid #cbd5f5;
  padding: 8px 12px;
}

button[type="submit"] {
  border: none;
  background: #2563eb;
  color: #fff;
  border-radius: 12px;
  padding: 10px 16px;
  cursor: pointer;
}

.empty {
  color: #94a3b8;
  font-size: 0.9rem;
}
</style>
