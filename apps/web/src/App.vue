<template>
  <div class="app-shell" :class="{ 'auth-mode': isAuthRoute, 'share-mode': isShareRoute }">
    <div v-if="isAuthRoute" class="auth-container">
      <RouterView />
    </div>
    <div v-else-if="isShareRoute" class="share-container">
      <RouterView />
    </div>
    <template v-else>
      <header class="app-header">
        <div class="brand">
          <div class="logo">R</div>
          <div>
            <p class="title">Renderly Studio</p>
            <small>{{ brandTagline }}</small>
          </div>
        </div>
        <nav>
          <RouterLink
            v-for="link in visibleLinks"
            :key="link.to"
            :to="link.to"
            :class="{ active: isActive(link.to) }"
          >
            <span v-if="link.icon" class="icon">{{ link.icon }}</span>
            {{ link.label }}
          </RouterLink>
        </nav>
        <div class="header-tools">
          <ThemeToggle />
          <div class="user-chip">
            <div class="avatar">{{ userInitials }}</div>
            <div>
              <strong>{{ userName }}</strong>
              <small>{{ userSubtitle }}</small>
            </div>
          </div>
          <button class="logout-btn" type="button" @click="handleLogout">Выйти</button>
        </div>
      </header>
      <main>
        <RouterView />
      </main>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watchEffect } from "vue";
import { useRoute, useRouter } from "vue-router";
import ThemeToggle from "@/components/ThemeToggle.vue";
import { useAuthStore } from "@/stores/auth";

interface NavLink {
  label: string;
  to: string;
  icon?: string;
  adminOnly?: boolean;
}

const navLinks: NavLink[] = [
  { label: "Dashboard", to: "/", icon: "🏠" },
  { label: "Editor", to: "/editor", icon: "🛠️" },
  { label: "Marketplace", to: "/marketplace", icon: "🧩" },
  { label: "Analytics", to: "/analytics", icon: "📈" },
  { label: "Block Admin", to: "/admin/blocks", icon: "🧱", adminOnly: true },
];

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const brandTagline =
  "\u0420\u0435\u0434\u0430\u043a\u0442\u043e\u0440\u002c\u0020\u043a\u043e\u0442\u043e\u0440\u044b\u0439\u0020\u0441\u043e\u0431\u0438\u0440\u0430\u0435\u0442\u0020\u0441\u0430\u0439\u0442\u0020\u0432\u043c\u0435\u0441\u0442\u043e\u0020\u0432\u0430\u0441";

const isAuthRoute = computed(() => route.name === "login");
const isShareRoute = computed(() => route.name === "share");
const visibleLinks = computed(() =>
  navLinks.filter((link) => !link.adminOnly || auth.isAdmin)
);

watchEffect(() => {
  if (typeof document === "undefined") {
    return;
  }
  document.body.style.overflow = isAuthRoute.value ? "hidden" : "";
});

const userName = computed(
  () =>
    auth.fullName?.trim() || auth.email || "\u0424\u0430\u043c\u0438\u043b\u0438\u044f\u0020\u0418\u043c\u044f"
);
const userSubtitle = computed(
  () => auth.email || "\u0420\u0430\u0431\u043e\u0447\u0438\u0439\u0020\u043f\u0440\u043e\u0444\u0438\u043b\u044c"
);
const userInitials = computed(() => {
  const source = auth.fullName?.trim() || auth.email || "\u0424\u0418";
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  if (parts.length === 1) {
    if (parts[0].includes("@")) {
      return (parts[0][0] + (parts[0][1] ?? "")).toUpperCase();
    }
    return (parts[0].slice(0, 2) || "\u0424\u0418").toUpperCase();
  }
  return "\u0424\u0418";
});

onMounted(() => {
  if (auth.token) {
    auth.fetchProfile().catch(() => {});
  }
});

function isActive(path: string) {
  if (path === "/") {
    return route.path === "/";
  }
  return route.path.startsWith(path);
}

function handleLogout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--page-gradient);
  color: var(--text-primary);
  font-family: var(--font-ui);
}

.app-shell.auth-mode {
  background: var(--page-gradient);
}

.app-shell.share-mode {
  background: var(--page-gradient);
}

.auth-container {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: transparent;
}

.auth-container :deep(.login-shell) {
  width: 100%;
  min-height: 100vh;
}

.share-container {
  width: 100%;
  min-height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px clamp(20px, 4vw, 48px);
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--glass-border);
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: var(--shadow-soft);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  box-shadow: 0 14px 32px rgba(79, 70, 229, 0.35);
}

.title {
  margin: 0;
  font-weight: 600;
  color: #0f172a;
}

.brand small {
  color: var(--text-secondary);
}

nav {
  display: flex;
  gap: 12px;
}

nav a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 999px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

nav a:hover {
  background: var(--accent-muted);
  color: var(--accent-strong);
}

nav a.active {
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  color: #fff;
  box-shadow: 0 12px 28px rgba(79, 70, 229, 0.35);
}

.icon {
  font-size: 0.95rem;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--glass-bg);
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--accent-muted);
  color: var(--accent-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.user-chip strong {
  display: block;
  font-size: 0.9rem;
}

.user-chip small {
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.logout-btn {
  border-radius: 999px;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.logout-btn:hover {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 10px 24px rgba(79, 70, 229, 0.25);
}

main {
  padding: 32px;
  background: transparent;
}
</style>


