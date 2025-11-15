<template>
  <div class="palette">
    <header class="palette-header">
      <div>
        <p class="eyebrow">{{ copy.hero.eyebrow }}</p>
        <h3>{{ copy.hero.title }}</h3>
        <p>{{ copy.hero.subtitle }}</p>
      </div>
      <div class="header-actions">
        <label class="search">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 20 20" role="presentation">
              <circle cx="9" cy="9" r="6" />
              <line x1="13.5" y1="13.5" x2="18" y2="18" />
            </svg>
          </span>
          <input
            v-model="search"
            type="search"
            :placeholder="copy.searchPlaceholder"
            autocomplete="off"
          />
        </label>
        <button type="button" class="ghost tiny" @click="compactMode = !compactMode">
          {{ compactMode ? copy.actions.expanded : copy.actions.compact }}
        </button>
      </div>
    </header>

    <section v-if="suggestedBlocks.length" class="suggested">
      <header>
        <div>
          <p class="eyebrow">{{ copy.suggested.title }}</p>
          <small>{{ copy.suggested.subtitle }}</small>
        </div>
      </header>
      <div class="suggested-list">
        <button
          v-for="block in suggestedBlocks"
          :key="`suggested-${block.key}`"
          type="button"
          @click="$emit('add', block.key)"
        >
          <span>{{ blockTitle(block) }}</span>
          <small>{{ categoryLabel(block.category) }}</small>
        </button>
      </div>
    </section>

    <section v-if="comboList.length" class="combos">
      <header>
        <div>
          <p class="eyebrow">{{ copy.combo.title }}</p>
          <small>{{ copy.combo.subtitle }}</small>
        </div>
      </header>
      <div class="combo-grid">
        <article v-for="combo in comboList" :key="combo.slug" :style="{ borderColor: combo.accent }">
          <div class="combo-head">
            <h4>{{ combo.title }}</h4>
            <p>{{ combo.description }}</p>
          </div>
          <ul class="combo-tags">
            <li v-for="tag in combo.tags" :key="tag">{{ tag }}</li>
          </ul>
          <button type="button" class="primary" @click="addComboPreset(combo)">
            {{ copy.combo.add }}
          </button>
        </article>
      </div>
    </section>

    <div class="filters">
      <button
        v-for="option in filterOptions"
        :key="option.value"
        type="button"
        :class="{ active: category === option.value }"
        :disabled="option.disabled"
        @click="!option.disabled && (category = option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <div class="grid" :class="{ dense: compactMode }">
      <article
        v-for="block in filteredBlocks"
        :key="block.key"
        class="card"
        :class="{ favorite: isFavorite(block.key) }"
        draggable="true"
        @dragstart="onDragStart(block, $event)"
        @dragend="onDragEnd"
        @click="$emit('add', block.key)"
      >
          <div class="thumb" :style="thumbStyle(block)">
          <div class="thumb-hero" v-if="previewEyebrow(block)">
            <span v-html="highlightText(previewEyebrow(block))"></span>
            <small>{{ categoryLabel(block.category) }}</small>
          </div>
            <div class="thumb-content">
              <h5 v-html="highlightText(previewTitle(block))"></h5>
            <p v-html="highlightText(previewExcerpt(block))"></p>
          </div>
        </div>
          <div class="meta">
            <div class="meta-head">
              <div class="meta-title">
                <strong v-html="highlightText(blockTitle(block))"></strong>
              <span class="pill">{{ categoryLabel(block.category) }}</span>
            </div>
            <button
              type="button"
              class="favorite-toggle"
              :class="{ active: isFavorite(block.key) }"
              :aria-pressed="isFavorite(block.key)"
              :aria-label="isFavorite(block.key) ? copy.actions.unfavorite : copy.actions.favorite"
              @click.stop="toggleFavorite(block.key)"
            >
              ★
            </button>
          </div>
          <small v-html="highlightText(block.description || fallbackDescription(block))"></small>
          <div class="preview">
            <div class="preview-content">
              <p
                v-if="previewEyebrow(block)"
                class="preview-eyebrow"
                v-html="highlightText(previewEyebrow(block))"
              ></p>
              <h4 v-html="highlightText(previewTitle(block))"></h4>
              <p v-html="highlightText(previewExcerpt(block))"></p>
            </div>
            <ul class="preview-tags" v-if="previewTags(block).length">
              <li v-for="tag in previewTags(block)" :key="tag">{{ tag }}</li>
            </ul>
          </div>
        </div>
        <footer>
          <div class="footer-meta">
            <span>{{ copy.fields }}: {{ block.schema.length }}</span>
          </div>
          <div class="footer-actions">
            <button type="button" class="ghost" @click.stop="$emit('add', block.key)">
              {{ copy.actions.add }}
            </button>
            <button type="button" class="soft" @click.stop="openPreview(block)">
              {{ copy.actions.preview }}
            </button>
          </div>
        </footer>
      </article>
    </div>

    <p v-if="!filteredBlocks.length" class="empty">{{ copy.empty }}</p>

    <teleport to="body">
      <div v-if="previewBlock" class="modal-backdrop" @click="closePreview">
        <div class="modal" @click.stop>
          <header>
            <div>
              <p class="eyebrow">{{ categoryLabel(previewBlock.category) }}</p>
              <h4 v-html="highlightText(blockTitle(previewBlock))"></h4>
              <p v-html="highlightText(previewBlock.description || fallbackDescription(previewBlock))"></p>
            </div>
            <button type="button" class="icon-button" @click="closePreview" :aria-label="copy.modal.close">
              &times;
            </button>
          </header>
          <div class="modal-body">
            <div class="modal-preview" :style="thumbStyle(previewBlock)">
              <p
                v-if="previewEyebrow(previewBlock)"
                class="preview-eyebrow"
                v-html="highlightText(previewEyebrow(previewBlock))"
              ></p>
              <h5 v-html="highlightText(previewTitle(previewBlock))"></h5>
              <p v-html="highlightText(previewExcerpt(previewBlock))"></p>
              <ul class="preview-tags" v-if="previewTags(previewBlock).length">
                <li v-for="tag in previewTags(previewBlock)" :key="tag">{{ tag }}</li>
              </ul>
            </div>
            <div class="modal-meta">
              <div class="schema">
                <h6>{{ copy.modal.schemaTitle }}</h6>
                <ul>
                  <li v-for="field in previewBlock.schema" :key="field.key">
                    <strong>{{ field.label }}</strong>
                    <span>{{ field.type }}</span>
                  </li>
                </ul>
              </div>
              <div class="variations" v-if="modalVariations.length">
                <h6>{{ copy.modal.variationsTitle }}</h6>
                <ul>
                  <li v-for="variation in modalVariations" :key="variation.slug">
                    <div>
                      <strong>{{ variation.name }}</strong>
                      <p>{{ variation.description }}</p>
                      <ul class="badge-row" v-if="variation.badges?.length">
                        <li v-for="badge in variation.badges" :key="badge">{{ badge }}</li>
                      </ul>
                    </div>
                    <button type="button" class="ghost tiny" @click="applyVariationFromPreview(variation)">
                      {{ copy.modal.applyVariation }}
                    </button>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <footer>
            <button type="button" class="primary" @click="addFromPreview">
              {{ copy.modal.add }}
            </button>
            <button type="button" class="ghost" @click="closePreview">{{ copy.modal.close }}</button>
          </footer>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import type { BlockDefinition, BlockInstance, BlockVariation } from "@/types/blocks";
import { comboPresets, type BlockComboPreset } from "@/data/blockCombos";
import {
  localizedBlockName,
  localizedCategoryLabel
} from "@/data/localeMap";

const props = defineProps<{ blocks: BlockDefinition[]; projectBlocks?: BlockInstance[] }>();
const emit = defineEmits<{
  add: [string];
  "add-variation": [{ definitionKey: string; config: Record<string, unknown> }];
  "add-combo": [BlockComboPreset];
}>();

const copy = {
  hero: {
    eyebrow: "Библиотека блоков",
    title: "Собирайте страницы как из конструктора",
    subtitle:
      "Hero, галереи, формы, CTA и десятки других секций. Перетаскивайте, комбинируйте и настраивайте без единой строки кода."
  },
  searchPlaceholder: "Искать по названию или описанию",
  filters: {
    all: "Все блоки",
    favorites: "Избранные",
    recent: "Недавние",
    content: "Контент",
    hero: "Hero",
    media: "Медиа",
    form: "Формы",
    layout: "Макеты"
  },
  suggested: {
    title: "Подборка дня",
    subtitle: "На основе последних действий и популярности. Попробуйте, чтобы ускорить работу."
  },
  combo: {
    title: "Комбо блоки",
    subtitle: "Готовые наборы: hero + преимущества + формы и CTA в одном клике.",
    add: "Вставить набор"
  },
  actions: {
    add: "Добавить",
    preview: "Превью",
    compact: "Компактно",
    expanded: "Развернуть",
    favorite: "В избранное",
    unfavorite: "Убрать",
    close: "Закрыть"
  },
  fields: "Полей",
  empty: "Ничего не нашли. Измените запрос или попробуйте другую категорию.",
  modal: {
    schemaTitle: "Поля блока",
    add: "Добавить блок",
    close: "Закрыть",
    variationsTitle: "Готовые варианты",
    applyVariation: "Использовать вариант"
  }
} as const;

const FAVORITES_KEY = "renderly:palette:favorites";
const search = ref("");
const category = ref("all");
const previewBlock = ref<BlockDefinition | null>(null);
const compactMode = ref(false);
const favoriteKeys = ref<string[]>([]);
const comboList = comboPresets;

onMounted(() => {
  if (typeof window === "undefined") return;
  try {
    const stored = localStorage.getItem(FAVORITES_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        favoriteKeys.value = parsed;
      }
    }
  } catch {
    favoriteKeys.value = [];
  }
});

watch(
  favoriteKeys,
  (value) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(value));
    if (category.value === "favorites" && !value.length) {
      category.value = "all";
    }
  },
  { deep: true }
);

const favoritesSet = computed(() => new Set(favoriteKeys.value));
const rawSearch = computed(() => search.value.trim());
const searchQuery = computed(() => rawSearch.value.toLowerCase());

const categories = computed(() =>
  Array.from(new Set(props.blocks.map((block) => block.category))).sort()
);

const recentlyUsedKeys = computed(() => {
  if (!props.projectBlocks?.length) return [] as string[];
  const seen = new Set<string>();
  const ordered: string[] = [];
  [...props.projectBlocks]
    .slice()
    .reverse()
    .forEach((instance) => {
      if (!seen.has(instance.definition_key)) {
        seen.add(instance.definition_key);
        ordered.push(instance.definition_key);
      }
    });
  return ordered;
});

type FilterOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

const filterOptions = computed<FilterOption[]>(() => {
  const base: FilterOption[] = [
    { value: "all", label: copy.filters.all, disabled: false },
    {
      value: "favorites",
      label: copy.filters.favorites,
      disabled: !favoriteKeys.value.length
    },
    {
      value: "recent",
      label: copy.filters.recent,
      disabled: !recentlyUsedKeys.value.length
    }
  ];
  const categoryOptions: FilterOption[] = categories.value.map((cat) => ({
    value: cat,
    label: categoryLabel(cat),
    disabled: false
  }));
  return [...base, ...categoryOptions];
});

const filteredBlocks = computed(() => {
  const query = searchQuery.value;
  return props.blocks.filter((block) => {
    let matchesCategory = true;
    if (category.value === "favorites") {
      matchesCategory = favoritesSet.value.has(block.key);
    } else if (category.value === "recent") {
      matchesCategory = recentlyUsedKeys.value.includes(block.key);
    } else if (category.value !== "all") {
      matchesCategory = block.category === category.value;
    }
    if (!matchesCategory) return false;

    if (!query) return true;
    const haystack = `${blockTitle(block)} ${block.description ?? ""} ${block.key}`.toLowerCase();
    return haystack.includes(query);
  });
});

const modalVariations = computed(() => blockVariations(previewBlock.value));

function blockVariations(definition: BlockDefinition | null): BlockVariation[] {
  return definition?.ui_meta?.variations ?? [];
}

const suggestedBlocks = computed(() => {
  const keys = recentlyUsedKeys.value.slice(0, 4);
  if (keys.length) {
    return props.blocks.filter((block) => keys.includes(block.key));
  }
  return props.blocks.slice(0, 4);
});

let dragGhostEl: HTMLDivElement | null = null;

function toggleFavorite(blockKey: string) {
  if (favoritesSet.value.has(blockKey)) {
    favoriteKeys.value = favoriteKeys.value.filter((key) => key !== blockKey);
  } else {
    favoriteKeys.value = [blockKey, ...favoriteKeys.value];
  }
}

function isFavorite(blockKey: string) {
  return favoritesSet.value.has(blockKey);
}

function onDragStart(block: BlockDefinition, event: DragEvent) {
  const dt = event.dataTransfer;
  if (!dt) return;
  dt.setData("application/x-renderly-block", block.key);
  dt.setData("text/plain", block.key);
  dt.effectAllowed = "copy";

  dragGhostEl = document.createElement("div");
  dragGhostEl.className = "palette-drag-ghost";
  dragGhostEl.textContent = blockTitle(block);
  document.body.appendChild(dragGhostEl);
  const rect = dragGhostEl.getBoundingClientRect();
  dt.setDragImage(dragGhostEl, rect.width / 2, rect.height / 2);
}

function onDragEnd(event: DragEvent) {
  event.dataTransfer?.clearData();
  if (dragGhostEl) {
    document.body.removeChild(dragGhostEl);
    dragGhostEl = null;
  }
}

function thumbStyle(block: BlockDefinition) {
  const gradients: Record<string, string> = {
    hero: "linear-gradient(120deg, #6366f1, #a855f7)",
    media: "linear-gradient(120deg, #0ea5e9, #22d3ee)",
    form: "linear-gradient(120deg, #14b8a6, #2dd4bf)",
    layout: "linear-gradient(120deg, #f97316, #facc15)",
    content: "linear-gradient(120deg, #8b5cf6, #ec4899)"
  };
  return { background: gradients[block.category] ?? "linear-gradient(120deg, #64748b, #1e293b)" };
}

function defaultConfig(block: BlockDefinition) {
  return (block.default_config || {}) as Record<string, unknown>;
}

function previewEyebrow(block: BlockDefinition) {
  const config = defaultConfig(block);
  const candidates = ["eyebrow", "kicker", "label", "category"];
  for (const key of candidates) {
    const value = config[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return "";
}

function previewTitle(block: BlockDefinition) {
  const config = defaultConfig(block);
  const candidates = ["headline", "title", "question", "name"];
  for (const key of candidates) {
    const value = config[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return blockTitle(block);
}

function previewExcerpt(block: BlockDefinition) {
  const config = defaultConfig(block);
  const candidates = ["subheading", "description", "text", "body"];
  for (const key of candidates) {
    const value = config[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return fallbackDescription(block);
}

function previewTags(block: BlockDefinition) {
  const config = defaultConfig(block);
  const keys = ["features", "items", "steps", "bullets"];
  const tags: string[] = [];
  for (const key of keys) {
    const list = config[key];
    if (Array.isArray(list)) {
      for (const item of list.slice(0, 3)) {
        if (typeof item === "string" && item.trim()) {
          tags.push(item);
        } else if (item && typeof item === "object") {
          const value =
            (item as Record<string, unknown>).title ??
            (item as Record<string, unknown>).label ??
            (item as Record<string, unknown>).name ??
            (item as Record<string, unknown>).description;
          if (typeof value === "string" && value.trim()) {
            tags.push(value);
          }
        }
      }
    }
    if (tags.length >= 3) break;
  }
  if (!tags.length) {
    tags.push(
      ...block.schema
        .slice(0, 3)
        .map((field) => field.label)
        .filter(Boolean)
    );
  }
  return tags.slice(0, 3);
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightText(value: string) {
  if (!value) return "";
  const safe = escapeHtml(value);
  const query = rawSearch.value;
  if (!query) return safe;
  const pattern = new RegExp(`(${escapeRegExp(escapeHtml(query))})`, "gi");
  return safe.replace(pattern, "<mark>$1</mark>");
}

function blockTitle(block: BlockDefinition | null | undefined) {
  if (!block) return "";
  return localizedBlockName(block.key, block.name);
}

function categoryLabel(value: string) {
  return localizedCategoryLabel(value, value);
}

function fallbackDescription(block: BlockDefinition) {
  const defaults: Record<string, string> = {
    hero: "Заголовок, медиа и кнопка для первого экрана.",
    "feature-grid": "Сетка преимуществ с иконками и описанием.",
    "media-gallery": "Галерея изображений или видео с подписями.",
    cta: "Призыв к действию с заметной кнопкой.",
    form: "Форма с полями и кнопкой отправки."
  };
  return defaults[block.key] ?? "Универсальный блок для быстрого старта.";
}

function openPreview(block: BlockDefinition) {
  previewBlock.value = block;
}

function closePreview() {
  previewBlock.value = null;
}

function addFromPreview() {
  if (!previewBlock.value) return;
  emit("add", previewBlock.value.key);
  closePreview();
}

function applyVariationFromPreview(variation: BlockVariation) {
  if (!previewBlock.value) return;
  emit("add-variation", {
    definitionKey: previewBlock.value.key,
    config: variation.config ?? {}
  });
  closePreview();
}

function addComboPreset(combo: BlockComboPreset) {
  emit("add-combo", combo);
}
</script>

<style scoped>
.palette {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.palette-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.2em;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.search {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--stroke);
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--bg-surface);
}

.search .icon {
  display: inline-flex;
  color: var(--text-secondary);
}

.search .icon svg {
  width: 14px;
  height: 14px;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.6;
  stroke-linecap: round;
}

.search input {
  border: none;
  background: transparent;
  width: 220px;
  max-width: 100%;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.search input:focus {
  outline: none;
}

.suggested {
  border: 1px solid var(--stroke);
  border-radius: 16px;
  padding: 14px 16px;
  background: var(--bg-soft);
}

.suggested header {
  margin-bottom: 8px;
}

.suggested-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.suggested-list button {
  border-radius: 999px;
  border: 1px solid var(--stroke);
  padding: 6px 12px;
  background: white;
  font-size: 0.85rem;
  cursor: pointer;
  display: inline-flex;
  gap: 6px;
  align-items: center;
}

.combos {
  border: 1px solid var(--stroke);
  border-radius: 18px;
  padding: 18px;
  background: var(--bg-surface);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.combo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.combo-grid article {
  border: 1px solid var(--stroke);
  border-radius: 16px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--bg-soft);
}

.combo-head h4 {
  margin: 0;
  font-size: 1rem;
}

.combo-head p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.combo-tags {
  list-style: none;
  display: flex;
  gap: 6px;
  padding: 0;
  margin: 0;
  flex-wrap: wrap;
}

.combo-tags li {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--text-secondary);
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filters button {
  border-radius: 999px;
  border: 1px solid var(--stroke);
  background: transparent;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.filters button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.filters button.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.grid.dense {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card {
  border: 1px solid var(--stroke);
  border-radius: 18px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--bg-surface);
  cursor: grab;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.card.favorite {
  border-color: var(--accent);
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.15);
}

.card:hover {
  border-color: var(--accent);
  box-shadow: 0 15px 30px rgba(15, 23, 42, 0.08);
  transform: translateY(-2px);
}

.thumb {
  border-radius: 14px;
  padding: 16px;
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 120px;
}

.grid.dense .card {
  flex-direction: row;
  align-items: center;
  padding: 12px 16px;
}

.grid.dense .thumb {
  max-width: 140px;
  min-height: auto;
}

.grid.dense .preview,
.grid.dense footer {
  display: none;
}

.grid.dense .meta {
  flex: 1;
}

.thumb-hero {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  opacity: 0.9;
}

.thumb-content h5 {
  margin: 0;
  font-size: 1rem;
}

.thumb-content p {
  margin: 4px 0 0;
  font-size: 0.85rem;
  opacity: 0.85;
}

.meta strong {
  font-size: 1rem;
}

.meta-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.meta-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pill {
  border-radius: 999px;
  background: var(--bg-soft);
  padding: 2px 8px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: inline-flex;
  align-self: flex-start;
}

.favorite-toggle {
  border: none;
  background: transparent;
  font-size: 1rem;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.2s ease;
}

.favorite-toggle.active {
  color: #fbbf24;
}

.preview {
  border: 1px solid var(--stroke);
  border-radius: 12px;
  padding: 12px;
  margin-top: 10px;
  background: #f8fafc;
}

.preview-content h4 {
  margin: 0;
}

.preview-content p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.preview-tags {
  list-style: none;
  display: flex;
  gap: 6px;
  margin: 8px 0 0;
  padding: 0;
  flex-wrap: wrap;
}

.preview-tags li {
  border-radius: 6px;
  padding: 2px 8px;
  background: #fff;
  border: 1px solid var(--stroke);
  font-size: 0.75rem;
}

footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.ghost,
.soft {
  border-radius: 12px;
  padding: 6px 14px;
  cursor: pointer;
  border: 1px solid var(--stroke);
  background: transparent;
}

.soft {
  background: var(--bg-soft);
}

.empty {
  text-align: center;
  border: 1px dashed var(--stroke);
  border-radius: 18px;
  padding: 24px;
  color: var(--text-secondary);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
  padding: 20px;
}

.modal {
  background: var(--bg-surface);
  border-radius: 24px;
  padding: 24px;
  width: min(640px, 100%);
  box-shadow: 0 40px 80px rgba(15, 23, 42, 0.25);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.icon-button {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
}

.modal-body {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

.modal-preview {
  border-radius: 16px;
  padding: 16px;
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.schema h6 {
  margin: 0 0 8px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.schema ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow: auto;
}

.schema li {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding: 6px 0;
  border-bottom: 1px solid var(--stroke);
}

.schema li span {
  color: var(--text-secondary);
}

.modal-meta {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.variations ul {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.variations li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--stroke);
  border-radius: 12px;
  padding: 10px;
  align-items: center;
}

.badge-row {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.badge-row li {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
}
.primary {
  border: none;
  border-radius: 12px;
  padding: 10px 18px;
  cursor: pointer;
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: white;
  font-weight: 600;
  box-shadow: 0 18px 35px rgba(37, 99, 235, 0.25);
}

.palette-drag-ghost {
  position: fixed;
  top: -1000px;
  left: -1000px;
  padding: 10px 16px;
  border-radius: 12px;
  background: var(--bg-surface);
  border: 1px solid var(--stroke);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.2);
  font-size: 0.85rem;
  color: var(--text-primary);
}

mark {
  background: rgba(37, 99, 235, 0.2);
  color: inherit;
  padding: 0 2px;
  border-radius: 4px;
}

@media (max-width: 900px) {
  .palette-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .modal-body {
    grid-template-columns: 1fr;
  }

  .search input {
    width: 100%;
  }
}
</style>
