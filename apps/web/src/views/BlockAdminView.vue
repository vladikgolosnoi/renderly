<template>
  <section class="block-admin">
    <header class="hero surface-card">
      <div>
        <p class="eyebrow">Renderly Studio · Admin</p>
        <h2>Центр управления</h2>
        <p>Добавляйте кастомные блоки, модерируйте шаблоны маркетплейса и управляйте аккаунтами.</p>
      </div>
      <button class="primary" type="button" @click="resetForm">Новый блок</button>
    </header>

    <nav class="admin-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: activeTab === tab.id }"
        type="button"
        @click="setActiveTab(tab.id)"
      >
        {{ tab.label }}
      </button>
    </nav>

    <section v-show="activeTab === 'blocks'" class="panel">
      <div class="layout">
        <aside class="list-panel surface-card">
          <div class="list-head">
            <h3>Существующие блоки</h3>
            <p>Нажмите, чтобы отредактировать схему и конфиг.</p>
          </div>
          <ul>
            <li
              v-for="block in store.blocks"
              :key="block.id"
              :class="{ active: form.id === block.id }"
              @click="selectBlock(block)"
            >
              <strong>{{ block.name }}</strong>
              <small>{{ block.key }}</small>
              <span class="meta">{{ block.category }} · v{{ block.version }}</span>
            </li>
          </ul>
        </aside>

        <div class="editor">
          <form class="surface-card form-card" @submit.prevent="save">
            <div class="row">
              <label>
                Key
                <input v-model="form.key" :disabled="!!form.id" required />
              </label>
              <label>
                Название
                <input v-model="form.name" required />
              </label>
            </div>
            <div class="row">
              <label>
                Категория
                <input v-model="form.category" />
              </label>
              <label>
                Версия
                <input v-model="form.version" />
              </label>
            </div>
            <label>
              Описание
              <textarea
                v-model="form.description"
                rows="2"
                placeholder="Кратко опишите назначение блока"
              ></textarea>
            </label>
            <label>
              Schema (JSON)
              <textarea v-model="form.schema" rows="6"></textarea>
            </label>
            <label>
              Default config (JSON)
              <textarea v-model="form.default_config" rows="6"></textarea>
            </label>
            <section class="template-fields">
              <header>
                <div>
                  <p class="field-title">Custom template</p>
                  <small>HTML/Jinja + CSS, которые используются при публикации и в Live Preview.</small>
                </div>
                <span :class="['badge', hasCustomTemplate ? 'success' : 'ghost']">
                  {{ hasCustomTemplate ? "Активен" : "По умолчанию" }}
                </span>
              </header>
              <div class="row template-inputs">
                <label>
                  Template markup (Jinja + helpers)
                  <textarea
                    v-model="form.template_markup"
                    rows="8"
                    placeholder='Например: {{ helpers.text("headline", tag="h2", classes="hero-title") }}'
                    spellcheck="false"
                  ></textarea>
                </label>
                <label>
                  Template styles (CSS)
                  <textarea
                    v-model="form.template_styles"
                    rows="8"
                    placeholder='[data-template-key="{{ form.key || "block-key" }}"] .card { ... }'
                    spellcheck="false"
                  ></textarea>
                </label>
              </div>
              <p class="helper">Подсказки:</p>
              <ul class="helper-list" v-pre>
                <li><code>{{ helpers.text("headline", tag="h2") }}</code> — текстовое поле с inline-редактированием.</li>
                <li><code>{{ helpers.asset("image_url", classes="media") }}</code> — изображение/видео с выбором из медиатеки.</li>
                <li><code>{% for item in helpers.list_items("stats") %}{{ helpers.item_text(item, "value") }}{% endfor %}</code> — цикл по массиву.</li>
              </ul>
            </section>
            <div class="actions">
              <button type="submit" class="primary">
                {{ form.id ? "Сохранить изменения" : "Создать блок" }}
              </button>
              <button type="button" class="ghost" @click="resetForm">
                Очистить
              </button>
              <button
                v-if="form.id"
                type="button"
                class="danger"
                @click="remove"
              >
                Удалить
              </button>
            </div>
          </form>
          <div class="surface-card preview">
            <h3>Предпросмотр конфигурации</h3>
            <p>Блок: <strong>{{ form.name || "—" }}</strong></p>
            <p>Описание: {{ form.description || "—" }}</p>
            <pre>{{ prettyDefaultConfig }}</pre>
          </div>
        </div>
      </div>
    </section>

    <section v-show="activeTab === 'templates'" class="panel template-panel">
      <div class="management-grid">
        <aside class="list-panel surface-card">
          <div class="list-head">
            <h3>Шаблоны маркетплейса</h3>
            <p>Выберите шаблон для редактирования текста, тегов и категорий.</p>
          </div>
          <ul>
            <li
              v-for="template in store.templates"
              :key="template.id"
              :class="{ active: templateForm.id === template.id }"
              @click="selectTemplate(template)"
            >
              <strong>{{ template.title }}</strong>
              <small>{{ template.owner_name }}</small>
              <span class="meta">
                {{ template.category || "Без категории" }} · {{ template.downloads || 0 }} скачиваний
              </span>
            </li>
          </ul>
        </aside>
        <div class="surface-card form-view">
          <h3>Карточка шаблона</h3>
          <p v-if="!templateForm.id" class="placeholder">
            Выберите шаблон слева, чтобы отредактировать описание или удалить его из маркетплейса.
          </p>
          <form v-else @submit.prevent="saveTemplateDetails">
            <label>
              Название
              <input v-model="templateForm.title" required />
            </label>
            <label>
              Описание
              <textarea v-model="templateForm.description" rows="3"></textarea>
            </label>
            <div class="row">
              <label>
                Категория
                <input v-model="templateForm.category" placeholder="events, product" />
              </label>
              <label>
                Thumbnail URL
                <input v-model="templateForm.thumbnail_url" placeholder="https://..." />
              </label>
            </div>
            <label>
              Теги (через запятую)
              <input v-model="templateForm.tags" placeholder="hero, landing, ai" />
            </label>
            <div class="actions">
              <button type="submit" class="primary">Сохранить шаблон</button>
              <button type="button" class="ghost" @click="resetTemplateForm">Сбросить</button>
              <button type="button" class="danger" @click="deleteTemplate">Удалить</button>
            </div>
          </form>
        </div>
      </div>
    </section>

    <section v-show="activeTab === 'accounts'" class="panel accounts-panel">
      <div class="management-grid">
        <aside class="list-panel surface-card">
          <div class="list-head">
            <h3>Аккаунты пользователей</h3>
            <p>Назначайте админов и блокируйте доступ.</p>
          </div>
          <ul>
            <li
              v-for="user in store.users"
              :key="user.id"
              :class="{ active: userForm.id === user.id }"
              @click="selectUser(user)"
            >
              <strong>{{ user.full_name || "Без имени" }}</strong>
              <small>{{ user.email }}</small>
              <div class="badges">
                <span v-if="user.is_admin" class="badge success">Админ</span>
                <span v-if="!user.is_active" class="badge danger">Заблокирован</span>
              </div>
            </li>
          </ul>
        </aside>
        <div class="surface-card form-view">
          <h3>Данные аккаунта</h3>
          <p v-if="!userForm.id" class="placeholder">
            Выберите пользователя слева, чтобы изменить имя, статус или роль.
          </p>
          <form v-else @submit.prevent="saveUser">
            <label>
              Email
              <input v-model="userForm.email" disabled />
            </label>
            <label>
              Имя
              <input v-model="userForm.full_name" placeholder="Имя Фамилия" />
            </label>
            <div class="switch-row">
              <label class="checkbox">
                <input type="checkbox" v-model="userForm.is_admin" />
                <span>Администратор</span>
              </label>
              <label class="checkbox">
                <input type="checkbox" v-model="userForm.is_active" />
                <span>Активен</span>
              </label>
            </div>
            <div class="actions">
              <button type="submit" class="primary">Сохранить</button>
              <button type="button" class="ghost" @click="resetUserForm">Сбросить</button>
              <button type="button" class="danger" @click="deleteUser">Удалить</button>
            </div>
          </form>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useBlockAdminStore } from "@/stores/blockAdmin";
import type { BlockDefinition, CommunityTemplate, UserAccount } from "@/types/blocks";

const tabs = [
  { id: "blocks", label: "Блоки" },
  { id: "templates", label: "Шаблоны" },
  { id: "accounts", label: "Аккаунты" }
] as const;

type AdminTab = (typeof tabs)[number]["id"];

const activeTab = ref<AdminTab>("blocks");

const store = useBlockAdminStore();

type BlockFormState = {
  id: number | null;
  key: string;
  name: string;
  category: string;
  description: string;
  version: string;
  schema: string;
  default_config: string;
  template_markup: string;
  template_styles: string;
};

const form = reactive<BlockFormState>({
  id: null,
  key: "",
  name: "",
  category: "content",
  description: "",
  version: "1.0.0",
  schema: "[]",
  default_config: "{}",
  template_markup: "",
  template_styles: ""
});

const templateForm = reactive({
  id: null as number | null,
  title: "",
  description: "",
  category: "",
  thumbnail_url: "",
  tags: ""
});

const userForm = reactive({
  id: null as number | null,
  email: "",
  full_name: "",
  is_admin: false,
  is_active: true
});

const prettyDefaultConfig = computed(() => {
  try {
    return JSON.stringify(JSON.parse(form.default_config || "{}"), null, 2);
  } catch {
    return "⚠️ Ошибка парсинга JSON";
  }
});

const hasCustomTemplate = computed(() => {
  return Boolean(form.template_markup.trim() || form.template_styles.trim());
});

onMounted(() => {
  store.fetchBlocks();
  store.fetchTemplates();
  store.fetchUsers();
});

function setActiveTab(tab: AdminTab) {
  activeTab.value = tab;
}

function selectBlock(block: BlockDefinition) {
  form.id = block.id ?? null;
  form.key = block.key;
  form.name = block.name;
  form.category = block.category;
  form.description = (block as any).description ?? "";
  form.version = block.version;
  form.schema = JSON.stringify(block.schema, null, 2);
  form.default_config = JSON.stringify(block.default_config, null, 2);
  form.template_markup = block.template_markup ?? "";
  form.template_styles = block.template_styles ?? "";
}

function resetForm() {
  form.id = null;
  form.key = "";
  form.name = "";
  form.category = "content";
  form.description = "";
  form.version = "1.0.0";
  form.schema = "[]";
  form.default_config = "{}";
  form.template_markup = "";
  form.template_styles = "";
}

async function save() {
  let parsedSchema;
  let parsedConfig;
  try {
    parsedSchema = JSON.parse(form.schema || "[]");
    parsedConfig = JSON.parse(form.default_config || "{}");
  } catch {
    alert("Проверьте JSON в schema/default_config");
    return;
  }

  const payload = {
    key: form.key,
    name: form.name,
    category: form.category,
    description: form.description,
    version: form.version,
    schema: parsedSchema,
    default_config: parsedConfig,
    template_markup: form.template_markup.trim() || null,
    template_styles: form.template_styles.trim() || null
  };

  if (form.id) {
    await store.updateBlock(form.id, payload);
  } else {
    const created = await store.createBlock(payload);
    form.id = created.id ?? null;
  }
}

async function remove() {
  if (!form.id) return;
  if (!confirm("Удалить блок?")) return;
  await store.deleteBlock(form.id);
  resetForm();
}

function selectTemplate(template: CommunityTemplate) {
  templateForm.id = template.id;
  templateForm.title = template.title;
  templateForm.description = template.description ?? "";
  templateForm.category = template.category ?? "";
  templateForm.thumbnail_url = template.thumbnail_url ?? "";
  templateForm.tags = (template.tags ?? []).join(", ");
}

function resetTemplateForm() {
  templateForm.id = null;
  templateForm.title = "";
  templateForm.description = "";
  templateForm.category = "";
  templateForm.thumbnail_url = "";
  templateForm.tags = "";
}

async function saveTemplateDetails() {
  if (!templateForm.id) return;
  const tags = templateForm.tags
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
  await store.updateTemplate(templateForm.id, {
    title: templateForm.title,
    description: templateForm.description,
    category: templateForm.category,
    thumbnail_url: templateForm.thumbnail_url,
    tags
  });
}

async function deleteTemplate() {
  if (!templateForm.id) return;
  if (!confirm("Удалить шаблон из маркетплейса?")) return;
  await store.deleteTemplate(templateForm.id);
  resetTemplateForm();
}

function selectUser(user: UserAccount) {
  userForm.id = user.id;
  userForm.email = user.email;
  userForm.full_name = user.full_name ?? "";
  userForm.is_admin = user.is_admin;
  userForm.is_active = user.is_active;
}

function resetUserForm() {
  userForm.id = null;
  userForm.email = "";
  userForm.full_name = "";
  userForm.is_admin = false;
  userForm.is_active = true;
}

async function saveUser() {
  if (!userForm.id) return;
  await store.updateUser(userForm.id, {
    full_name: userForm.full_name,
    is_admin: userForm.is_admin,
    is_active: userForm.is_active
  });
}

async function deleteUser() {
  if (!userForm.id) return;
  if (!confirm("Удалить аккаунт? Действие необратимо.")) return;
  await store.deleteUser(userForm.id);
  resetUserForm();
}
</script>

<style scoped>
.block-admin {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 24px;
}

.hero h2 {
  margin: 8px 0 4px;
}

.hero p {
  margin: 0;
  color: var(--text-secondary);
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.admin-tabs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.admin-tabs button {
  border-radius: 999px;
  border: 1px solid transparent;
  background: var(--accent-muted);
  color: var(--text-secondary);
  padding: 8px 18px;
  cursor: pointer;
  font-weight: 600;
}

.admin-tabs button.active {
  border-color: var(--accent);
  color: #fff;
  background: linear-gradient(120deg, var(--accent), var(--accent-strong));
  box-shadow: 0 10px 24px rgba(79, 70, 229, 0.25);
}

.panel {
  display: block;
}

.layout,
.management-grid {
  display: grid;
  grid-template-columns: minmax(260px, 340px) 1fr;
  gap: 24px;
  align-items: stretch;
}

.list-panel {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  overflow: hidden;
}

.list-head h3 {
  margin: 0;
}

.list-head p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.list-panel ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  flex: 1 1 auto;
  min-height: 0;
  padding-right: 6px;
}

.list-panel li {
  border: 1px solid var(--stroke);
  border-radius: 18px;
  padding: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.list-panel li.active {
  border-color: var(--accent);
  background: var(--accent-muted);
}

.list-panel li strong {
  font-size: 1rem;
}

.list-panel li small {
  color: var(--text-secondary);
}

.meta {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.editor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 360px);
  gap: 16px;
}

.form-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
}

.row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

input,
textarea {
  border-radius: 14px;
  border: 1px solid var(--stroke);
  padding: 10px 12px;
  font-family: inherit;
  font-size: 1rem;
  background: var(--bg-soft);
  color: var(--text-primary);
}

textarea {
  resize: vertical;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.primary,
.ghost,
.danger {
  border-radius: 14px;
  border: none;
  font-weight: 600;
  padding: 10px 18px;
  cursor: pointer;
}

.primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: #fff;
  box-shadow: 0 16px 32px rgba(79, 70, 229, 0.3);
}

.ghost {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
}

.danger {
  background: #ef4444;
  color: #fff;
}

.preview {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview pre {
  margin: 0;
  background: #0f172a;
  color: #f8fafc;
  border-radius: 14px;
  padding: 12px;
  overflow-x: auto;
  font-size: 0.85rem;
}

.template-fields {
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8fafc;
}

.template-fields header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.template-fields .field-title {
  margin: 0;
  font-weight: 600;
}

.template-inputs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.template-inputs textarea {
  min-height: 180px;
  font-family: "JetBrains Mono", Consolas, monospace;
}

.helper-list {
  margin: 0;
  padding-left: 18px;
  font-size: 0.85rem;
  color: #475569;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.helper-list code {
  background: #0f172a;
  color: #f8fafc;
  border-radius: 6px;
  padding: 2px 6px;
}

.form-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-view form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.placeholder {
  margin: 0;
  color: var(--text-secondary);
}

.switch-row {
  display: flex;
  gap: 18px;
}

.checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
}

.checkbox input {
  width: 18px;
  height: 18px;
}

.badges {
  display: flex;
  gap: 6px;
}

.badge {
  border-radius: 999px;
  font-size: 0.75rem;
  padding: 2px 8px;
  border: 1px solid transparent;
}

.badge.success {
  background: rgba(34, 197, 94, 0.15);
  color: #15803d;
  border-color: rgba(34, 197, 94, 0.2);
}

.badge.danger {
  background: rgba(239, 68, 68, 0.15);
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.2);
}

@media (max-width: 1024px) {
  .layout,
  .management-grid {
    grid-template-columns: 1fr;
  }

  .editor {
    grid-template-columns: 1fr;
  }
}
</style>
