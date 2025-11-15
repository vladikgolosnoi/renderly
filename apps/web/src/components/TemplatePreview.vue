<template>
  <div class="template-preview" :class="{ compact }" :style="previewStyle">
    <header v-if="!compact" class="preview-header">
      <div>
        <p class="eyebrow">Онлайн-превью</p>
        <strong>{{ title }}</strong>
      </div>
      <button type="button" class="refresh" :disabled="loading" @click="reload">
        {{ loading ? "Обновляем..." : "Обновить превью" }}
      </button>
    </header>
    <div class="frame-wrapper" :class="{ loading, compact }">
      <div v-if="loading" class="skeleton">
        <div v-for="index in 5" :key="index" class="skeleton-row" />
      </div>
      <div v-else-if="error" class="preview-error">
        <p>{{ error }}</p>
        <button type="button" @click="reload">Повторить</button>
      </div>
      <div v-else class="preview-frame">
        <iframe
          ref="iframeRef"
          title="Предпросмотр шаблона"
          :srcdoc="html"
          :style="{ height: `${previewHeight}px` }"
          scrolling="yes"
          @load="handleLoad"
        />
        <div class="preview-mask top" />
        <div class="preview-mask bottom" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import api from "@/api/client";

const FALLBACK_IMAGE =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHZpZXdCb3g9JzAgMCA4MDAgNTAwJz48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9J2cnIHgxPScwJScgeTE9JzAlJyB4Mj0nMTAwJScgeTI9JzEwMCUnPjxzdG9wIG9mZnNldD0nMCUnIHN0b3AtY29sb3I9JyNjNGI1ZmQnLz48c3RvcCBvZmZzZXQ9JzEwMCUnIHN0b3AtY29sb3I9JyNhNWI0ZmMnLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cmVjdCB3aWR0aD0nODAwJyBoZWlnaHQ9JzUwMCcgZmlsbD0ndXJsKCNnKScgcng9JzI0Jy8+PHRleHQgeD0nNTAlJyB5PSc1MCUnIGZpbGw9JyNmZmYnIGZvbnQtZmFtaWx5PSdJbnRlcixBcmlhbCxzYW5zLXNlcmlmJyBmb250LXNpemU9JzMyJyB0ZXh0LWFuY2hvcj0nbWlkZGxlJz7QndC10YIg0L/RgNC10LLRjNGOPC90ZXh0Pjwvc3ZnPg==";
const BLOCKED_ASSET_REGEX =
  /https:\/\/cdn\.renderly\.dev\/[\w\-./]+?\.(?:png|jpe?g|webp|gif|svg)/gi;

const categoryAccent: Record<string, string> = {
  landing: "#6366f1",
  lead: "#ec4899",
  events: "#f97316",
  education: "#0ea5e9",
  commerce: "#10b981",
  story: "#facc15",
  default: "#818cf8"
};

const emit = defineEmits<{
  (e: "height-change", payload: number): void;
}>();

const props = defineProps<{
  templateId: number;
  title: string;
  category?: string | null;
  compact?: boolean;
  targetHeight?: number;
}>();

const accent = computed(() => categoryAccent[props.category ?? ""] ?? categoryAccent.default);
const previewStyle = computed(() => ({
  "--accent": accent.value
}));

const iframeRef = ref<HTMLIFrameElement | null>(null);
const html = ref("");
const loading = ref(true);
const error = ref<string | null>(null);
const compact = computed(() => Boolean(props.compact));
const baseTarget = computed(() => props.targetHeight ?? (compact.value ? 480 : 640));
const baseMin = computed(() => Math.max(compact.value ? 340 : 460, baseTarget.value - 180));
const baseMax = computed(() => Math.max(baseTarget.value + 260, compact.value ? 780 : 1020));
const previewHeight = ref(baseTarget.value);
let requestCursor = 0;

async function loadPreview() {
  const token = ++requestCursor;
  loading.value = true;
  error.value = null;
  try {
    const { data } = await api.get<{ html: string }>(`/templates/${props.templateId}/preview`);
    if (token !== requestCursor) {
      return;
    }
    html.value = stripBlockedAssets(data.html);
  } catch (err) {
    if (token !== requestCursor) {
      return;
    }
    console.error(err);
    error.value = "Не удалось загрузить превью. Попробуйте ещё раз.";
    html.value = "";
  } finally {
    if (token !== requestCursor) {
      return;
    }
    loading.value = false;
  }
}

function reload() {
  void loadPreview();
}

function handleLoad() {
  const iframe = iframeRef.value;
  if (!iframe) return;
  requestAnimationFrame(() => {
    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      if (!doc) {
        previewHeight.value = baseTarget.value;
        return;
      }
      enhanceIframeDocument(doc);
      installImageFallbacks(doc);
      const height = doc.body?.scrollHeight ?? 520;
      const clamped = Math.max(baseMin.value, Math.min(height, baseMax.value));
      previewHeight.value = clamped;
    } catch (err) {
      console.error(err);
      previewHeight.value = baseTarget.value;
    }
  });
}

onMounted(() => {
  void loadPreview();
});

watch(baseTarget, (value) => {
  previewHeight.value = value;
});

watch(
  previewHeight,
  (value) => {
    emit("height-change", value);
  },
  { immediate: true }
);

watch(
  () => props.templateId,
  () => {
    void loadPreview();
  }
);

function enhanceIframeDocument(doc: Document) {
  const htmlEl = doc.documentElement;
  const body = doc.body;
  if (htmlEl) {
    htmlEl.style.overflowX = "hidden";
    htmlEl.style.overflowY = "auto";
  }
  if (body) {
    body.style.overflowX = "hidden";
    body.style.overflowY = "auto";
    body.style.margin = "0 auto";
    body.style.maxWidth = "1200px";
    body.style.width = "100%";
    body.style.backgroundColor = "#fff";
    body.style.fontFamily = "'Inter', 'Manrope', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif";
  }
  const style = doc.createElement("style");
  style.textContent = `
    ::-webkit-scrollbar { width: 0 !important; height: 0 !important; }
    body { scrollbar-width: none; -ms-overflow-style: none; font-family: 'Inter', 'Manrope', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif; }
    img { max-width: 100%; height: auto; }
  `;
  doc.head?.appendChild(style);
}

function installImageFallbacks(doc: Document) {
  doc.querySelectorAll("img").forEach((img) => {
    const element = img as HTMLImageElement;
    const applyFallback = () => {
      if (element.dataset.fallbackApplied === "true") return;
      element.dataset.fallbackApplied = "true";
      element.src = FALLBACK_IMAGE;
    };
    element.addEventListener("error", applyFallback, { once: true });
    if (element.complete && element.naturalWidth === 0) {
      applyFallback();
    }
  });
}

function stripBlockedAssets(markup: string): string {
  if (!markup) return "";
  return markup.replace(BLOCKED_ASSET_REGEX, FALLBACK_IMAGE);
}
</script>

<style scoped>
.template-preview {
  border-radius: 28px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  background: radial-gradient(120% 120% at 0% 0%, rgba(255, 255, 255, 0.95), rgba(99, 102, 241, 0.08));
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  overflow: hidden;
}

.template-preview::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 100% 0%, rgba(255, 255, 255, 0.35), transparent 45%);
  pointer-events: none;
}

.template-preview.compact {
  padding: 0;
  border-radius: 22px;
  background: transparent;
  width: 100%;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  position: relative;
  z-index: 1;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  color: rgba(15, 23, 42, 0.55);
  margin: 0 0 4px;
}

.preview-header strong {
  font-size: 1.05rem;
  color: #0f172a;
}

.refresh {
  border: 1px solid rgba(99, 102, 241, 0.4);
  background: rgba(255, 255, 255, 0.85);
  color: #312e81;
  border-radius: 999px;
  padding: 6px 16px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.refresh:disabled {
  opacity: 0.6;
  cursor: default;
}

.frame-wrapper {
  border-radius: 24px;
  border: 1px solid rgba(15, 23, 42, 0.05);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.02), rgba(15, 23, 42, 0.07));
  padding: 18px;
  position: relative;
  overflow: hidden;
  min-height: 520px;
}

.frame-wrapper.compact {
  min-height: 380px;
  padding: 12px;
  border-radius: 20px;
  width: 100%;
}

.frame-wrapper.compact .preview-frame {
  width: 100%;
}

.frame-wrapper.loading {
  min-height: 320px;
}

.preview-frame {
  position: relative;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: #fff;
}

.preview-frame iframe {
  width: 100%;
  border: none;
  display: block;
  background: #fff;
  scrollbar-width: none;
}

.preview-frame iframe::-webkit-scrollbar {
  display: none;
}

.preview-mask {
  position: absolute;
  left: 0;
  right: 0;
  height: 28px;
  pointer-events: none;
  z-index: 2;
}

.preview-mask.top {
  top: 0;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.9), transparent);
}

.preview-mask.bottom {
  bottom: 0;
  background: linear-gradient(0deg, rgba(248, 250, 252, 0.9), transparent);
}

.skeleton {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.skeleton-row {
  flex: 1;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(226, 232, 240, 0.8), rgba(248, 250, 252, 0.6), rgba(226, 232, 240, 0.8));
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.preview-error {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
  justify-content: center;
  min-height: 200px;
  color: #1e1b4b;
}

.preview-error button {
  border: none;
  border-radius: 12px;
  background: var(--accent);
  color: #fff;
  padding: 8px 18px;
  cursor: pointer;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
