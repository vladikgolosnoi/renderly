<template>
  <div class="wizard-overlay" role="dialog" aria-modal="true">
    <div class="wizard-card">
      <header>
        <div>
          <p class="eyebrow">{{ copy.hero.eyebrow }}</p>
          <h3>{{ copy.hero.title }}</h3>
          <p>{{ copy.hero.subtitle }}</p>
        </div>
        <button class="ghost" type="button" @click="('close')">{{ copy.actions.close }}</button>
      </header>

      <section class="presets">
        <article
          v-for="preset in presets"
          :key="preset.name"
          class="preset"
          @click="applyPreset(preset.palette)"
        >
          <strong>{{ preset.name }}</strong>
          <p>{{ preset.description }}</p>
          <div class="swatches">
            <span v-for="(color, key) in preset.palette" :key="key" :style="{ background: color }"></span>
          </div>
        </article>
      </section>

      <section class="logo-section">
        <h4>{{ copy.upload.title }}</h4>
        <p>{{ copy.upload.description }}</p>
        <label class="upload">
          <input type="file" accept="image/*" @change="handleLogo" />
          <span>{{ extracting ? copy.upload.loading : copy.upload.cta }}</span>
        </label>
        <div v-if="generatedPalette" class="generated">
          <div class="swatches">
            <span
              v-for="(color, key) in generatedPalette"
              :key="key"
              :style="{ background: color }"
              :title="key"
            ></span>
          </div>
          <button type="button" class="primary" @click="applyGenerated" :disabled="!generatedPalette">
            {{ copy.upload.apply }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const copy = {
  hero: {
    eyebrow: "Ассистент палитр",
    title: "Подберите стиль так, будто с вами арт-директор",
    subtitle: "Выберите готовый сет или загрузите логотип — под скажем вам цвета для страницы и CTA.",
  },
  upload: {
    title: "Есть логотип?",
    description: "Мы проанализируем изображение и предложим палитру в фирменном стиле.",
    cta: "Загрузить логотип",
    loading: "Извлекаем цвета...",
    apply: "Применить палитру",
  },
  actions: {
    close: "Закрыть",
  },
} as const;

const props = defineProps<{
  currentTheme: Record<string, string>;
}>();

const emit = defineEmits<{
  apply: [Record<string, string>];
  close: [];
}>();

interface Preset {
  name: string;
  description: string;
  palette: Record<string, string>;
}

const presets: Preset[] = [
  {
    name: "Неоновый кампус",
    description: "Контрастные акценты и глубокий фон для технологичных школ и демо-дней.",
    palette: {
      page_bg: "#f1f5ff",
      text_color: "#0f172a",
      accent: "#2f5aff",
      header_bg: "#ffffff",
      header_text: "#172554",
      footer_bg: "#111c44",
      footer_text: "#ffffff",
    },
  },
  {
    name: "Эмоциональный бренд",
    description: "Мягкие розовые и фиолетовые оттенки для комьюнити и креативных продуктов.",
    palette: {
      page_bg: "#fdf2f8",
      text_color: "#311b58",
      accent: "#f43f5e",
      header_bg: "#ffffff",
      header_text: "#311b58",
      footer_bg: "#311b58",
      footer_text: "#fdf2f8",
    },
  },
  {
    name: "Смелый маркетинг",
    description: "Минималистичный фон и яркий CTA для лендингов с конверсией в заявку.",
    palette: {
      page_bg: "#f5f7fa",
      text_color: "#1f2933",
      accent: "#f97316",
      header_bg: "#ffffff",
      header_text: "#1f2933",
      footer_bg: "#1f2933",
      footer_text: "#ffffff",
    },
  },
];

const generatedPalette = ref<Record<string, string> | null>(null);
const extracting = ref(false);

function applyPreset(palette: Record<string, string>) {
  emit("apply", palette);
}

const MAX_CANVAS_SIZE = 320;

function handleLogo(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  extracting.value = true;
  const reader = new FileReader();
  reader.onload = () => {
    const img = new Image();
    img.onload = () => {
      try {
        const scale = Math.min(MAX_CANVAS_SIZE / img.width, MAX_CANVAS_SIZE / img.height, 1);
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        if (!ctx) throw new Error("Canvas context unavailable");
        canvas.width = Math.max(1, Math.round(img.width * scale));
        canvas.height = Math.max(1, Math.round(img.height * scale));
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height);
        generatedPalette.value = buildPaletteFromData(data);
      } catch (error) {
        console.error("Palette extraction failed", error);
        generatedPalette.value = null;
      } finally {
        extracting.value = false;
      }
    };
    img.src = reader.result as string;
  };
  reader.readAsDataURL(file);
}

function buildPaletteFromData(data: Uint8ClampedArray): Record<string, string> {
  let r = 0;
  let g = 0;
  let b = 0;
  let count = 0;
  for (let i = 0; i < data.length; i += 12) {
    r += data[i];
    g += data[i + 1];
    b += data[i + 2];
    count += 1;
  }
  if (!count) {
    return {
      page_bg: "#f4f4f5",
      text_color: "#111827",
      accent: "#6366f1",
      header_bg: "#ffffff",
      header_text: "#111827",
      footer_bg: "#111827",
      footer_text: "#ffffff",
    };
  }
  const avg = {
    r: Math.round(r / count),
    g: Math.round(g / count),
    b: Math.round(b / count),
  };
  const accent = rgbToHex(avg.r, avg.g, avg.b);
  const page = lighten(accent, 0.75);
  const header = lighten(accent, 0.45);
  const footer = darken(accent, 0.35);
  const text = contrastColor(page);
  const footerText = contrastColor(footer);
  return {
    page_bg: page,
    text_color: text,
    accent,
    header_bg: header,
    header_text: contrastColor(header),
    footer_bg: footer,
    footer_text: footerText,
  };
}

function applyGenerated() {
  if (!generatedPalette.value) return;
  emit("apply", generatedPalette.value);
}

function rgbToHex(r: number, g: number, b: number) {
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function toHex(value: number) {
  return value.toString(16).padStart(2, "0");
}

function lighten(color: string, amount: number) {
  const { r, g, b } = hexToRgb(color);
  return rgbToHex(
    Math.min(255, Math.round(r + (255 - r) * amount)),
    Math.min(255, Math.round(g + (255 - g) * amount)),
    Math.min(255, Math.round(b + (255 - b) * amount)),
  );
}

function darken(color: string, amount: number) {
  const { r, g, b } = hexToRgb(color);
  return rgbToHex(
    Math.max(0, Math.round(r * (1 - amount))),
    Math.max(0, Math.round(g * (1 - amount))),
    Math.max(0, Math.round(b * (1 - amount))),
  );
}

function contrastColor(color: string) {
  const { r, g, b } = hexToRgb(color);
  const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
  return luminance > 150 ? "#0f172a" : "#ffffff";
}

function hexToRgb(color: string) {
  const value = color.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return { r, g, b };
}
</script>

<style scoped>
.wizard-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 999;
}

.wizard-card {
  width: min(860px, 100%);
  background: var(--bg-surface);
  border-radius: 32px;
  padding: 32px;
  box-shadow: 0 40px 80px rgba(15, 23, 42, 0.35);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eyebrow {
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.14em;
  margin: 0 0 6px;
  color: var(--accent);
}

header p {
  margin: 0;
  color: var(--text-secondary);
}

header h3 {
  margin: 0;
}

.preset {
  border: 1px solid var(--stroke);
  border-radius: 20px;
  padding: 16px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.preset:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-soft);
}

.swatches {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(32px, 1fr));
  gap: 6px;
  margin-top: 12px;
}

.swatches span {
  height: 30px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.15);
}

.logo-section {
  border-top: 1px solid var(--stroke);
  padding-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload {
  border: 1px dashed var(--stroke);
  border-radius: 20px;
  padding: 18px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.upload input {
  display: none;
}

.generated {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.primary {
  border: none;
  border-radius: 12px;
  padding: 10px 18px;
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.ghost {
  border-radius: 12px;
  border: 1px solid var(--stroke);
  background: transparent;
  color: var(--text-primary);
  padding: 8px 14px;
  cursor: pointer;
}

@media (max-width: 720px) {
  .wizard-card {
    padding: 20px;
  }

  header {
    flex-direction: column;
  }
}
</style>
