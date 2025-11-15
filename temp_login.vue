<template>
  <div class="auth-shell">
    <section class="hero">
      <div class="hero-copy">
        <header>
          <p class="eyebrow">renderly studio</p>
          <h1>Соберите страницу быстрее, чем появятся правки</h1>
          <p>
            Готовые блоки, zero-grid, CRM-интеграции и автоматизация форм — всё в одном окне.
            Renderly помогает запускать посадочные за часы, а не недели.
          </p>
        </header>

        <div class="pill-group">
          <article>
            <strong>Библиотека</strong>
            <span>125 hero, лид-магнитов и CTA + zero-grid сетки</span>
          </article>
          <article>
            <strong>Automation</strong>
            <span>Форма -> CRM -> Telegram / Notion</span>
          </article>
          <article>
            <strong>Инструменты</strong>
            <span>Live Preview, эксперименты и Brand Wizard</span>
          </article>
        </div>

        <div class="stats">
          <div>
            <strong>7 200+</strong>
            <span>собранных страниц</span>
          </div>
          <div>
            <strong>4.9/5</strong>
            <span>средний рейтинг команд</span>
          </div>
        </div>
      </div>

      <div class="hero-media">
        <video
          autoplay
          muted
          loop
          playsinline
          poster="https://files.renderly.dev/hero-poster.jpg"
        >
          <source src="https://files.renderly.dev/hero-loop.mp4" type="video/mp4" />
        </video>
        <div class="media-overlay">
          <p>
            Live Preview + Theme Designer + цепочка заявок > CRM. Всё синхронизируется и защищено.
          </p>
          <span>Renderly OS (beta)</span>
        </div>
      </div>
    </section>

    <section class="auth-card">
      <div class="tabs">
        <button type="button" :class="{ active: mode === 'login' }" @click="mode = 'login'">
          Вход
        </button>
        <button type="button" :class="{ active: mode === 'signup' }" @click="mode = 'signup'">
          Создать аккаунт
        </button>
      </div>

      <form v-if="mode === 'login'" @submit.prevent="submitLogin" aria-label="Форма входа">
        <label>
          Email
          <input v-model="loginEmail" type="email" placeholder="name@company.com" required />
        </label>
        <label class="password-field">
          Пароль
          <input v-model="loginPassword" :type="showPassword ? 'text' : 'password'" required />
          <button type="button" class="ghost icon" @click="showPassword = !showPassword">
            {{ showPassword ? "Скрыть" : "Показать" }}
          </button>
        </label>
        <div class="form-row">
          <label class="checkbox">
            <input type="checkbox" v-model="staySigned" />
            <span>Запомнить меня</span>
          </label>
          <a class="link" href="mailto:support@renderly.dev?subject=Reset password">Забыли пароль?</a>
        </div>
        <button type="submit" class="primary" :disabled="loading">
          {{ loading ? "Входим..." : "Войти" }}
        </button>
        <button type="button" class="secondary" @click="useDemo" :disabled="loading">
          Посмотреть демо
        </button>
        <p v-if="error" class="error">{{ error }}</p>
        <p class="hint">Демо-аккаунт: demo@renderly.dev / renderly123</p>
      </form>

      <form v-else @submit.prevent="submitSignup" aria-label="Форма заявки на доступ">
        <label>
          Компания или проект
          <input v-model="signupName" type="text" placeholder="Renderly, Taplink, pet-проект" required />
        </label>
        <label>
          Email
          <input v-model="signupEmail" type="email" placeholder="founder@startup.com" required />
        </label>
        <label>
          Задача
          <textarea
            v-model="signupGoal"
            placeholder="Запустить лендинг, собрать прогрев, протестировать оффер, автоматизировать лиды..."
            rows="3"
          />
        </label>
        <button type="submit" class="primary" :disabled="loading">
          {{ loading ? "Отправляем..." : "Получить доступ" }}
        </button>
        <p class="hint">
          Пишем на русском. Поможем пройти онбординг и подключить интеграции после заявки.
        </p>
        <p v-if="success" class="success">Готово! Мы уже отправили инструкцию на почту.</p>
      </form>
    </section>
  </div>
</template>


<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const mode = ref<"login" | "signup">("login");
const loginEmail = ref("demo@renderly.dev");
const loginPassword = ref("renderly123");
const staySigned = ref(true);
const showPassword = ref(false);
const signupName = ref("");
const signupEmail = ref("");
const signupGoal = ref("");
const loading = ref(false);
const error = ref("");
const success = ref(false);

const redirectTo = computed(() => (typeof route.query.redirect === "string" ? route.query.redirect : "/"));

watch(
  () => auth.isAuthenticated,
  (authed) => {
    if (authed) {
      router.replace(redirectTo.value);
    }
  },
  { immediate: true }
);

async function submitLogin() {
  loading.value = true;
  error.value = "";
  try {
    await auth.login(loginEmail.value, loginPassword.value, staySigned.value);
    router.replace(redirectTo.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Не удалось войти. Проверьте данные.";
  } finally {
    loading.value = false;
  }
}

async function useDemo() {
  loginEmail.value = "demo@renderly.dev";
  loginPassword.value = "renderly123";
  await submitLogin();
}

async function submitSignup() {
  loading.value = true;
  success.value = false;
  await new Promise((resolve) => setTimeout(resolve, 1200));
  success.value = true;
  loading.value = false;
}
</script>

<style scoped>
.auth-shell {
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 32px;
  padding: clamp(24px, 6vw, 72px);
  background: #050712;
  color: #fff;
  align-items: center;
  overflow: hidden;
}

.auth-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 12% 20%, rgba(14, 165, 233, 0.28), transparent 40%),
    radial-gradient(circle at 80% 10%, rgba(99, 102, 241, 0.35), transparent 50%),
    linear-gradient(135deg, #050712, #0f172a 60%, #10102d);
  z-index: -1;
}

.hero {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(280px, 1fr);
  gap: 24px;
  max-width: 960px;
  width: 100%;
  z-index: 1;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero header h1 {
  font-size: clamp(2rem, 3vw, 3.4rem);
  margin: 0;
  color: #111322;
}

.hero header p {
  color: #4b5563;
  max-width: 520px;
}

.hero-media {
  position: relative;
  border-radius: 32px;
  overflow: hidden;
  box-shadow: 0 40px 120px rgba(6, 8, 20, 0.8);
}

.hero-media video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.media-overlay {
  position: absolute;
  inset: auto 16px 16px 16px;
  background: rgba(3, 5, 20, 0.75);
  border-radius: 18px;
  padding: 14px 18px;
  backdrop-filter: blur(6px);
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.9rem;
}

.pill-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.pill-group article {
  border-radius: 18px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
}

.stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.stats strong {
  font-size: 2.4rem;
  display: block;
}

.testimonial {
  padding: 20px;
  border-radius: 20px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.3);
  font-style: italic;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.2em;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.55);
}

.auth-card {
  background: #fff;
  border-radius: 32px;
  padding: 36px;
  color: #0f172a;
  box-shadow: 0 40px 90px rgba(15, 23, 42, 0.4);
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 430px;
  justify-self: center;
  align-self: center;
  border: 1px solid rgba(148, 163, 184, 0.2);
  z-index: 1;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  background: #f1f5f9;
  border-radius: 999px;
  padding: 6px;
}

.tabs button {
  border: none;
  background: transparent;
  border-radius: 999px;
  padding: 12px 18px;
  font-weight: 600;
  cursor: pointer;
}

.tabs button.active {
  background: linear-gradient(135deg, #2563eb, #4338ca);
  color: #fff;
  box-shadow: 0 10px 25px rgba(67, 56, 202, 0.25);
}

form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.9rem;
}

.password-field {
  position: relative;
}

.password-field .icon {
  position: absolute;
  right: 8px;
  bottom: 8px;
}

input,
textarea {
  border-radius: 14px;
  border: 1px solid #cbd5f5;
  padding: 12px 14px;
  font-size: 1rem;
  font-family: inherit;
}

textarea {
  resize: vertical;
}

.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.primary,
.secondary,
.ghost {
  border-radius: 14px;
  padding: 12px 16px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.primary {
  background: linear-gradient(120deg, #2563eb, #4338ca);
  color: #fff;
  box-shadow: 0 18px 35px rgba(37, 99, 235, 0.25);
}

.secondary {
  background: #f1f5f9;
  color: #1e293b;
  border: 1px solid #cbd5f5;
}

.ghost {
  border: 1px solid transparent;
  background: transparent;
  color: #1e1b4b;
}

.icon {
  padding: 6px 10px;
  font-size: 0.8rem;
}

.link {
  color: #6366f1;
  text-decoration: none;
  font-size: 0.85rem;
}

.error {
  color: #b91c1c;
  font-size: 0.85rem;
}

.success {
  color: #0f9d58;
  font-size: 0.85rem;
}

.hint {
  color: #94a3b8;
  font-size: 0.85rem;
  margin: 0;
}

@media (max-width: 960px) {
  .auth-shell {
    grid-template-columns: 1fr;
    padding: 32px 20px;
  }

  .hero {
    max-width: none;
    text-align: center;
  }

  .hero ul {
    align-items: center;
  }
}
</style>
