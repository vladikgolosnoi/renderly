<template>
  <teleport to="body">
    <transition name="fade">
      <div v-if="open" class="asset-modal">
        <div class="backdrop" @click="$emit('close')"></div>
        <div class="dialog">
          <header>
            <div>
              <p class="eyebrow">{{ mode === "select" ? "Выбор медиа" : "Просмотр файла" }}</p>
              <h3>{{ selectingFor || "Медиатека" }}</h3>
            </div>
            <button type="button" class="ghost" @click="$emit('close')">Закрыть</button>
          </header>

          <div v-if="mode === 'preview' && previewUrl" class="preview-pane">
            <img v-if="isImage(previewUrl)" :src="previewUrl" alt="" />
            <video
              v-else-if="isVideo(previewUrl)"
              :src="previewUrl"
              controls
              playsinline
            ></video>
            <iframe
              v-else
              :src="previewUrl"
              title="asset-preview"
            ></iframe>
            <a :href="previewUrl" target="_blank" rel="noopener">Открыть в новой вкладке</a>
          </div>

          <AssetManager :selecting-for="selectingFor" @select="$emit('select', $event)" />
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import AssetManager from "@/components/AssetManager.vue";

const props = defineProps<{
  open: boolean;
  mode: "select" | "preview";
  selectingFor?: string | null;
  previewUrl?: string | null;
}>();

defineEmits<{
  close: [];
  select: [string];
}>();

function isImage(url: string) {
  return /\.(png|jpe?g|gif|webp|svg|avif)$/i.test(url.split("?")[0]);
}

function isVideo(url: string) {
  return /\.(mp4|webm|mov|m4v|ogg)$/i.test(url.split("?")[0]);
}
</script>

<style scoped>
.asset-modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
}

.dialog {
  position: relative;
  width: min(960px, 90vw);
  max-height: 90vh;
  background: #fff;
  border-radius: 24px;
  padding: 24px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 40px 120px rgba(15, 23, 42, 0.25);
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.75rem;
  color: #94a3b8;
}

.ghost {
  border: 1px solid #cbd5f5;
  border-radius: 999px;
  padding: 6px 12px;
  background: transparent;
  cursor: pointer;
}

.preview-pane {
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-pane img,
.preview-pane video,
.preview-pane iframe {
  width: 100%;
  max-height: 360px;
  border-radius: 12px;
  object-fit: contain;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
