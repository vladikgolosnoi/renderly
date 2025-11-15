<template>
  <section class="dashboard">
    <Breadcrumbs :items="[{ label: copy.meta.dashboard }]" />
    <OnboardingWelcome />

    <div class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">{{ copy.hero.eyebrow }}</p>
        <h2>{{ copy.hero.title }}</h2>
        <p class="lead">{{ copy.hero.subtitle }}</p>
        <div class="hero-actions">
          <button class="primary" @click="createProject">{{ copy.hero.primaryCta }}</button>
          <button class="ghost" @click="openMarketplace">{{ copy.hero.secondaryCta }}</button>
        </div>
        <ul class="hero-stats">
          <li>
            <strong>{{ store.projects.length }}</strong>
            <span>{{ copy.hero.stats.projects }}</span>
          </li>
          <li>
            <strong>12+</strong>
            <span>{{ copy.hero.stats.presets }}</span>
          </li>
          <li>
            <strong>5 минут</strong>
            <span>{{ copy.hero.stats.time }}</span>
          </li>
        </ul>
      </div>
      <div class="hero-illustration">
        <div class="glow"></div>
        <div class="card mock"></div>
        <div class="card mock secondary"></div>
      </div>
    </div>

    <section class="quick-start">
      <header>
        <div>
          <h3>{{ copy.quickStart.title }}</h3>
          <p>{{ copy.quickStart.subtitle }}</p>
        </div>
      </header>
      <div class="preset-grid">
        <article v-for="preset in quickPresets" :key="preset.slug">
          <div>
            <h4>{{ preset.title }}</h4>
            <p>{{ preset.description }}</p>
          </div>
          <button class="secondary" @click="createFromPreset(preset)" :disabled="creatingPreset">
            {{ creatingPreset ? copy.quickStart.loading : copy.quickStart.cta }}
          </button>
        </article>
      </div>
    </section>

    <section class="projects">
      <header>
        <div>
          <h3>{{ copy.projects.title }}</h3>
          <p>{{ copy.projects.subtitle }}</p>
        </div>
        <button class="ghost" @click="createProject">{{ copy.projects.addCta }}</button>
      </header>
      <div class="cards">
        <article v-for="project in store.projects" :key="project.id" @click="open(project.id)">
          <div class="badge" :class="project.status">{{ project.status }}</div>
          <h4>{{ project.title }}</h4>
          <p>{{ project.description || copy.projects.fallbackDescription }}</p>
          <footer>
            <span>{{ copy.projects.visibilityLabel }}: {{ project.visibility }}</span>
            <span class="link">{{ copy.projects.open }}</span>
          </footer>
        </article>
        <div v-if="!store.projects.length" class="empty">
          <h4>{{ copy.projects.emptyTitle }}</h4>
          <p>{{ copy.projects.emptyText }}</p>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useProjectStore, type ProjectPreset } from "@/stores/project";
import { useOnboardingStore } from "@/stores/onboarding";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import OnboardingWelcome from "@/components/OnboardingWelcome.vue";

const copy = {
  meta: {
    dashboard: "Главная"
  },
  hero: {
    eyebrow: "Обновление редактора",
    title: "Собирайте лендинги и публикуйте в пару кликов",
    subtitle: "Выберите пресет, настройте цвета и отправьте проект в мир. Всё работает без кода и сложной настройки.",
    primaryCta: "+ Новый проект",
    secondaryCta: "Смотреть шаблоны",
    stats: {
      projects: "проектов",
      presets: "готовых пресетов",
      time: "до публикации"
    }
  },
  quickStart: {
    title: "Быстрый старт",
    subtitle: "Выберите сценарий и мы сразу подставим блоки и тексты.",
    cta: "Развернуть шаблон",
    loading: "Загружаем..."
  },
  projects: {
    title: "Мои проекты",
    subtitle: "Все лендинги, над которыми вы работаете прямо сейчас.",
    addCta: "+ Новый проект",
    fallbackDescription: "Описание появится позже",
    visibilityLabel: "Видимость",
    open: "Открыть →",
    emptyTitle: "Пока нет проектов",
    emptyText: "Нажмите «Новый проект» или воспользуйтесь одним из пресетов выше.",
    defaultTitle: "Новый проект",
    defaultDescription: "Черновик"
  }
} as const;

const router = useRouter();
const store = useProjectStore();
const onboarding = useOnboardingStore();
const creatingPreset = ref(false);

const quickPresets: ProjectPreset[] = [
  {
    slug: "open-day",
    title: "День открытых дверей",
    description: "Для мероприятий факультета: программа, преимущества и форма регистрации.",
    seo: {
      title: "День открытых дверей",
      description: "Пригласите абитуриентов за пару минут"
    },
    blocks: [
      {
        definition_key: "hero",
        config: {
          eyebrow: "12 апреля · 12:00",
          headline: "День открытых дверей",
          subheading: "Расскажите про кампус, команды и лаборатории.",
          cta_label: "Зарегистрироваться",
          cta_url: "#lead-form"
        }
      },
      {
        definition_key: "feature-grid",
        config: {
          title: "Что ждёт участников",
          features: [
            { title: "Экскурсия", description: "Прогулка по кампусу и лабораториям." },
            { title: "Нетворкинг", description: "Встреча с преподавателями и студентами." },
            { title: "Q&A", description: "Ответы на вопросы о поступлении." }
          ]
        }
      },
      {
        definition_key: "form",
        config: {
          title: "Регистрация",
          description: "Напомните о событии и пришлите программу.",
          fields: ["Имя", "Email", "Телефон"],
          webhook_url: "https://hooks.renderly.dev/open-day",
          success_message: "Спасибо! Письмо уже в пути."
        }
      }
    ]
  },
  {
    slug: "online-course",
    title: "Онлайн-курс",
    description: "Стартовая страница с преимуществами и CTA на запись.",
    seo: {
      title: "Онлайн-курс",
      description: "Покажите программу и соберите лиды"
    },
    blocks: [
      {
        definition_key: "hero",
        config: {
          eyebrow: "15 лекций",
          headline: "Intensive по no-code",
          subheading: "Запускайте MVP без разработчиков.",
          cta_label: "Записаться",
          cta_url: "#lead-form"
        }
      },
      {
        definition_key: "feature-grid",
        config: {
          title: "Преимущества курса",
          features: [
            { title: "Практика", description: "Работаем с реальными кейсами." },
            { title: "Наставники", description: "1:1 созвоны и персональная поддержка." },
            { title: "Комьюнити", description: "Чат выпускников и вакансии." }
          ]
        }
      },
      {
        definition_key: "cta",
        config: {
          title: "Присоединяйтесь к потоку",
          description: "Места ограничены.",
          action_label: "Получить программу",
          action_url: "https://renderly.dev/demo"
        }
      }
    ]
  },
  {
    slug: "faculty",
    title: "Факультет",
    description: "Лендинг факультета с образовательными программами и формой связи.",
    blocks: [
      {
        definition_key: "hero",
        config: {
          eyebrow: "Факультет цифрового дизайна",
          headline: "Современное образование",
          subheading: "Практика, лаборатории и стажировки для студентов.",
          cta_label: "Получить консультацию",
          cta_url: "#lead-form"
        }
      },
      {
        definition_key: "feature-grid",
        config: {
          title: "Почему выбирают нас",
          features: [
            { title: "Технологии", description: "Лаборатории AR/VR и медиа." },
            { title: "Преподаватели", description: "Практики из топ-компаний." },
            { title: "Партнёры", description: "Более 20 компаний." }
          ]
        }
      },
      {
        definition_key: "form",
        config: {
          title: "Обратная связь",
          description: "Оставьте контакты — мы расскажем о поступлении.",
          fields: ["Имя", "Email", "Город"],
          webhook_url: "https://hooks.renderly.dev/faculty",
          success_message: "Спасибо! Мы пришлём подборку материалов."
        }
      }
    ]
  }
];

onMounted(async () => {
  await store.fetchProjects();
  onboarding.syncProjects(store.projects);
  void store.loadCatalog();
});

async function createProject() {
  const slug = `project-${Date.now()}`;
  await store.createProject({
    title: copy.projects.defaultTitle,
    slug,
    description: copy.projects.defaultDescription,
    theme: {},
    settings: {}
  });
  router.push(`/editor/${store.current?.id}`);
}

async function createFromPreset(preset: ProjectPreset) {
  creatingPreset.value = true;
  try {
    await store.createProjectFromPreset(preset);
    if (store.current) {
      router.push(`/editor/${store.current.id}`);
    }
  } finally {
    creatingPreset.value = false;
  }
}

function openMarketplace() {
  router.push("/marketplace");
}

function open(id: number) {
  router.push(`/editor/${id}`);
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-card {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  padding: 32px;
  border-radius: 28px;
  background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.25), transparent 55%),
    linear-gradient(120deg, #1e3a8a, #4338ca, #7c3aed);
  color: white;
  box-shadow: 0 30px 70px rgba(15, 23, 42, 0.3);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-size: 0.8rem;
  margin: 0 0 8px;
  color: rgba(255, 255, 255, 0.7);
}

.hero-copy h2 {
  margin: 0;
  font-size: 2rem;
}

.lead {
  color: rgba(255, 255, 255, 0.8);
  max-width: 460px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 18px 0;
}

.hero-actions .primary {
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: #fff;
  padding: 12px 18px;
  border-radius: 999px;
  border: none;
  font-weight: 600;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25);
  cursor: pointer;
}

.hero-actions .ghost {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  background: transparent;
  color: #fff;
  padding: 12px 18px;
  cursor: pointer;
}

.hero-stats {
  list-style: none;
  padding: 0;
  margin: 24px 0 0;
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}

.hero-stats li {
  background: rgba(15, 23, 42, 0.35);
  border-radius: 16px;
  padding: 12px 16px;
  min-width: 120px;
}

.hero-stats strong {
  display: block;
  font-size: 1.4rem;
}

.hero-illustration {
  position: relative;
  min-height: 220px;
}

.hero-illustration .glow {
  position: absolute;
  inset: 20px;
  border-radius: 30px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.7), transparent 60%);
  filter: blur(10px);
}

.hero-illustration .card {
  position: absolute;
  width: 220px;
  height: 140px;
  border-radius: 20px;
  background: var(--panel-surface);
  box-shadow: var(--panel-shadow);
}

.hero-illustration .card.mock {
  top: 20px;
  right: 10px;
}

.hero-illustration .card.secondary {
  top: 110px;
  right: 80px;
  opacity: 0.8;
}

.quick-start {
  background: var(--panel-surface);
  border: 1px solid var(--divider-color);
  padding: 24px;
  border-radius: 24px;
  box-shadow: var(--panel-shadow);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quick-start header h3 {
  margin: 0;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.preset-grid article {
  border: 1px solid var(--divider-color);
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: linear-gradient(135deg, var(--panel-surface), var(--panel-soft));
}

.preset-grid h4 {
  margin: 0;
}

button.secondary {
  border: none;
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: #fff;
  padding: 10px 16px;
  border-radius: 12px;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.2);
}

.projects {
  background: var(--panel-surface);
  border: 1px solid var(--divider-color);
  padding: 24px;
  border-radius: 24px;
  box-shadow: var(--panel-shadow);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.projects header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.projects header h3 {
  margin: 0;
}

.projects .cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.projects .cards article {
  border: 1px solid var(--divider-color);
  border-radius: 18px;
  padding: 18px;
  background: var(--panel-soft);
  cursor: pointer;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.projects .cards article:hover {
  transform: translateY(-4px);
  box-shadow: var(--panel-shadow);
}

.badge {
  align-self: flex-start;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: var(--accent-muted);
  color: var(--accent);
}

.badge.published {
  background: #dcfce7;
  color: #166534;
}

.badge.draft {
  background: #fee2e2;
  color: #b91c1c;
}

.projects footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.projects footer .link {
  color: var(--accent);
  font-weight: 600;
}

.empty {
  border: 1px dashed var(--divider-color);
  border-radius: 18px;
  padding: 24px;
  text-align: center;
  grid-column: 1 / -1;
  background: var(--panel-soft);
}
</style>
