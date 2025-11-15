<template>
  <div class="modal-overlay" role="dialog" aria-modal="true">
    <div class="modal-card">
      <header>
        <div>
          <p class="eyebrow">ПЕРЕД ПУБЛИКАЦИЕЙ</p>
          <h3>Проверьте ключевые настройки вашего лендинга</h3>
        </div>
        <button class="ghost" type="button" @click="$emit('close')">Закрыть</button>
      </header>
      <section class="checklist">
        <article v-for="item in checklist" :key="item.key" :class="{ ok: item.ok }">
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
            <small v-if="!item.required" class="optional">Опционально</small>
          </div>
          <span class="status" :class="{ ok: item.ok }">
            {{ item.ok ? status.ready : status.fix }}
          </span>
        </article>
      </section>
      <footer>
        <button class="ghost" type="button" @click="$emit('close')">Вернуться</button>
        <button class="primary" type="button" :disabled="!canPublish" @click="$emit('publish')">
          {{ publishLabel }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const status = {
  ready: "Готово",
  fix: "Нужно исправить"
};

const props = defineProps<{
  hasSeo: boolean;
  hasBlocks: boolean;
  hasForms: boolean;
  publishing?: boolean;
}>();

type ChecklistItem = {
  key: string;
  title: string;
  description: string;
  ok: boolean;
  required: boolean;
};

const checklist = computed<ChecklistItem[]>(() => [
  {
    key: "blocks",
    title: "Контент готов",
    description: "На странице есть хотя бы один блок, включая hero и CTA.",
    ok: props.hasBlocks,
    required: true
  },
  {
    key: "seo",
    title: "Метаданные заполнены",
    description: "В настройках проекта указаны title и description.",
    ok: props.hasSeo,
    required: false
  },
  {
    key: "forms",
    title: "Формы настроены",
    description: "Форма содержит webhook или включён сбор лидов.",
    ok: props.hasForms,
    required: false
  }
]);

const requiredChecks = computed(() => checklist.value.filter((item) => item.required));
const canPublish = computed(() => requiredChecks.value.every((item) => item.ok) && !props.publishing);
const publishLabel = computed(() => (props.publishing ? "Публикуем..." : "Опубликовать"));
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  z-index: 60;
}

.modal-card {
  background: #fff;
  border-radius: 28px;
  padding: 24px;
  max-width: 640px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.25);
}

header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  color: #94a3b8;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

article {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

article.ok {
  border-color: #22c55e;
  background: #ecfdf5;
}

.status {
  font-size: 0.85rem;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #fcd34d;
  color: #92400e;
}

.status.ok {
  border-color: #22c55e;
  color: #15803d;
}

.optional {
  display: inline-block;
  color: #94a3b8;
  margin-top: 4px;
}

footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.ghost {
  border: 1px solid #94a3b8;
  background: transparent;
  color: #0f172a;
  border-radius: 12px;
  padding: 8px 14px;
  cursor: pointer;
}

.primary {
  border: none;
  border-radius: 12px;
  background: #2563eb;
  color: #fff;
  padding: 8px 18px;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
