<template>
  <section class="panel" id="asset-manager">
    <header>
      <div>
        <h3>Медиатека</h3>
        <p>Загрузите изображения, видео или PDF и используйте их в блоках.</p>
      </div>
      <span class="limit">до {{ maxMb }} МБ</span>
    </header>

    <p v-if="selectingFor" class="hint">
      Подбираем файл для «{{ selectingFor }}». Нажмите «Выбрать», чтобы вставить его в блок.
    </p>

    <div class="uploader">
      <input
        ref="fileInput"
        type="file"
        accept="image/*,video/*,application/pdf"
        @change="onSelect"
      />
      <button type="button" :disabled="uploading" @click="triggerUpload">
        {{ uploading ? "Загружаем..." : "Загрузить файл" }}
      </button>
    </div>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <ul class="asset-list" v-if="assets.length">
      <li v-for="asset in assets" :key="asset.id">
        <div class="preview">
          <img
            v-if="isImage(asset)"
            :src="asset.thumbnail_url || asset.url"
            :alt="asset.filename"
            loading="lazy"
          />
          <video v-else-if="isVideo(asset)" :src="asset.url" muted playsinline loop></video>
          <div v-else class="placeholder">PDF</div>
        </div>
        <div class="meta">
          <strong>{{ asset.filename }}</strong>
          <small>{{ formatSize(asset.size_bytes) }} · {{ formatDate(asset.created_at) }}</small>
        </div>
        <div class="actions">
          <button class="ghost" type="button" @click="emitSelect(asset.url)">Выбрать</button>
          <button class="ghost" type="button" @click="copy(asset.url)">Скопировать URL</button>
        </div>
      </li>
    </ul>
    <p v-else class="empty">
      Загрузите первое изображение или PDF, чтобы начать работать с медиатекой.
    </p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useProjectStore } from "@/stores/project";
import type { AssetItem } from "@/types/blocks";
import { isAxiosError } from "axios";

const props = defineProps<{
  selectingFor?: string | null;
}>();

const emit = defineEmits<{ select: [string] }>();

const store = useProjectStore();
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const errorMessage = ref<string | null>(null);
const maxMb = import.meta.env.VITE_ASSET_MAX_MB ?? 10;

const assets = computed(() => store.assets);

onMounted(() => {
  if (store.current?.id && !store.assets.length) {
    void store.fetchAssets(store.current.id);
  }
});

function triggerUpload() {
  fileInput.value?.click();
}

async function onSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  uploading.value = true;
  try {
    await store.uploadAsset(file);
    errorMessage.value = null;
  } catch (error) {
    if (isAxiosError(error)) {
      const detail = (error.response?.data as { detail?: string })?.detail;
      errorMessage.value = detail ?? "Не удалось загрузить файл. Попробуйте позже.";
    } else {
      errorMessage.value = "Не удалось загрузить файл. Попробуйте позже.";
    }
  } finally {
    uploading.value = false;
    target.value = "";
  }
}

function formatSize(bytes: number) {
  const mb = bytes / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(1)} МБ`;
  const kb = bytes / 1024;
  return `${kb.toFixed(1)} КБ`;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function isImage(asset: AssetItem) {
  return asset.mime_type.startsWith("image/");
}

function isVideo(asset: AssetItem) {
  return asset.mime_type.startsWith("video/");
}

async function copy(url: string) {
  await navigator.clipboard?.writeText(url);
  alert("Ссылка скопирована в буфер обмена.");
}

function emitSelect(url: string) {
  emit("select", url);
}
</script>

<style scoped>
.panel {
  background: #fff;
  border-radius: 18px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.limit {
  font-size: 0.85rem;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 999px;
  color: #475569;
}

.uploader {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hint {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 0.85rem;
  color: #0369a1;
}

input[type="file"] {
  width: 100%;
  border: 1px dashed #cbd5f5;
  padding: 10px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.04);
  font-size: 0.9rem;
  box-sizing: border-box;
}

.uploader button {
  border-radius: 12px;
  border: none;
  padding: 10px 16px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.asset-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.asset-list li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 8px;
}

.preview {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  overflow: hidden;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview img,
.preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  font-size: 0.75rem;
  color: #475569;
}

.meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ghost {
  background: transparent;
  color: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 999px;
  padding: 6px 12px;
  cursor: pointer;
}

.empty {
  color: #475569;
}

.error {
  color: #b91c1c;
  font-weight: 600;
}
</style>
