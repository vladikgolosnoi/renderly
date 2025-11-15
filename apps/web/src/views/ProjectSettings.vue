п»ї<template>
  <section v-if="project" class="settings-page">
    <Breadcrumbs :items="[{ label: copy.meta.dashboard, to: '/' }, { label: copy.meta.settings }]" />

    <header class="settings-hero">
      <div>
        <p class="eyebrow">{{ copy.hero.eyebrow }}</p>
        <h2>{{ project.title }}</h2>
        <p>{{ copy.hero.description }}</p>
      </div>
      <div class="header-actions">
        <button class="ghost" @click="goBack">{{ copy.hero.back }}</button>
        <button class="primary" @click="goMarketplace">{{ copy.hero.marketplace }}</button>
      </div>
    </header>

    <article class="card">
      <div class="card-header">
        <div>
          <h3>{{ copy.sections.general.title }}</h3>
          <p>{{ copy.sections.general.subtitle }}</p>
        </div>
      </div>
      <form class="rename-form" @submit.prevent="submitRename">
        <label>
          <span>{{ copy.sections.general.labels.title }}</span>
          <input
            v-model="titleDraft"
            type="text"
            :placeholder="copy.sections.general.placeholder"
            maxlength="255"
            required
          />
        </label>
        <div class="form-actions">
          <button class="primary" type="submit" :disabled="renameSaving || !project">
            {{
              renameSaving
                ? copy.sections.general.actions.saving
                : copy.sections.general.actions.save
            }}
          </button>
          <p v-if="renameSuccess" class="success">{{ renameSuccess }}</p>
          <p v-if="renameError" class="error">{{ renameError }}</p>
        </div>
      </form>
    </article>

    <article class="card">
      <h3>{{ copy.sections.visibility.title }}</h3>
      <p>{{ copy.sections.visibility.subtitle }}</p>
      <div class="visibility-options">
        <label v-for="option in visibilityOptions" :key="option.value">
          <input
            type="radio"
            name="visibility"
            :value="option.value"
            :checked="project.visibility === option.value"
            @change="() => changeVisibility(option.value)"
          />
          <span>
            <strong>{{ option.label }}</strong>
            <small>{{ option.description }}</small>
          </span>
        </label>
      </div>
    </article>

    <article class="card marketplace-card">
      <div class="card-header">
        <div>
          <h3>{{ copy.sections.marketplace.title }}</h3>
          <p>{{ copy.sections.marketplace.subtitle }}</p>
        </div>
        <button
          class="primary"
          type="button"
          :disabled="project.visibility === 'private'"
          @click="openPublishModal"
        >
          {{ copy.sections.marketplace.action }}
        </button>
      </div>
      <p v-if="project.visibility === 'private'" class="hint">
        {{ copy.sections.marketplace.visibilityHint }}
      </p>
      <p v-if="marketplaceSuccess" class="success">{{ marketplaceSuccess }}</p>
      <p v-if="marketplaceError" class="error">{{ marketplaceError }}</p>
    </article>

    <TemplatePublishModal
      v-if="publishModalOpen"
      :project="project"
      :publishing="marketplacePublishing"
      :error-message="marketplaceModalError"
      @close="closePublishModal"
      @publish="submitTemplatePublish"
    />

    <article class="card">
      <div class="card-header">
        <div>
          <h3>{{ copy.sections.publication.title }}</h3>
          <p>{{ copy.sections.publication.subtitle }}</p>
        </div>
        <button class="ghost" type="button" @click="refreshPublicationStatus">
          {{ copy.actions.refreshPublication }}
        </button>
      </div>
      <template v-if="publication">
        <div class="publication-row">
          <input :value="publicationLink" readonly />
          <div class="publication-actions">
            <button class="ghost" type="button" @click="copyPublicationUrl">
              {{ copy.sections.publication.copy }}
            </button>
            <button class="ghost" type="button" @click="openPublication">
              {{ copy.sections.publication.open }}
            </button>
            <button
              class="danger"
              type="button"
              :disabled="removePublicationLoading"
              @click="removePublication"
            >
              {{
                removePublicationLoading
                  ? copy.sections.publication.removing
                  : copy.sections.publication.remove
              }}
            </button>
          </div>
        </div>
        <p class="hint">{{ copy.sections.publication.note }}</p>
      </template>
      <p v-else class="empty">{{ copy.sections.publication.empty }}</p>
      <p v-if="publicationMessage" class="success">{{ publicationMessage }}</p>
      <p v-if="publicationError" class="error">{{ publicationError }}</p>
    </article>

    <article class="card">
      <div class="card-header">
        <div>
          <h3>{{ copy.sections.members.title }}</h3>
          <p>{{ copy.sections.members.subtitle }}</p>
        </div>
        <form class="invite-form" @submit.prevent="invite">
          <input v-model="inviteEmail" type="email" placeholder="user@example.com" required />
          <select v-model="inviteRole">
            <option value="viewer">{{ copy.roles.viewer }}</option>
            <option value="editor">{{ copy.roles.editor }}</option>
          </select>
          <button type="submit">{{ copy.actions.invite }}</button>
        </form>
      </div>
      <p v-if="shareError" class="error">{{ shareError }}</p>
      <table v-if="members.length">
        <thead>
          <tr>
            <th>{{ copy.table.email }}</th>
            <th>{{ copy.table.role }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in members" :key="member.id">
            <td>{{ member.email }}</td>
            <td>
              <select :value="member.role" @change="(event) => updateRole(member, event)">
                <option value="viewer">{{ copy.roles.viewer }}</option>
                <option value="editor">{{ copy.roles.editor }}</option>
              </select>
            </td>
            <td class="actions">
              <button class="ghost" type="button" @click="remove(member)">
                {{ copy.actions.remove }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">{{ copy.table.empty }}</p>
    </article>

    <article class="card">
      <div class="card-header">
        <div>
          <h3>{{ copy.sections.share.title }}</h3>
          <p>{{ copy.sections.share.subtitle }}</p>
        </div>
        <form class="share-form" @submit.prevent="createShare">
          <input
            v-model="shareLabel"
            type="text"
            :placeholder="copy.share.form.label"
            maxlength="80"
          />
          <select v-model="shareExpiry">
            <option v-for="option in shareDurationOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <label class="checkbox">
            <input type="checkbox" v-model="shareAllowComments" />
            <span>{{ copy.share.form.allowComments }}</span>
          </label>
          <button class="primary" type="submit" :disabled="shareCreating">
            {{ shareCreating ? copy.share.actions.creating : copy.share.actions.create }}
          </button>
        </form>
      </div>
      <p v-if="shareLinkError" class="error">{{ shareLinkError }}</p>
      <div v-if="shareLinks.length" class="share-list">
        <article v-for="link in shareLinks" :key="link.id" class="share-row">
          <div class="share-meta">
            <strong>{{ link.label || copy.share.defaultLabel }}</strong>
            <p class="share-url">{{ formatShareUrl(link.token) }}</p>
            <small>{{ describeExpiration(link.expires_at) }}</small>
            <small>{{ describeLastAccess(link) }}</small>
            <small>{{ copy.share.views }} {{ link.access_count }}</small>
            <small>{{ commentSummary(link) }}</small>
          </div>
          <div class="share-actions">
            <button type="button" class="ghost" @click="copyShareLink(link)">
              {{
                copiedShareId === link.id ? copy.share.actions.copied : copy.share.actions.copy
              }}
            </button>
            <button type="button" class="danger" @click="revokeShare(link.id)">
              {{ copy.share.actions.revoke }}
            </button>
          </div>
        </article>
      </div>
      <p v-else class="empty">{{ copy.share.empty }}</p>
    </article>

    <article class="card danger-card">
      <div class="card-header">
        <div>
          <h3>{{ copy.sections.danger.title }}</h3>
          <p>{{ copy.sections.danger.subtitle }}</p>
        </div>
      </div>
      <p>{{ copy.sections.danger.description }}</p>
      <label class="danger-input">
        <span>
          {{ copy.sections.danger.instructions }}
          <strong v-if="project">"{{ project.title }}"</strong>
        </span>
        <input
          v-model="deleteConfirmation"
          type="text"
          :placeholder="copy.sections.danger.placeholder"
        />
      </label>
      <button
        type="button"
        class="danger"
        :disabled="!canDelete || deleteLoading"
        @click="confirmDelete"
      >
        {{ deleteLoading ? copy.sections.danger.deleting : copy.sections.danger.action }}
      </button>
      <p v-if="deleteError" class="error">{{ deleteError }}</p>
    </article>
  </section>
  <p v-else>{{ copy.actions.loading }}</p>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import TemplatePublishModal from "@/components/TemplatePublishModal.vue";
import { useProjectStore } from "@/stores/project";
import type { ProjectShareLink, ProjectVisibility } from "@/types/blocks";
import { isAxiosError } from "axios";

const copy = {
  meta: {
    dashboard: "Мои проекты",
    settings: "Настройки"
  },
  hero: {
    eyebrow: "Управление проектом",
    description: "Переименуйте лендинг, приглашайте коллег и управляйте публикациями.",
    back: "Вернуться в редактор",
    marketplace: "В каталог шаблонов"
  },
  sections: {
    general: {
      title: "Общие настройки",
      subtitle: "Название и описание помогут найти проект в команде.",
      labels: {
        title: "Название проекта"
      },
      placeholder: "Например, витрина агентства",
      actions: {
        save: "Сохранить",
        saving: "Сохраняем..."
      },
      success: "Название обновлено",
      unchanged: "Без изменений",
      error: "Не удалось сохранить проект",
      validation: "Название не может быть пустым"
    },
    visibility: {
      title: "Доступ",
      subtitle: "Укажите, кто видит проект в списке и редакторе."
    },
    marketplace: {
      title: "Публикация в каталоге",
      subtitle: "Расскажите о проекте в сообществе Renderly.",
      action: "Отправить заявку",
      visibilityHint: "Сделайте проект общим доступным прежде чем отправлять заявку.",
      success: "Заявка отправлена",
      error: "Не удалось отправить заявку. Попробуйте ещё раз."
    },
    publication: {
      title: "Публичная ссылка",
      subtitle: "Появляется после публикации из редактора.",
      empty: "Ссылка ещё не создана. Опубликуйте проект в редакторе.",
      copy: "Скопировать",
      copied: "Ссылка скопирована",
      open: "Открыть",
      remove: "Удалить",
      removing: "Удаляем...",
      removed: "Публикация удалена",
      error: "Не удалось удалить ссылку. Попробуйте позже.",
      note: "Чтобы обновить страницу, нажмите «Опубликовать» в редакторе."
    },
    members: {
      title: "Команда",
      subtitle: "Добавьте редакторов по email и назначьте роли."
    },
    share: {
      title: "Публичные ссылки",
      subtitle: "Создайте предпросмотр для отзывов."
    },
    danger: {
      title: "Опасная зона",
      subtitle: "Удаление проекта",
      description: "Удалённый проект нельзя восстановить.",
      instructions: "Введите название проекта, чтобы подтвердить удаление:",
      placeholder: "Название проекта",
      action: "Удалить проект",
      deleting: "Удаляем...",
      error: "Не удалось удалить проект"
    }
  },
  visibility: {
    private: {
      label: "Приватный",
      description: "Виден только вам и приглашённым участникам."
    },
    shared: {
      label: "По ссылке",
      description: "Доступ по приглашению или прямой ссылке."
    },
    public: {
      label: "Публичный",
      description: "Показывается всем пользователям команды."
    }
  },
  roles: {
    viewer: "Читатель",
    editor: "Редактор"
  },
  actions: {
    invite: "Пригласить",
    remove: "Удалить",
    refreshPublication: "Обновить ссылку",
    loading: "Загружаем..."
  },
  table: {
    email: "Email",
    role: "Роль",
    empty: "Пока нет участников."
  },
  errors: {
    invite: "Не удалось отправить приглашение. Проверьте email и попробуйте снова.",
    share: "Не получилось создать ссылку. Попробуйте ещё раз."
  },
  share: {
    defaultLabel: "Предпросмотр",
    empty: "Нет активных ссылок. Создайте первую.",
    views: "Просмотры:",
    commentsLabel: "Комментарии:",
    commentsDisabled: "Комментарии отключены",
    expiresNever: "Без срока",
    expiresOn: "Истекает",
    lastOpened: "Последний просмотр:",
    neverOpened: "Ещё не открывали",
    actions: {
      create: "Создать",
      creating: "Создаём...",
      copy: "Скопировать",
      copied: "Скопировано!",
      revoke: "Отозвать"
    },
    form: {
      label: "Название ссылки",
      allowComments: "Разрешить комментарии",
      expiry: "Срок действия",
      durations: {
        day: "24 часа",
        week: "7 дней",
        month: "30 дней",
        unlimited: "Не ограничено"
      }
    }
  }
} as const;

const router = useRouter();
const route = useRoute();
const store = useProjectStore();

const project = computed(() => store.current);
const inviteEmail = ref("");
const inviteRole = ref("viewer");
const shareError = ref<string | null>(null);
const shareLabel = ref("");
const shareExpiry = ref<"24" | "168" | "720" | "none">("168");
const shareAllowComments = ref(false);
const shareCreating = ref(false);
const shareLinkError = ref<string | null>(null);
const copiedShareId = ref<number | null>(null);
const publishModalOpen = ref(false);
const marketplacePublishing = ref(false);
const marketplaceSuccess = ref<string | null>(null);
const marketplaceError = ref<string | null>(null);
const marketplaceModalError = ref<string | null>(null);
const titleDraft = ref("");
const renameSaving = ref(false);
const renameSuccess = ref<string | null>(null);
const renameError = ref<string | null>(null);
const deleteConfirmation = ref("");
const deleteLoading = ref(false);
const deleteError = ref<string | null>(null);
const publicationMessage = ref<string | null>(null);
const publicationError = ref<string | null>(null);
const removePublicationLoading = ref(false);

const visibilityOptions: Array<{ value: ProjectVisibility; label: string; description: string }> = [
  {
    value: "private",
    label: copy.visibility.private.label,
    description: copy.visibility.private.description
  },
  {
    value: "shared",
    label: copy.visibility.shared.label,
    description: copy.visibility.shared.description
  },
  {
    value: "public",
    label: copy.visibility.public.label,
    description: copy.visibility.public.description
  }
];

const members = computed(() => store.members);
const shareLinks = computed(() => store.shareLinks);
const shareDurationOptions: Array<{ value: "24" | "168" | "720" | "none"; label: string }> = [
  { value: "24", label: copy.share.form.durations.day },
  { value: "168", label: copy.share.form.durations.week },
  { value: "720", label: copy.share.form.durations.month },
  { value: "none", label: copy.share.form.durations.unlimited }
];
const canDelete = computed(
  () => !!project.value && deleteConfirmation.value.trim() === project.value.title
);
const publication = computed(() => store.latestPublication);
const publicationLink = computed(() => {
  const info = publication.value;
  if (!info) {
    return "";
  }
  return info.custom_domain_url ?? info.cdn_url ?? "";
});

onMounted(async () => {
  const id = Number(route.params.id);
  if (!store.current || store.current.id !== id) {
    await store.fetchProject(id);
  }
  await Promise.all([
    store.fetchMembers(id),
    store.fetchShareLinks(id),
    store.fetchLatestPublication(id)
  ]);
});

watch(
  () => project.value?.title,
  (nextTitle) => {
    titleDraft.value = nextTitle ?? "";
    deleteConfirmation.value = "";
  },
  { immediate: true }
);

watch(titleDraft, () => {
  renameSuccess.value = null;
  renameError.value = null;
});

watch(deleteConfirmation, () => {
  deleteError.value = null;
});

watch(publication, () => {
  publicationError.value = null;
  removePublicationLoading.value = false;
});

function goBack() {
  router.push(`/editor/${project.value?.id}`);
}

function goMarketplace() {
  router.push("/marketplace");
}

function openPublishModal() {
  if (!project.value || project.value.visibility === "private") {
    marketplaceError.value = copy.sections.marketplace.visibilityHint;
    return;
  }
  marketplaceSuccess.value = null;
  marketplaceError.value = null;
  marketplaceModalError.value = null;
  publishModalOpen.value = true;
}

function closePublishModal() {
  if (marketplacePublishing.value) return;
  marketplaceModalError.value = null;
  publishModalOpen.value = false;
}

async function refreshPublicationStatus() {
  if (!project.value) return;
  publicationMessage.value = null;
  publicationError.value = null;
  try {
    await store.fetchLatestPublication(project.value.id);
  } catch {
    publicationError.value = copy.sections.publication.error;
  }
}

async function copyPublicationUrl() {
  const url = publicationLink.value;
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = url;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
  }
  publicationMessage.value = copy.sections.publication.copied;
  publicationError.value = null;
}

function openPublication() {
  const url = publicationLink.value;
  if (!url) return;
  window.open(url, "_blank", "noopener");
}

async function removePublication() {
  if (!project.value) return;
  removePublicationLoading.value = true;
  publicationMessage.value = null;
  publicationError.value = null;
  try {
    await store.clearLatestPublication();
    publicationMessage.value = copy.sections.publication.removed;
  } catch {
    publicationError.value = copy.sections.publication.error;
  } finally {
    removePublicationLoading.value = false;
  }
}

async function submitRename() {
  if (!project.value) return;
  const nextTitle = titleDraft.value.trim();
  if (!nextTitle) {
    renameError.value = copy.sections.general.validation;
    return;
  }
  if (nextTitle === project.value.title) {
    renameSuccess.value = copy.sections.general.unchanged;
    return;
  }
  renameSaving.value = true;
  renameSuccess.value = null;
  renameError.value = null;
  try {
    await store.renameProject(nextTitle);
    renameSuccess.value = copy.sections.general.success;
  } catch (error) {
    if (isAxiosError(error)) {
      const detail = (error.response?.data as { detail?: string })?.detail;
      renameError.value = detail ?? copy.sections.general.error;
    } else {
      renameError.value = copy.sections.general.error;
    }
  } finally {
    renameSaving.value = false;
  }
}

async function confirmDelete() {
  if (!project.value || !canDelete.value) return;
  deleteLoading.value = true;
  deleteError.value = null;
  try {
    await store.deleteProject(project.value.id);
    router.push("/");
  } catch (error) {
    if (isAxiosError(error)) {
      const detail = (error.response?.data as { detail?: string })?.detail;
      deleteError.value = detail ?? copy.sections.danger.error;
    } else {
      deleteError.value = copy.sections.danger.error;
    }
  } finally {
    deleteLoading.value = false;
  }
}

async function submitTemplatePublish(payload: {
  title: string;
  description?: string;
  category?: string;
  tags?: string[];
  thumbnailUrl?: string;
}) {
  if (!project.value) return;
  marketplacePublishing.value = true;
  marketplaceError.value = null;
  marketplaceModalError.value = null;
  try {
    await store.publishTemplate({
      projectId: project.value.id,
      title: payload.title,
      description: payload.description,
      category: payload.category,
      tags: payload.tags,
      thumbnailUrl: payload.thumbnailUrl
    });
    await store.fetchTemplates();
    marketplaceSuccess.value = copy.sections.marketplace.success;
    publishModalOpen.value = false;
  } catch (error) {
    console.error(error);
    let message: string = copy.sections.marketplace.error;
    if (isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail) && detail.length) {
        message = detail[0]?.msg ?? message;
      }
    }
    marketplaceModalError.value = message;
    marketplaceError.value = message;
  } finally {
    marketplacePublishing.value = false;
  }
}

async function changeVisibility(value: "private" | "shared" | "public") {
  await store.updateVisibility(value);
}

async function invite() {
  try {
    await store.inviteMember(inviteEmail.value, inviteRole.value as "viewer" | "editor");
    inviteEmail.value = "";
    shareError.value = null;
  } catch (error) {
    console.error(error);
    shareError.value = copy.errors.invite;
  }
}

function updateRole(member: (typeof members.value)[number], event: Event) {
  const target = event.target as HTMLSelectElement;
  void store.updateMemberRole(member.id, target.value as "viewer" | "editor");
}

function remove(member: (typeof members.value)[number]) {
  void store.removeMember(member.id);
}

function formatShareUrl(token: string) {
  if (typeof window === "undefined") {
    return `/share/${token}`;
  }
  return `${window.location.origin}/share/${token}`;
}

function formatDate(value?: string | null) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short"
  });
}

function describeExpiration(expiresAt?: string | null) {
  const formatted = formatDate(expiresAt);
  if (!formatted) {
    return copy.share.expiresNever;
  }
  return `${copy.share.expiresOn} ${formatted}`;
}

function describeLastAccess(link: ProjectShareLink) {
  const formatted = formatDate(link.last_accessed_at);
  if (!formatted) {
    return copy.share.neverOpened;
  }
  return `${copy.share.lastOpened} ${formatted}`;
}

function commentSummary(link: ProjectShareLink) {
  if (!link.allow_comments) {
    return copy.share.commentsDisabled;
  }
  const count = link.comment_count ?? 0;
  return `${copy.share.commentsLabel} ${count}`;
}

async function copyShareLink(link: ProjectShareLink) {
  const url = formatShareUrl(link.token);
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(url);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = url;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    copiedShareId.value = link.id;
    window.setTimeout(() => {
      if (copiedShareId.value === link.id) {
        copiedShareId.value = null;
      }
    }, 2000);
  } catch (error) {
    console.error(error);
  }
}

async function createShare() {
  if (!project.value) return;
  shareCreating.value = true;
  shareLinkError.value = null;
  try {
    const expires = shareExpiry.value === "none" ? null : Number(shareExpiry.value);
    await store.createShareLink({
      label: shareLabel.value.trim() || undefined,
      expiresInHours: expires,
      allowComments: shareAllowComments.value
    });
    shareLabel.value = "";
    shareAllowComments.value = false;
    shareExpiry.value = "168";
  } catch (error) {
    console.error(error);
    shareLinkError.value = copy.errors.share;
  } finally {
    shareCreating.value = false;
  }
}

async function revokeShare(shareId: number) {
  try {
    await store.revokeShareLink(shareId);
  } catch (error) {
    console.error(error);
    shareLinkError.value = copy.errors.share;
  }
}
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
  padding: 24px;
  border-radius: 24px;
  background: var(--hero-gradient);
  box-shadow: var(--shadow-soft);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card {
  background: var(--bg-surface);
  border-radius: 24px;
  padding: 20px;
  box-shadow: var(--shadow-soft);
  border: 1px solid var(--stroke);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.visibility-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.visibility-options label {
  border: 1px solid var(--stroke);
  border-radius: 16px;
  padding: 12px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.rename-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rename-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
  color: var(--text-primary);
}

.rename-form input {
  border: 1px solid var(--stroke);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 1rem;
}

.form-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.danger-card {
  border: 1px solid #fecaca;
  background: #fff5f5;
}

.danger-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.danger-input input {
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 10px 14px;
}

.danger-card .danger {
  align-self: flex-start;
}

.invite-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.invite-form input,
.invite-form select {
  border: 1px solid var(--stroke);
  border-radius: 12px;
  padding: 8px 12px;
}

.invite-form button {
  border: none;
  border-radius: 12px;
  background: var(--accent);
  color: white;
  padding: 8px 16px;
}

.share-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  align-items: center;
}

.share-form input,
.share-form select {
  border: 1px solid var(--stroke);
  border-radius: 12px;
  padding: 8px 12px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.checkbox input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.share-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-row {
  border: 1px solid var(--stroke);
  border-radius: 18px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.share-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.share-meta strong {
  font-size: 1rem;
}

.share-url {
  font-family: "JetBrains Mono", monospace;
  color: var(--accent);
  word-break: break-all;
  margin: 0;
}

.share-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

table {
  width: 100%;
  border-collapse: collapse;
}

table th,
table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--stroke);
}

.domain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.publication-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.publication-row input {
  width: 100%;
  border: 1px solid var(--stroke);
  border-radius: 12px;
  padding: 10px 12px;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.95rem;
  background: #f8fafc;
  color: var(--text-primary);
}

.publication-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.publication-actions .ghost,
.publication-actions .danger {
  padding: 8px 16px;
}

.hint {
  color: #64748b;
  font-size: 0.9rem;
  margin-top: 6px;
}

.domain-card {
  border: 1px solid var(--stroke);
  border-radius: 18px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.primary {
  border: none;
  border-radius: 12px;
  padding: 10px 18px;
  background: var(--accent);
  color: white;
  cursor: pointer;
}

.ghost {
  border: 1px solid var(--stroke);
  border-radius: 12px;
  background: transparent;
  color: var(--text-primary);
  padding: 10px 18px;
}

.danger {
  border: 1px solid #fecaca;
  border-radius: 12px;
  background: #fee2e2;
  color: #b91c1c;
  padding: 10px 18px;
}

.error {
  color: #b91c1c;
}

.success {
  color: #15803d;
}

.hint {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.empty {
  color: var(--text-secondary);
}
</style>







