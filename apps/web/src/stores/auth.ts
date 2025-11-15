import { defineStore } from "pinia";
import api from "@/api/client";

interface AuthState {
  token: string | null;
  email: string | null;
  fullName: string | null;
  isAdmin: boolean;
}

interface RegisterPayload {
  email: string;
  password: string;
  fullName?: string | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem("renderly:token"),
    email: null,
    fullName: null,
    isAdmin: false
  }),
  actions: {
    async register(payload: RegisterPayload) {
      const { data } = await api.post("/auth/register", {
        email: payload.email,
        password: payload.password,
        full_name: payload.fullName
      });
      this.email = data.email;
      this.fullName = data.full_name ?? null;
      this.isAdmin = data.is_admin ?? false;
    },
    async login(email: string, password: string) {
      const { data } = await api.post("/auth/login", { email, password });
      this.token = data.access_token;
      this.email = email;
      localStorage.setItem("renderly:token", data.access_token);
      try {
        await this.fetchProfile();
      } catch (error) {
        console.error("Failed to fetch profile", error);
      }
    },
    async fetchProfile() {
      if (!this.token) {
        return;
      }
      const { data } = await api.get("/auth/me");
      this.email = data.email;
      this.fullName = data.full_name ?? null;
      this.isAdmin = data.is_admin ?? false;
    },
    logout() {
      this.token = null;
      this.email = null;
      this.fullName = null;
      this.isAdmin = false;
      localStorage.removeItem("renderly:token");
    }
  }
});
