<template>
  <div
    class="canvas"
    :style="canvasStyle"
    @dragover="onCanvasDragOver"
    @drop="onCanvasDrop"
    @dragleave="onCanvasDragLeave"
  >
    <div class="preview-surface">
      <template v-for="(block, index) in blocks" :key="block.id">
        <div v-if="hoverIndex === index" class="drop-indicator"></div>
        <section
          class="block"
          :class="blockClasses(block, index)"
          draggable="true"
          @dragstart="onDragStart(index)"
          @dragover.prevent="onBlockDragOver($event, index)"
          @drop="onBlockDrop($event, index)"
          @dragend="onDragEnd"
          @click="$emit('select', block.id)"
        >
          <BlockPreview
            :block="block"
            :definition="definitionFor(block)"
            :active-locale="activeLocale"
            :default-locale="defaultLocale"
            :quick-assets="props.quickAssets"
            @inline-edit="(payload) => emit('inline-edit', payload)"
            @request-asset="(payload) => emit('request-asset', payload)"
          />
          <div class="block-status" v-if="blockStatus(block.id) !== 'idle'">
            <span :class="['status-chip', `status-${blockStatus(block.id)}`]">
              {{ statusLabels[blockStatus(block.id)] }}
            </span>
          </div>
        </section>
      </template>
      <div v-if="hoverIndex === blocks.length" class="drop-indicator end"></div>
      <p v-if="!blocks.length" class="empty">Здесь пока нет блоков — перетащите их из палитры.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import BlockPreview from "@/components/BlockPreview.vue";
import type { AssetItem, BlockDefinition, BlockInstance } from "@/types/blocks";

type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";

const props = defineProps<{
  blocks: BlockInstance[];
  catalog: BlockDefinition[];
  activeLocale: string;
  defaultLocale: string;
  saveStates?: Record<number, SaveState>;
  quickAssets?: AssetItem[];
  theme?: Record<string, string>;
}>();

const emit = defineEmits<{
  select: [number];
  reorder: [{ from: number; to: number }];
  insert: [{ definitionKey: string; index: number }];
  "inline-edit": [{ blockId: number; fieldKey: string; value: string; path?: (string | number)[] }];
  "request-asset": [{ blockId: number; fieldKey: string; label: string; path: (string | number)[] }];
}>();

const draggingIndex = ref<number | null>(null);
const hoverIndex = ref<number | null>(null);
const paletteMime = "application/x-renderly-block";
const statusLabels: Record<SaveState, string> = {
  idle: "",
  dirty: "Есть изменения",
  saving: "Сохраняем...",
  saved: "Сохранено",
  error: "Ошибка"
};

const canvasStyle = computed(() => ({
  "--page-bg": props.theme?.page_bg ?? "#f8fafc",
  "--text-color": props.theme?.text_color ?? "#0f172a",
  "--accent-color": props.theme?.accent ?? "#6366f1",
  "--card-bg": props.theme?.card_bg ?? "#ffffff"
}));

function definitionFor(block: BlockInstance) {
  return props.catalog.find((item) => item.key === block.definition_key);
}

function blockStatus(blockId: number): SaveState {
  return (props.saveStates?.[blockId] ?? "idle") as SaveState;
}

function blockClasses(block: BlockInstance, index: number) {
  const state = blockStatus(block.id);
  return {
    dragging: draggingIndex.value === index,
    [`state-${state}`]: state !== "idle"
  };
}

function onDragStart(index: number) {
  draggingIndex.value = index;
}

function onDragEnd() {
  draggingIndex.value = null;
  hoverIndex.value = null;
}

function onBlockDragOver(event: DragEvent, index: number) {
  if (isPaletteDrag(event)) {
    event.preventDefault();
    hoverIndex.value = index;
  }
}

function onBlockDrop(event: DragEvent, index: number) {
  if (isPaletteDrag(event)) {
    event.preventDefault();
    hoverIndex.value = index;
    const payload = parsePalettePayload(event);
    if (payload?.definitionKey) {
      emit("insert", { definitionKey: payload.definitionKey, index });
    }
    hoverIndex.value = null;
    return;
  }
  const from = draggingIndex.value;
  if (from === null) return;
  const to = index;
  if (from === to) return;
  emit("reorder", { from, to });
  hoverIndex.value = null;
}

function onCanvasDragOver(event: DragEvent) {
  if (isPaletteDrag(event)) {
    event.preventDefault();
    if (!props.blocks.length) {
      hoverIndex.value = 0;
    }
  }
}

function onCanvasDrop(event: DragEvent) {
  if (isPaletteDrag(event)) {
    event.preventDefault();
    const payload = parsePalettePayload(event);
    if (payload?.definitionKey) {
      emit("insert", { definitionKey: payload.definitionKey, index: props.blocks.length });
    }
  }
  hoverIndex.value = null;
}

function onCanvasDragLeave(event: DragEvent) {
  if (!event.relatedTarget) {
    hoverIndex.value = null;
  }
}

function isPaletteDrag(event: DragEvent) {
  return event.dataTransfer?.types.includes(paletteMime);
}

function parsePalettePayload(event: DragEvent) {
  const raw = event.dataTransfer?.getData(paletteMime);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
</script>

<style scoped>
.canvas {
  width: 100%;
  min-height: 600px;
  padding: 32px;
  box-sizing: border-box;
  background: var(--page-bg);
  color: var(--text-color);
  border-radius: 32px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2), 0 25px 80px rgba(15, 23, 42, 0.12);
}

.preview-surface {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.block {
  position: relative;
}

.block.dragging {
  opacity: 0.6;
}

.block-status {
  position: absolute;
  top: 12px;
  right: 12px;
}

.status-chip {
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.75);
  color: #fff;
}

.status-chip.status-dirty {
  background: rgba(249, 115, 22, 0.9);
}

.status-chip.status-saving {
  background: rgba(251, 191, 36, 0.95);
  color: #0f172a;
}

.status-chip.status-saved {
  background: rgba(16, 185, 129, 0.9);
}

.status-chip.status-error {
  background: rgba(239, 68, 68, 0.95);
}

.drop-indicator {
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.6), rgba(79, 70, 229, 0.4));
  border: 1px solid rgba(99, 102, 241, 0.35);
}

.drop-indicator.end {
  margin-top: 8px;
}

.empty {
  text-align: center;
  color: #94a3b8;
  margin: 32px 0;
}
</style>
