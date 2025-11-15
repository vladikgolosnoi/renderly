import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "@/views/DashboardView.vue";
import EditorView from "@/views/EditorView.vue";
import LoginView from "@/views/LoginView.vue";
import BlockAdminView from "@/views/BlockAdminView.vue";
import ProjectSettingsView from "@/views/ProjectSettings.vue";
import AnalyticsView from "@/views/AnalyticsView.vue";
import MarketplaceView from "@/views/MarketplaceView.vue";
import ShareView from "@/views/ShareView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginView },
    { path: "/", name: "dashboard", component: DashboardView },
    { path: "/editor/:id?", name: "editor", component: EditorView, props: true },
    { path: "/admin/blocks", name: "block-admin", component: BlockAdminView },
    { path: "/marketplace", name: "marketplace", component: MarketplaceView },
    {
      path: "/projects/:id/settings",
      name: "project-settings",
      component: ProjectSettingsView,
      props: true
    },
    { path: "/analytics", name: "analytics", component: AnalyticsView },
    {
      path: "/share/:token",
      name: "share",
      component: ShareView,
      props: true,
      meta: { public: true, chromeLess: true }
    }
  ]
});

router.beforeEach((to) => {
  const token = localStorage.getItem("renderly:token");
  const isAuthenticated = Boolean(token);
  const isPublicRoute = Boolean(to.meta?.public);

  if (!isAuthenticated && !isPublicRoute && to.name !== "login") {
    return {
      name: "login",
      query: to.fullPath ? { redirect: to.fullPath } : undefined
    };
  }

  if (isAuthenticated && to.name === "login") {
    return { name: "dashboard" };
  }

  return true;
});

export default router;
