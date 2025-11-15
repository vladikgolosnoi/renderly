<template>
  <section class="comment-feed">
    <header>
      <div class="header-text">
        <p class="eyebrow">{{ title }}</p>
        <span class="muted">Отзывы от сообщества</span>
      </div>
      <span class="pill">{{ comments?.length ?? 0 }}</span>
    </header>

    <form class="composer" @submit.prevent="handleSubmit">
      <textarea
        v-model="draft"
        rows="3"
        placeholder="Поделитесь впечатлениями или идеями улучшения"
        :disabled="submitting"
      />
      <div class="composer-actions">
        <small>{{ helperText }}</small>
        <button type="submit" :disabled="!canSubmit || submitting">
          {{ submitting ? "Отправляем..." : "Опубликовать" }}
        </button>
      </div>
    </form>

    <div v-if="loading" class="skeleton">
      <div v-for="n in 2" :key="n" class="skeleton-row" />
    </div>

    <TransitionGroup name="comment-list" tag="ul" class="comments">
      <li v-for="comment in comments" :key="comment.id">
        <div class="avatar">{{ initials(comment.author_name) }}</div>
        <div>
          <div class="comment-meta">
            <strong>{{ comment.author_name || "Гость Renderly" }}</strong>
            <span>{{ formatDate(comment.created_at) }}</span>
          </div>
          <p>{{ comment.message }}</p>
        </div>
      </li>
    </TransitionGroup>
    <p v-if="!loading && !comments?.length" class="empty">Пока нет комментариев — будьте первыми</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import type { TemplateComment } from "@/types/blocks";

const props = defineProps<{
  templateId: number;
  title: string;
  comments?: TemplateComment[];
  loading?: boolean;
  submitting?: boolean;
  autoload?: boolean;
}>();

const emit = defineEmits<{
  (event: "load"): void;
  (event: "submit", payload: { templateId: number; message: string }): void;
}>();

const draft = ref("");
const helperText = computed(() =>
  draft.value.length ? `${draft.value.length}/2000` : "До 2000 символов"
);
const canSubmit = computed(() => draft.value.trim().length > 0 && draft.value.length <= 2000);
const shouldAutoload = computed(() => props.autoload !== false);

function handleSubmit() {
  if (!canSubmit.value) return;
  emit("submit", { templateId: props.templateId, message: draft.value.trim() });
  draft.value = "";
}

function initials(name?: string | null) {
  if (!name) {
    return "Г";
  }
  const parts = name.trim().split(" ");
  const first = parts[0]?.[0] ?? "";
  const last = parts[1]?.[0] ?? "";
  const letters = `${first}${last}`.trim();
  return letters ? letters.toUpperCase() : first.toUpperCase() || "Г";
}

const formatter = new Intl.DateTimeFormat("ru-RU", {
  dateStyle: "medium",
  timeStyle: "short"
});
const formatDate = (value: string) => formatter.format(new Date(value));

onMounted(() => {
  if (shouldAutoload.value) {
    emit("load");
  }
});

watch(
  () => [props.templateId, shouldAutoload.value],
  ([, autoload]) => {
    if (autoload) {
      emit("load");
    }
  }
);
</script>

<style scoped>
.comment-feed {
  border-radius: 20px;
  background: rgba(248, 250, 252, 0.95);
  border: 1px solid rgba(99, 102, 241, 0.12);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
  color: rgba(15, 23, 42, 0.65);
}

.muted {
  font-size: 0.8rem;
  color: rgba(15, 23, 42, 0.55);
}

.pill {
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.25);
  padding: 4px 12px;
  font-size: 0.8rem;
  color: #312e81;
  background: rgba(255, 255, 255, 0.9);
}

.composer textarea {
  width: 100%;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 14px;
  padding: 12px;
  resize: none;
  font-family: inherit;
  font-size: 0.95rem;
  min-height: 86px;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.05);
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  gap: 12px;
}

.composer-actions button {
  border: none;
  border-radius: 12px;
  background: #4f46e5;
  color: #fff;
  padding: 8px 18px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 8px 16px rgba(79, 70, 229, 0.25);
}

.composer-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.comments {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comments li {
  display: flex;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.comments li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(129, 140, 248, 0.3), rgba(14, 165, 233, 0.25));
  color: #1e1b4b;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.comment-meta {
  display: flex;
  gap: 8px;
  font-size: 0.82rem;
  color: rgba(15, 23, 42, 0.5);
}

.comment-meta strong {
  color: #0f172a;
}

.empty {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(15, 23, 42, 0.6);
}

.skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton-row {
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(90deg, #e2e8f0, #f8fafc, #e2e8f0);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.comment-list-enter-active,
.comment-list-leave-active {
  transition: all 0.2s ease;
}

.comment-list-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}

.comment-list-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
