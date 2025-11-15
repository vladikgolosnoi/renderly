<template>
  <nav class="breadcrumbs" aria-label="Хлебные крошки">
    <ol>
      <li v-for="(item, index) in items" :key="item.label">
        <RouterLink v-if="item.to && index < items.length - 1" :to="item.to">
          {{ item.label }}
        </RouterLink>
        <span v-else :class="{ current: index === items.length - 1 }">{{ item.label }}</span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
type Crumb = {
  label: string;
  to?: string;
};

defineProps<{
  items: Crumb[];
}>();
</script>

<style scoped>
.breadcrumbs {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 16px;
}

ol {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

li {
  display: flex;
  align-items: center;
  gap: 8px;
}

li::after {
  content: "›";
  font-size: 0.8rem;
  color: #cbd5f5;
}

li:last-child::after {
  display: none;
}

a {
  text-decoration: none;
  color: #2563eb;
  font-weight: 500;
}

.current {
  color: #0f172a;
  font-weight: 600;
}
</style>
