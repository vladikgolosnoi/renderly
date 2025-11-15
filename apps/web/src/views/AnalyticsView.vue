<template>
  <section class="analytics">
    <Breadcrumbs :items="[{ label: copy.meta.dashboard, to: '/' }, { label: copy.meta.title }]" />

    <section class="hero-card">
      <div>
        <p class="eyebrow">{{ copy.hero.eyebrow }}</p>
        <h2>{{ copy.hero.title }}</h2>
        <p>{{ copy.hero.subtitle }}</p>
        <ul class="hero-metrics">
          <li>
            <span>{{ copy.hero.metrics.total }}</span>
            <strong>{{ totals.submissions }}</strong>
          </li>
          <li>
            <span>{{ copy.hero.metrics.conversion }}</span>
            <strong>{{ (totals.average_conversion * 100).toFixed(1) }}%</strong>
          </li>
          <li>
            <span>{{ copy.hero.metrics.projects }}</span>
            <strong>{{ totals.projects }}</strong>
          </li>
        </ul>
      </div>
      <div class="hero-actions">
        <label>
          {{ copy.hero.filterLabel }}
          <select v-model="selectedProject" @change="refresh">
            <option value="all">{{ copy.hero.filterAll }}</option>
            <option v-for="project in projectOptions" :key="project.id" :value="project.id">
              {{ project.title }}
            </option>
          </select>
        </label>
        <div class="hero-sync">
          <span>{{ copy.hero.updated }}</span>
          <strong>{{ generatedLabel }}</strong>
        </div>
      </div>
    </section>

    <div v-if="loading" class="loading">{{ copy.loading }}</div>

    <template v-else>
      <section v-if="statusRows.length" class="pulse">
        <div class="pulse-header">
          <h3>{{ copy.pulse.title }}</h3>
          <p>{{ copy.pulse.subtitle }}</p>
        </div>
        <ul class="pulse-list">
          <li v-for="status in statusRows" :key="status.key">
            <div class="pill" :style="{ background: status.color + '22', color: status.color }">{{ status.label }}</div>
            <div class="bar">
              <div class="fill" :style="{ width: statusPercent(status.count), background: status.color }"></div>
            </div>
            <span class="count">{{ status.count }}</span>
          </li>
        </ul>
      </section>

      <section v-if="insights" class="insights">
        <article>
          <p>{{ copy.insights.topProject }}</p>
          <h4>{{ insights.best.project_title }}</h4>
          <small>{{ copy.insights.conversion }} {{ (insights.best.conversion_rate * 100).toFixed(1) }}%</small>
        </article>
        <article>
          <p>{{ copy.insights.forms }}</p>
          <h4>{{ insights.best.form_blocks }}</h4>
          <small>{{ copy.insights.formsHint }}</small>
        </article>
        <article>
          <p>{{ copy.insights.lastSync }}</p>
          <h4>{{ generatedLabel }}</h4>
          <small>{{ copy.insights.lastSyncHint }}</small>
        </article>
      </section>

      <div v-if="summary.length" class="summary-grid">
        <article v-for="stat in summary" :key="stat.project_id">
          <div class="badge">{{ stat.project_title }}</div>
          <p class="metric">{{ stat.submissions }}</p>
          <small>
            {{ copy.summary.forms }}: {{ stat.form_blocks }} ·
            {{ copy.summary.conversion }} {{ (stat.conversion_rate * 100).toFixed(1) }}%
          </small>
        </article>
      </div>
      <p v-else class="empty">{{ copy.empty }}</p>

      <section v-if="timeseries.length" class="timeseries">
        <div class="card-header">
          <div>
            <h3>{{ copy.timeseries.title }}</h3>
            <p>{{ copy.timeseries.subtitle }}</p>
          </div>
        </div>
        <div class="chart">
          <div v-for="point in timeseries" :key="point.date" class="bar">
            <span class="value">{{ point.submissions }}</span>
            <div class="fill" :style="{ height: barHeight(point.submissions) }"></div>
            <span class="label">{{ formatDate(point.date) }}</span>
          </div>
        </div>
      </section>

      <section v-if="summary.length" class="table-wrapper">
        <div class="card-header">
          <div>
            <h3>{{ copy.table.title }}</h3>
            <p>{{ copy.table.subtitle }}</p>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>{{ copy.table.project }}</th>
              <th>{{ copy.table.submissions }}</th>
              <th>{{ copy.table.forms }}</th>
              <th>{{ copy.table.conversion }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stat in summary" :key="stat.project_id">
              <td>{{ stat.project_title }}</td>
              <td>{{ stat.submissions }}</td>
              <td>{{ stat.form_blocks }}</td>
              <td>{{ (stat.conversion_rate * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import api from "@/api/client";
import { useProjectStore } from "@/stores/project";
import type { LeadAnalyticsResponse, ProjectLeadStat, LeadTimeseriesPoint } from "@/types/analytics";

const statusLabels: Record<string, string> = {
  delivered: "Доставлено",
  sent: "Отправлено",
  queued: "В очереди",
  failed: "Ошибки"
};
const statusColors: Record<string, string> = {
  delivered: "#10b981",
  sent: "#60a5fa",
  queued: "#facc15",
  failed: "#f87171"
};

const copy = {
  meta: {
    dashboard: "Проекты",
    title: "Аналитика"
  },
  hero: {
    eyebrow: "Пульс заявок",
    title: "Статистика по лид-формам",
    subtitle: "Следите за тем, как заполняют формы и какие проекты конвертят лучше остальных.",
    updated: "Обновлено",
    filterLabel: "Фильтр по проекту",
    filterAll: "Все проекты",
    metrics: {
      total: "Всего заявок",
      conversion: "Средняя конверсия",
      projects: "Проектов с формами"
    }
  },
  loading: "Собираем статистику...",
  pulse: {
    title: "Статусы отправки",
    subtitle: "Понимайте, сколько заявок доставлено, зависло в очереди или упало с ошибкой"
  },
  insights: {
    topProject: "Самый эффективный проект",
    conversion: "Конверсия",
    forms: "Форм в проекте",
    formsHint: "Больше форм ≠ лучше. Смотрите на качество.",
    lastSync: "Последнее обновление",
    lastSyncHint: "Данные обновляются при каждом открытии страницы"
  },
  summary: {
    forms: "Форм",
    conversion: "Конверсия"
  },
  timeseries: {
    title: "Динамика заявок",
    subtitle: "Сколько отправок приходит каждый день"
  },
  table: {
    title: "Проекты и конверсия",
    subtitle: "Сравните нагрузку на формы",
    project: "Проект",
    submissions: "Заявок",
    forms: "Форм",
    conversion: "Конверсия"
  },
  empty: "Пока никто не отправлял формы. Разместите блок формы на странице и соберите первые заявки."
} as const;

const store = useProjectStore();
const loading = ref(false);
const summary = ref<ProjectLeadStat[]>([]);
const timeseries = ref<LeadTimeseriesPoint[]>([]);
const totals = ref({ submissions: 0, projects: 0, average_conversion: 0 });
const statusBreakdown = ref<Record<string, number>>({});
const selectedProject = ref<string | number>("all");
const generatedAt = ref<string | null>(null);

const projectOptions = computed(() => store.projects);

const insights = computed(() => {
  if (!summary.value.length) return null;
  const best = [...summary.value].sort((a, b) => b.conversion_rate - a.conversion_rate)[0];
  return { best };
});

const generatedLabel = computed(() => {
  if (!generatedAt.value) return "-";
  return new Date(generatedAt.value).toLocaleString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "short"
  });
});

const statusRows = computed(() => {
  return Object.entries(statusBreakdown.value)
    .map(([key, count]) => ({
      key,
      count,
      label: statusLabels[key] ?? key,
      color: statusColors[key] ?? "#94a3b8"
    }))
    .sort((a, b) => b.count - a.count);
});

const statusTotal = computed(() =>
  statusRows.value.reduce((acc, row) => acc + row.count, 0)
);

onMounted(async () => {
  if (!store.projects.length) {
    await store.fetchProjects();
  }
  await refresh();
});

async function refresh() {
  loading.value = true;
  try {
    const params = selectedProject.value === "all" ? {} : { project_id: selectedProject.value };
    const { data } = await api.get<LeadAnalyticsResponse>("/analytics/leads", { params });
    summary.value = data.summary;
    timeseries.value = data.timeseries;
    totals.value = data.totals;
    statusBreakdown.value = data.status_breakdown;
    generatedAt.value = data.generated_at;
  } finally {
    loading.value = false;
  }
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("ru-RU", { month: "short", day: "numeric" });
}

const maxSubmissions = computed(() =>
  Math.max(1, ...timeseries.value.map((point) => point.submissions))
);

function barHeight(value: number) {
  return `${(value / maxSubmissions.value) * 100}%`;
}

function statusPercent(count: number) {
  if (!statusTotal.value) return "0%";
  return `${((count / statusTotal.value) * 100).toFixed(0)}%`;
}
</script>

<style scoped>
.analytics {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 24px;
  border-radius: 28px;
  background: linear-gradient(135deg, #1d4ed8, #7c3aed);
  color: #fff;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  opacity: 0.8;
}

.hero-metrics {
  display: flex;
  gap: 18px;
  list-style: none;
  padding: 0;
  margin: 18px 0 0;
}

.hero-metrics li span {
  display: block;
  font-size: 0.85rem;
  opacity: 0.8;
}

.hero-metrics li strong {
  font-size: 1.8rem;
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
}

.hero-actions select {
  border-radius: 12px;
  border: none;
  padding: 8px 12px;
}

.hero-sync {
  text-align: right;
}

.hero-sync span {
  font-size: 0.8rem;
  opacity: 0.7;
}

.loading {
  border: 1px dashed var(--stroke);
  border-radius: 18px;
  padding: 24px;
  text-align: center;
}

.pulse {
  border-radius: 24px;
  border: 1px solid var(--stroke);
  padding: 20px;
  background: var(--bg-surface);
}

.pulse-list {
  list-style: none;
  padding: 0;
  margin: 16px 0 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pulse-list li {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pill {
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 0.85rem;
}

.pulse-list .bar {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.3);
  overflow: hidden;
}

.pulse-list .fill {
  height: 100%;
  border-radius: 999px;
}

.pulse-list .count {
  font-weight: 600;
}

.insights {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.insights article {
  border-radius: 20px;
  border: 1px solid var(--stroke);
  padding: 16px;
  background: var(--bg-surface);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.summary-grid article {
  border-radius: 18px;
  border: 1px solid var(--stroke);
  padding: 18px;
  background: var(--bg-surface);
}

.summary-grid .badge {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.15);
  color: #4338ca;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-grid .metric {
  margin: 12px 0 4px;
  font-size: 2rem;
  font-weight: 600;
}

.summary-grid small {
  color: var(--text-secondary);
}

.empty {
  text-align: center;
  padding: 24px;
  border-radius: 18px;
  border: 1px dashed var(--stroke);
  color: var(--text-secondary);
}

.timeseries {
  border-radius: 24px;
  border: 1px solid var(--stroke);
  padding: 24px;
  background: var(--bg-surface);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  min-height: 260px;
}

.chart .bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.chart .fill {
  width: 100%;
  border-radius: 12px 12px 0 0;
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.9), rgba(14, 165, 233, 0.4));
  transition: height 0.3s ease;
}

.table-wrapper {
  border-radius: 24px;
  border: 1px solid var(--stroke);
  padding: 24px;
  background: var(--bg-surface);
}

.card-header h3 {
  margin: 0 0 4px;
}

.card-header p {
  margin: 0;
  color: var(--text-secondary);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead th {
  text-align: left;
  font-size: 0.85rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--stroke);
}

tbody td {
  padding: 12px 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

@media (max-width: 900px) {
  .hero-card {
    flex-direction: column;
  }

  .hero-actions {
    align-items: flex-start;
  }
}
</style>
