<template>
  <label class="editable-field">
    <span class="label">{{ label }}</span>
    <div
      class="editable"
      :class="{ multiline, empty: !draft }"
      contenteditable="true"
      :data-placeholder="placeholder || 'Введите текст'"
      ref="editableRef"
      @input="onInput"
      @focus="onFocus"
      @blur="onBlur"
      @keydown="onKeyDown"
    ></div>
  </label>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

const props = defineProps<{
  label: string;
  value?: string | null;
  placeholder?: string;
  multiline?: boolean;
}>();

const emit = defineEmits<{
  change: [string];
}>();

const editableRef = ref<HTMLDivElement | null>(null);
const draft = ref(props.value ?? "");

watch(
  () => props.value,
  (next) => {
    draft.value = next ?? "";
    syncDom();
  }
);

onMounted(() => syncDom());

function syncDom() {
  if (editableRef.value && editableRef.value.innerText !== draft.value) {
    editableRef.value.innerText = draft.value;
  }
}

function onInput(event: Event) {
  const target = event.target as HTMLDivElement;
  draft.value = target.innerText;
}

function onFocus() {
  editableRef.value?.classList.add("focused");
}

function onBlur() {
  editableRef.value?.classList.remove("focused");
  emit("change", draft.value.trim());
}

function onKeyDown(event: KeyboardEvent) {
  if (!props.multiline && event.key === "Enter") {
    event.preventDefault();
    editableRef.value?.blur();
  }
}
</script>

<style scoped>
.editable-field {
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

.editable {
  min-height: 32px;
  border-radius: 12px;
  border: 1px solid transparent;
  padding: 8px 10px;
  font-size: 1rem;
  background: rgba(148, 163, 184, 0.1);
  transition: border-color 0.15s ease, background 0.15s ease;
  outline: none;
}

.editable.empty::before {
  content: attr(data-placeholder);
  color: #cbd5f5;
}

.editable.focused {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
}

.editable.multiline {
  min-height: 64px;
}
</style>
