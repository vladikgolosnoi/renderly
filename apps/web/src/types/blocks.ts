export interface BlockField {
  key: string;
  label: string;
  type: string;
  required?: boolean;
  description?: string;
  default?: unknown;
  widget?: "asset" | string;
  item_schema?: BlockField[];
}

export interface BlockVariation {
  slug: string;
  name: string;
  description?: string | null;
  badges?: string[];
  preview?: string;
  config: Record<string, unknown>;
}

export interface BlockDefinitionMeta {
  tags?: string[];
  variations?: BlockVariation[];
}

export interface BlockDefinition {
  id?: number;
  key: string;
  name: string;
  category: string;
  description?: string | null;
  version: string;
  schema: BlockField[];
  default_config: Record<string, unknown>;
  ui_meta?: BlockDefinitionMeta | null;
}

export interface BlockTranslations {
  [locale: string]: Record<string, unknown>;
}

export interface BlockInstance {
  id: number;
  definition_key: string;
  order_index: number;
  config: Record<string, unknown>;
  translations?: BlockTranslations;
}

export type ProjectVisibility = "private" | "shared" | "public";

export interface ProjectLocales {
  default_locale: string;
  locales: string[];
}

export interface ProjectSettings extends Record<string, unknown> {
  locales?: ProjectLocales;
}

export interface Project {
  id: number;
  title: string;
  slug: string;
  description?: string | null;
  status: string;
  theme: Record<string, unknown>;
  settings: ProjectSettings;
  visibility: ProjectVisibility;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  blocks: BlockInstance[];
}

export interface PublicationInfo {
  version: string;
  cdn_url: string;
  object_path: string;
  custom_domain_url?: string | null;
}

export interface ProjectMember {
  id: number;
  project_id: number;
  member_id: number;
  email: string;
  role: "viewer" | "editor";
  created_at: string;
}

export interface ThemeTemplate {
  id: number;
  name: string;
  description?: string | null;
  slug: string;
  palette: Record<string, string>;
}

export interface CommunityTemplate {
  id: number;
  title: string;
  description?: string | null;
  thumbnail_url?: string | null;
  owner_name: string;
  category?: string | null;
  tags?: string[] | null;
  downloads?: number;
  comment_count?: number;
  created_at: string;
}

export interface ProjectDomain {
  id: number;
  hostname: string;
  status: string;
  verification_token: string;
  last_checked_at?: string | null;
  last_error?: string | null;
  created_at: string;
}

export interface AssetItem {
  id: number;
  filename: string;
  mime_type: string;
  size_bytes: number;
  url: string;
  thumbnail_url?: string | null;
  created_at: string;
}

export interface ProjectRevision {
  id: number;
  action: string;
  user_name?: string | null;
  diff: ProjectRevisionDiff;
  created_at: string;
}

export interface ProjectRevisionDiff {
  added?: string[];
  removed?: string[];
  changed?: string[];
  theme_changed?: boolean;
}

export interface ProjectShareLink {
  id: number;
  token: string;
  label?: string | null;
  allow_comments: boolean;
  expires_at?: string | null;
  created_at: string;
  created_by?: number | null;
  last_accessed_at?: string | null;
  access_count: number;
  comment_count?: number;
}

export interface ProjectShareComment {
  id: number;
  author_name?: string | null;
  author_email?: string | null;
  message: string;
  created_at: string;
}

export interface TemplateComment {
  id: number;
  author_name?: string | null;
  message: string;
  created_at: string;
}

export interface UserAccount {
  id: number;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}
