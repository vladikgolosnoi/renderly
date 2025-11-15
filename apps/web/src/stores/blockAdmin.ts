import { defineStore } from "pinia";
import api from "@/api/client";
import type { BlockDefinition, CommunityTemplate, UserAccount } from "@/types/blocks";

interface BlockAdminState {
  blocks: BlockDefinition[];
  templates: CommunityTemplate[];
  users: UserAccount[];
  loading: boolean;
  templatesLoading: boolean;
  usersLoading: boolean;
}

export const useBlockAdminStore = defineStore("blockAdmin", {
  state: (): BlockAdminState => ({
    blocks: [],
    templates: [],
    users: [],
    loading: false,
    templatesLoading: false,
    usersLoading: false
  }),
  actions: {
    async fetchBlocks() {
      this.loading = true;
      const { data } = await api.get<BlockDefinition[]>("/catalog/blocks");
      this.blocks = data;
      this.loading = false;
    },
    async createBlock(payload: Omit<BlockDefinition, "id">) {
      const { data } = await api.post<BlockDefinition>("/catalog/blocks", payload);
      this.blocks.push(data);
      return data;
    },
    async updateBlock(blockId: number, payload: Partial<BlockDefinition>) {
      const { data } = await api.put<BlockDefinition>(
        `/catalog/blocks/${blockId}`,
        payload
      );
      const index = this.blocks.findIndex((item) => item.id === data.id);
      if (index !== -1) {
        this.blocks[index] = data;
      }
      return data;
    },
    async deleteBlock(blockId: number) {
      await api.delete(`/catalog/blocks/${blockId}`);
      this.blocks = this.blocks.filter((item) => item.id !== blockId);
    },
    async fetchTemplates() {
      this.templatesLoading = true;
      const { data } = await api.get<CommunityTemplate[]>("/templates");
      this.templates = data;
      this.templatesLoading = false;
    },
    async updateTemplate(
      templateId: number,
      payload: Partial<Pick<CommunityTemplate, "title" | "description" | "category" | "thumbnail_url">> & {
        tags?: string[];
      }
    ) {
      const { data } = await api.put<CommunityTemplate>(`/templates/${templateId}`, payload);
      const index = this.templates.findIndex((item) => item.id === data.id);
      if (index !== -1) {
        this.templates[index] = data;
      }
      return data;
    },
    async deleteTemplate(templateId: number) {
      await api.delete(`/templates/${templateId}`);
      this.templates = this.templates.filter((item) => item.id !== templateId);
    },
    async fetchUsers() {
      this.usersLoading = true;
      const { data } = await api.get<UserAccount[]>("/users");
      this.users = data;
      this.usersLoading = false;
    },
    async updateUser(
      userId: number,
      payload: Partial<Pick<UserAccount, "full_name" | "is_admin" | "is_active">>
    ) {
      const { data } = await api.put<UserAccount>(`/users/${userId}`, payload);
      const index = this.users.findIndex((item) => item.id === data.id);
      if (index !== -1) {
        this.users[index] = data;
      }
      return data;
    },
    async deleteUser(userId: number) {
      await api.delete(`/users/${userId}`);
      this.users = this.users.filter((item) => item.id !== userId);
    }
  }
});
