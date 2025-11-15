<template>
  <div ref="shellRef" class="login-shell">
    <canvas ref="bgCanvas" class="ambient-canvas" aria-hidden="true"></canvas>
    <div class="login-grid">
            <section class="hero-card">
        <p class="eyebrow">RENDERLY STUDIO</p>
        <h1>Редактор, который собирает сайт вместо вас</h1>
        <p class="lead">
          Соберите лендинг уровня Tilda/Taplink за минуты: готовые блоки, гибкая сетка и автоматические
          интеграции с CRM, чат-ботами и рассылками.
        </p>
        <div class="stats-grid">
          <article v-for="stat in heroStats" :key="stat.label" class="stat-card">
            <p class="stat-label">{{ stat.label }}</p>
            <p class="stat-value">{{ stat.value }}</p>
          </article>
        </div>
        <div class="pill-row">
          <article v-for="pill in heroPills" :key="pill.title" class="pill-card">
            <p class="pill-title">{{ pill.title }}</p>
          </article>
        </div>
      </section>

      <section class="interaction-column">
        <div class="glass-column">
        <div class="media-card">
          <div class="media-header">
            <span class="status-dot"></span>
            <span>Live Preview &middot; Theme Designer &middot; Automation</span>
          </div>
          <div class="media-screen">
              <div class="screen-toolbar">
                <span class="toolbar-dot red"></span>
                <span class="toolbar-dot yellow"></span>
                <span class="toolbar-dot green"></span>
              </div>
              <div class="screen-content">
                <div class="track highlight"></div>
                <div class="track"></div>
                <div class="track small"></div>
                <div
                  v-for="chip in stickerChips"
                  :key="chip.label"
                  class="screen-chip"
                  :style="{ top: chip.top, animationDelay: chip.delay + 's' }"
                >
                  {{ chip.label }}
                </div>
              </div>
            </div>
          </div>

          <div class="auth-card">
            <div class="tabs">
              <button type="button" :class="{ active: mode === 'login' }" @click="setMode('login')">
                Войти
              </button>
              <button
                type="button"
                :class="{ active: mode === 'signup' }"
                @click="setMode('signup')"
              >
                Регистрация
              </button>
            </div>

            <form class="auth-form" @submit.prevent="handleSubmit">
              <label>
                <span>Email</span>
                <input
                  v-model="email"
                  type="email"
                  placeholder="founder@brand.ru"
                  autocomplete="email"
                  required
                />
              </label>
              <label>
                <span>Пароль</span>
                <div class="password-field">
                  <input
                    v-model="password"
                    :type="passwordType"
                    placeholder="••••••••"
                    required
                  />
                  <button type="button" @click="togglePassword">
                    {{ showPassword ? "Скрыть" : "Показать" }}
                  </button>
                </div>
              </label>
              <div v-if="mode === 'signup'" class="signup-condensed">
                <label>
                  <span>Фамилия Имя</span>
                  <input
                    v-model="fullName"
                    type="text"
                    placeholder="Иванова Анна"
                    required
                  />
                </label>
                <label>
                  <span>Компания</span>
                  <input
                    v-model="company"
                    type="text"
                    placeholder="Renderly Studio"
                    required
                  />
                </label>
              </div>
              <div v-if="mode === 'login'" class="form-meta">
                <label class="checkbox">
                  <input type="checkbox" v-model="rememberMe" />
                  <span>Запомнить меня</span>
                </label>
                <button type="button" class="link-btn" @click="handleForgot">
                  Забыли пароль?
                </button>
              </div>

              <button class="primary" type="submit" :disabled="loading">
                <span v-if="!loading">
                  {{ mode === "login" ? "Войти" : "Зарегистрироваться" }}
                </span>
                <span v-else>Отправляем...</span>
              </button>
              <button
                v-if="mode === 'login'"
                class="ghost"
                type="button"
                :disabled="loading"
                @click="useDemoProfile"
              >
                Попробовать демо-профиль
              </button>
              <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
              <p v-if="signupSuccess" class="notice">
                Заявка отправлена — мы свяжемся в течение рабочего дня.
              </p>
            </form>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

type Mode = "login" | "signup";

interface AmbientBlob {
  radius: number;
  speed: number;
  hue: number;
  offset: number;
}

const heroStats = [
  { label: "Блоков в библиотеке", value: "120+" },
  { label: "Сайтов создано", value: "7 200" },
  { label: "Оценка команды", value: "4.9 / 5" }
];

const heroPills = [
  { title: "Zero grid" },
  { title: "Интеграции" },
  { title: "AI-помощник" }
];
const stickerChips = [
  { label: "Live preview", top: "12%", delay: 0 },
  { label: "Theme designer", top: "48%", delay: 0.4 },
  { label: "Automation", top: "78%", delay: 0.9 }
];

const shellRef = ref<HTMLElement | null>(null);
const mode = ref<Mode>("login");
const email = ref("demo@renderly.dev");
const password = ref("renderly123");
const rememberMe = ref(true);
const showPassword = ref(false);
const loading = ref(false);
const fullName = ref("");
const company = ref("");
const signupSuccess = ref(false);
const errorMessage = ref("");
const bgCanvas = ref<HTMLCanvasElement | null>(null);

const passwordType = computed(() => (showPassword.value ? "text" : "password"));

const router = useRouter();
const auth = useAuthStore();

const ambientBlobs: AmbientBlob[] = Array.from({ length: 4 }, (_, index) => ({
  radius: 320 + index * 80,
  speed: 0.0003 + index * 0.00015,
  hue: 212 + index * 10,
  offset: Math.random() * Math.PI * 2
}));

let ctx: CanvasRenderingContext2D | null = null;
let frameId = 0;
let resizeObserver: ResizeObserver | null = null;

function syncCanvasSize() {
  const canvas = bgCanvas.value;
  const context = ctx;
  if (!canvas || !context) {
    return;
  }
  const container = shellRef.value;
  const dpr = window.devicePixelRatio || 1;
  const width = container ? container.offsetWidth : window.innerWidth;
  const height = container ? container.offsetHeight : window.innerHeight;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  context.setTransform(1, 0, 0, 1, 0, 0);
  context.scale(dpr, dpr);
}

function renderFrame(time: number) {
  const canvas = bgCanvas.value;
  const context = ctx;
  if (!canvas || !context) {
    return;
  }
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.width / dpr;
  const height = canvas.height / dpr;

  context.clearRect(0, 0, width, height);
  const baseGradient = context.createLinearGradient(0, 0, width, height);
  baseGradient.addColorStop(0, "#f3edff");
  baseGradient.addColorStop(1, "#e0f4ff");
  context.fillStyle = baseGradient;
  context.fillRect(0, 0, width, height);

  ambientBlobs.forEach((blob) => {
    const x = (0.5 + Math.sin(time * blob.speed + blob.offset) * 0.35) * width;
    const y = (0.5 + Math.cos(time * blob.speed + blob.offset) * 0.3) * height;
    const gradient = context.createRadialGradient(x, y, 0, x, y, blob.radius);
    gradient.addColorStop(0, `hsla(${blob.hue}, 85%, 72%, 0.55)`);
    gradient.addColorStop(1, `hsla(${blob.hue}, 85%, 72%, 0)`);
    context.fillStyle = gradient;
    context.beginPath();
    context.arc(x, y, blob.radius, 0, Math.PI * 2);
    context.fill();
  });

  frameId = requestAnimationFrame(renderFrame);
}

function initCanvas() {
  const canvas = bgCanvas.value;
  if (!canvas) {
    return;
  }
  ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }
  syncCanvasSize();
  frameId = requestAnimationFrame(renderFrame);

  if (
    !resizeObserver &&
    shellRef.value &&
    typeof ResizeObserver !== "undefined"
  ) {
    resizeObserver = new ResizeObserver(() => {
      syncCanvasSize();
    });
    resizeObserver.observe(shellRef.value);
  }
}

async function handleSubmit() {
  signupSuccess.value = false;
  errorMessage.value = "";
  loading.value = true;

  try {
    if (mode.value === "login") {
      await auth.login(email.value, password.value);
      if (!rememberMe.value) {
        localStorage.removeItem("renderly:token");
      }
      await router.push("/");
    } else {
      const normalizedFullName = fullName.value.trim();
      await auth.register({
        email: email.value,
        password: password.value,
        fullName: normalizedFullName || null
      });
      await auth.login(email.value, password.value);
      signupSuccess.value = true;
      await router.push("/");
    }
  } catch (error) {
    console.error(error);
    errorMessage.value =
      "Не удалось выполнить действие. Проверьте данные и попробуйте снова.";
  } finally {
    loading.value = false;
  }
}

function setMode(nextMode: Mode) {
  mode.value = nextMode;
  signupSuccess.value = false;
  errorMessage.value = "";
}

function togglePassword() {
  showPassword.value = !showPassword.value;
}

async function useDemoProfile() {
  email.value = "demo@renderly.dev";
  password.value = "renderly123";
  mode.value = "login";
  rememberMe.value = true;
  await handleSubmit();
}

function handleForgot() {
  window.alert("Напишите на hi@renderly.dev — поможем восстановить доступ.");
}

onMounted(() => {
  initCanvas();
  window.addEventListener("resize", syncCanvasSize);
});

onBeforeUnmount(() => {
  if (frameId) {
    cancelAnimationFrame(frameId);
  }
  window.removeEventListener("resize", syncCanvasSize);
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
});
</script>

<style scoped>
.login-shell {
  --shell-padding: clamp(48px, 10vh, 96px);
  position: relative;
  min-height: 100vh;
  padding: var(--shell-padding) clamp(20px, 5vw, 100px);
  overflow: hidden;
  font-family: "Inter", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont,
    "SF Pro Display", sans-serif;
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background: linear-gradient(135deg, #f3edff 0%, #e0f4ff 50%, #d3f2ff 100%);
  isolation: isolate;
}

.ambient-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.login-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 40px;
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  align-items: stretch;
}


.hero-card {
  position: relative;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(243, 248, 255, 0.98) 100%);
  border: 1px solid rgba(189, 204, 255, 0.6);
  border-radius: 46px;
  padding: clamp(32px, 4vw, 48px);
  box-shadow: 0 35px 90px rgba(56, 33, 132, 0.18);
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: auto;
  overflow: hidden;
}

.hero-card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at -20% -20%, rgba(129, 140, 248, 0.3), transparent 60%);
  pointer-events: none;
}

.hero-card > * {
  position: relative;
  z-index: 1;
}

.eyebrow {
  margin: 0 0 12px;
  letter-spacing: 0.28em;
  font-size: 0.78rem;
  color: #94a3b8;
}

.hero-card h1 {
  margin: 0;
  font-size: clamp(2.3rem, 3.8vw, 3rem);
  line-height: 1.05;
  color: #020617;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.lead {
  margin: 0;
  font-size: 1.02rem;
  color: #4b5563;
  max-width: 420px;
  line-height: 1.45;
}

.stats-grid {
  display: flex;
  gap: 14px;
  justify-content: space-between;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1 1 calc(33.333% - 10px);
  min-width: 150px;
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: linear-gradient(180deg, rgba(247, 249, 255, 0.95) 0%, rgba(235, 241, 255, 0.95) 100%);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.07);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  margin: 0;
  font-size: 0.82rem;
  color: #94a3b8;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.stat-value {
  margin: 4px 0 0;
  font-size: 1.7rem;
  font-weight: 700;
  color: #1a31d6;
}

.pill-row {
  display: flex;
  gap: 14px;
  justify-content: space-between;
  flex-wrap: wrap;
}

.pill-card {
  flex: 1 1 calc(33.333% - 10px);
  min-width: 130px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(247, 249, 255, 0.9);
  border: 1px solid rgba(135, 155, 255, 0.4);
  box-shadow: 0 12px 22px rgba(79, 70, 229, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70px;
  text-align: center;
}

.pill-title {
  margin: 0;
  font-weight: 600;
  color: #0f172a;
  font-size: 1rem;
}

@media (min-width: 1200px) {
  .login-grid {
    grid-template-columns: minmax(360px, 520px) minmax(360px, 460px);
  }
}
.interaction-column {
  display: flex;
  justify-content: center;
}

.glass-column {
  position: relative;
  width: min(480px, 100%);
  background: rgba(255, 255, 255, 0.95);
  border-radius: 40px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  box-shadow: 0 35px 90px rgba(15, 23, 42, 0.15);
  backdrop-filter: blur(32px);
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  min-height: 0;
}

.glass-column::before {
  content: "";
  position: absolute;
  inset: 12px;
  border-radius: 32px;
  background: radial-gradient(circle at top, rgba(148, 163, 255, 0.16), transparent 55%);
  z-index: -1;
}

.media-card {
  border-radius: 28px;
  padding: 18px;
  background: rgba(248, 250, 255, 0.93);
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.media-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #111827;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4ade80, #16a34a);
  box-shadow: 0 0 12px rgba(34, 197, 94, 0.7);
}

.media-screen {
  border-radius: 26px;
  padding: 18px;
  background: linear-gradient(135deg, #1f1a44, #3a1f6e 60%, #6d28d9);
  min-height: 200px;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.25);
}

.screen-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.toolbar-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
  opacity: 0.65;
}

.toolbar-dot.red {
  background: #ef4444;
}

.toolbar-dot.yellow {
  background: #f59e0b;
}

.toolbar-dot.green {
  background: #22c55e;
}

.screen-content {
  position: relative;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.35);
  padding: 18px;
  height: 150px;
  overflow: hidden;
}

.track {
  height: 30px;
  border-radius: 16px;
  background: linear-gradient(135deg, #5f6fff, #a855f7);
  margin-bottom: 14px;
  opacity: 0.8;
}

.track.highlight {
  background: linear-gradient(135deg, #6f7aff, #d946ef);
}

.track.small {
  width: 65%;
  opacity: 0.6;
}

.screen-chip {
  position: absolute;
  right: 18px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 0.8rem;
  color: #e0e7ff;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(6px);
  animation: floatChip 6s ease-in-out infinite;
}

.auth-card {
  border-radius: 28px;
  padding: 22px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
  flex: none;
  width: 100%;
  max-width: 440px;
  height: 560px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
  padding: 8px;
  border-radius: 999px;
  background: rgba(244, 247, 255, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.tabs button {
  position: relative;
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 999px;
  background: transparent;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.tabs button::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: 1px solid transparent;
  transition: border 0.2s ease;
  pointer-events: none;
}

.tabs button.active {
  background: linear-gradient(135deg, #6d5efc, #a855f7);
  color: #fff;
  box-shadow: 0 12px 28px rgba(109, 94, 252, 0.35);
  transform: translateY(-1px);
}

.tabs button.active::after {
  border-color: rgba(255, 255, 255, 0.4);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
  margin-right: -4px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.92rem;
  color: #475569;
}

input,
textarea {
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  padding: 12px 16px;
  background: rgba(246, 248, 255, 0.95);
  font-size: 1rem;
  transition: border 0.2s ease, box-shadow 0.2s ease;
  font-family: inherit;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18);
}

textarea {
  resize: none;
}

.password-field {
  display: flex;
  align-items: center;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(246, 248, 255, 0.95);
  padding: 0 8px;
}

.password-field input {
  border: none;
  background: transparent;
  flex: 1;
  padding: 12px 8px;
  box-shadow: none;
}

.password-field button {
  border: none;
  background: transparent;
  color: #4c1d95;
  font-weight: 600;
  cursor: pointer;
  padding: 8px 10px;
}

.signup-condensed {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  padding: 12px;
  border-radius: 18px;
  background: rgba(247, 250, 255, 0.85);
  border: 1px dashed rgba(99, 102, 241, 0.3);
}

.signup-condensed label {
  margin: 0;
}

.form-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #334155;
}

.checkbox input {
  width: 18px;
  height: 18px;
}

.link-btn {
  border: none;
  background: none;
  color: #4338ca;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;
}

.primary,
.ghost {
  border: none;
  border-radius: 20px;
  padding: 14px 18px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.primary {
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  color: #fff;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.3);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost {
  background: rgba(248, 250, 255, 0.9);
  color: #111827;
  border: 1px solid rgba(148, 163, 184, 0.4);
}

.hint {
  margin: 0;
  font-size: 0.85rem;
  color: #64748b;
}

.error {
  margin: 0;
  color: #dc2626;
  font-size: 0.9rem;
}

.notice {
  margin: 4px 0 0;
  color: #0f766e;
  font-size: 0.9rem;
}

@keyframes floatChip {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

@media (max-width: 1024px) {
.login-shell {
    padding: 48px 24px;
    height: auto;
  }

  .login-grid {
    max-height: none;
  }

  .hero-card,
  .glass-column {
    height: auto;
  }

  .hero-card,
  .auth-card {
    height: auto;
    min-height: auto;
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .hero-card,
  .glass-column {
    border-radius: 24px;
    padding: 24px;
  }

  .glass-column {
    width: 100%;
  }

  .form-meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>



