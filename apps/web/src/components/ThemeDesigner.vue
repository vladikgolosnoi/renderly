<template>
  <section class="theme-designer" :class="{ compact: compactMode }">
    <div class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">{{ copy.hero.eyebrow }}</p>
        <h3>{{ copy.hero.title }}</h3>
        <p>{{ copy.hero.description }}</p>
        <div class="hero-actions">
          <button type="button" class="primary" @click="showWizard = true">{{ copy.hero.wizardCta }}</button>
          <button type="button" class="secondary" @click="resetToDefault">{{ copy.hero.resetCta }}</button>
        </div>
      </div>
      <div class="hero-preview" aria-hidden="true">
        <div class="preview-header" :style="previewStyles.header">
          <span>Renderly</span>
          <span class="status-dot" :style="{ background: localTheme.accent }"></span>
        </div>
        <div class="preview-body" :style="previewStyles.body">
          <div class="preview-card">
            <div class="pill" :style="{ background: localTheme.accent }"></div>
            <div class="lines">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
          <div class="preview-card muted"></div>
        </div>
        <div class="preview-footer" :style="previewStyles.footer">
          <span>Footer</span>
        </div>
      </div>
    </div>

    <div class="presets-panel">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{{ copy.presets.eyebrow }}</p>
          <h4>{{ copy.presets.title }}</h4>
          <p>{{ copy.presets.description }}</p>
        </div>
        <div class="save-control">
          <input v-model="templateName" type="text" :placeholder="copy.presets.placeholder" />
          <button type="button" :disabled="!templateName" @click="saveTemplate">{{ copy.presets.save }}</button>
        </div>
      </div>

      <div class="preset-grid" v-if="hasTemplates">
        <button
          v-for="template in curatedTemplates"
          :key="template.id"
          type="button"
          class="preset-card"
          :class="{ active: selectedTemplateId === String(template.id) }"
          @click="handleTemplateClick(template)"
        >
          <div class="preset-head">
            <span>{{ template.name }}</span>
            <span class="badge">Live</span>
          </div>
          <div class="swatches">
            <span
              v-for="key in swatchKeys"
              :key="`${template.id}-${key}`"
              :style="{ background: template.palette[key] ?? defaultTheme[key] }"
            ></span>
          </div>
          <small>{{ copy.presets.swatchLegend }}</small>
        </button>
        <button type="button" class="preset-card ghost-card" @click="showWizard = true">
          <div class="ghost-icon">+</div>
          <p>{{ copy.presets.assistCard }}</p>
        </button>
      </div>
      <div class="empty-presets" v-else>
        <p>{{ copy.presets.empty }}</p>
        <button type="button" class="primary ghost" @click="showWizard = true">
          {{ copy.presets.wizardCta }}
        </button>
      </div>
    </div>

    <div class="fields-panel">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{{ copy.fields.eyebrow }}</p>
          <h4>{{ copy.fields.title }}</h4>
          <p>{{ copy.fields.description }}</p>
        </div>
      </div>
      <div class="groups">
        <div v-for="group in colorGroups" :key="group.key" class="group-card">
          <div class="group-head">
            <h5>{{ group.title }}</h5>
            <p>{{ group.description }}</p>
          </div>
          <div class="group-fields">
            <label v-for="field in group.fields" :key="field.key">
              <span>{{ field.label }}</span>
              <div class="field-controls">
                <input type="color" v-model="localTheme[field.key]" />
                <input
                  type="text"
                  v-model="localTheme[field.key]"
                  @blur="normalizeHex(field.key)"
                  maxlength="7"
                />
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>

    <BrandWizard
      v-if="showWizard"
      :current-theme="localTheme"
      @apply="applyWizardPalette"
      @close="showWizard = false"
    />
  </section>
</template>

<script setup lang="ts">
import { reactive, watch, ref, computed, nextTick } from "vue";
import type { ThemeTemplate } from "@/types/blocks";
import BrandWizard from "@/components/BrandWizard.vue";

type ThemeKey =
  | "page_bg"
  | "text_color"
  | "accent"
  | "header_bg"
  | "header_text"
  | "footer_bg"
  | "footer_text";

type ColorField = { key: ThemeKey; label: string };
type ColorGroup = { key: string; title: string; description: string; fields: ColorField[] };

const copy = {
  hero: {
    eyebrow: "\u0421\u0442\u0443\u0434\u0438\u044f \u0431\u0440\u0435\u043d\u0434\u0430",
    title: "\u0421\u043e\u0431\u0435\u0440\u0438\u0442\u0435 \u0432\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u043a\u043e\u0434 \u043f\u0440\u043e\u0435\u043a\u0442\u0430",
    description:
      "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u043f\u0440\u0435\u0434\u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u043d\u044b\u0435 \u043f\u0430\u043b\u0438\u0442\u0440\u044b \u0438\u043b\u0438 \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u0442\u0435 \u043a\u0430\u0436\u0434\u0443\u044e \u0440\u043e\u043b\u044c \u0432\u0440\u0443\u0447\u043d\u0443\u044e, \u0447\u0442\u043e\u0431\u044b \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0430 \u0432\u044b\u0433\u043b\u044f\u0434\u0435\u043b\u0430 \u043a\u0430\u043a \u043f\u0440\u0435\u043c\u0438\u0430\u043b\u044c\u043d\u044b\u0439 \u043b\u0435\u043d\u0434\u0438\u043d\u0433 \u0438\u0437 Tilda \u0438\u043b\u0438 Taplink.",
    wizardCta: "\u0410\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442 \u043f\u0430\u043b\u0438\u0442\u0440",
    resetCta: "\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0446\u0432\u0435\u0442\u0430"
  },
  presets: {
    eyebrow: "\u0413\u043e\u0442\u043e\u0432\u044b\u0435 \u0440\u0435\u0448\u0435\u043d\u0438\u044f",
    title: "\u041f\u0430\u043b\u0438\u0442\u0440\u044b \u043a\u0430\u043a \u0443 \u043b\u0443\u0447\u0448\u0438\u0445 \u043a\u043e\u043d\u0441\u0442\u0440\u0443\u043a\u0442\u043e\u0440\u043e\u0432",
    description:
      "\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043d\u0430 \u043a\u0430\u0440\u0442\u043e\u0447\u043a\u0443, \u0447\u0442\u043e\u0431\u044b \u043c\u0433\u043d\u043e\u0432\u0435\u043d\u043d\u043e \u043f\u0440\u0438\u043c\u0435\u0440\u0438\u0442\u044c \u0441\u0442\u0438\u043b\u044c.",
    placeholder: "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043f\u0440\u0435\u0441\u0435\u0442\u0430",
    save: "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c",
    swatchLegend: "\u0424\u043e\u043d \u00b7 \u0430\u043a\u0446\u0435\u043d\u0442 \u00b7 \u0442\u0435\u043a\u0441\u0442 \u00b7 \u0448\u0430\u043f\u043a\u0430 \u00b7 \u043f\u043e\u0434\u0432\u0430\u043b",
    assistCard: "\u041f\u043e\u0434\u043e\u0431\u0440\u0430\u0442\u044c \u043f\u0430\u043b\u0438\u0442\u0440\u0443 \u0441 \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442\u043e\u043c",
    empty:
      "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u0435 \u043f\u0435\u0440\u0432\u0443\u044e \u043f\u0430\u043b\u0438\u0442\u0440\u0443 \u0438\u043b\u0438 \u0432\u043e\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435\u0441\u044c \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442\u043e\u043c \u043f\u043e\u0434\u0431\u043e\u0440\u0430.",
    wizardCta: "\u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c Brand Wizard"
  },
  fields: {
    eyebrow: "\u0422\u043e\u0447\u043d\u0430\u044f \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430",
    title: "\u0426\u0432\u0435\u0442\u043e\u0432\u044b\u0435 \u0440\u043e\u043b\u0438",
    description:
      "\u0424\u0438\u043a\u0441\u0438\u0440\u0443\u0435\u043c \u0435\u0434\u0438\u043d\u044b\u0439 \u0432\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0440\u0438\u0442\u043c \u0434\u043b\u044f \u0434\u0430\u0448\u0431\u043e\u0440\u0434\u0430 \u0438 \u0440\u0435\u0434\u0430\u043a\u0442\u043e\u0440\u0430."
  },
  groups: {
    foundation: {
      title: "\u0411\u0430\u0437\u043e\u0432\u044b\u0435 \u043f\u043e\u0432\u0435\u0440\u0445\u043d\u043e\u0441\u0442\u0438",
      description:
        "\u0424\u043e\u043d \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u044b \u0438 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0442\u0435\u043a\u0441\u0442 \u2014 \u0437\u0430\u0434\u0430\u044e\u0442 \u043f\u0435\u0440\u0432\u043e\u0435 \u0432\u043f\u0435\u0447\u0430\u0442\u043b\u0435\u043d\u0438\u0435 \u0438 \u0447\u0438\u0442\u0430\u0435\u043c\u043e\u0441\u0442\u044c.",
      labels: {
        page_bg: "\u0424\u043e\u043d \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u044b",
        text_color: "\u041e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0442\u0435\u043a\u0441\u0442"
      }
    },
    accent: {
      title: "\u0410\u043a\u0446\u0435\u043d\u0442\u044b \u0438 CTA",
      description:
        "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u043a\u043e\u043d\u0442\u0440\u0430\u0441\u0442\u043d\u044b\u0439 \u043e\u0442\u0442\u0435\u043d\u043e\u043a \u0434\u043b\u044f \u043a\u043d\u043e\u043f\u043e\u043a, \u0441\u0441\u044b\u043b\u043e\u043a \u0438 \u0432\u0430\u0436\u043d\u044b\u0445 \u0431\u043b\u043e\u043a\u043e\u0432.",
      labels: {
        accent: "\u0410\u043a\u0446\u0435\u043d\u0442\u043d\u044b\u0439 \u0446\u0432\u0435\u0442"
      }
    },
    layout: {
      title: "\u0428\u0430\u043f\u043a\u0430 \u0438 \u043f\u043e\u0434\u0432\u0430\u043b",
      description:
        "\u0417\u0434\u0435\u0441\u044c \u0437\u0430\u043a\u0440\u0435\u043f\u043b\u044f\u0435\u043c \u0431\u0440\u0435\u043d\u0434\u043e\u0432\u044b\u0435 \u043a\u043e\u043d\u0442\u0440\u0430\u0441\u0442\u044b \u0438 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u043c \u0431\u0430\u043b\u0430\u043d\u0441.",
      labels: {
        header_bg: "\u0424\u043e\u043d \u0448\u0430\u043f\u043a\u0438",
        header_text: "\u0422\u0435\u043a\u0441\u0442 \u0448\u0430\u043f\u043a\u0438",
        footer_bg: "\u0424\u043e\u043d \u043f\u043e\u0434\u0432\u0430\u043b\u0430",
        footer_text: "\u0422\u0435\u043a\u0441\u0442 \u043f\u043e\u0434\u0432\u0430\u043b\u0430"
      }
    }
  }
} as const;

const colorGroups: ColorGroup[] = [
  {
    key: "foundation",
    title: copy.groups.foundation.title,
    description: copy.groups.foundation.description,
    fields: [
      { key: "page_bg", label: copy.groups.foundation.labels.page_bg },
      { key: "text_color", label: copy.groups.foundation.labels.text_color }
    ]
  },
  {
    key: "accent",
    title: copy.groups.accent.title,
    description: copy.groups.accent.description,
    fields: [{ key: "accent", label: copy.groups.accent.labels.accent }]
  },
  {
    key: "layout",
    title: copy.groups.layout.title,
    description: copy.groups.layout.description,
    fields: [
      { key: "header_bg", label: copy.groups.layout.labels.header_bg },
      { key: "header_text", label: copy.groups.layout.labels.header_text },
      { key: "footer_bg", label: copy.groups.layout.labels.footer_bg },
      { key: "footer_text", label: copy.groups.layout.labels.footer_text }
    ]
  }
];

const swatchKeys: ThemeKey[] = ["page_bg", "accent", "text_color", "header_bg", "footer_bg"];

const props = withDefaults(
  defineProps<{
  theme: Record<string, string>;
  templates: ThemeTemplate[];
  compact?: boolean;
}>(),
  {
    compact: false
  }
);

const emit = defineEmits<{
  change: [Record<string, string>];
  "save-template": [string];
  "apply-template": [Record<string, string>];
}>();

const defaultTheme: Record<ThemeKey, string> = {
  page_bg: "#f8fafc",
  text_color: "#0f172a",
  accent: "#6366f1",
  header_bg: "#ffffff",
  header_text: "#0f172a",
  footer_bg: "#0f172a",
  footer_text: "#ffffff"
};

const localTheme = reactive<Record<ThemeKey, string>>({ ...defaultTheme, ...props.theme });
const templateName = ref("");
const selectedTemplateId = ref<string>("");
const showWizard = ref(false);
const syncing = ref(false);

const curatedTemplates = computed(() => props.templates?.slice(0, 6) ?? []);
const hasTemplates = computed(() => curatedTemplates.value.length > 0);
const compactMode = computed(() => props.compact);
const previewStyles = computed(() => ({
  header: {
    background: localTheme.header_bg,
    color: localTheme.header_text
  },
  body: {
    background: localTheme.page_bg,
    color: localTheme.text_color
  },
  footer: {
    background: localTheme.footer_bg,
    color: localTheme.footer_text
  }
}));

watch(
  () => props.theme,
  (theme) => {
    syncing.value = true;
    Object.assign(localTheme, defaultTheme, theme ?? {});
    selectedTemplateId.value = "";
    nextTick(() => {
      syncing.value = false;
    });
  },
  { deep: true }
);

watch(
  localTheme,
  () => {
    if (syncing.value) return;
    emit("change", { ...localTheme });
  },
  { deep: true }
);

function saveTemplate() {
  if (!templateName.value.trim()) return;
  emit("save-template", templateName.value.trim());
  templateName.value = "";
}

function handleTemplateClick(template: ThemeTemplate) {
  selectedTemplateId.value = String(template.id);
  emit("apply-template", template.palette);
}

function resetToDefault() {
  Object.assign(localTheme, defaultTheme);
  emit("change", { ...localTheme });
  selectedTemplateId.value = "";
}

function normalizeHex(key: ThemeKey) {
  const value = (localTheme[key] ?? "").trim();
  if (!value) return;
  localTheme[key] = value.startsWith("#") ? value : `#${value}`;
}

function applyWizardPalette(palette: Record<string, string>) {
  Object.assign(localTheme, defaultTheme, palette);
  emit("change", { ...localTheme });
  showWizard.value = false;
}
</script>

<style scoped>
.theme-designer {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

.theme-designer * {
  box-sizing: border-box;
}

.hero-card {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  padding: 32px;
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(14, 165, 233, 0.08));
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: var(--shadow-soft);
}

.theme-designer.compact .hero-card {
  grid-template-columns: 1fr;
  padding: 24px;
}

.hero-copy h3 {
  margin: 8px 0 12px;
  font-size: 1.6rem;
}

.hero-copy p {
  color: var(--text-secondary);
  margin: 0 0 20px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.theme-designer.compact .hero-actions {
  flex-direction: column;
}

.primary,
.secondary {
  border-radius: 12px;
  border: none;
  padding: 10px 18px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.primary {
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: #fff;
  box-shadow: 0 15px 25px rgba(37, 99, 235, 0.25);
}

.secondary {
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: var(--text-primary);
}

.primary:hover,
.secondary:hover {
  transform: translateY(-1px);
}

.hero-preview {
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  gap: 0;
  background: var(--bg-surface);
}

.theme-designer.compact .hero-preview {
  max-width: 100%;
}

.preview-header,
.preview-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  font-weight: 600;
}

.preview-body {
  padding: 20px;
  display: grid;
  gap: 12px;
}

.preview-card {
  border-radius: 14px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(15, 23, 42, 0.05);
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-card.muted {
  opacity: 0.6;
  min-height: 54px;
}

.pill {
  width: 48px;
  height: 48px;
  border-radius: 14px;
}

.lines {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.lines span {
  display: block;
  height: 6px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.5;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.presets-panel,
.fields-panel {
  background: var(--bg-surface);
  border-radius: 24px;
  padding: 28px;
  border: 1px solid var(--stroke);
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.07);
}

.section-heading {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.eyebrow {
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: 0.75rem;
  color: var(--accent-strong);
  margin: 0;
}

.save-control {
  display: flex;
  gap: 12px;
  align-items: center;
  width: 100%;
}

.theme-designer.compact .save-control {
  flex-direction: column;
  align-items: stretch;
  width: 100%;
}

.save-control input {
  border-radius: 12px;
  border: 1px solid var(--stroke);
  padding: 10px 14px;
  background: var(--bg-soft);
  flex: 1;
  min-width: 0;
}

.save-control button {
  background: var(--text-primary);
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s ease;
}

.save-control button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.theme-designer.compact .preset-grid {
  grid-template-columns: 1fr;
}

.preset-card {
  border-radius: 20px;
  border: 1px solid var(--stroke);
  background: var(--bg-soft);
  padding: 18px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.preset-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-soft);
}

.preset-card.active {
  border-color: var(--accent);
  box-shadow: 0 18px 35px rgba(37, 99, 235, 0.18);
}

.preset-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.badge {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent-strong);
}

.swatches {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}

.swatches span {
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.ghost-card {
  justify-content: center;
  align-items: center;
  text-align: center;
  gap: 12px;
  border-style: dashed;
  color: var(--text-secondary);
}

.ghost-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  border: 1px solid var(--stroke);
  display: grid;
  place-items: center;
  font-size: 1.4rem;
}

.empty-presets {
  padding: 32px;
  text-align: center;
  border-radius: 18px;
  background: var(--bg-soft);
  border: 1px dashed var(--stroke);
  display: grid;
  gap: 14px;
  justify-items: center;
}

.empty-presets .primary.ghost {
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  box-shadow: none;
}

.groups {
  display: grid;
  gap: 18px;
}

.group-card {
  border-radius: 20px;
  border: 1px solid var(--stroke);
  padding: 20px;
  background: linear-gradient(120deg, rgba(148, 187, 233, 0.08), rgba(238, 174, 202, 0.08));
}

.group-head h5 {
  margin: 0 0 6px;
  font-size: 1.05rem;
}

.group-head p {
  margin: 0 0 14px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.group-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  width: 100%;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  width: 100%;
}

.field-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(15, 23, 42, 0.06);
  width: 100%;
  box-sizing: border-box;
}

.field-controls input[type="color"] {
  width: 44px;
  height: 32px;
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
}

.field-controls input[type="text"] {
  flex: 1;
  border: none;
  background: transparent;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 0;
}

.field-controls input[type="text"]:focus {
  outline: none;
}

@media (max-width: 768px) {
  .hero-card {
    padding: 24px;
  }

  .save-control {
    flex-direction: column;
    width: 100%;
  }

.save-control input {
    width: 100%;
  }
}

</style>
