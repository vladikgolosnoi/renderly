<template>
  <section class="share-view" :class="{ loading }">
    <header class="share-hero">
      <div>
        <p class="eyebrow">{{ copy.eyebrow }}</p>
        <h1>{{ share?.project.title ?? copy.fallbackTitle }}</h1>
        <p>{{ share ? copy.subtitle : copy.loading }}</p>
      </div>
      <div class="share-actions" v-if="share">
        <button class="ghost" type="button" @click="copyLink">
          {{ copied ? copy.actions.copied : copy.actions.copy }}
        </button>
        <button class="primary" type="button" @click="openEditor">
          {{ copy.actions.edit }}
        </button>
      </div>
    </header>

    <div v-if="loading" class="share-state">
      <div class="spinner" />
      <p>{{ copy.loading }}</p>
    </div>

    <div v-else-if="error" class="share-state error">
      <h2>{{ error.title }}</h2>
      <p>{{ error.message }}</p>
      <button v-if="error.retriable" class="primary" type="button" @click="loadShare">
        {{ copy.actions.retry }}
      </button>
    </div>

    <div v-else-if="share" class="share-body">
      <aside class="share-details">
        <dl>
          <div>
            <dt>{{ copy.details.project }}</dt>
            <dd>{{ share.project.title }}</dd>
          </div>
          <div>
            <dt>{{ copy.details.updated }}</dt>
            <dd>{{ formatDate(share.project.updated_at) }}</dd>
          </div>
          <div>
            <dt>{{ copy.details.expires }}</dt>
            <dd>{{ describeExpiration(share.expires_at) }}</dd>
          </div>
          <div>
            <dt>{{ copy.details.comments }}</dt>
            <dd>{{ share.allow_comments ? copy.details.commentsOn : copy.details.commentsOff }}</dd>
          </div>
          <div>
            <dt>{{ copy.details.slug }}</dt>
            <dd>{{ share.project.slug }}</dd>
          </div>
          <div>
            <dt>{{ copy.details.link }}</dt>
            <dd class="share-link">{{ publicLink }}</dd>
          </div>
        </dl>
      </aside>
      <div class="share-frame">
        <iframe
          title="share-preview"
          :srcdoc="share.html"
          sandbox="allow-same-origin allow-scripts allow-forms"
        />
      </div>
    </div>

    <section v-if="share?.allow_comments" class="comment-panel">
      <header>
        <div>
          <h2>{{ copy.comments.title }}</h2>
          <p>{{ copy.comments.subtitle }}</p>
        </div>
        <button class="ghost" type="button" @click="loadComments" :disabled="commentsLoading">
          {{ commentsLoading ? copy.comments.refreshing : copy.comments.refresh }}
        </button>
      </header>
      <div class="comment-body">
        <div class="comment-feed">
          <p v-if="!comments.length && !commentsLoading" class="comment-empty">
            {{ copy.comments.empty }}
          </p>
          <ul v-else>
            <li v-for="comment in comments" :key="comment.id">
              <article>
                <header>
                  <strong>{{ comment.author_name || copy.comments.anonymous }}</strong>
                  <time>{{ formatDate(comment.created_at) }}</time>
                </header>
                <p>{{ comment.message }}</p>
              </article>
            </li>
          </ul>
        </div>
        <form class="comment-form" @submit.prevent="submitComment">
          <h3>{{ copy.comments.form.title }}</h3>
          <p>{{ copy.comments.form.subtitle }}</p>
          <div class="input-row">
            <input
              v-model="commentForm.name"
              type="text"
              :placeholder="copy.comments.form.name"
              maxlength="120"
            />
            <input
              v-model="commentForm.email"
              type="email"
              :placeholder="copy.comments.form.email"
            />
          </div>
          <textarea
            v-model="commentForm.message"
            :placeholder="copy.comments.form.message"
            rows="4"
            maxlength="2000"
            required
          ></textarea>
          <p v-if="commentError" class="comment-error">{{ commentError }}</p>
          <p v-if="commentSuccess" class="comment-success">{{ commentSuccess }}</p>
          <button class="primary" type="submit" :disabled="commentSending">
            {{ commentSending ? copy.comments.form.sending : copy.comments.form.submit }}
          </button>
        </form>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";
import api from "@/api/client";
import type { Project, ProjectShareComment } from "@/types/blocks";

interface ShareResponse {
  project: Project;
  html: string;
  label?: string | null;
  expires_at?: string | null;
  allow_comments: boolean;
  comment_count?: number;
}

const copy = {
  eyebrow: "Renderly Preview",
  fallbackTitle: "Загружаем проект...",
  subtitle: "Это интерактивный предпросмотр. Внесите правки вместе с командой в редакторе.",
  loading: "Собираем HTML и данные...",
  actions: {
    copy: "Скопировать ссылку",
    copied: "Скопировано!",
    edit: "Открыть в Renderly",
    retry: "Попробовать снова"
  },
  details: {
    project: "Проект",
    updated: "Обновлён",
    expires: "Доступен до",
    comments: "Комментарии",
    commentsOn: "Можно оставлять комментарии",
    commentsOff: "Комментарии отключены",
    slug: "Slug",
    link: "Прямая ссылка"
  },
  comments: {
    title: "Отзывы и комментарии",
    subtitle: "Оставьте заметку для команды Renderly.",
    refresh: "Обновить",
    refreshing: "Обновляем...",
    empty: "Комментариев пока нет. Станьте первым!",
    anonymous: "Гость",
    success: "Спасибо! Комментарий отправлен.",
    error: "Не удалось отправить комментарий. Попробуйте ещё раз.",
    form: {
      title: "Новый комментарий",
      subtitle: "Имя и email необязательны.",
      name: "Ваше имя",
      email: "Email для связи",
      message: "Сообщение",
      submit: "Отправить",
      sending: "Отправляем..."
    }
  },
  errors: {
    expired: {
      title: "Ссылка больше не активна",
      message: "Попросите владельца проекта отправить новую ссылку.",
      retriable: false
    },
    generic: {
      title: "Не удалось загрузить проект",
      message: "Проверьте интернет-соединение и попробуйте ещё раз.",
      retriable: true
    }
  }
} as const;

const route = useRoute();
const share = ref<ShareResponse | null>(null);
const loading = ref(true);
const copied = ref(false);
const error = ref<{ title: string; message: string; retriable: boolean } | null>(null);
const comments = ref<ProjectShareComment[]>([]);
const commentsLoading = ref(false);
const commentSending = ref(false);
const commentError = ref<string | null>(null);
const commentSuccess = ref<string | null>(null);
const commentForm = reactive({
  name: "",
  email: "",
  message: ""
});

const publicLink = computed(() => {
  if (typeof window === "undefined") {
    return route.fullPath;
  }
  return `${window.location.origin}${route.fullPath}`;
});

function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short"
  });
}

function describeExpiration(value?: string | null) {
  if (!value) {
    return "Без ограничения";
  }
  return formatDate(value);
}

async function loadShare() {
  loading.value = true;
  error.value = null;
  try {
    const token = route.params.token;
    const { data } = await api.get<ShareResponse>(`/shares/${token}`);
    share.value = data;
    if (data.allow_comments) {
      await loadComments();
    } else {
      comments.value = [];
    }
  } catch (err) {
    const status = axios.isAxiosError(err) ? err.response?.status : (err as { response?: { status?: number } } | null)?.response?.status;
    if (status === 410) {
      error.value = copy.errors.expired;
    } else {
      error.value = copy.errors.generic;
    }
  } finally {
    loading.value = false;
  }
}

async function copyLink() {
  const text = publicLink.value;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const area = document.createElement("textarea");
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      document.body.removeChild(area);
    }
    copied.value = true;
    window.setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    console.error(err);
  }
}

function openEditor() {
  if (!share.value) return;
  const target = `/login?redirect=/editor/${share.value.project.id}`;
  window.open(target, "_blank", "noopener");
}

async function loadComments() {
  if (!share.value?.allow_comments) return;
  commentsLoading.value = true;
  commentError.value = null;
  try {
    const { data } = await api.get<ProjectShareComment[]>(`/shares/${route.params.token}/comments`);
    comments.value = data;
  } catch (err) {
    console.error(err);
    commentError.value = copy.comments.error;
  } finally {
    commentsLoading.value = false;
  }
}

async function submitComment() {
  if (!share.value?.allow_comments || !commentForm.message.trim()) return;
  commentSending.value = true;
  commentError.value = null;
  commentSuccess.value = null;
  try {
    const payload = {
      author_name: commentForm.name || undefined,
      author_email: commentForm.email || undefined,
      message: commentForm.message
    };
    const { data } = await api.post<ProjectShareComment>(
      `/shares/${route.params.token}/comments`,
      payload
    );
    comments.value = [...comments.value, data];
    commentForm.name = "";
    commentForm.email = "";
    commentForm.message = "";
    commentSuccess.value = copy.comments.success;
  } catch (err) {
    console.error(err);
    commentError.value = copy.comments.error;
  } finally {
    commentSending.value = false;
  }
}

onMounted(() => {
  loadShare().catch(() => {
    error.value = copy.errors.generic;
  });
});
</script>

<style scoped>
.share-view {
  min-height: 100vh;
  padding: 32px clamp(16px, 5vw, 48px);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.share-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-size: 0.75rem;
  color: #64748b;
  margin: 0 0 8px;
}

.share-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.share-state {
  border: 1px dashed #cbd5f5;
  border-radius: 18px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #475569;
}

.share-state.error h2 {
  margin: 0;
  color: #b91c1c;
}

.spinner {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 3px solid #cbd5f5;
  border-top-color: #2563eb;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.share-body {
  display: grid;
  grid-template-columns: minmax(260px, 320px) 1fr;
  gap: 20px;
  align-items: flex-start;
}

.share-details {
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 20px;
  background: #fff;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
}

.share-details dl {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.share-details dt {
  font-size: 0.8rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.share-details dd {
  margin: 4px 0 0;
  font-size: 1rem;
  color: #0f172a;
}

.share-link {
  font-family: "JetBrains Mono", monospace;
  word-break: break-all;
  color: #2563eb;
}

.share-frame {
  background: #fff;
  border-radius: 32px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.06);
}

.share-frame iframe {
  width: 100%;
  min-height: 70vh;
  border: none;
  border-radius: 24px;
  background: #fff;
  box-shadow: inset 0 0 10px rgba(15, 23, 42, 0.05);
}

.comment-panel {
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 24px;
  background: #fff;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-panel header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.comment-panel h2 {
  margin: 0 0 4px;
}

.comment-panel p {
  margin: 0;
}

.comment-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 24px;
}

.comment-feed ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-feed article {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 16px;
  background: #f8fafc;
}

.comment-feed header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.85rem;
  color: #475569;
}

.comment-feed p {
  margin: 8px 0 0;
  color: #0f172a;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.comment-empty {
  color: #94a3b8;
  font-style: italic;
}

.comment-form {
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 16px;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-form h3 {
  margin: 0;
}

.comment-form .input-row {
  display: flex;
  gap: 12px;
}

.comment-form input,
.comment-form textarea {
  width: 100%;
  border: 1px solid #cbd5f5;
  border-radius: 12px;
  padding: 10px 12px;
  font-family: inherit;
  font-size: 1rem;
}

.comment-form textarea {
  resize: vertical;
}

.comment-error {
  color: #b91c1c;
  margin: 0;
}

.comment-success {
  color: #15803d;
  margin: 0;
}

.primary {
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  padding: 10px 20px;
  cursor: pointer;
}

.ghost {
  border: 1px solid #cbd5f5;
  border-radius: 12px;
  background: transparent;
  color: #2563eb;
  padding: 10px 20px;
  cursor: pointer;
}

@media (max-width: 960px) {
  .share-body {
    grid-template-columns: 1fr;
  }
  .comment-body {
    grid-template-columns: 1fr;
  }
  .comment-form .input-row {
    flex-direction: column;
  }
}
</style>
