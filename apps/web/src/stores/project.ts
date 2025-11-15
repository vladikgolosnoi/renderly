import { defineStore } from "pinia";
import api from "@/api/client";
import type { AxiosError } from "axios";
import type {
  BlockDefinition,
  Project,
  ProjectDetail,
  BlockInstance,
  ThemeTemplate,
  ProjectMember,
  ProjectVisibility,
  CommunityTemplate,
  ProjectLocales,
  ProjectDomain,
  AssetItem,
  ProjectRevision,
  ProjectShareLink,
  TemplateComment,
  PublicationInfo
} from "@/types/blocks";
import { useHistory } from "./history";
import { useOnboardingStore } from "./onboarding";

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value ?? {}));

interface ProjectState {
  projects: Project[];
  current: ProjectDetail | null;
  blockCatalog: BlockDefinition[];
  loading: boolean;
  historyCanUndo: boolean;
  historyCanRedo: boolean;
  themeTemplates: ThemeTemplate[];
  members: ProjectMember[];
  templates: CommunityTemplate[];
  locales: string[];
  defaultLocale: string;
  activeLocale: string;
  domains: ProjectDomain[];
  assets: AssetItem[];
  revisions: ProjectRevision[];
  revisionsLoading: boolean;
  shareLinks: ProjectShareLink[];
  templateComments: Record<number, TemplateComment[]>;
  templateCommentsLoading: Record<number, boolean>;
  latestPublication: PublicationInfo | null;
}

const reorderHistory = useHistory<BlockInstance[]>();

const cloneBlocks = (blocks: BlockInstance[]) => JSON.parse(JSON.stringify(blocks));
const defaultTheme = {
  page_bg: "#f8fafc",
  text_color: "#0f172a",
  accent: "#6366f1",
  header_bg: "#ffffff",
  header_text: "#0f172a",
  footer_bg: "#0f172a",
  footer_text: "#ffffff"
};

type PresetBlockConfig = {
  definition_key: string;
  config: Record<string, unknown>;
};

type BundleBlockConfig = {
  definitionKey: string;
  config?: Record<string, unknown>;
};

export interface ProjectPreset {
  slug?: string;
  title: string;
  description?: string;
  theme?: Record<string, string>;
  seo?: { title: string; description: string };
  blocks: PresetBlockConfig[];
}

const DEFAULT_LOCALE = "ru";

const normalizeLocales = (settings?: Project["settings"]): ProjectLocales => {
  const locales = settings?.locales;
  const defaultLocale = (locales?.default_locale ?? DEFAULT_LOCALE).toLowerCase();
  const result = Array.from(
    new Set(
      (locales?.locales ?? [defaultLocale])
        .map((code) => code?.toLowerCase())
        .filter((code): code is string => Boolean(code))
    )
  );
  if (!result.includes(defaultLocale)) {
    result.unshift(defaultLocale);
  }
  return {
    default_locale: defaultLocale,
    locales: result
  };
};

export const useProjectStore = defineStore("project", {
  state: (): ProjectState => ({
    projects: [],
    current: null,
    blockCatalog: [],
    loading: false,
    historyCanUndo: false,
    historyCanRedo: false,
    themeTemplates: [],
    members: [],
    templates: [],
    locales: [DEFAULT_LOCALE],
    defaultLocale: DEFAULT_LOCALE,
    activeLocale: DEFAULT_LOCALE,
    domains: [],
    assets: [],
    revisions: [],
    revisionsLoading: false,
    shareLinks: [],
    templateComments: {},
    templateCommentsLoading: {},
    latestPublication: null
  }),
  getters: {
    canUndo: (state) => state.historyCanUndo,
    canRedo: (state) => state.historyCanRedo
  },
  actions: {
    applyLocales(locales: ProjectLocales) {
      this.locales = locales.locales;
      this.defaultLocale = locales.default_locale;
      if (!this.locales.includes(this.activeLocale)) {
        this.activeLocale = locales.default_locale;
      }
      if (this.current) {
        this.current = {
          ...this.current,
          settings: { ...(this.current.settings ?? {}), locales }
        };
      }
    },
    async fetchProjects() {
      this.loading = true;
      const { data } = await api.get<Project[]>("/projects");
      this.projects = data;
      this.loading = false;
      useOnboardingStore().syncProjects(this.projects);
    },
    async fetchProject(id: number) {
      const { data } = await api.get<ProjectDetail>(`/projects/${id}`);
      this.current = data;
      this.applyLocales(normalizeLocales(data.settings));
      this.resetReorderHistory();
      this.members = [];
      this.domains = [];
      this.revisions = [];
      this.assets = [];
      this.latestPublication = null;
      await this.fetchAssets(data.id);
      useOnboardingStore().syncProjectDetail(data);
    },
    async createProject(payload: Partial<ProjectDetail>) {
      const { data } = await api.post<ProjectDetail>("/projects", payload);
      this.projects.unshift(data);
      this.current = data;
      this.applyLocales(normalizeLocales(data.settings));
      this.resetReorderHistory();
      this.members = [];
      this.domains = [];
      this.revisions = [];
      this.assets = [];
      this.latestPublication = null;
      await this.fetchAssets(data.id);
      useOnboardingStore().markProjectCreated();
      useOnboardingStore().syncProjectDetail(data);
    },
    async renameProject(title: string) {
      if (!this.current) return;
      const normalized = title.trim();
      if (!normalized || normalized === this.current.title) return;
      const { data } = await api.put<ProjectDetail>(`/projects/${this.current.id}`, {
        title: normalized
      });
      this.current = data;
      this.applyLocales(normalizeLocales(data.settings));
      this.projects = this.projects.map((project) =>
        project.id === data.id ? { ...project, title: data.title } : project
      );
      useOnboardingStore().syncProjectDetail(data);
    },
    async deleteProject(projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) return;
      await api.delete(`/projects/${id}`);
      this.projects = this.projects.filter((project) => project.id !== id);
      if (this.current?.id === id) {
        this.current = null;
        this.locales = [DEFAULT_LOCALE];
        this.defaultLocale = DEFAULT_LOCALE;
        this.activeLocale = DEFAULT_LOCALE;
        this.members = [];
        this.domains = [];
        this.revisions = [];
        this.shareLinks = [];
      }
    },
    async loadCatalog() {
      const { data } = await api.get<BlockDefinition[]>("/catalog/blocks");
      this.blockCatalog = data;
    },
    setActiveLocale(locale: string) {
      if (this.locales.includes(locale)) {
        this.activeLocale = locale;
      }
    },
    async fetchProjectLocales(projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) return;
      const { data } = await api.get<ProjectLocales>(`/projects/${id}/locales`);
      this.applyLocales(data);
    },
    async saveLocales(payload: ProjectLocales) {
      if (!this.current) return;
      const { data } = await api.put<ProjectLocales>(
        `/projects/${this.current.id}/locales`,
        payload
      );
      this.applyLocales(data);
    },
    async addLocale(code: string) {
      const normalized = code.trim().toLowerCase();
      if (!normalized || this.locales.includes(normalized)) return;
      await this.saveLocales({
        default_locale: this.defaultLocale,
        locales: [...this.locales, normalized]
      });
    },
    async removeLocale(code: string) {
      const normalized = code.trim().toLowerCase();
      if (normalized === this.defaultLocale || this.locales.length <= 1) return;
      const next = this.locales.filter((item) => item !== normalized);
      await this.saveLocales({
        default_locale: this.defaultLocale,
        locales: next
      });
    },
    async setDefaultLocale(locale: string) {
      if (!this.locales.includes(locale)) return;
      await this.saveLocales({
        default_locale: locale,
        locales: this.locales
      });
      this.activeLocale = locale;
    },
    async addBlock(
      definitionKey: string,
      targetIndex?: number,
      configOverride?: Record<string, unknown>
    ) {
      if (!this.current) return;
      const order =
        typeof targetIndex === "number"
          ? Math.max(0, Math.min(targetIndex, this.current.blocks.length))
          : this.current.blocks.length;
      const existingIds = new Set(this.current.blocks.map((block) => block.id));
      const definition = this.blockCatalog.find((b) => b.key === definitionKey);
      const config = configOverride ?? definition?.default_config ?? {};
      const { data } = await api.post<ProjectDetail>(
        `/projects/${this.current.id}/blocks`,
        {
          definition_key: definitionKey,
          order_index: order,
          config,
          translations: {}
        }
      );
      this.current = data;
      this.applyLocales(normalizeLocales(data.settings));
      this.resetReorderHistory();
      const onboarding = useOnboardingStore();
      onboarding.markBlockAdded();
      onboarding.triggerEditorHints();
      if (typeof targetIndex === "number" && this.current.blocks.length > 1) {
        const insertedBlockIndex = this.current.blocks.findIndex((block) => !existingIds.has(block.id));
        if (insertedBlockIndex !== -1 && insertedBlockIndex !== targetIndex) {
          await this.reorderBlocks(insertedBlockIndex, targetIndex);
        }
      }
    },
    async addBlockBundle(bundle: BundleBlockConfig[], targetIndex?: number) {
      if (!this.current || !bundle.length) return;
      let insertIndex =
        typeof targetIndex === "number" ? Math.max(0, targetIndex) : this.current.blocks.length;
      for (const step of bundle) {
        await this.addBlock(step.definitionKey, insertIndex, step.config);
        insertIndex += 1;
      }
    },
    stageBlockConfig(blockId: number, config: Record<string, unknown>, locale?: string) {
      if (!this.current) return;
      const targetLocale = (locale ?? this.activeLocale ?? this.defaultLocale).toLowerCase();
      const nextBlocks = this.current.blocks.map((block) => {
        if (block.id !== blockId) return block;
        if (targetLocale === this.defaultLocale.toLowerCase()) {
          return { ...block, config: clone(config) };
        }
        const translations = { ...(block.translations ?? {}) };
        translations[targetLocale] = clone(config);
        return { ...block, translations };
      });
      this.current = { ...this.current, blocks: nextBlocks };
    },
    async updateBlock(blockId: number, config: Record<string, unknown>, locale?: string) {
      if (!this.current) return;
      const projectId = this.current.id;
      const targetLocale = (locale ?? this.activeLocale ?? this.defaultLocale).toLowerCase();
      const payload: Record<string, unknown> = {};
      if (targetLocale === this.defaultLocale) {
        payload.config = config;
      } else {
        const block = this.current.blocks.find((item) => item.id === blockId);
        const nextTranslations = { ...(block?.translations ?? {}) };
        nextTranslations[targetLocale] = config;
        payload.translations = nextTranslations;
      }
      const { data } = await api.put<ProjectDetail>(
        `/projects/${projectId}/blocks/${blockId}`,
        payload
      );
      this.current = data;
      this.applyLocales(normalizeLocales(data.settings));
      this.resetReorderHistory();
    },
    async publishCurrent(locale?: string) {
      if (!this.current) return null;
      const lang = locale ?? this.activeLocale ?? this.defaultLocale;
      const { data } = await api.post(`/projects/${this.current.id}/publish`, null, {
        params: { lang }
      });
      this.latestPublication = data.publication;
      return data;
    },
    async fetchLatestPublication(projectId: number) {
      try {
        const { data } = await api.get<PublicationInfo>(`/projects/${projectId}/published/latest`);
        this.latestPublication = data;
        return data;
      } catch (error) {
        const axiosError = error as AxiosError;
        if (axiosError.response?.status === 404) {
          this.latestPublication = null;
          return null;
        }
        throw error;
      }
    },
    async clearLatestPublication() {
      if (!this.current) return;
      await api.delete(`/projects/${this.current.id}/published/latest`);
      this.latestPublication = null;
    },
    async reorderBlocks(from: number, to: number) {
      if (!this.current || from === to) return;
      const blocks = cloneBlocks(this.current.blocks);
      if (from < 0 || from >= blocks.length || to < 0 || to >= blocks.length) return;
      this.captureReorderSnapshot();
      const [moved] = blocks.splice(from, 1);
      blocks.splice(to, 0, moved);
      const normalized = blocks.map((block: BlockInstance, index: number) => ({
        ...block,
        order_index: index
      }));
      this.current = { ...this.current, blocks: normalized };
      await this.persistBlockOrder(normalized);
      this.updateHistoryFlags();
    },
    undo() {
      if (!this.current) return;
      const snapshot = reorderHistory.undo(this.current.blocks);
      if (!snapshot) return;
      this.current = { ...this.current, blocks: snapshot };
      this.updateHistoryFlags();
      void this.persistBlockOrder(snapshot);
    },
    redo() {
      if (!this.current) return;
      const snapshot = reorderHistory.redo(this.current.blocks);
      if (!snapshot) return;
      this.current = { ...this.current, blocks: snapshot };
      this.updateHistoryFlags();
      void this.persistBlockOrder(snapshot);
    },
    captureReorderSnapshot() {
      if (!this.current) return;
      reorderHistory.push(cloneBlocks(this.current.blocks));
      this.updateHistoryFlags();
    },
    resetReorderHistory() {
      reorderHistory.reset();
      this.updateHistoryFlags();
    },
    updateHistoryFlags() {
      this.historyCanUndo = reorderHistory.canUndo();
      this.historyCanRedo = reorderHistory.canRedo();
    },
    async persistBlockOrder(blocks: BlockInstance[]) {
      if (!this.current) return;
      const projectId = this.current.id;
      await Promise.all(
        blocks.map((block, index) =>
          api.put(`/projects/${projectId}/blocks/${block.id}`, {
            order_index: index
          })
        )
      );
    },
    async updateTheme(partialTheme: Record<string, string>) {
      if (!this.current) return;
      const nextTheme = { ...defaultTheme, ...(this.current.theme ?? {}), ...partialTheme };
      this.current = { ...this.current, theme: nextTheme };
      await api.put(`/projects/${this.current.id}`, { theme: nextTheme });
    },
    async fetchThemeTemplates() {
      const { data } = await api.get<ThemeTemplate[]>("/themes");
      this.themeTemplates = data;
    },
    async saveThemeTemplate(name: string, description?: string) {
      if (!this.current) return;
      const payload = {
        name,
        description: description ?? "",
        palette: this.current.theme ?? defaultTheme
      };
      const { data } = await api.post<ThemeTemplate>("/themes", payload);
      this.themeTemplates.unshift(data);
    },
    async fetchMembers(projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) return;
      const { data } = await api.get<ProjectMember[]>(`/projects/${id}/members`);
      this.members = data;
    },
    async fetchShareLinks(projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) return;
      const { data } = await api.get<ProjectShareLink[]>(`/projects/${id}/share-links`);
      this.shareLinks = data;
    },
    async fetchDomains(projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) return;
      const { data } = await api.get<ProjectDomain[]>(`/projects/${id}/domains`);
      this.domains = data;
    },
    async createDomain(hostname: string) {
      if (!this.current) return;
      const { data } = await api.post<ProjectDomain>(`/projects/${this.current.id}/domains`, {
        hostname
      });
      this.domains = [...this.domains, data];
    },
    async verifyDomain(domainId: number) {
      if (!this.current) return;
      const { data } = await api.post<ProjectDomain>(
        `/projects/${this.current.id}/domains/${domainId}/verify`
      );
      this.domains = this.domains.map((domain) => (domain.id === domainId ? data : domain));
    },
    async deleteDomain(domainId: number) {
      if (!this.current) return;
      await api.delete(`/projects/${this.current.id}/domains/${domainId}`);
      this.domains = this.domains.filter((domain) => domain.id !== domainId);
    },
    async fetchRevisions(projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) return;
      this.revisionsLoading = true;
      try {
        const { data } = await api.get<ProjectRevision[]>(`/projects/${id}/revisions`);
        this.revisions = data;
      } finally {
        this.revisionsLoading = false;
      }
    },
    async restoreRevision(revisionId: number) {
      if (!this.current) return;
      const { data } = await api.post<ProjectDetail>(
        `/projects/${this.current.id}/revisions/${revisionId}/restore`
      );
      this.current = data;
      this.applyLocales(normalizeLocales(data.settings));
      await this.fetchRevisions(this.current.id);
    },
    async fetchAssets(projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) return;
      const { data } = await api.get<AssetItem[]>("/assets", {
        params: { project_id: id }
      });
      this.assets = data;
    },
    async uploadAsset(file: File, projectId?: number) {
      const id = projectId ?? this.current?.id;
      if (!id) {
        throw new Error("Невозможно загрузить файл: проект не выбран");
      }
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<AssetItem>("/assets", form, {
        params: { project_id: id },
        headers: { "Content-Type": "multipart/form-data" }
      });
      this.assets = [data, ...this.assets];
      return data;
    },
    async inviteMember(email: string, role: "viewer" | "editor") {
      if (!this.current) return;
      const { data } = await api.post<ProjectMember>(`/projects/${this.current.id}/members`, {
        email,
        role
      });
      const withoutExisting = this.members.filter((member) => member.id !== data.id);
      this.members = [...withoutExisting, data].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
    },
    async updateMemberRole(memberId: number, role: "viewer" | "editor") {
      if (!this.current) return;
      const { data } = await api.put<ProjectMember>(
        `/projects/${this.current.id}/members/${memberId}`,
        { role }
      );
      this.members = this.members.map((member) => (member.id === memberId ? data : member));
    },
    async removeMember(memberId: number) {
      if (!this.current) return;
      await api.delete(`/projects/${this.current.id}/members/${memberId}`);
      this.members = this.members.filter((member) => member.id !== memberId);
    },
    async createShareLink(options: {
      label?: string;
      expiresInHours?: number | null;
      allowComments?: boolean;
    }) {
      if (!this.current) return null;
      const { data } = await api.post<ProjectShareLink>(
        `/projects/${this.current.id}/share-links`,
        {
          label: options.label,
          expires_in_hours: options.expiresInHours ?? null,
          allow_comments: options.allowComments ?? false
        }
      );
      this.shareLinks = [data, ...this.shareLinks.filter((link) => link.id !== data.id)];
      return data;
    },
    async revokeShareLink(shareId: number) {
      if (!this.current) return;
      await api.delete(`/projects/${this.current.id}/share-links/${shareId}`);
      this.shareLinks = this.shareLinks.filter((link) => link.id !== shareId);
    },
    async updateVisibility(visibility: ProjectVisibility) {
      if (!this.current) return;
      const { data } = await api.put<ProjectDetail>(`/projects/${this.current.id}`, {
        visibility
      });
      this.current = data;
      this.applyLocales(normalizeLocales(data.settings));
    },
    async createProjectFromPreset(preset: ProjectPreset) {
      const baseSlug =
        preset.slug ??
        preset.title
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-+|-+$/g, "");
      const slug = `${baseSlug}-${Date.now()}`;
      await this.createProject({
        title: preset.title,
        slug,
        description: preset.description ?? "",
        theme: preset.theme ?? {},
        settings: {
          ...(preset.seo ? { seo: preset.seo } : {})
        }
      });
      if (!this.current) return;
      for (const block of preset.blocks) {
        await this.addBlock(block.definition_key, undefined, block.config);
      }
    },
    async fetchTemplates(filters?: { category?: string | null; search?: string | null }) {
      const params: Record<string, string> = {};
      if (filters?.category) {
        params.category = filters.category;
      }
      if (filters?.search) {
        params.search = filters.search;
      }
      const axiosConfig = Object.keys(params).length ? { params } : undefined;
      const { data } = await api.get<CommunityTemplate[]>("/templates", axiosConfig);
      this.templates = data;
    },
    async publishTemplate(options: {
      projectId: number;
      title?: string;
      description?: string;
      thumbnailUrl?: string;
      category?: string;
      tags?: string[];
    }) {
      const { data } = await api.post<CommunityTemplate>("/templates", {
        project_id: options.projectId,
        title: options.title,
        description: options.description,
        thumbnail_url: options.thumbnailUrl,
        category: options.category,
        tags: options.tags ?? []
      });
      this.templates = [data, ...this.templates.filter((tmpl) => tmpl.id !== data.id)];
      return data;
    },
    async importTemplate(templateId: number) {
      const { data } = await api.post<ProjectDetail>(`/templates/${templateId}/import`);
      this.projects = [data, ...this.projects.filter((project) => project.id !== data.id)];
      return data;
    },
    async fetchTemplateComments(templateId: number) {
      if (this.templateCommentsLoading[templateId]) {
        return;
      }
      this.templateCommentsLoading = {
        ...this.templateCommentsLoading,
        [templateId]: true
      };
      try {
        const { data } = await api.get<TemplateComment[]>(`/templates/${templateId}/comments`);
        this.templateComments = {
          ...this.templateComments,
          [templateId]: data
        };
      } finally {
        this.templateCommentsLoading = {
          ...this.templateCommentsLoading,
          [templateId]: false
        };
      }
    },
    async addTemplateComment(templateId: number, message: string) {
      const trimmed = message.trim();
      if (!trimmed) {
        return null;
      }
      const { data } = await api.post<TemplateComment>(`/templates/${templateId}/comments`, {
        message: trimmed
      });
      const existing = this.templateComments[templateId] ?? [];
      this.templateComments = {
        ...this.templateComments,
        [templateId]: [data, ...existing]
      };
      const templateIndex = this.templates.findIndex((template) => template.id === templateId);
      if (templateIndex >= 0) {
        const template = this.templates[templateIndex];
        const updated = {
          ...template,
          comment_count: (template.comment_count ?? 0) + 1
        };
        this.templates = [
          ...this.templates.slice(0, templateIndex),
          updated,
          ...this.templates.slice(templateIndex + 1)
        ];
      }
      return data;
    }
  }
});
