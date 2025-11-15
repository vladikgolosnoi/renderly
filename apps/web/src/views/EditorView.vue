<template>
  <section v-if="project" class="editor-page">
    <Breadcrumbs :items="breadcrumbItems" />

    <header class="editor-hero">
      <div class="title-stack">
        <div class="title-meta">
          <p class="eyebrow">{{ copy.header.eyebrow }}</p>
          <span class="status-chip" :class="{ ready: hasBlocks }">
            {{ hasBlocks ? copy.header.ready : copy.header.empty }}
          </span>
          <span class="status-chip subtle" :class="{ ready: hasForms }">
            {{ hasForms ? copy.header.formsReady : copy.header.formsMissing }}
          </span>
        </div>
        <h1>{{ project.title }}</h1>
        <p class="subtitle">
          {{ project.blocks.length }} {{ copy.header.blocks }} · {{ store.locales.length }} локалей
        </p>
      </div>
      <div class="hero-metrics">
        <article>
          <small>{{ copy.metrics.locales }}</small>
          <strong>{{ store.locales.length }}</strong>
        </article>
        <article>
          <small>{{ copy.metrics.revisions }}</small>
          <strong>{{ store.revisions.length }}</strong>
        </article>
        <article>
          <small>{{ copy.metrics.forms }}</small>
          <strong>{{ hasForms ? "✓" : "—" }}</strong>
        </article>
      </div>
      <div class="action-cluster">
        <button class="ghost icon-button" v-if="project" @click="openSettings(project.id)">
          <span aria-hidden="true">⚙</span>
          {{ copy.actions.settings }}
        </button>
        <button class="ghost icon-button" :disabled="!store.canUndo" @click="undo">
          <span aria-hidden="true">↺</span>
          {{ copy.actions.undo }}
        </button>
        <button class="ghost icon-button" :disabled="!store.canRedo" @click="redo">
          <span aria-hidden="true">↻</span>
          {{ copy.actions.redo }}
        </button>
        <button class="ghost icon-button" :disabled="exporting" @click="exportCode">
          <span aria-hidden="true">⇩</span>
          {{ exporting ? copy.actions.exporting : copy.actions.export }}
        </button>
        <button class="primary" @click="publish">{{ copy.actions.publish }}</button>
        <button class="ghost text-only" @click="router.push('/')">{{ copy.actions.exit }}</button>
      </div>
      <p v-if="publishLinkPreview" class="publish-hint">
        {{ copy.actions.publishHint }}
        <strong>{{ publishLinkPreview }}</strong>
      </p>
    </header>

    <div class="utility-row">
      <div class="panel-card locale-card">
        <LocaleSwitcher
          :locales="store.locales"
          :default-locale="store.defaultLocale"
          :active-locale="store.activeLocale"
          @change-locale="store.setActiveLocale"
          @add-locale="addLocale"
          @set-default="setDefaultLocale"
          @remove-locale="removeLocale"
        />
      </div>
      <EditorTourCard class="tour-anchor" />
    </div>

    <div class="editor-grid">
      <div class="left-panel">
        <section class="panel-card">
          <header class="panel-card__header">
            <div>
              <p class="panel-title">{{ copy.sections.paletteTitle }}</p>
              <p class="panel-subtitle">{{ copy.sections.paletteHint }}</p>
            </div>
          </header>
          <BlockPalette
            :blocks="store.blockCatalog"
            :project-blocks="project.blocks"
            @add="store.addBlock"
            @add-variation="addVariationFromPalette"
            @add-combo="applyComboPreset"
          />
        </section>
        <section v-if="onboarding.showEditorHints" class="panel-card">
          <header class="panel-card__header">
            <div>
              <p class="panel-title">{{ copy.sections.hintsTitle }}</p>
              <p class="panel-subtitle">{{ copy.sections.hintsHint }}</p>
            </div>
            <button type="button" class="ghost tiny" @click="onboarding.dismissEditorHints()">Скрыть</button>
          </header>
          <EditorHints @close="onboarding.dismissEditorHints()" />
        </section>
      </div>

      <div class="preview-shell">
        <LivePreview
          :project-id="project.id"
          :title="project.title"
          :blocks="project.blocks"
          :catalog="store.blockCatalog"
          :theme="projectTheme"
          :settings="project.settings"
          :locale="store.activeLocale"
          :default-locale="store.defaultLocale"
          :save-states="blockSaveStates"
          :quick-assets="quickAssets"
          :selected-block-id="selectedId"
          @select="selectBlock"
          @reorder="handleReorder"
          @insert="insertBlock"
          @inline-edit="handleInlineEdit"
          @request-asset="handleAssetRequest"
          @preview-asset="openAssetPreview"
        />
      </div>

      <div class="inspector-window">
        <div class="inspector">
          <article
            v-for="section in inspectorOrder"
            :key="section"
            class="inspector-section"
            :class="{ open: isSectionOpen(section) }"
          >
            <header @click="toggleSection(section)">
              <div class="inspector-title">
                <span class="badge">{{ inspectorMeta[section].icon }}</span>
                <div>
                  <p>{{ inspectorMeta[section].title }}</p>
                  <small>{{ inspectorDescriptions[section] }}</small>
                </div>
              </div>
              <button
                type="button"
                class="ghost tiny"
                :aria-expanded="isSectionOpen(section)"
                @click.stop="toggleSection(section)"
              >
                {{ isSectionOpen(section) ? "Свернуть" : "Развернуть" }}
              </button>
            </header>
            <transition name="accordion">
              <div v-show="isSectionOpen(section)" class="section-body">
                <BlockForm
                  v-if="section === 'block'"
                  :block="selectedBlock"
                  :catalog="store.blockCatalog"
                  :locale="store.activeLocale"
                  :default-locale="store.defaultLocale"
                  @save="saveBlock"
                  @request-asset="handleAssetRequest"
                />
                <ThemeDesigner
                  v-else-if="section === 'theme'"
                  :theme="projectTheme"
                  :templates="store.themeTemplates"
                  :compact="true"
                  @change="updateTheme"
                  @save-template="saveTemplate"
                  @apply-template="applyTemplate"
                />
                <AssetManager
                  v-else-if="section === 'assets'"
                  :selecting-for="assetTargetLabel"
                  @select="handleAssetSelect"
                />
                <RevisionTimeline
                  v-else
                  :revisions="store.revisions"
                  :loading="store.revisionsLoading"
                  @restore="restoreRevision"
                  @refresh="refreshRevisions"
                />
              </div>
            </transition>
          </article>
        </div>
      </div>
    </div>

      <PublishChecklist
        v-if="showPublishChecklist && project"
        :has-seo="hasSeo"
        :has-blocks="hasBlocks"
        :has-forms="hasForms"
        :publishing="publishLoading"
        @close="showPublishChecklist = false"
      @publish="confirmPublish"
    />

    <AssetGalleryModal
      :open="assetModalOpen"
      :mode="assetModalMode"
      :selecting-for="assetModalLabel || assetTargetLabel"
      :preview-url="assetModalPreview"
      @close="closeAssetModal"
      @select="handleAssetModalSelect"
    />
  </section>
  <p v-else>{{ copy.loading }}</p>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch, provide } from "vue";
import { useRoute, useRouter } from "vue-router";
import BlockPalette from "@/components/BlockPalette.vue";
import BlockForm from "@/components/BlockForm.vue";
import ThemeDesigner from "@/components/ThemeDesigner.vue";
import LivePreview from "@/components/LivePreview.vue";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import AssetManager from "@/components/AssetManager.vue";
import AssetGalleryModal from "@/components/AssetGalleryModal.vue";
import RevisionTimeline from "@/components/RevisionTimeline.vue";
import EditorTourCard from "@/components/EditorTourCard.vue";
import EditorHints from "@/components/EditorHints.vue";
import PublishChecklist from "@/components/PublishChecklist.vue";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import { useProjectStore } from "@/stores/project";
import { useOnboardingStore } from "@/stores/onboarding";
import type { BlockInstance, AssetItem } from "@/types/blocks";
import type { BlockComboPreset } from "@/data/blockCombos";
import api from "@/api/client";


const copy = {
  meta: {
    dashboard: "Мои проекты",
    projects: "Проекты",
    fallback: "Проект"
  },
  header: {
    eyebrow: "Редактор проекта",
    blocks: "блоков",
    ready: "Готов к публикации",
    empty: "Нет контента",
    formsReady: "Формы подключены",
    formsMissing: "Нужна форма"
  },
  actions: {
    settings: "Настройки",
    undo: "Отменить",
    redo: "Вернуть",
    export: "Выгрузить код",
    exporting: "Готовим...",
    publish: "Опубликовать",
    exit: "Выйти",
    publishHint: "После публикации страница будет доступна по адресу:"
  },
  metrics: {
    locales: "Локали",
    revisions: "Версии",
    forms: "Формы",
    checklist: "Чек-лист"
  },
  sections: {
    paletteTitle: "Библиотека блоков",
    paletteHint: "Перетащите блок или нажмите «Добавить».",
    hintsTitle: "Подсказки",
    hintsHint: "Подобрали короткие сценарии и советы."
  },
  loading: "Загружаем проект..."
} as const;


type AssetTarget = {
  blockId: number;
  fieldKey: string;
  label: string;
  path: (string | number)[];
};

const route = useRoute();
const router = useRouter();
const store = useProjectStore();
const envSubdomainRoot =
  import.meta.env.VITE_PROJECT_SUBDOMAIN_ROOT || import.meta.env.VITE_CUSTOM_DOMAIN_TARGET || "";
const projectSubdomainRoot = envSubdomainRoot.trim();
const onboarding = useOnboardingStore();
const selectedId = ref<number | null>(null);

const project = computed(() => store.current);
const publishLinkPreview = computed(() => {
  if (!project.value) return null;
  if (!projectSubdomainRoot) return null;
  const slug = project.value.slug?.trim();
  if (!slug) return null;
  const sanitizedRoot = projectSubdomainRoot.replace(/^\.+/, "");
  if (!sanitizedRoot) return null;
  return `https://${slug}.${sanitizedRoot}/`;
});
const projectTheme = computed<Record<string, string>>(
  () => ({ ...(project.value?.theme ?? {}) } as Record<string, string>)
);
const selectedBlock = computed(() =>
  store.current?.blocks.find((block) => block.id === selectedId.value) ?? null
);
const selectedDefinition = computed(() => {
  const key = selectedBlock.value?.definition_key;
  if (!key) return null;
  return store.blockCatalog.find((definition) => definition.key === key) ?? null;
});
const showPublishChecklist = ref(false);
const publishLoading = ref(false);
const assetTarget = ref<AssetTarget | null>(null);
const assetTargetLabel = computed(() => assetTarget.value?.label ?? null);
const quickAssets = computed<AssetItem[]>(() => store.assets.slice(0, 8));
const assetModalOpen = ref(false);
const exporting = ref(false);
const assetModalMode = ref<"select" | "preview">("select");
const assetModalPreview = ref<string | null>(null);
const assetModalLabel = ref<string | null>(null);

watch(
  () => store.current?.id,
  (id) => {
    if (id) {
      void store.fetchAssets(id);
    }
  },
  { immediate: true }
);
type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";
const blockSaveStates = reactive<Record<number, SaveState>>({});
const pendingLocales = reactive<Record<number, string>>({});
const pendingConfigs = reactive<Record<string, Record<string, unknown>>>({});
const saveTimers = new Map<number, number>();
const resetTimers = new Map<number, number>();
const AUTOSAVE_DELAY = 800;
const SAVE_RESET_DELAY = 1600;
const pendingKey = (blockId: number, locale: string) => `${blockId}:${locale}`;

watch(
  () => project.value?.blocks.map((block) => block.id) ?? [],
  (ids) => {
    const active = new Set(ids);
    Object.keys(blockSaveStates).forEach((key) => {
      const id = Number(key);
      if (!active.has(id)) {
        delete blockSaveStates[id];
        clearSaveTimer(id);
        clearResetTimer(id);
      }
    });
    Object.keys(pendingLocales).forEach((key) => {
      const id = Number(key);
      if (!active.has(id)) {
        const locale = pendingLocales[id];
        if (locale) {
          delete pendingConfigs[pendingKey(id, locale)];
        }
        delete pendingLocales[id];
      }
    });
  }
);

onBeforeUnmount(() => {
  saveTimers.forEach((timer) => window.clearTimeout(timer));
  resetTimers.forEach((timer) => window.clearTimeout(timer));
  saveTimers.clear();
  resetTimers.clear();
});

function clearSaveTimer(blockId: number) {
  const timer = saveTimers.get(blockId);
  if (timer) {
    window.clearTimeout(timer);
    saveTimers.delete(blockId);
  }
}

function clearResetTimer(blockId: number) {
  const timer = resetTimers.get(blockId);
  if (timer) {
    window.clearTimeout(timer);
    resetTimers.delete(blockId);
  }
}

function setBlockState(blockId: number, state: SaveState) {
  blockSaveStates[blockId] = state;
}

function queueBlockSave(blockId: number) {
  setBlockState(blockId, "dirty");
  clearSaveTimer(blockId);
  const timer = window.setTimeout(() => persistBlock(blockId), AUTOSAVE_DELAY);
  saveTimers.set(blockId, timer);
}

async function persistBlock(blockId: number) {
  clearSaveTimer(blockId);
  const config = currentConfigSnapshot(blockId);
  if (!config) return;
  setBlockState(blockId, "saving");
  try {
    await store.updateBlock(blockId, config, pendingLocales[blockId] ?? store.activeLocale);
    const locale = pendingLocales[blockId];
    if (locale) {
      delete pendingConfigs[pendingKey(blockId, locale)];
      delete pendingLocales[blockId];
    }
    setBlockState(blockId, "saved");
    clearResetTimer(blockId);
    const timer = window.setTimeout(() => {
      if (blockSaveStates[blockId] === "saved") {
        setBlockState(blockId, "idle");
      }
      resetTimers.delete(blockId);
    }, SAVE_RESET_DELAY);
    resetTimers.set(blockId, timer);
  } catch (error) {
    console.error(error);
    setBlockState(blockId, "error");
  }
}

function currentConfigSnapshot(blockId: number) {
  const block = store.current?.blocks.find((item) => item.id === blockId);
  if (!block) return null;
  const locale = (pendingLocales[blockId] ?? store.activeLocale ?? store.defaultLocale).toLowerCase();
  const key = pendingKey(blockId, locale);
  if (pendingConfigs[key]) {
    return cloneDeep(pendingConfigs[key]);
  }
  return localizedConfig(block, locale);
}

function stageBlockConfig(blockId: number, config: Record<string, unknown>) {
  const locale = (store.activeLocale ?? store.defaultLocale).toLowerCase();
  pendingLocales[blockId] = locale;
  pendingConfigs[pendingKey(blockId, locale)] = cloneDeep(config);
  store.stageBlockConfig(blockId, config, locale);
  queueBlockSave(blockId);
}

const hasBlocks = computed(() => (project.value?.blocks.length ?? 0) > 0);
const hasSeo = computed(() => {
  const seo = (project.value?.settings as any)?.seo;
  return Boolean(seo?.title && seo?.description);
});
const hasForms = computed(() => {
  if (!project.value) return false;
  return project.value.blocks.some((block) => {
    if (block.definition_key !== "form") return false;
    const config = block.config || {};
    return Boolean((config as any).webhook_url || (config as any).fields?.length);
  });
});
type InspectorKey = "block" | "theme" | "assets" | "revisions";
const inspectorMeta: Record<InspectorKey, { title: string; icon: string }> = {
  block: { title: "Контент", icon: "🧱" },
  theme: { title: "Тема", icon: "🎨" },
  assets: { title: "Медиа", icon: "📁" },
  revisions: { title: "Версии", icon: "🕘" }
};
const inspectorOrder: InspectorKey[] = ["block", "theme", "assets", "revisions"];
const expandedSections = ref<InspectorKey[]>(["block", "theme"]);
function isSectionOpen(key: InspectorKey) {
  return expandedSections.value.includes(key);
}
function toggleSection(key: InspectorKey) {
  expandedSections.value = isSectionOpen(key)
    ? expandedSections.value.filter((item) => item !== key)
    : [...expandedSections.value, key];
}
function ensureSectionOpen(key: InspectorKey) {
  if (!isSectionOpen(key)) {
    expandedSections.value = [...expandedSections.value, key];
  }
}
const inspectorDescriptions = computed<Record<InspectorKey, string>>(() => ({
  block: selectedBlock.value
    ? `Редактируем «${selectedDefinition.value?.name ?? selectedBlock.value.definition_key}»`
    : "Выберите блок на канвасе",
  theme: project.value?.theme ? "Своя тема подключена" : "Создайте или примените шаблон",
  assets: assetTargetLabel.value ? `Подбираем для «${assetTargetLabel.value}»` : "Иллюстрации, PDF, видео и файлы",
  revisions: store.revisions.length ? `${store.revisions.length} сохранённых версий` : "История появится после публикаций"
}));
const breadcrumbItems = computed(() => [
  { label: copy.meta.dashboard, to: "/" },
  { label: copy.meta.projects, to: "/" },
  { label: project.value?.title ?? copy.meta.fallback }
]);

onMounted(async () => {
  if (!store.blockCatalog.length) {
    await store.loadCatalog();
  }
  if (!store.themeTemplates.length) {
    await store.fetchThemeTemplates();
  }
  if (!store.assets.length) {
    await store.fetchAssets();
  }
  const id = Number(route.params.id);
  if (id) {
    await store.fetchProject(id);
    onboarding.syncProjectDetail(store.current);
    await store.fetchProjectLocales(id);
    await store.fetchRevisions(id);
    await store.fetchDomains(id);
    onboarding.triggerEditorHints();
  }
});

watch(
  () => project.value,
  (detail) => {
    onboarding.syncProjectDetail(detail);
  },
  { deep: true }
);

watch(
  () => selectedBlock.value?.id,
  () => {
    assetTarget.value = null;
  }
);

watch(
  () => store.activeLocale,
  () => {
    assetTarget.value = null;
  }
);

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value ?? {}));
}

function applyValueAtPath(
  source: Record<string, unknown> | undefined,
  path: (string | number)[],
  nextValue: unknown
) {
  const root: any = Array.isArray(source) ? [...source] : { ...(source ?? {}) };
  let cursor = root;
  for (let idx = 0; idx < path.length; idx += 1) {
    const key = path[idx];
    const isLast = idx === path.length - 1;
    if (isLast) {
      cursor[key as any] = nextValue;
      break;
    }
    const nextKey = path[idx + 1];
    const current = cursor[key as any];
    if (Array.isArray(current)) {
      cursor[key as any] = [...current];
    } else if (current && typeof current === "object") {
      cursor[key as any] = { ...current };
    } else {
      cursor[key as any] = typeof nextKey === "number" ? [] : {};
    }
    cursor = cursor[key as any];
  }
  return root;
}

function selectBlock(id: number) {
  selectedId.value = id;
  ensureSectionOpen("block");
}

function saveBlock(config: Record<string, unknown>) {
  if (!selectedBlock.value) return;
  stageBlockConfig(selectedBlock.value.id, config);
}

function handleReorder(payload: { from: number; to: number }) {
  store.reorderBlocks(payload.from, payload.to);
}

function insertBlock(payload: { definitionKey: string; index: number }) {
  store.addBlock(payload.definitionKey, payload.index);
  onboarding.markBlockAdded();
}

function addVariationFromPalette(payload: { definitionKey: string; config: Record<string, unknown> }) {
  store.addBlock(payload.definitionKey, undefined, payload.config);
}

async function applyComboPreset(combo: BlockComboPreset) {
  await store.addBlockBundle(
    combo.blocks.map((block) => ({
      definitionKey: block.definitionKey,
      config: block.config
    }))
  );
}

function handleInlineEdit(payload: { blockId: number; fieldKey: string; value: string; path?: (string | number)[] }) {
  if (!store.current) return;
  const block = store.current.blocks.find((item) => item.id === payload.blockId);
  if (!block) return;
  const path = payload.path ?? [payload.fieldKey];
  const nextConfig = applyValueAtPath(localizedConfig(block), path, payload.value);
  stageBlockConfig(payload.blockId, nextConfig);
}

function localizedConfig(block: BlockInstance, locale?: string) {
  const target = (locale ?? store.activeLocale ?? store.defaultLocale).toLowerCase();
  if (target === store.defaultLocale.toLowerCase()) {
    return cloneDeep(block.config ?? {});
  }
  return cloneDeep(block.translations?.[target] ?? block.config ?? {});
}

function updateTheme(theme: Record<string, string>) {
  store.updateTheme(theme);
}

async function publish() {
  if (project.value) {
    await store.fetchDomains(project.value.id);
  }
  showPublishChecklist.value = true;
}

async function confirmPublish() {
  if (!hasBlocks.value) {
    return;
  }
  publishLoading.value = true;
  try {
    const publication = await store.publishCurrent(store.activeLocale);
    const url = publication?.publication?.custom_domain_url ?? publication?.publication?.cdn_url;
    const message = url
      ? `Страница опубликована. URL: ${url}`
      : "Публикация завершена, но ссылку получить не удалось. Проверьте настройки CDN.";
    alert(message);
    showPublishChecklist.value = false;
  } finally {
    publishLoading.value = false;
  }
}

async function exportCode() {
  if (!project.value || exporting.value) return;
  exporting.value = true;
  try {
    const response = await api.get<Blob>(`/projects/${project.value.id}/export/html`, {
      responseType: "blob"
    });
    const blob = response.data instanceof Blob ? response.data : new Blob([response.data], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const slug = project.value.slug?.trim() || project.value.title?.trim() || "renderly-export";
    link.href = url;
    link.download = `${slug.replace(/\s+/g, "-").toLowerCase() || "renderly-export"}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Failed to export HTML", error);
    alert("Не удалось выгрузить HTML. Попробуйте ещё раз.");
  } finally {
    exporting.value = false;
  }
}

function undo() {
  store.undo();
}

function redo() {
  store.redo();
}

function saveTemplate(name: string) {
  store.saveThemeTemplate(name);
}

function applyTemplate(palette: Record<string, string>) {
  store.updateTheme(palette);
}

function openSettings(projectId: number) {
  router.push(`/projects/${projectId}/settings`);
}

async function addLocale(code: string) {
  await store.addLocale(code);
}

async function setDefaultLocale(locale: string) {
  await store.setDefaultLocale(locale);
}

async function removeLocale(locale: string) {
  await store.removeLocale(locale);
}

async function restoreRevision(revisionId: number) {
  await store.restoreRevision(revisionId);
}

async function refreshRevisions() {
  if (project.value) {
    await store.fetchRevisions(project.value.id);
  }
}

function handleAssetRequest(payload: { blockId: number; fieldKey: string; label: string; path?: (string | number)[] }) {
  assetTarget.value = {
    blockId: payload.blockId,
    fieldKey: payload.fieldKey,
    label: payload.label,
    path: payload.path ?? [payload.fieldKey]
  };
  ensureSectionOpen("assets");
  nextTick(() => {
    document.getElementById("asset-manager")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  openAssetPicker(payload.label ?? null);
}

async function handleAssetSelect(url: string) {
  if (!assetTarget.value || !store.current) return;
  const block = store.current.blocks.find((item) => item.id === assetTarget.value?.blockId);
  if (!block) {
    assetTarget.value = null;
    return;
  }
  const nextConfig = applyValueAtPath(localizedConfig(block), assetTarget.value.path, url);
  stageBlockConfig(assetTarget.value.blockId, nextConfig);
  assetTarget.value = null;
}

function openAssetPicker(label: string | null) {
  assetModalMode.value = "select";
  assetModalPreview.value = null;
  assetModalLabel.value = label;
  assetModalOpen.value = true;
}

function openAssetPreview(url?: string | null) {
  if (!url) return;
  assetModalMode.value = "preview";
  assetModalPreview.value = url;
  assetModalLabel.value = null;
  assetModalOpen.value = true;
}

function closeAssetModal() {
  assetModalOpen.value = false;
  assetModalPreview.value = null;
}

async function handleAssetModalSelect(url: string) {
  await handleAssetSelect(url);
  closeAssetModal();
}

provide("openAssetPreview", openAssetPreview);
</script>

<style scoped>
.editor-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.editor-hero {
  display: grid;
  grid-template-columns: minmax(320px, 2fr) repeat(2, minmax(200px, auto));
  gap: 24px;
  padding: 32px;
  border-radius: 32px;
  background: linear-gradient(135deg, #eef2ff, #e0f2fe);
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.12);
  align-items: center;
}

.title-stack h1 {
  margin: 8px 0 12px;
  font-size: clamp(1.8rem, 3vw, 2.8rem);
}

.title-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.subtitle {
  margin: 0;
  color: #475569;
}

.status-chip {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid rgba(37, 99, 235, 0.3);
  font-size: 0.85rem;
  text-transform: lowercase;
}

.status-chip.ready {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.4);
  color: #15803d;
}

.status-chip.subtle {
  border-color: rgba(99, 102, 241, 0.2);
  color: #4338ca;
  background: rgba(99, 102, 241, 0.08);
}

.hero-metrics {
  display: flex;
  gap: 16px;
  align-items: stretch;
  justify-content: center;
}

.hero-metrics article {
  background: #fff;
  border-radius: 18px;
  padding: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.25);
}

.hero-metrics strong {
  display: block;
  font-size: 1.8rem;
  margin-top: 6px;
  color: #0f172a;
}

.action-cluster {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
}

.publish-hint {
  margin-top: 8px;
  text-align: right;
  font-size: 0.95rem;
  color: #475569;
}

.publish-hint strong {
  color: #0f172a;
}

.primary {
  border: none;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  padding: 12px 20px;
  border-radius: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 18px 40px rgba(79, 70, 229, 0.25);
}

.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ghost {
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.6);
  background: transparent;
  color: #312e81;
  padding: 10px 16px;
  font-weight: 500;
  cursor: pointer;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.text-only {
  border-color: transparent;
  color: #475569;
}

.utility-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  align-items: start;
}

.panel-card {
  background: #fff;
  border-radius: 28px;
  padding: 20px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.25);
}

.panel-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-title {
  margin: 0;
  font-weight: 600;
}

.panel-subtitle {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 0.9rem;
}

.editor-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 340px;
  gap: 24px;
  align-items: start;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 120px;
  height: calc(100vh - 160px);
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.left-panel::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.preview-shell {
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.inspector-window {
  position: sticky;
  top: 120px;
  height: calc(100vh - 160px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.inspector-window::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.inspector {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #fff;
  border-radius: 32px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.08);
}

.inspector-section {
  border-radius: 24px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.3);
  padding: 16px 18px;
  box-shadow: 0 12px 35px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.inspector-section header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.inspector-title {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.inspector-title p {
  margin: 0;
  font-weight: 600;
}

.inspector-title small {
  color: #64748b;
  font-size: 0.85rem;
}

.badge {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: #eef2ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.section-body {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-body > * {
  width: 100%;
  min-width: 0;
}

.section-body :deep(.theme-designer),
.section-body :deep(.panel),
.section-body :deep(#asset-manager),
.section-body :deep(.revision-timeline) {
  width: 100%;
  min-width: 0;
}

.accordion-enter-active,
.accordion-leave-active {
  transition: all 0.2s ease;
}

.accordion-enter-from,
.accordion-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.locale-card :deep(.locale-switcher) {
  width: 100%;
}

.tour-anchor {
  align-self: stretch;
}

.ghost.tiny {
  padding: 6px 10px;
  font-size: 0.85rem;
}

@media (max-width: 1440px) {
  .editor-hero {
    grid-template-columns: 1fr;
  }

  .hero-metrics {
    justify-content: flex-start;
  }
}

@media (max-width: 1180px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .canvas-shell {
    min-height: auto;
  }

  .left-panel,
  .inspector-window {
    position: static;
    top: auto;
    height: auto;
    overflow: visible;
    padding-right: 0;
  }
}
</style>
