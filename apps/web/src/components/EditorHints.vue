<template>
  <div class="editor-hints">
    <strong>Блок добавлен!</strong>
    <p>Дальше:</p>
    <ul>
      <li>Кликните по нужному полю внутри блока, чтобы отредактировать текст без JSON.</li>
      <li>Настройте форму: откройте блок «Lead Form» и укажите поля + webhook.</li>
      <li>Обновите Live Preview и убедитесь, что страница выглядит как надо.</li>
    </ul>
    <button class="primary" type="button" @click="$emit('close')">Понятно</button>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  close: [];
}>();
</script>

<style scoped>
.editor-hints {
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  padding: 12px;
  background: #eef2ff;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

ul {
  margin: 0;
  padding-left: 18px;
  color: #475569;
}

.primary {
  align-self: flex-start;
  border: none;
  border-radius: 10px;
  background: #2563eb;
  color: #fff;
  padding: 6px 12px;
  cursor: pointer;
}
</style>
