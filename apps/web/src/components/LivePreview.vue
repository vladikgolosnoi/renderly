<template>
  <div class="preview" id="live-preview">
    <header>
      <div class="heading">
        <h3>Live Preview</h3>
        <span v-if="isSyncing">{{ copy.syncing }}</span>
      </div>
      <div class="controls">
        <div class="viewports">
          <button
            v-for="option in viewportOptions"
            :key="option.value"
            type="button"
            :class="{ active: viewport === option.value }"
            @click="viewport = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <button type="button" class="ghost" @click="openCurrentInTab" :disabled="!lastSnapshot">
          {{ copy.openInTab }}
        </button>
      </div>
    </header>
    <div class="device-preview" :class="`device-${viewport}`" :style="deviceStyle">
      <div class="device-shell">
        <div class="device-frame">
          <div class="device-screen">
            <div class="device-screen-inner">
              <iframe
                v-for="index in 2"
                :key="index"
                class="preview-frame"
                :class="{ active: activeFrameIndex === index - 1 }"
                :ref="(el) => setFrameRef(el as HTMLIFrameElement | null, index - 1)"
                title="preview"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    <section class="history">
      <header>
        <strong>{{ copy.historyTitle }}</strong>
        <span>{{ history.length }}/5</span>
      </header>
      <ul>
        <li v-for="entry in history" :key="entry.id">
          <button type="button" @click="loadSnapshot(entry)">
            {{ formatTimestamp(entry.createdAt) }}
          </button>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed, reactive } from "vue";
import api from "@/api/client";
import type { AssetItem, BlockDefinition, BlockInstance } from "@/types/blocks";
import { useOnboardingStore } from "@/stores/onboarding";

type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";

const copy = {
  syncing: "SSR обновляется...",
  openInTab: "Открыть в новой вкладке",
  historyTitle: "История предпросмотров",
  saveStates: {
    dirty: "Есть несохранённые правки",
    saving: "Сохраняем...",
    saved: "Обновлено",
    error: "Ошибка синхронизации",
    idle: ""
  }
} as const;

const props = defineProps<{
  projectId?: number;
  title: string;
  blocks: BlockInstance[];
  catalog: BlockDefinition[];
  theme: Record<string, string>;
  settings: Record<string, unknown>;
  locale: string;
  defaultLocale: string;
  saveStates?: Record<number, SaveState>;
  quickAssets?: AssetItem[];
  selectedBlockId?: number | null;
}>();

const SAVE_STATE_LABELS = copy.saveStates;
const BRIDGE_SAVE_STATE_LABELS = JSON.stringify(SAVE_STATE_LABELS);

const emit = defineEmits<{
  select: [number];
  reorder: [{ from: number; to: number }];
  insert: [{ definitionKey: string; index: number }];
  "inline-edit": [{ blockId: number; fieldKey: string; value: string; path?: (string | number)[] }];
  "request-asset": [{ blockId: number; fieldKey: string; label: string; path: (string | number)[] }];
}>();

const isSyncing = ref(false);
const viewport = ref<Viewport>("desktop");
let debounceHandle: number | undefined;
const onboarding = useOnboardingStore();
const onboardingNotified = ref(false);
const history = ref<PreviewSnapshot[]>([]);
const frameRefs = reactive<Array<HTMLIFrameElement | null>>([null, null]);
const activeFrameIndex = ref(0);
let pendingFrameIndex: number | null = null;
let activeBridgeReady = false;
let pendingHighlight: number | null = null;
let latestSaveStates: Record<number, SaveState> = {};
const deferredPreview = ref(false);
const hasPendingSave = computed(() => {
  const states = props.saveStates ?? {};
  return Object.values(states).some((state) => state === "dirty" || state === "saving");
});
let lastScrollTop = 0;

function setFrameRef(el: HTMLIFrameElement | null, index: number) {
  frameRefs[index] = el;
}

function getFrameWindow(index = activeFrameIndex.value) {
  return frameRefs[index]?.contentWindow ?? null;
}

function getFrameDocument(index = activeFrameIndex.value) {
  return getFrameWindow(index)?.document ?? null;
}

function idleFrameIndex() {
  return activeFrameIndex.value === 0 ? 1 : 0;
}

function frameIndexFromSource(source: MessageEvent["source"]) {
  if (!source || typeof source === "string") {
    return null;
  }
  const windowSource = source as Window;
  for (let i = 0; i < frameRefs.length; i += 1) {
    if (frameRefs[i]?.contentWindow === windowSource) {
      return i;
    }
  }
  return null;
}

function captureScrollPosition() {
  const win = getFrameWindow();
  if (!win) {
    return;
  }
  try {
    lastScrollTop =
      win.scrollY ??
      win.document?.documentElement?.scrollTop ??
      win.document?.body?.scrollTop ??
      0;
  } catch {
    lastScrollTop = 0;
  }
}

function restoreScrollPosition(index = activeFrameIndex.value) {
  const win = getFrameWindow(index);
  if (!win) return;
  try {
    win.scrollTo(0, lastScrollTop);
  } catch {
    // ignore
  }
}
const viewportOptions: Array<{
  label: string;
  value: Viewport;
  width: number;
  height: number;
  ratio: string;
}> = [
  { label: "Desktop", value: "desktop", width: 1280, height: 720, ratio: "1280 / 720" },
  { label: "Tablet", value: "tablet", width: 1024, height: 1366, ratio: "1024 / 1366" },
  { label: "Mobile", value: "mobile", width: 390, height: 844, ratio: "390 / 844" }
];

const BRIDGE_SOURCE = "renderly-bridge";
const PARENT_SOURCE = "renderly-parent";
const BRIDGE_STYLE = String.raw`
[data-field-path][contenteditable="true"]:focus {
  outline: 2px solid rgba(99, 102, 241, 0.5);
  border-radius: 6px;
}
[data-field-kind="asset"] {
  cursor: pointer;
}
[data-block-section] {
  position: relative;
}
[data-block-section].renderly-active-block {
  outline: 2px solid rgba(99, 102, 241, 0.9);
  outline-offset: 6px;
  border-radius: 16px;
}
[data-block-section].renderly-state-dirty {
  box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.35);
}
[data-block-section].renderly-state-saving {
  box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.45);
}
[data-block-section].renderly-state-saved {
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.4);
}
[data-block-section].renderly-state-error {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.4);
}
.renderly-save-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.9);
  color: #fff;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.18);
  pointer-events: none;
  opacity: 0;
  transform: translateY(-6px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.renderly-save-indicator.is-visible {
  opacity: 1;
  transform: translateY(0);
}
.renderly-save-indicator[data-state="dirty"] {
  background: rgba(234, 88, 12, 0.92);
}
.renderly-save-indicator[data-state="saving"] {
  background: rgba(251, 191, 36, 0.95);
  color: #0f172a;
}
.renderly-save-indicator[data-state="saved"] {
  background: rgba(16, 185, 129, 0.95);
}
.renderly-save-indicator[data-state="error"] {
  background: rgba(239, 68, 68, 0.95);
}
`;
const BRIDGE_RUNTIME = String.raw`
(function () {
  var SOURCE = "${BRIDGE_SOURCE}";
  var PARENT_SOURCE = "${PARENT_SOURCE}";
  var SAVE_STATE_LABELS = ${BRIDGE_SAVE_STATE_LABELS};
  var activeSection = null;
  var saveStateCache = {};
  var SAVE_STATE_CLASSES = ["renderly-state-dirty", "renderly-state-saving", "renderly-state-saved", "renderly-state-error"];
  var EMBEDDED = window.parent && window.parent !== window;
  if (!EMBEDDED) {
    return;
  }

  function send(type, payload) {
    if (window.parent) {
      window.parent.postMessage({ source: SOURCE, type: type, payload: payload }, "*");
    }
  }

  function selectBlock(blockId) {
    if (blockId) {
      send("select-block", { blockId: blockId });
    }
  }

  function hasFieldInPath(event) {
    if (typeof event.composedPath === "function") {
      var path = event.composedPath();
      for (var i = 0; i < path.length; i += 1) {
        var node = path[i];
        if (node && node.getAttribute && node.hasAttribute("data-field-path")) {
          return true;
        }
      }
      return false;
    }
    var target = event.target;
    while (target && target !== document) {
      if (target && target.getAttribute && target.hasAttribute("data-field-path")) {
        return true;
      }
      target = target.parentElement;
    }
    return false;
  }

  function enhanceLinksAndForms() {
    document.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
      });
    });
    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
      });
    });
  }

  function enhanceFields() {
    document.querySelectorAll("[data-field-path]").forEach(function (node) {
      var blockId = Number(node.getAttribute("data-block-id"));
      var fieldPath = node.getAttribute("data-field-path");
      var fieldLabel = node.getAttribute("data-field-label") || fieldPath;
      var kind = node.getAttribute("data-field-kind") || "text";
      if (!blockId || !fieldPath) {
        return;
      }
      var emitSelect = function () {
        selectBlock(blockId);
      };
      node.addEventListener("focus", emitSelect);
      node.addEventListener("pointerdown", emitSelect);
      node.addEventListener("mousedown", emitSelect);
      node.addEventListener("touchstart", emitSelect, { passive: true });

      if (kind === "asset") {
        node.addEventListener("click", function (event) {
          event.preventDefault();
          event.stopPropagation();
          selectBlock(blockId);
          send("request-asset", { blockId: blockId, fieldPath: fieldPath, fieldLabel: fieldLabel });
        });
        return;
      }

      node.setAttribute("contenteditable", "true");
      node.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          var current = event.currentTarget;
          if (current && current.blur) {
            current.blur();
          }
        }
      });
      node.addEventListener("blur", function (event) {
        var target = event.currentTarget;
        var value = target && target.innerText ? target.innerText : "";
        send("inline-edit", { blockId: blockId, fieldPath: fieldPath, value: value });
      });
    });
  }

  function enhanceSections() {
    document.querySelectorAll("[data-block-section]").forEach(function (section) {
      var blockId = Number(section.getAttribute("data-block-section"));
      var handlePointer = function (event) {
        if (!blockId) {
          return;
        }
        if (!hasFieldInPath(event)) {
          event.preventDefault();
        }
        selectBlock(blockId);
      };
      section.addEventListener("pointerdown", handlePointer);
      section.addEventListener("mousedown", handlePointer);
      section.addEventListener("touchstart", handlePointer, { passive: false });
    });
  }

  function highlightBlock(blockId) {
    if (activeSection) {
      activeSection.classList.remove("renderly-active-block");
    }
    if (!blockId) {
      activeSection = null;
      return;
    }
    var next = document.querySelector('[data-block-section="' + blockId + '"]');
    if (next) {
      next.classList.add("renderly-active-block");
      activeSection = next;
      if (next.scrollIntoView) {
        next.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    } else {
      activeSection = null;
    }
  }

  function applySaveStateToSection(section, state) {
    SAVE_STATE_CLASSES.forEach(function (cls) {
      section.classList.remove(cls);
    });
    var indicator = section.querySelector(".renderly-save-indicator");
    if (!state || state === "idle") {
      if (indicator) {
        indicator.classList.remove("is-visible");
        indicator.textContent = "";
        indicator.removeAttribute("data-state");
      }
      return;
    }
    if (!indicator) {
      indicator = document.createElement("div");
      indicator.className = "renderly-save-indicator";
      section.appendChild(indicator);
    }
    indicator.textContent = SAVE_STATE_LABELS[state] || "";
    indicator.setAttribute("data-state", state);
    indicator.classList.add("is-visible");
    section.classList.add("renderly-state-" + state);
  }

  function syncSaveStates(map) {
    saveStateCache = map || {};
    document.querySelectorAll("[data-block-section]").forEach(function (section) {
      var blockId = Number(section.getAttribute("data-block-section"));
      if (!blockId) {
        return;
      }
      var state = saveStateCache[blockId];
      applySaveStateToSection(section, state);
    });
  }

  function handleParentMessage(event) {
    var data = event.data;
    if (!data || data.source !== PARENT_SOURCE) {
      return;
    }
    if (data.type === "highlight-block") {
      var blockId = data.payload && data.payload.blockId ? Number(data.payload.blockId) : null;
      highlightBlock(blockId);
    } else if (data.type === "update-save-states") {
      var states = data.payload && data.payload.states ? data.payload.states : {};
      syncSaveStates(states);
    }
  }

  function initBridge() {
    enhanceLinksAndForms();
    enhanceFields();
    enhanceSections();
    window.addEventListener("message", handleParentMessage);
    syncSaveStates(saveStateCache);
    send("bridge-ready");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBridge, { once: true });
  } else {
    initBridge();
  }
})();
`;

const deviceStyle = computed(() => {
  const option = viewportOptions.find((item) => item.value === viewport.value) ?? viewportOptions[0];
  return {
    "--screen-width": `${option.width}px`,
    "--screen-height": `${option.height}px`,
    "--screen-ratio": option.ratio
  };
});

const lastSnapshot = computed(() => history.value[0] ?? null);

type Viewport = "desktop" | "tablet" | "mobile";
interface PreviewSnapshot {
  id: string;
  html: string;
  createdAt: number;
}

function writeHtml(html: string, frameIndex: number) {
  const doc = getFrameDocument(frameIndex);
  if (!doc) return;
  if (frameIndex === activeFrameIndex.value) {
    activeBridgeReady = false;
  }
  pendingFrameIndex = frameIndex;
  doc.open();
  doc.write(html);
  doc.close();
  const applyBridge = () => {
    ensureScrollbarHidden(doc);
    injectBridgeAssets(doc);
  };
  if (doc.readyState === "complete" || doc.readyState === "interactive") {
    applyBridge();
  } else {
    doc.addEventListener("DOMContentLoaded", applyBridge, { once: true });
  }
}

function ensureScrollbarHidden(doc: Document) {
  const host = doc.head ?? doc.documentElement;
  if (!host) return;
  let styleEl = doc.getElementById("renderly-scrollbar-mask");
  if (!styleEl) {
    styleEl = doc.createElement("style");
    styleEl.id = "renderly-scrollbar-mask";
    host.appendChild(styleEl);
  }
  styleEl.textContent = `
    html {
      scrollbar-width: none;
      -ms-overflow-style: none;
    }
    body {
      -ms-overflow-style: none;
    }
    html::-webkit-scrollbar,
    body::-webkit-scrollbar {
      width: 0;
      height: 0;
    }
  `;
}

function injectBridgeAssets(doc: Document) {
  const head = doc.head ?? doc.documentElement;
  const body = doc.body ?? doc.documentElement;
  if (head) {
    let styleEl = doc.getElementById("renderly-bridge-style");
    if (!styleEl) {
      styleEl = doc.createElement("style");
      styleEl.id = "renderly-bridge-style";
      head.appendChild(styleEl);
    }
    styleEl.textContent = BRIDGE_STYLE;
  }
  if (body) {
    const existingScript = doc.getElementById("renderly-bridge-script");
    if (existingScript && existingScript.parentNode) {
      existingScript.parentNode.removeChild(existingScript);
    }
    const scriptEl = doc.createElement("script");
    scriptEl.id = "renderly-bridge-script";
    scriptEl.type = "text/javascript";
    scriptEl.text = BRIDGE_RUNTIME;
    body.appendChild(scriptEl);
  }
}

function getLocalizedConfig(block: BlockInstance) {
  if (props.locale === props.defaultLocale) {
    return block.config ?? {};
  }
  return block.translations?.[props.locale] ?? block.config ?? {};
}

function styleToString(style?: Record<string, unknown>) {
  if (!style) return "";
  const parts: string[] = [];
  if (typeof style.background === "string" && style.background) {
    parts.push(`background:${style.background}`);
  }
  if (typeof style.padding === "string" && style.padding) {
    parts.push(`padding:${style.padding}`);
  }
  if (typeof style.border_color === "string" && style.border_color) {
    const width = typeof style.border_width === "string" ? style.border_width : "1px";
    parts.push(`border:${width} solid ${style.border_color}`);
  }
  if (typeof style.border_radius === "number") {
    parts.push(`border-radius:${style.border_radius}px`);
  }
  return parts.join(";");
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderFallbackHtml(message: string) {
  const heading = escapeHtml(props.title || "Live Preview");
  const info = escapeHtml(message);
  const html = `
    <!doctype html>
    <html lang="ru">
      <head>
        <meta charset="utf-8" />
        <style>
          :root { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color-scheme: light; }
          body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #eef2ff; color: #0f172a; padding: 24px; }
          .fallback { border-radius: 24px; border: 1px dashed rgba(99, 102, 241, 0.45); background: rgba(255,255,255,0.9); padding: 32px; text-align: center; max-width: 420px; box-shadow: 0 35px 65px rgba(15, 23, 42, 0.08); }
          .fallback h2 { margin: 0 0 12px; font-size: 1.3rem; }
          .fallback p { margin: 0; font-size: 0.95rem; color: #475569; }
        </style>
      </head>
      <body>
        <div class="fallback">
          <h2>${heading}</h2>
          <p>${info}</p>
        </div>
      </body>
    </html>
  `;
  captureScrollPosition();
  writeHtml(html, activeFrameIndex.value);
}

async function renderServerPreview(trackCompletion = false) {
  if (!props.projectId) {
    renderFallbackHtml("Нет ID проекта — сохраните проект, чтобы увидеть живое превью.");
    return;
  }
  isSyncing.value = true;
  try {
    const payload = {
      project: {
        title: props.title,
        theme: props.theme,
        settings: props.settings
      },
      blocks: props.blocks.map((block) => ({
        id: block.id,
        definition_key: block.definition_key,
        order_index: block.order_index,
        config: block.config,
        translations: block.translations ?? {}
      }))
    };
    const { data } = await api.post<{ html: string }>(
      `/projects/${props.projectId}/preview`,
      payload,
      {
        params: { lang: props.locale }
      }
    );
    captureScrollPosition();
    const targetFrame =
      frameRefs.every((frame) => frame) && activeBridgeReady ? idleFrameIndex() : activeFrameIndex.value;
    writeHtml(data.html, targetFrame);
    pushSnapshot(data.html);
    if (trackCompletion || !onboardingNotified.value) {
      onboarding.markPreviewed();
      onboardingNotified.value = true;
    }
  } catch (error) {
    console.error("Preview failed", error);
    if (!history.value.length) {
      renderFallbackHtml("Не удалось обновить превью. Попробуйте ещё раз.");
    }
  } finally {
    isSyncing.value = false;
  }
}

function pushSnapshot(html: string) {
  const entry: PreviewSnapshot = {
    id: crypto.randomUUID(),
    html,
    createdAt: Date.now()
  };
  history.value = [entry, ...history.value].slice(0, 5);
}

function parseFieldPath(fieldPath: string): (string | number)[] {
  return fieldPath.split(".").map((segment) => (/^\d+$/.test(segment) ? Number(segment) : segment));
}

function handleBridgeMessage(event: MessageEvent) {
  const data = event.data;
  if (!data || data.source !== BRIDGE_SOURCE) {
    return;
  }
  const frameIndex = frameIndexFromSource(event.source);
  if (frameIndex === null) {
    return;
  }
  const payload = data.payload ?? {};
  if (data.type === "bridge-ready") {
    if (pendingFrameIndex !== null && frameIndex === pendingFrameIndex) {
      activeFrameIndex.value = frameIndex;
      pendingFrameIndex = null;
      activeBridgeReady = true;
      restoreScrollPosition(frameIndex);
      postHighlight(pendingHighlight);
      postSaveStates(latestSaveStates);
    } else if (frameIndex === activeFrameIndex.value && !activeBridgeReady) {
      activeBridgeReady = true;
      restoreScrollPosition(frameIndex);
      postHighlight(pendingHighlight);
      postSaveStates(latestSaveStates);
    }
    return;
  }

  if (frameIndex !== activeFrameIndex.value) {
    return;
  }

  if (data.type === "inline-edit") {
    const blockId = Number(payload.blockId);
    if (!blockId || typeof payload.fieldPath !== "string") {
      return;
    }
    emit("inline-edit", {
      blockId,
      fieldKey: payload.fieldPath,
      value: typeof payload.value === "string" ? payload.value : String(payload.value ?? ""),
      path: parseFieldPath(payload.fieldPath)
    });
  } else if (data.type === "request-asset") {
    const blockId = Number(payload.blockId);
    if (!blockId || typeof payload.fieldPath !== "string") {
      return;
    }
    emit("request-asset", {
      blockId,
      fieldKey: payload.fieldPath,
      label: typeof payload.fieldLabel === "string" ? payload.fieldLabel : payload.fieldPath,
      path: parseFieldPath(payload.fieldPath)
    });
  } else if (data.type === "select-block") {
    const blockId = Number(payload.blockId);
    if (blockId) {
      emit("select", blockId);
    }
  }
}

function postHighlight(blockId: number | null) {
  pendingHighlight = blockId ?? null;
  if (!activeBridgeReady) {
    return;
  }
  const targetWindow = getFrameWindow();
  if (!targetWindow) {
    return;
  }
  targetWindow.postMessage(
    {
      source: PARENT_SOURCE,
      type: "highlight-block",
      payload: { blockId }
    },
    "*"
  );
}

function postSaveStates(states: Record<number, SaveState>) {
  latestSaveStates = states;
  if (!activeBridgeReady) {
    return;
  }
  const targetWindow = getFrameWindow();
  if (!targetWindow) {
    return;
  }
  targetWindow.postMessage(
    {
      source: PARENT_SOURCE,
      type: "update-save-states",
      payload: { states }
    },
    "*"
  );
}

function scheduleServerPreview() {
  if (debounceHandle) {
    clearTimeout(debounceHandle);
  }
  debounceHandle = window.setTimeout(() => {
    void renderServerPreview();
  }, 300);
}

function requestPreviewRefresh(force = false) {
  if (!force && hasPendingSave.value) {
    deferredPreview.value = true;
    return;
  }
  deferredPreview.value = false;
  scheduleServerPreview();
}

function openCurrentInTab() {
  if (!lastSnapshot.value) return;
  const blob = new Blob([lastSnapshot.value.html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}

function loadSnapshot(entry: PreviewSnapshot) {
  captureScrollPosition();
  const targetFrame =
    frameRefs.every((frame) => frame) && activeBridgeReady ? idleFrameIndex() : activeFrameIndex.value;
  writeHtml(entry.html, targetFrame);
}

function formatTimestamp(timestamp: number) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function normalizeSaveStates(states?: Record<number, SaveState>) {
  const result: Record<number, SaveState> = {};
  if (!states) {
    return result;
  }
  Object.entries(states).forEach(([key, value]) => {
    const id = Number(key);
    if (Number.isNaN(id)) {
      return;
    }
    result[id] = (value ?? "idle") as SaveState;
  });
  return result;
}

onMounted(() => {
  window.addEventListener("message", handleBridgeMessage);
  renderFallbackHtml("Загружаем превью проекта...");
  scheduleServerPreview();
});

onBeforeUnmount(() => {
  window.removeEventListener("message", handleBridgeMessage);
  if (debounceHandle) {
    window.clearTimeout(debounceHandle);
  }
});

watch(
  () => [props.projectId, props.blocks, props.theme, props.settings, props.title, props.locale],
  () => {
    requestPreviewRefresh();
  },
  { deep: true }
);

watch(
  hasPendingSave,
  (pending) => {
    if (!pending && deferredPreview.value) {
      requestPreviewRefresh(true);
    }
  }
);

watch(
  () => props.saveStates,
  (states) => {
    postSaveStates(normalizeSaveStates(states));
  },
  { deep: true, immediate: true }
);

watch(
  () => props.selectedBlockId ?? null,
  (blockId) => {
    postHighlight(blockId ?? null);
  },
  { immediate: true }
);
</script>

<style scoped>
.preview {
  background: var(--panel-surface);
  border-radius: 18px;
  padding: 16px;
  border: 1px solid var(--divider-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--panel-shadow);
}

.preview > header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.heading span {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.viewports {
  display: inline-flex;
  background: var(--panel-soft);
  border-radius: 999px;
  padding: 4px;
  border: 1px solid var(--divider-color);
}

.viewports button {
  border: none;
  background: transparent;
  color: var(--text-secondary);
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.85rem;
  cursor: pointer;
}

.viewports button.active {
  background: linear-gradient(125deg, var(--accent), var(--accent-strong));
  color: #fff;
}

.device-preview {
  position: relative;
  width: 100%;
  padding: 60px 28px 96px;
  border-radius: 42px;
  border: 1px solid var(--divider-color);
  background: radial-gradient(circle at 20% 20%, rgba(147, 197, 253, 0.35), transparent 55%),
    radial-gradient(circle at 80% 0%, rgba(199, 210, 254, 0.5), transparent 60%),
    linear-gradient(145deg, #f9fbff 0%, #eef4ff 55%, #fefefe 100%);
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 40px 70px rgba(15, 23, 42, 0.12), inset 0 0 0 1px rgba(255, 255, 255, 0.9);
  isolation: isolate;
}

.device-preview::before,
.device-preview::after {
  content: "";
  position: absolute;
  inset: 32% 14% 10%;
  background: radial-gradient(circle, rgba(148, 163, 184, 0.2), transparent 70%);
  filter: blur(32px);
  opacity: 0.75;
  pointer-events: none;
  z-index: -1;
}

.device-preview::after {
  inset: 10% 20% auto;
  height: 60%;
  background: radial-gradient(circle at 50% 20%, rgba(96, 165, 250, 0.25), transparent 65%);
  filter: blur(60px);
  opacity: 0.55;
}


.device-shell {
  position: relative;
  width: min(100%, var(--screen-width, 1280px));
  padding: 24px;
  border-radius: 52px;
  display: flex;
  justify-content: center;
  background: linear-gradient(140deg, #f9fbff 0%, #e6edff 55%, #dbe4ff 100%);
  border: 1px solid rgba(147, 197, 253, 0.45);
  box-shadow: 0 50px 80px rgba(148, 163, 184, 0.35), inset 0 0 0 1px rgba(255, 255, 255, 0.85);
}

.device-frame {
  position: relative;
  width: 100%;
  padding: 14px;
  border-radius: 42px;
  background: linear-gradient(145deg, #ffffff, #eff3ff 55%, #dfe6fb);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), inset 0 -12px 20px rgba(148, 163, 184, 0.2),
    0 18px 38px rgba(148, 163, 184, 0.24);
}

.device-frame::before {
  content: "";
  position: absolute;
  inset: 4px;
  border-radius: inherit;
  border: 1px solid rgba(148, 163, 184, 0.35);
  opacity: 0.8;
  pointer-events: none;
}

.device-screen {
  position: relative;
  width: 100%;
  border-radius: 34px;
  padding: 6px;
  background: linear-gradient(180deg, #111a2b, #1b263a 65%, #202c44);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.device-screen-inner {
  width: 100%;
  aspect-ratio: var(--screen-ratio, 1280 / 720);
  max-height: min(80vh, var(--screen-height, 720px));
  min-height: 320px;
  border-radius: 26px;
  overflow: hidden;
  background: var(--bg-surface);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
  position: relative;
}

.preview-frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: none;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
  background: transparent;
}

.preview-frame.active {
  opacity: 1;
  pointer-events: auto;
}

.device-screen-inner::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at 30% 0%, rgba(255, 255, 255, 0.45), transparent 55%),
    linear-gradient(180deg, rgba(148, 163, 184, 0.12), transparent 55%);
  pointer-events: none;
  mix-blend-mode: screen;
}

.device-desktop .device-shell {
  padding: 26px 26px 70px;
  border-radius: 60px;
}

.device-desktop .device-frame {
  border-radius: 48px;
  padding: 16px;
}

.device-desktop .device-frame::after {
  content: "";
  position: absolute;
  top: 8px;
  left: 50%;
  width: 120px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(15, 23, 42, 0.75), rgba(15, 23, 42, 0.15));
  transform: translateX(-50%);
  box-shadow: inset 0 0 6px rgba(255, 255, 255, 0.25), 0 0 8px rgba(15, 23, 42, 0.25);
}

.device-desktop .device-shell::before {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 110px;
  height: 42px;
  border-radius: 32px;
  background: linear-gradient(180deg, #dfe6ff, #adbbff);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7), 0 15px 24px rgba(148, 163, 184, 0.35);
  transform: translate(-50%, 60%);
  z-index: 1;
}

.device-desktop .device-shell::after {
  content: "";
  position: absolute;
  bottom: -36px;
  left: 50%;
  width: 260px;
  height: 26px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(148, 163, 184, 0.4), transparent 70%);
  transform: translateX(-50%);
  box-shadow: 0 20px 35px rgba(148, 163, 184, 0.35);
}

.device-tablet .device-shell {
  padding: 20px;
  border-radius: 52px;
}

.device-tablet .device-shell::before {
  content: "";
  position: absolute;
  left: -6px;
  top: 60px;
  width: 6px;
  height: 120px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.45), rgba(99, 102, 241, 0.3));
  box-shadow: 0 8px 14px rgba(148, 163, 184, 0.25);
}

.device-tablet .device-shell::after {
  content: "";
  position: absolute;
  right: -6px;
  top: 80px;
  width: 6px;
  height: 90px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.35), rgba(59, 130, 246, 0.25));
  box-shadow: 0 6px 12px rgba(59, 130, 246, 0.2);
}

.device-tablet .device-frame {
  border-radius: 46px;
  padding: 12px;
}

.device-tablet .device-frame::after {
  content: "";
  position: absolute;
  top: 8px;
  left: 50%;
  width: 72px;
  height: 10px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(147, 197, 253, 0.7), rgba(99, 102, 241, 0.45));
  transform: translateX(-50%);
  box-shadow: inset 0 0 8px rgba(255, 255, 255, 0.6);
}

.device-mobile .device-shell {
  padding: 26px 16px;
  border-radius: 64px;
}

.device-mobile .device-shell::before {
  content: "";
  position: absolute;
  right: -4px;
  top: 110px;
  width: 4px;
  height: 120px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.4), rgba(30, 64, 175, 0.35));
  box-shadow: 0 8px 16px rgba(30, 64, 175, 0.25);
}

.device-mobile .device-shell::after {
  content: "";
  position: absolute;
  left: -3px;
  top: 150px;
  width: 3px;
  height: 70px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.35), rgba(59, 130, 246, 0.2));
  box-shadow: 0 6px 10px rgba(15, 23, 42, 0.2);
}

.device-mobile .device-frame {
  padding: 10px;
  border-radius: 52px;
}

.device-mobile .device-screen {
  border-radius: 42px;
  padding-top: 14px;
}

.device-mobile .device-screen::before {
  content: "";
  position: absolute;
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 36%;
  height: 18px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.75);
  box-shadow: inset 0 -2px 4px rgba(255, 255, 255, 0.12);
}

.device-mobile .device-screen-inner {
  border-radius: 30px;
}

.device-mobile .device-screen-inner::after {
  content: "";
  position: absolute;
  bottom: 14px;
  left: 50%;
  width: 32%;
  height: 4px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
}

iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
  background: transparent;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

iframe::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.history {
  border-top: 1px solid var(--divider-color);
  padding-top: 8px;
}

.history header {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.history ul {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: flex;
  gap: 8px;
}

.history button {
  border: 1px solid var(--divider-color);
  background: transparent;
  border-radius: 10px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.ghost {
  border: 1px solid var(--divider-color);
  background: transparent;
  color: var(--text-primary);
  border-radius: 999px;
  padding: 6px 14px;
  cursor: pointer;
}

.ghost:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

:global(.theme-dark) .device-preview {
  background: radial-gradient(circle at 20% 20%, rgba(79, 70, 229, 0.25), transparent 55%),
    radial-gradient(circle at 80% 0%, rgba(14, 165, 233, 0.25), transparent 60%),
    linear-gradient(155deg, #0f172a 0%, #0b1424 55%, #060b13 100%);
  border-color: var(--divider-color);
  box-shadow: 0 45px 80px rgba(0, 0, 0, 0.65), inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

:global(.theme-dark) .device-shell {
  background: linear-gradient(145deg, #1c2740, #121a2f 55%, #0c1323);
  border-color: rgba(99, 102, 241, 0.45);
  box-shadow: 0 55px 90px rgba(0, 0, 0, 0.7), inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

:global(.theme-dark) .device-frame {
  background: linear-gradient(145deg, #0c1323, #111a2f 55%, #1b2340);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), inset 0 -12px 20px rgba(0, 0, 0, 0.45),
    0 18px 38px rgba(0, 0, 0, 0.55);
}

:global(.theme-dark) .device-screen-inner {
  background: #0b1220;
  box-shadow: 0 22px 45px rgba(0, 0, 0, 0.65);
}
</style>
