<template>
  <div class="panel" v-if="definition && props.block">
    <header class="panel-head">
      <div>
        <p class="eyebrow">Контент · инспектор</p>
        <h3>{{ displayBlockName }} · {{ localeLabel }}</h3>
      </div>
      <span class="locale-chip">{{ localeLabel }}</span>
    </header>

    <section v-if="variations.length" class="variation-panel">
      <p class="variation-title">Готовые варианты</p>
      <div class="variation-list">
        <button
          v-for="variation in variations"
          :key="variation.slug"
          type="button"
          class="variation-chip"
          @click="applyVariation(variation)"
        >
          <strong>{{ variation.name }}</strong>
          <small>{{ variation.description }}</small>
        </button>
      </div>
    </section>

    <form @submit.prevent="submit">
      <section
        v-for="field in definition.schema"
        :key="field.key"
        class="field-block"
      >
        <header>
          <div>
            <span>{{ getFieldLabel(field) }}</span>
            <small v-if="field.description">{{ field.description }}</small>
          </div>
          <span class="badge" v-if="field.required">обязательно</span>
        </header>

        <template v-if="field.type !== 'list'">
          <div class="control-row">
            <textarea
              v-if="field.type === 'richtext' || field.type === 'textarea'"
              v-model="local[field.key]"
              rows="3"
              placeholder="Введите текст"
            ></textarea>
            <input
              v-else
              v-model="local[field.key]"
              type="text"
              placeholder="Введите значение"
            />
          </div>
          <AssetFieldControls
            v-if="isAssetField(field)"
            :value="local[field.key]"
            :kind="mediaKind(local[field.key])"
            :uploading="isUploadingPath([field.key])"
            :error="fieldUploadError([field.key])"
            @choose="requestAsset(field)"
            @upload="triggerInlineUpload([field.key])"
            @preview="(url) => emit('preview-asset', url)"
          />
        </template>

        <template v-else>
          <div class="list-panel">
            <p class="helper">{{ listHelper(field) }}</p>
            <div v-if="listValue(field.key).length" class="list-items">
              <article
                v-for="(item, index) in listValue(field.key)"
                :key="`${field.key}-${index}`"
              >
                <header>
                  <strong>#{{ index + 1 }}</strong>
                  <button type="button" class="ghost tiny" @click="removeListItem(field, index)">
                    Удалить
                  </button>
                </header>

                <template v-if="isPrimitiveList(field)">
                  <input
                    type="text"
                    v-model="listValue(field.key)[index]"
                    placeholder="Введите значение"
                  />
                </template>

                <template v-else>
                  <label
                    v-for="subField in field.item_schema ?? []"
                    :key="`${field.key}-${subField.key}-${index}`"
                  >
                    <span>{{ getFieldLabel(subField) }}</span>
                    <div class="control-row">
                      <textarea
                        v-if="subField.type === 'richtext' || subField.type === 'textarea'"
                        v-model="listValue(field.key)[index][subField.key]"
                        rows="2"
                        placeholder="Введите текст"
                      ></textarea>
                      <input
                        v-else
                        v-model="listValue(field.key)[index][subField.key]"
                        type="text"
                        placeholder="Введите значение"
                      />
                    </div>
                    <AssetFieldControls
                      v-if="subField.widget === 'asset'"
                      :value="listValue(field.key)[index][subField.key]"
                      :kind="mediaKind(listValue(field.key)[index][subField.key])"
                      :uploading="isUploadingPath([field.key, index, subField.key])"
                      :error="fieldUploadError([field.key, index, subField.key])"
                      @choose="requestListAsset(field, index, subField)"
                      @upload="triggerInlineUpload([field.key, index, subField.key])"
                      @preview="(url) => emit('preview-asset', url)"
                    />
                  </label>
                </template>
              </article>
            </div>
            <p v-else class="list-empty">Элементов пока нет.</p>
            <button type="button" class="ghost tiny add-item" @click="addListItem(field)">
              Добавить элемент
            </button>
          </div>
        </template>
      </section>

      <section v-if="showStyleControls" class="style-panel">
        <h4>Оформление блока</h4>
        <label>
          <span>Фон секции</span>
          <input type="color" v-model="styleSettings.background" />
        </label>
        <label>
          <span>Отступы (например, 64px 24px)</span>
          <input type="text" v-model="styleSettings.padding" placeholder="64px 24px" />
        </label>
        <label>
          <span>Цвет рамки</span>
          <input type="color" v-model="styleSettings.border_color" />
        </label>
        <label>
          <span>Скругление рамки (px)</span>
          <input type="number" min="0" v-model.number="styleSettings.border_radius" />
        </label>
      </section>

      <button type="submit" class="primary">Сохранить блок</button>
    </form>
  </div>
  <div class="panel empty" v-else>
    <p>Выберите блок на канвасе, чтобы изменить его настройки.</p>
  </div>
  <input
    ref="inlineUploader"
    type="file"
    accept="image/*,video/*,application/pdf"
    class="sr-only"
    @change="handleInlineUpload"
  />
</template>

<script setup lang="ts">
import { computed, reactive, watch, ref, nextTick, onBeforeUnmount } from "vue";
import type { BlockDefinition, BlockInstance, BlockVariation } from "@/types/blocks";
import { localizedBlockName, localizedFieldLabel } from "@/data/localeMap";
import AssetFieldControls from "@/components/AssetFieldControls.vue";
import { useProjectStore } from "@/stores/project";
import { isAxiosError } from "axios";

const props = defineProps<{
  block: BlockInstance | null;
  catalog: BlockDefinition[];
  locale: string;
  defaultLocale: string;
}>();

const emit = defineEmits<{
  save: [Record<string, unknown>];
  "request-asset": [{ blockId: number; fieldKey: string; label: string; path: (string | number)[] }];
  "preview-asset": [string];
}>();

const store = useProjectStore();
if (!store.assets.length) {
  void store.fetchAssets();
}

const local = reactive<Record<string, any>>({});
const styleDefaults = {
  background: "#ffffff",
  padding: "64px 24px",
  border_color: "#e2e8f0",
  border_radius: 0
};
const styleSettings = reactive<Record<string, any>>({ ...styleDefaults });
const inlineUploader = ref<HTMLInputElement | null>(null);
const uploadTargetPath = ref<(string | number)[] | null>(null);
const inlineUploadingKey = ref<string | null>(null);
const inlineUploadError = ref<{ key: string; message: string } | null>(null);
const AUTOSAVE_DEBOUNCE = 400;
let autosaveHandle: number | null = null;
let suppressAutosave = false;

const definition = computed(() =>
  props.catalog.find((item) => item.key === props.block?.definition_key)
);
const displayBlockName = computed(() =>
  localizedBlockName(props.block?.definition_key ?? "", definition.value?.name ?? "")
);
const variations = computed(() => definition.value?.ui_meta?.variations ?? []);
const localeLabel = computed(() => props.locale.toUpperCase());
const showStyleControls = computed(() => props.locale === props.defaultLocale);

watch(
  () => [props.block?.id, props.locale],
  () => {
    cancelAutosave();
    resetLocalState();
  },
  { immediate: true }
);

watch(
  () => local,
  () => scheduleAutosave(),
  { deep: true }
);

watch(
  () => styleSettings,
  () => {
    if (showStyleControls.value) {
      scheduleAutosave();
    }
  },
  { deep: true }
);

function scheduleAutosave() {
  if (suppressAutosave || !props.block) {
    return;
  }
  if (autosaveHandle) {
    window.clearTimeout(autosaveHandle);
  }
  autosaveHandle = window.setTimeout(() => {
    autosaveHandle = null;
    submit();
  }, AUTOSAVE_DEBOUNCE);
}

function cancelAutosave() {
  if (autosaveHandle) {
    window.clearTimeout(autosaveHandle);
    autosaveHandle = null;
  }
}

onBeforeUnmount(() => cancelAutosave());

function resetLocalState() {
  suppressAutosave = true;
  Object.keys(local).forEach((key) => delete local[key]);
  if (!props.block || !definition.value) {
    nextTick(() => {
      suppressAutosave = false;
    });
    return;
  }
  const sourceConfig = getLocalizedConfig();
  Object.assign(local, clone(sourceConfig));
  if (showStyleControls.value) {
    const style = (props.block.config as any)?.style ?? {};
    Object.assign(styleSettings, styleDefaults, style);
    delete local.style;
  }
  nextTick(() => {
    suppressAutosave = false;
  });
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value ?? {}));
}

function getLocalizedConfig(): Record<string, unknown> {
  if (!props.block) return {};
  if (props.locale === props.defaultLocale) {
    return clone(props.block.config ?? {});
  }
  return clone(props.block.translations?.[props.locale] ?? props.block.config ?? {});
}

function isAssetField(field: BlockDefinition["schema"][number]) {
  return field.widget === "asset" && field.type !== "list";
}

function getFieldLabel(field: BlockDefinition["schema"][number]) {
  return localizedFieldLabel(field.key, field.label);
}

function listValue(fieldKey: string): any[] {
  const value = local[fieldKey];
  if (Array.isArray(value)) {
    return value;
  }
  const next: any[] = [];
  local[fieldKey] = next;
  return next;
}

function isPrimitiveList(field: BlockDefinition["schema"][number]) {
  return !(field.item_schema && field.item_schema.length);
}

function listHelper(field: BlockDefinition["schema"][number]) {
  if (isPrimitiveList(field)) {
    return "Каждый элемент — отдельная строка списка.";
  }
  return "Заполните поля для каждого элемента. Можно добавить столько карточек, сколько потребуется.";
}

function addListItem(field: BlockDefinition["schema"][number]) {
  const list = listValue(field.key);
  if (isPrimitiveList(field)) {
    list.push("");
    return;
  }
  const item: Record<string, unknown> = {};
  (field.item_schema ?? []).forEach((schema) => {
    item[schema.key] = schema.default ?? "";
  });
  list.push(item);
}

function removeListItem(field: BlockDefinition["schema"][number], index: number) {
  listValue(field.key).splice(index, 1);
}

function requestAsset(field: BlockDefinition["schema"][number]) {
  if (!props.block) return;
  emit("request-asset", {
    blockId: props.block.id,
    fieldKey: field.key,
    label: field.label,
    path: [field.key]
  });
}

function requestListAsset(
  field: BlockDefinition["schema"][number],
  index: number,
  subField: NonNullable<BlockDefinition["schema"][number]["item_schema"]>[number]
) {
  if (!props.block) return;
  emit("request-asset", {
    blockId: props.block.id,
    fieldKey: `${field.key}.${subField.key}`,
    label: subField.label,
    path: [field.key, index, subField.key]
  });
}

function applyVariation(variation: BlockVariation) {
  Object.keys(local).forEach((key) => delete local[key]);
  Object.assign(local, clone(variation.config ?? {}));
  if (showStyleControls.value && variation.config?.style) {
    Object.assign(styleSettings, styleDefaults, variation.config.style);
    delete local.style;
  }
  submit();
}

function submit() {
  const payload = clone(local);
  if (showStyleControls.value) {
    payload.style = { ...styleSettings };
  }
  emit("save", payload);
}

function triggerInlineUpload(path: (string | number)[]) {
  uploadTargetPath.value = path;
  inlineUploadError.value =
    inlineUploadError.value?.key === pathKey(path) ? null : inlineUploadError.value;
  nextTick(() => inlineUploader.value?.click());
}

async function handleInlineUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  const path = uploadTargetPath.value;
  if (!file || !path) return;
  const token = pathKey(path);
  inlineUploadingKey.value = token;
  try {
    const asset = await store.uploadAsset(file);
    setValueAtPath(local, path, asset.url);
    inlineUploadError.value = null;
  } catch (error) {
    let message = "Не удалось загрузить файл. Попробуйте позже.";
    if (isAxiosError(error)) {
      const detail = (error.response?.data as { detail?: string })?.detail;
      if (detail) message = detail;
    }
    inlineUploadError.value = { key: token, message };
  } finally {
    inlineUploadingKey.value = null;
    uploadTargetPath.value = null;
    target.value = "";
  }
}

function setValueAtPath(target: Record<string, any>, path: (string | number)[], value: unknown) {
  if (!path.length) return;
  let cursor: any = target;
  for (let i = 0; i < path.length - 1; i += 1) {
    const key = path[i];
    if (cursor[key] === undefined) {
      cursor[key] = typeof path[i + 1] === "number" ? [] : {};
    }
    cursor = cursor[key];
  }
  cursor[path[path.length - 1]] = value;
}

function mediaKind(value?: string) {
  if (!value) return null;
  const asset = store.assets.find((item) => item.url === value);
  if (asset?.mime_type.startsWith("image/")) return "image";
  if (asset?.mime_type.startsWith("video/")) return "video";
  const clean = value.split("?")[0].split("#")[0];
  const ext = clean.split(".").pop()?.toLowerCase();
  if (!ext) return "file";
  if (["jpg", "jpeg", "png", "gif", "webp", "svg", "avif"].includes(ext)) return "image";
  if (["mp4", "webm", "mov", "m4v", "ogg"].includes(ext)) return "video";
  return "file";
}

function pathKey(path: (string | number)[]) {
  return path.map((segment) => String(segment)).join(".");
}

function isUploadingPath(path: (string | number)[]) {
  return inlineUploadingKey.value === pathKey(path);
}

function fieldUploadError(path: (string | number)[]) {
  return inlineUploadError.value?.key === pathKey(path) ? inlineUploadError.value.message : null;
}
</script>

<style scoped>
.panel {
  background: var(--panel-surface);
  border-radius: 24px;
  padding: 18px;
  border: 1px solid var(--divider-color);
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: var(--panel-shadow);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.panel-head h3 {
  margin: 4px 0 0;
  font-size: 1.1rem;
}

.locale-chip {
  border-radius: 999px;
  background: var(--accent-muted);
  color: var(--accent);
  padding: 4px 10px;
  font-size: 0.75rem;
}

.variation-panel {
  border: 1px dashed var(--divider-color);
  border-radius: 16px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--panel-soft);
}

.variation-title {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.variation-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.variation-chip {
  border: 1px solid var(--divider-color);
  border-radius: 12px;
  padding: 6px 10px;
  background: var(--panel-surface);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  min-width: 180px;
}

.variation-chip strong {
  font-size: 0.85rem;
}

.variation-chip small {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid var(--divider-color);
  border-radius: 18px;
  padding: 14px;
  background: var(--panel-soft);
}

.field-block header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.field-block header span {
  font-weight: 600;
  text-transform: none;
}

.field-block header small {
  display: block;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.badge {
  font-size: 0.7rem;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.16);
  border-radius: 999px;
  padding: 2px 8px;
}

.control-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.control-row.with-action textarea,
.control-row.with-action input {
  flex: 1;
}

input,
textarea {
  border-radius: 12px;
  border: 1px solid var(--input-border);
  padding: 8px 12px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;
  background: var(--input-bg);
  color: var(--input-text);
}

.list-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.helper {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.list-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-items article {
  border: 1px solid var(--divider-color);
  border-radius: 16px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--panel-surface);
}

.list-items article header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-empty {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.add-item {
  align-self: flex-start;
}

.ghost {
  border-radius: 12px;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  padding: 6px 12px;
  cursor: pointer;
  flex-shrink: 0;
}

.ghost.tiny {
  font-size: 0.8rem;
  padding: 4px 10px;
}

.style-panel {
  border: 1px solid var(--divider-color);
  border-radius: 18px;
  padding: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  background: var(--panel-soft);
}

.style-panel h4 {
  grid-column: 1 / -1;
  margin: 0 0 4px;
}

.primary {
  margin-top: 8px;
  padding: 10px 16px;
  border-radius: 16px;
  border: none;
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.2);
}

.empty {
  text-align: center;
  color: var(--text-secondary);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>
