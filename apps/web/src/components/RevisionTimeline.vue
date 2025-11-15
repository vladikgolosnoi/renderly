<template>
  <section class="panel">
    <header>
      <div>
        <h3>История версий</h3>
        <p>Просматривайте изменения и откатывайтесь к любому состоянию.</p>
      </div>
      <div class="actions">
        <button class="ghost" type="button" :disabled="loading" @click="$emit('refresh')">
          Обновить
        </button>
      </div>
    </header>
    <ul v-if="revisions.length" class="timeline">
      <li v-for="revision in revisions" :key="revision.id">
        <div class="meta">
          <strong>{{ formatAction(revision.action) }}</strong>
          <small>
            {{ formatDate(revision.created_at) }}
            <span v-if="revision.user_name">· {{ revision.user_name }}</span>
          </small>
        </div>
        <div class="diff">
          <span v-if="revision.diff?.added?.length">+{{ revision.diff.added.length }} блок(а)</span>
          <span v-if="revision.diff?.removed?.length">-{{ revision.diff.removed.length }} блок(а)</span>
          <span v-if="revision.diff?.changed?.length">Δ {{ revision.diff.changed.length }} блок(а)</span>
          <span v-if="revision.diff?.theme_changed">Тема изменена</span>
        </div>
        <button class="ghost" type="button" @click="$emit('restore', revision.id)">
          Откатить
        </button>
      </li>
    </ul>
    <p v-else class="empty">{{ loading ? "Загрузка..." : "Ревизий пока нет." }}</p>
  </section>
</template>

<script setup lang="ts">
import type { ProjectRevision } from "@/types/blocks";

defineProps<{
  revisions: ProjectRevision[];
  loading: boolean;
}>();

defineEmits<{
  (e: "restore", id: number): void;
  (e: "refresh"): void;
}>();

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function formatAction(action: string) {
  const map: Record<string, string> = {
    "block.add": "Добавлен блок",
    "block.update": "Изменён блок",
    "block.delete": "Удалён блок",
    "theme.update": "Обновлена тема",
    "revision.restore": "Откат к ревизии"
  };
  return map[action] ?? action;
}
</script>

<style scoped>
.panel {
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 8px;
}

.timeline {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.timeline li {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta strong {
  font-size: 0.95rem;
}

.meta small {
  color: #64748b;
}

.diff {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 0.85rem;
  color: #334155;
}

.ghost {
  border-radius: 999px;
  border: 1px solid #2563eb;
  background: transparent;
  color: #2563eb;
  padding: 6px 12px;
  align-self: flex-start;
  cursor: pointer;
}

.empty {
  color: #94a3b8;
}
</style>
