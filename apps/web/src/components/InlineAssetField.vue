<template>
  <div class="asset-inline">
    <div class="meta">
      <span class="label">{{ label }}</span>
      <div v-if="value" class="preview" @click="handlePreview">
        <img v-if="isImage" :src="value" :alt="label" loading="lazy" />
        <video v-else-if="isVideo" :src="value" muted loop playsinline></video>
        <span v-else class="placeholder">Файл</span>
      </div>
      <p v-else class="placeholder">Добавьте изображение или видео.</p>
      <div v-if="quickAssets?.length" class="quick-assets">
        <button
          v-for="asset in quickAssets"
          :key="asset.url"
          type="button"
          class="thumb"
          @click="$emit('select', asset.url)"
        >
          <img :src="asset.thumbnail_url || asset.url" :alt="asset.filename ?? 'asset'" loading="lazy" />
        </button>
      </div>
    </div>
    <button type="button" class="ghost" @click="$emit('request')">
      {{ value ? "Заменить" : "Выбрать" }} из медиатеки
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";

interface QuickAsset {
  url: string;
  thumbnail_url?: string | null;
  filename?: string;
}

const props = defineProps<{
  label: string;
  value?: string | null;
  quickAssets?: QuickAsset[];
}>();

const emit = defineEmits<{
  request: [];
  select: [string];
  preview: [string];
}>();

const openPreview = inject<((url: string) => void) | undefined>("openAssetPreview", undefined);

const isImage = computed(() =>
  Boolean(props.value && props.value.match(/\.(png|jpe?g|webp|gif|svg|avif)(\?|$)/i))
);
const isVideo = computed(() =>
  Boolean(props.value && props.value.match(/\.(mp4|webm|mov|m4v|ogg)(\?|$)/i))
);

function handlePreview() {
  if (!props.value) return;
  openPreview?.(props.value);
  emit("preview", props.value);
}
</script>

<style scoped>
.asset-inline {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
}

.meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.preview {
  max-width: 200px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  cursor: pointer;
}

.preview img,
.preview video {
  width: 100%;
  display: block;
  object-fit: cover;
}

.placeholder {
  margin: 0;
  font-size: 0.85rem;
  color: #94a3b8;
}

.quick-assets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.quick-assets .thumb {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 2px;
  background: #fff;
  cursor: pointer;
  width: 48px;
  height: 48px;
}

.quick-assets img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.ghost {
  border: 1px dashed #2563eb;
  background: transparent;
  color: #2563eb;
  border-radius: 12px;
  padding: 8px 12px;
  cursor: pointer;
  flex-shrink: 0;
}
</style>
