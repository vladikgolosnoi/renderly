<template>
  <div class="marketplace-frame">
    <section class="marketplace">
      <Breadcrumbs :items="[{ label: copy.meta.dashboard, to: '/' }, { label: copy.meta.marketplace }]" />

      <header class="hero-card section-wide">
        <div class="hero-text">
          <p class="eyebrow">{{ copy.hero.eyebrow }}</p>
          <h2>{{ copy.hero.title }}</h2>
          <p>{{ copy.hero.subtitle }}</p>
          <div class="hero-badges">
            <span v-for="badge in copy.hero.badges" :key="badge" class="hero-badge">{{ badge }}</span>
          </div>
          <div class="hero-actions">
            <button type="button" class="primary" :disabled="loading" @click="reload">
              {{ loading ? copy.actions.refreshing : copy.actions.refresh }}
            </button>
            <button type="button" class="ghost" @click="router.push('/editor')">{{ copy.actions.create }}</button>
          </div>
          <div class="hero-meta">
            <div class="metric">
              <small>{{ copy.hero.stats.templates }}</small>
              <strong>{{ heroStats.templates }}</strong>
            </div>
            <div class="metric">
              <small>{{ copy.hero.stats.categories }}</small>
              <strong>{{ heroStats.categories }}</strong>
            </div>
            <div class="metric">
              <small>{{ copy.hero.stats.tags }}</small>
              <strong>{{ heroStats.tags }}</strong>
            </div>
            <div class="metric">
              <small>{{ copy.hero.stats.updated }}</small>
              <strong>{{ updatedLabel }}</strong>
            </div>
          </div>
        </div>
        <div class="hero-visual">
          <div class="hero-canvas">
            <div class="canvas-grid"></div>
            <div class="canvas-glow"></div>
            <div class="canvas-curve curve-one"></div>
            <div class="canvas-curve curve-two"></div>
            <div class="canvas-window">
              <div class="window-header">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div class="window-body">
                <div class="window-line long"></div>
                <div class="window-line medium"></div>
                <div class="window-line short"></div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <section class="filters-card section-wide">
        <div class="filters-column">
          <p class="eyebrow">{{ copy.filters.searchLabel }}</p>
          <div class="search-control">
            <input v-model="searchInput" type="search" :placeholder="copy.filters.search" />
            <button v-if="searchInput || selectedCategory" class="ghost small" type="button" @click="clearFilters">
              {{ copy.filters.clear }}
            </button>
          </div>
        </div>
        <div class="filters-divider" />
        <div class="filters-column">
          <p class="eyebrow small">{{ copy.filters.categories }}</p>
          <div class="select-control">
            <select :value="selectedCategory ?? ''" @change="onCategorySelect">
              <option value="">{{ copy.filters.categoriesAll }}</option>
              <option v-for="option in categoryOptions" :key="option.label" :value="option.value ?? ''">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="filters-divider" />
        <div class="filters-column">
          <p class="eyebrow small">{{ copy.filters.trending }}</p>
          <div class="select-control">
            <select v-model="selectedTag" @change="onTagSelect">
              <option value="">{{ copy.filters.tagPlaceholder }}</option>
              <option v-for="tag in trendingTags" :key="tag" :value="tag">#{{ tag }}</option>
            </select>
          </div>
        </div>
      </section>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <div class="card-list card-stack" :class="{ dimmed: loading && displayedTemplates.length }">
        <article v-for="template in displayedTemplates" :key="template.id" class="template-card">
          <div class="card-preview">
            <div class="preview-shell" :ref="(el) => bindPreviewShell(template.id, el)">
              <TemplatePreview
                :template-id="template.id"
                :title="template.title"
                :category="template.category"
                compact
                :target-height="500"
              />
            </div>
          </div>
          <div class="card-panel">
            <div class="panel-shell" :style="panelShellStyle(template.id)">
              <div class="panel-wrapper">
                <div class="panel-frame">
                  <div class="panel-body">
                    <div class="panel-header">
                      <div>
                        <span class="category-pill">{{ categoryLabel(template.category) }}</span>
                        <h3>{{ template.title }}</h3>
                      </div>
                      <span class="owner">{{ copy.cards.author }} {{ template.owner_name }}</span>
                    </div>
                    <p class="description">{{ template.description || copy.cards.fallback }}</p>
                    <ul v-if="template.tags?.length" class="tag-list">
                      <li v-for="tag in template.tags" :key="tag">#{{ tag }}</li>
                    </ul>
                    <div class="stats-row">
                      <div class="stat">
                        <small>{{ copy.cards.downloads }}</small>
                        <strong>{{ template.downloads ?? 0 }}</strong>
                      </div>
                      <div class="stat">
                        <small>{{ copy.cards.comments }}</small>
                        <strong>{{ commentsCount(template.id, template.comment_count ?? 0) }}</strong>
                      </div>
                      <div class="stat">
                        <small>{{ copy.cards.updated }}</small>
                        <strong>{{ formatDate(template.created_at) }}</strong>
                      </div>
                    </div>
                    <div class="panel-actions">
                      <button class="use-template" :disabled="importingId === template.id" @click="useTemplate(template.id)">
                        {{ importingId === template.id ? copy.cards.importing : copy.cards.use }}
                      </button>
                    <button class="flat" type="button" @click="toggleComments(template)">
                      {{ expandedCard === template.id ? copy.cards.hideToggle : copy.cards.commentCTA }}
                      &middot; {{ commentsCount(template.id, template.comment_count ?? 0) }}
                    </button>
                    </div>
                  </div>
                  <Transition name="collapse">
                    <div v-show="expandedCard === template.id" class="panel-comments">
                      <TemplateCommentFeed
                        :template-id="template.id"
                        :title="copy.cards.feedTitle"
                        :comments="commentsMap[template.id]"
                        :loading="commentsLoadingMap[template.id]"
                        :submitting="commentSubmitting[template.id]"
                        :autoload="false"
                        @submit="submitComment"
                      />
                    </div>
                  </Transition>
                </div>
              </div>
            </div>
          </div>
        </article>
        <div v-if="!displayedTemplates.length && !loading" class="empty-state">{{ copy.empty }}</div>
        <div v-if="loading && !displayedTemplates.length" class="skeleton-list">
          <div class="skeleton-card" v-for="n in 2" :key="n" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch, type ComponentPublicInstance } from "vue";
import { useRouter } from "vue-router";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import TemplatePreview from "@/components/TemplatePreview.vue";
import TemplateCommentFeed from "@/components/TemplateCommentFeed.vue";
import { useProjectStore } from "@/stores/project";
import type { CommunityTemplate } from "@/types/blocks";

const copy = {
  meta: {
    dashboard: "Панель управления",
    marketplace: "Маркетплейс"
  },
  hero: {
    eyebrow: "Галерея сообщества",
    title: "Готовые сайты и пресеты на любой случай",
    subtitle:
      "Витрина Renderly постоянно пополняется шаблонами дизайнеров. Просматривайте живые превью, вдохновляйтесь и переносите структуру в редактор за пару кликов.",
    stats: {
      templates: "Шаблонов в базе",
      categories: "Категории",
      tags: "Популярные теги",
      updated: "Обновлено"
    },
    badges: ["Тренды недели", "Анимация и 3D", "Готовые лендинги"]
  },
  actions: {
    refresh: "Обновить ленту",
    refreshing: "Обновляем...",
    create: "Открыть редактор"
  },
  filters: {
    searchLabel: "Поиск",
    search: "Введите нишу или название",
    categories: "Категория",
    categoriesAll: "Все категории",
    trending: "Теги",
    tagPlaceholder: "Любой тег",
    clear: "Сбросить фильтры"
  },
  cards: {
    author: "Автор:",
    fallback: "Описание пока не добавлено. Откройте превью, чтобы увидеть содержимое страницы.",
    downloads: "Использований",
    comments: "Комментарии",
    updated: "Добавлен",
    feedTitle: "Лента комментариев",
    importing: "Импортируем...",
    use: "Использовать шаблон",
    commentCTA: "Комментарии",
    hideToggle: "Скрыть"
  },
  empty: "Нет результатов по выбранным условиям. Попробуйте изменить фильтры.",
  errors: {
    load: "Не удалось загрузить шаблоны. Попробуйте позже.",
    import: "Не получилось импортировать шаблон. Проверьте соединение и повторите."
  }
} as const;

const categoryOptions = [
  { value: null, label: "Все" },
  { value: "landing", label: "Лендинги" },
  { value: "lead", label: "Заявки и лиды" },
  { value: "events", label: "События" },
  { value: "education", label: "Обучение" },
  { value: "commerce", label: "Интернет-магазины" },
  { value: "story", label: "Истории брендов" }
] as const;

const trendingTags = ["портфолио", "мероприятие", "онлайн-школа", "чат-бот", "маркетинг", "доставка"] as const;

const store = useProjectStore();
const router = useRouter();

const loading = ref(false);
const importingId = ref<number | null>(null);
const errorMessage = ref<string | null>(null);
const searchInput = ref("");
const searchTerm = ref("");
const selectedCategory = ref<string | null>(null);
const displayedTemplates = ref<CommunityTemplate[]>([]);
const commentSubmitting = ref<Record<number, boolean>>({});
const expandedCard = ref<number | null>(null);
const lastRefreshAt = ref(new Date());
const selectedTag = ref("");
const previewHeightMap = reactive<Record<number, number>>({});
const DEFAULT_PANEL_HEIGHT = 600;
const previewShellObservers = new Map<number, ResizeObserver>();

const commentsMap = computed(() => store.templateComments);
const commentsLoadingMap = computed(() => store.templateCommentsLoading);

const formatter = new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" });
const formatDate = (value: string) => formatter.format(new Date(value));

const updatedLabel = computed(() =>
  new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(
    lastRefreshAt.value
  )
);

const heroStats = computed(() => {
  const dataset = displayedTemplates.value.length ? displayedTemplates.value : store.templates;
  const templates = dataset.length;
  const categories = new Set(dataset.map((item) => item.category).filter(Boolean)).size;
  const tags = new Set(
    dataset.flatMap((item) => item.tags ?? []).filter((tag): tag is string => Boolean(tag && tag.trim()))
  ).size;
  return {
    templates: templates || "—",
    categories: categories || "—",
    tags: tags || "—"
  };
});

async function loadTemplates() {
  loading.value = true;
  try {
    await store.fetchTemplates({
      category: selectedCategory.value ?? undefined,
      search: searchTerm.value || undefined
    });
    errorMessage.value = null;
    lastRefreshAt.value = new Date();
  } catch (error) {
    console.error(error);
    errorMessage.value = copy.errors.load;
  } finally {
    loading.value = false;
  }
}

function reload() {
  void loadTemplates();
}

function selectCategory(value: string | null) {
  selectedCategory.value = value;
  reload();
}

function clearFilters() {
  searchInput.value = "";
  searchTerm.value = "";
  selectedCategory.value = null;
  reload();
}

function applyTag(tag: string) {
  searchInput.value = tag;
  searchTerm.value = tag;
  reload();
}

function onCategorySelect(event: Event) {
  const target = event.target as HTMLSelectElement;
  const value = target.value || null;
  if (selectedCategory.value === value) {
    return;
  }
  selectCategory(value);
}

function onTagSelect() {
  if (!selectedTag.value) {
    return;
  }
  applyTag(selectedTag.value);
  selectedTag.value = "";
}

let searchDebounce: ReturnType<typeof setTimeout> | null = null;
watch(
  () => searchInput.value,
  (value) => {
    if (searchDebounce) {
      clearTimeout(searchDebounce);
    }
    searchDebounce = setTimeout(() => {
      searchTerm.value = value.trim();
      reload();
    }, 350);
  }
);

watch(
  () => store.templates,
  (templates) => {
    displayedTemplates.value = templates;
    if (expandedCard.value && !templates.some((template) => template.id === expandedCard.value)) {
      expandedCard.value = null;
    }
  },
  { immediate: true }
);

function categoryLabel(value?: string | null) {
  if (!value) {
    return "Без категории";
  }
  return categoryOptions.find((option) => option.value === value)?.label ?? "Без категории";
}

function commentsCount(templateId: number, fallback = 0) {
  return commentsMap.value[templateId]?.length ?? fallback;
}

type PreviewShellTarget = Element | ComponentPublicInstance | null;

function resolvePreviewElement(target: PreviewShellTarget): HTMLElement | null {
  if (!target) return null;
  if (target instanceof HTMLElement) return target;
  const candidate = (target as ComponentPublicInstance).$el;
  return candidate instanceof HTMLElement ? candidate : null;
}

function bindPreviewShell(templateId: number, target: PreviewShellTarget) {
  const el = resolvePreviewElement(target);
  const existing = previewShellObservers.get(templateId);
  if (existing) {
    existing.disconnect();
    previewShellObservers.delete(templateId);
  }
  if (!el) {
    delete previewHeightMap[templateId];
    return;
  }
  if (typeof ResizeObserver === "undefined") {
    previewHeightMap[templateId] = el.offsetHeight || DEFAULT_PANEL_HEIGHT;
    return;
  }
  const observer = new ResizeObserver((entries) => {
    for (const entry of entries) {
      if (entry.target !== el) continue;
      const blockSize = entry.borderBoxSize?.[0]?.blockSize ?? entry.contentRect.height;
      previewHeightMap[templateId] = blockSize;
    }
  });
  observer.observe(el);
  previewShellObservers.set(templateId, observer);
}

function panelShellStyle(templateId: number) {
  const target = previewHeightMap[templateId] ?? DEFAULT_PANEL_HEIGHT;
  return {
    minHeight: `${target}px`,
    height: `${target}px`
  };
}

async function useTemplate(templateId: number) {
  try {
    importingId.value = templateId;
    const project = await store.importTemplate(templateId);
    router.push(`/editor/${project.id}`);
  } catch (error) {
    console.error(error);
    errorMessage.value = copy.errors.import;
  } finally {
    importingId.value = null;
  }
}

function ensureCommentsLoaded(templateId: number) {
  if (commentsMap.value[templateId]) return;
  void store.fetchTemplateComments(templateId);
}

function toggleComments(template: CommunityTemplate) {
  if (expandedCard.value === template.id) {
    expandedCard.value = null;
    return;
  }
  expandedCard.value = template.id;
  ensureCommentsLoaded(template.id);
}

async function submitComment(payload: { templateId: number; message: string }) {
  commentSubmitting.value = { ...commentSubmitting.value, [payload.templateId]: true };
  try {
    await store.addTemplateComment(payload.templateId, payload.message);
  } catch (error) {
    console.error(error);
  } finally {
    commentSubmitting.value = { ...commentSubmitting.value, [payload.templateId]: false };
  }
}

onMounted(() => {
  void loadTemplates();
});

onBeforeUnmount(() => {
  previewShellObservers.forEach((observer) => observer.disconnect());
  previewShellObservers.clear();
});
</script>

<style scoped>
.marketplace-frame {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(180deg, #edf2ff 0%, #f7f9ff 55%, #ffffff 100%);
  padding: 8px 0 80px;
}

.marketplace {
  display: flex;
  flex-direction: column;
  gap: 32px;
  width: 100%;
}

.section-wide {
  width: 100%;
  margin: 0;
  padding: 0 clamp(16px, 3.5vw, 56px);
  box-sizing: border-box;
}

.hero-card {
  display: grid;
  grid-template-columns: minmax(320px, 1.3fr) minmax(260px, 1fr);
  gap: clamp(18px, 2.8vw, 36px);
  padding: clamp(20px, 2.6vw, 32px) clamp(24px, 4vw, 56px);
  border-radius: 26px;
  background: linear-gradient(120deg, #c084fc 0%, #a855f7 55%, #7c3aed 100%);
  color: #fff;
  box-shadow: 0 26px 60px rgba(124, 58, 237, 0.45);
  position: relative;
  overflow: hidden;
}

.hero-card::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.35), transparent 55%);
  pointer-events: none;
}

.hero-text {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hero-text h2 {
  margin: 0;
  font-size: clamp(1.8rem, 2.4vw, 2.1rem);
  line-height: 1.2;
}

.hero-text p {
  margin: 0;
  color: rgba(255, 255, 255, 0.92);
  max-width: 520px;
}

.hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hero-badge {
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-weight: 600;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 2px;
}

.hero-actions .primary {
  background: #fff;
  color: #4338ca;
}

.hero-actions .ghost {
  border-color: rgba(255, 255, 255, 0.65);
}

.hero-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 6px;
}

.metric {
  border-radius: 14px;
  padding: 9px 10px;
  background: rgba(15, 23, 42, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric small {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.metric strong {
  font-size: 1.15rem;
}

.hero-visual {
  position: relative;
  min-height: clamp(180px, 24vw, 260px);
  display: flex;
  align-items: stretch;
  justify-content: stretch;
}

.hero-canvas {
  width: 100%;
  min-height: clamp(220px, 32vw, 320px);
  border-radius: 30px;
  padding: clamp(20px, 3vw, 36px);
  background: linear-gradient(120deg, #b388ff 0%, #cea4ff 45%, #f4f0ff 100%);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
  position: relative;
  overflow: hidden;
}

.canvas-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(255, 255, 255, 0.16) 1px, transparent 1px);
  background-size: 34px 34px;
  opacity: 0.2;
  pointer-events: none;
  z-index: 0;
}

.canvas-glow {
  position: absolute;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0));
  filter: blur(16px);
  top: 6%;
  left: 18%;
  opacity: 0.7;
  z-index: 0;
}

.canvas-curve {
  position: absolute;
  width: 180%;
  height: 140%;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transform-origin: center;
  opacity: 0.32;
  z-index: 0;
}

.canvas-curve.curve-one {
  top: -60%;
  left: -18%;
  transform: rotate(10deg);
}

.canvas-curve.curve-two {
  bottom: -70%;
  right: -28%;
  transform: rotate(-12deg);
  border-color: rgba(255, 255, 255, 0.14);
}

.canvas-window {
  position: absolute;
  inset: 18% 6%;
  border-radius: 28px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 255, 0.9));
  box-shadow: 0 40px 80px rgba(109, 40, 217, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.7);
  padding: clamp(22px, 2.4vw, 34px);
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 2;
}

.window-header {
  display: flex;
  gap: 8px;
}

.window-header span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(203, 213, 225, 0.85);
}

.window-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.window-line {
  height: 14px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.38);
}

.window-line.long {
  width: 94%;
  background: rgba(99, 102, 241, 0.88);
  height: 16px;
}

.window-line.medium {
  width: 74%;
}

.window-line.short {
  width: 60%;
}

.filters-card {
  border-radius: 22px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 22px 55px rgba(15, 23, 42, 0.08);
  padding: clamp(14px, 2vw, 20px) clamp(18px, 3vw, 28px);
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.filters-column {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.eyebrow.small {
  font-size: 0.75rem;
  letter-spacing: 0.1em;
}

.search-control {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-control input {
  flex: 1;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 10px 14px;
  font-size: 0.95rem;
  background: rgba(249, 250, 255, 0.92);
  height: 44px;
}

.filters-divider {
  width: 1px;
  background: rgba(15, 23, 42, 0.08);
  height: 48px;
  align-self: stretch;
}

.select-control {
  display: flex;
  flex-direction: column;
}

.select-control select {
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 10px 14px;
  font-size: 0.95rem;
  background: rgba(249, 250, 255, 0.95);
  height: 44px;
}

.chip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  color: rgba(15, 23, 42, 0.75);
}

.chip-header span {
  font-size: 0.8rem;
  color: rgba(15, 23, 42, 0.55);
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip {
  border-radius: 999px;
  padding: 8px 18px;
  border: 1px solid rgba(79, 70, 229, 0.2);
  background: rgba(99, 102, 241, 0.08);
  color: #312e81;
  cursor: pointer;
  transition: 0.2s ease;
}

.chip.active {
  background: #4f46e5;
  color: #fff;
  border-color: transparent;
}

.chip.ghost-chip {
  background: rgba(15, 23, 42, 0.05);
  border-color: transparent;
  color: rgba(15, 23, 42, 0.7);
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding-block: 8px 36px;
}

.card-stack {
  width: min(1140px, 100%);
  margin: 0 auto;
}

.card-list.dimmed {
  opacity: 0.6;
  pointer-events: none;
}

.template-card {
  position: relative;
  border-radius: 34px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: linear-gradient(135deg, #fcfbff 0%, #f5f2ff 45%, #fefefe 100%);
  display: grid;
  grid-template-columns: minmax(520px, 1.15fr) minmax(0, 0.85fr);
  box-shadow: 0 45px 90px rgba(15, 23, 42, 0.1);
  overflow: hidden;
  isolation: isolate;
}

.template-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 18% 20%, rgba(148, 163, 255, 0.18), transparent 55%),
    radial-gradient(circle at 75% 80%, rgba(244, 114, 182, 0.15), transparent 60%);
  opacity: 0.9;
  z-index: 0;
}

.card-preview {
  position: relative;
  padding: 12px;
  border-right: 1px solid rgba(15, 23, 42, 0.05);
  display: flex;
  z-index: 1;
}

.preview-shell {
  position: relative;
  flex: 1;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.05);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.02), rgba(15, 23, 42, 0.07));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6), 0 18px 32px rgba(15, 23, 42, 0.08);
  padding: 8px;
  display: flex;
}

.preview-shell::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 20px;
  background: radial-gradient(circle at 0% 0%, rgba(255, 255, 255, 0.4), transparent 55%);
  pointer-events: none;
}

.preview-shell > * {
  flex: 1;
  position: relative;
  z-index: 1;
}

.card-panel {
  position: relative;
  padding: 12px;
  z-index: 1;
  display: flex;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.01), rgba(15, 23, 42, 0.06));
  border-left: 1px solid rgba(15, 23, 42, 0.05);
}

.panel-shell {
  position: relative;
  flex: 1;
  padding: 12px;
  border-radius: 22px;
  border: 1px solid rgba(15, 23, 42, 0.05);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.02), rgba(15, 23, 42, 0.07));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65), 0 16px 28px rgba(15, 23, 42, 0.08);
  display: flex;
  height: 100%;
  overflow: hidden;
}

.panel-shell::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 22px;
  background: radial-gradient(circle at 0% 0%, rgba(255, 255, 255, 0.4), transparent 55%);
  pointer-events: none;
}

.panel-shell > * {
  position: relative;
  z-index: 1;
}

.panel-wrapper {
  position: relative;
  flex: 1;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.05);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.02), rgba(15, 23, 42, 0.08));
  padding: 10px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65), 0 20px 38px rgba(15, 23, 42, 0.1);
  display: flex;
}

.panel-wrapper::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 20px;
  background: radial-gradient(circle at 0% 0%, rgba(255, 255, 255, 0.4), transparent 55%);
  pointer-events: none;
}

.panel-wrapper > * {
  position: relative;
  flex: 1;
  z-index: 1;
}

.panel-frame {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: #fff;
  box-shadow: 0 2px 14px rgba(15, 23, 42, 0.08);
  padding: 18px 20px;
  height: 100%;
}

.panel-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 0 0 auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.category-pill {
  border-radius: 999px;
  padding: 5px 14px;
  font-size: 0.72rem;
  background: rgba(79, 70, 229, 0.12);
  color: #4338ca;
  margin-bottom: 8px;
  display: inline-block;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.owner {
  font-size: 0.9rem;
  color: rgba(15, 23, 42, 0.65);
  background: rgba(15, 23, 42, 0.05);
  padding: 6px 14px;
  border-radius: 999px;
}

.description {
  font-size: 0.94rem;
  color: rgba(15, 23, 42, 0.8);
  line-height: 1.4;
  margin-bottom: 2px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 0;
  margin-top: -2px;
}

.tag-list li {
  border-radius: 999px;
  padding: 4px 12px;
  background: rgba(226, 232, 240, 0.65);
  font-size: 0.8rem;
  color: #1e1b4b;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.stat {
  border-radius: 16px;
  padding: 12px 18px;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.stat small {
  font-size: 0.75rem;
  color: rgba(15, 23, 42, 0.6);
}

.stat strong {
  font-size: 1.2rem;
  color: #1e1b4b;
}

.panel-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  align-items: center;
}

.use-template {
  border: none;
  border-radius: 18px;
  background: linear-gradient(125deg, #4f46e5, #7c3aed);
  color: #fff;
  padding: 12px 26px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 18px 40px rgba(79, 70, 229, 0.35);
}

.use-template[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.flat {
  border-radius: 16px;
  border: 1px solid rgba(79, 70, 229, 0.18);
  background: rgba(79, 70, 229, 0.08);
  color: #4f46e5;
  font-weight: 600;
  cursor: pointer;
  padding: 10px 18px;
}

.panel-comments {
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  margin-top: 14px;
  padding-top: 14px;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  background: rgba(248, 250, 252, 0.75);
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 102, 241, 0.35) transparent;
}

.panel-comments::-webkit-scrollbar {
  width: 6px;
}

.panel-comments::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.35);
  border-radius: 999px;
}

.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.25s ease;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skeleton-card {
  height: 380px;
  border-radius: 32px;
  background: linear-gradient(90deg, #e2e8f0, #f8fafc, #e2e8f0);
  background-size: 200% 100%;
  animation: shimmer 1.3s infinite;
}

.empty-state {
  text-align: center;
  color: rgba(15, 23, 42, 0.6);
}

.primary {
  border: none;
  border-radius: 18px;
  padding: 12px 22px;
  background: #fff;
  color: #312e81;
  cursor: pointer;
  font-weight: 600;
}

.ghost {
  border-radius: 18px;
  padding: 12px 22px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: transparent;
  color: #fff;
  cursor: pointer;
}

.ghost.small {
  color: #1e1b4b;
  border-color: rgba(15, 23, 42, 0.15);
  padding: 10px 14px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.8rem;
  color: rgba(15, 23, 42, 0.7);
}

.error {
  color: #b91c1c;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 1100px) {
  .filters-card {
    flex-direction: column;
  }

  .filters-divider {
    display: none;
  }

  .template-card {
    grid-template-columns: 1fr;
  }

  .card-preview {
    border-right: none;
    border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  }
}
</style>






