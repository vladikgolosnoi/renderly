<template>
  <div class="template-modal" role="dialog" aria-modal="true">
    <div class="modal-card">
      <header>
        <div>
          <p class="eyebrow">Маркетплейс</p>
          <h3>Опубликовать шаблон проекта</h3>
          <p class="subtitle">
            Шаблон появится в каталоге и его смогут установить другие редакторы. Добавьте описание,
            категорию и пару тегов — так страницу быстрее найдут нужные люди.
          </p>
        </div>
        <button type="button" class="icon ghost" aria-label="Закрыть" @click="$emit('close')">
          ✕
        </button>
      </header>

      <form class="form" @submit.prevent="handleSubmit">
        <label>
          <span>Название</span>
          <input v-model="form.title" type="text" maxlength="80" required />
        </label>

        <label>
          <span>Короткое описание</span>
          <textarea
            v-model="form.description"
            rows="3"
            maxlength="240"
            placeholder="Что внутри набора блоков и для кого он подойдёт?"
          />
        </label>

        <label>
          <span>Категория</span>
          <div class="pill-row">
            <button
              v-for="option in categoryOptions"
              :key="option.value"
              type="button"
              class="pill"
              :class="{ active: form.category === option.value }"
              @click="toggleCategory(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </label>

        <label>
          <span>Теги</span>
          <div class="tags-field">
            <div class="selected-tags">
              <button
                v-for="tag in form.tags"
                :key="tag"
                type="button"
                class="tag active"
                @click="removeTag(tag)"
              >
                #{{ tag }}
                <span aria-hidden="true">×</span>
              </button>
              <input
                v-if="form.tags.length < maxTags"
                v-model="form.tagsInput"
                type="text"
                placeholder="Введите и нажмите Enter"
                @keydown.enter.prevent="commitTag"
                @keydown="handleTagKeydown"
              />
            </div>
            <div class="suggested">
              <button
                v-for="tag in suggestedTags"
                :key="tag"
                type="button"
                class="tag"
                :class="{ active: form.tags.includes(tag) }"
                @click="toggleTag(tag)"
              >
                #{{ tag }}
              </button>
            </div>
          </div>
        </label>

        <label>
          <span>Превью (URL картинки)</span>
          <input
            v-model="form.thumbnailUrl"
            type="url"
            placeholder="https://cdn.example.com/preview.png"
          />
        </label>

        <footer>
          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <button type="button" class="ghost" @click="$emit('close')">Отмена</button>
          <button type="submit" class="primary" :disabled="!canSubmit || publishing">
            {{ publishing ? "Публикуем..." : "Опубликовать" }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import type { ProjectDetail } from "@/types/blocks";

const categoryOptions = [
  { value: "landing", label: "Лендинг/промо" },
  { value: "lead", label: "Лид-магнит" },
  { value: "events", label: "События" },
  { value: "education", label: "Обучение" },
  { value: "commerce", label: "Продажи" },
  { value: "story", label: "История/кейс" }
] as const;

const suggestedTags = ["it", "образование", "маркетинг", "финансы", "стартап", "event"];
const maxTags = 5;

const props = defineProps<{
  project: ProjectDetail | null;
  publishing?: boolean;
  errorMessage?: string | null;
}>();

const emit = defineEmits<{
  (event: "close"): void;
  (event: "publish", payload: {
    title: string;
    description?: string;
    category?: string;
    tags?: string[];
    thumbnailUrl?: string;
  }): void;
}>();

const form = reactive({
  title: "",
  description: "",
  category: "",
  tags: [] as string[],
  tagsInput: "",
  thumbnailUrl: ""
});

const canSubmit = computed(() => Boolean(form.title.trim()));

watch(
  () => props.project,
  (project) => {
    if (!project) return;
    form.title = project.title || "";
    form.description = project.description || "";
    form.category = "";
    form.tags = [];
    form.tagsInput = "";
    form.thumbnailUrl = "";
  },
  { immediate: true }
);

function toggleCategory(value: string) {
  form.category = form.category === value ? "" : value;
}

function toggleTag(tag: string) {
  if (form.tags.includes(tag)) {
    form.tags = form.tags.filter((current) => current !== tag);
  } else if (form.tags.length < maxTags) {
    form.tags = [...form.tags, tag];
  }
}

function removeTag(tag: string) {
  form.tags = form.tags.filter((current) => current !== tag);
}

function commitTag() {
  const normalized = form.tagsInput.trim().toLowerCase();
  if (!normalized) return;
  toggleTag(normalized);
  form.tagsInput = "";
}

function handleTagKeydown(event: KeyboardEvent) {
  if (event.key === ",") {
    event.preventDefault();
    commitTag();
  }
}

function handleSubmit() {
  emit("publish", {
    title: form.title.trim(),
    description: form.description.trim() || undefined,
    category: form.category || undefined,
    tags: form.tags,
    thumbnailUrl: form.thumbnailUrl.trim() || undefined
  });
}
</script>

<style scoped>
.template-modal {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 32px 20px;
  z-index: 80;
}

.modal-card {
  background: #fff;
  border-radius: 28px;
  width: min(720px, 100%);
  max-height: 90vh;
  overflow: auto;
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 40px 100px rgba(15, 23, 42, 0.35);
}

header {
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 4px;
}

.subtitle {
  color: #475569;
  margin: 4px 0 0;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.9rem;
  color: #475569;
}

input,
textarea {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 10px 14px;
  font-size: 1rem;
}

textarea {
  resize: none;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill {
  border: 1px solid #cbd5f5;
  border-radius: 999px;
  padding: 6px 14px;
  background: #f8fafc;
  cursor: pointer;
  font-size: 0.85rem;
}

.pill.active {
  background: #312e81;
  border-color: #312e81;
  color: #fff;
}

.tags-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  border: 1px dashed #c7d2fe;
  border-radius: 16px;
}

.selected-tags input {
  border: none;
  outline: none;
  padding: 4px;
  min-width: 140px;
}

.tag {
  border: 1px solid #c7d2fe;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 0.85rem;
  background: #f8fafc;
  cursor: pointer;
}

.tag.active {
  background: #eef2ff;
  border-color: #818cf8;
  color: #312e81;
}

.suggested {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.error {
  color: #b91c1c;
  font-size: 0.85rem;
  margin-right: auto;
}

.primary {
  border: none;
  border-radius: 12px;
  background: #2563eb;
  color: #fff;
  padding: 10px 18px;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ghost {
  border: 1px solid #cbd5f5;
  border-radius: 12px;
  padding: 10px 18px;
  background: transparent;
  color: #0f172a;
  cursor: pointer;
}

.icon {
  height: 40px;
  width: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
