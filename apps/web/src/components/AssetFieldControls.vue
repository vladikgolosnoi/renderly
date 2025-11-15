<template>
  <div class="asset-inline">
    <div class="actions">
      <button type="button" class="ghost" @click="$emit('choose')">Выбрать из библиотеки</button>
      <button type="button" class="ghost" :disabled="uploading" @click="$emit('upload')">
        {{ uploading ? "Загружаем..." : "Загрузить файл" }}
      </button>
      <button v-if="value" type="button" class="ghost" @click="previewValue">Просмотр</button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <div v-if="value" class="preview" :class="{ video: kind === 'video' }">
      <img v-if="kind === 'image'" :src="value" alt="" loading="lazy" />
      <video
        v-else-if="kind === 'video'"
        :src="value"
        controls
        playsinline
        preload="metadata"
      ></video>
      <a v-else :href="value" target="_blank" rel="noopener">Открыть файл</a>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  value?: string;
  kind: "image" | "video" | "file" | null;
  uploading: boolean;
  error?: string | null;
}>();

const emit = defineEmits<{
  choose: [];
  upload: [];
  preview: [string];
}>();

function previewValue() {
  if (props.value) {
    emit("preview", props.value);
  }
}
</script>

<style scoped>
.asset-inline {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ghost {
  border: 1px solid #cbd5f5;
  border-radius: 999px;
  padding: 6px 12px;
  background: transparent;
  color: #1d4ed8;
  cursor: pointer;
}

.ghost:disabled {
  opacity: 0.5;
  cursor: default;
}

.error {
  color: #b91c1c;
  font-size: 0.85rem;
  margin: 0;
}

.preview {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
}

.preview img,
.preview video {
  max-width: 100%;
  border-radius: 10px;
}
</style>
