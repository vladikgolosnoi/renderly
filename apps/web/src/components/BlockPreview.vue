<template>
  <section class="preview-block" :class="[`preview-${block.definition_key}`]">
    <template v-if="block.definition_key === 'hero'">
      <div class="hero">
        <div class="hero-copy">
          <InlineEditableField
            class="bare eyebrow"
            label="Eyebrow"
            :value="textValue('eyebrow')"
            placeholder="Добавьте плашку"
            @change="updateField('eyebrow', $event)"
          />
          <InlineEditableField
            class="bare headline"
            label="Headline"
            :value="textValue('headline')"
            placeholder="Заголовок"
            @change="updateField('headline', $event)"
          />
          <InlineEditableField
            class="bare subheading"
            label="Subheading"
            :value="textValue('subheading')"
            placeholder="Описание"
            multiline
            @change="updateField('subheading', $event)"
          />
          <div class="cta-row">
            <InlineEditableField
              class="bare cta-label"
              label="CTA label"
              :value="textValue('cta_label')"
              placeholder="Подпись кнопки"
              @change="updateField('cta_label', $event)"
            />
            <InlineEditableField
              class="bare cta-url"
              label="CTA url"
              :value="textValue('cta_url')"
              placeholder="https://"
              @change="updateField('cta_url', $event)"
            />
          </div>
        </div>
        <figure class="hero-media" @click.stop="requestAsset('image_url', 'Hero media')">
          <img :src="assetValue('image_url')" alt="Hero media" />
          <button type="button">Сменить медиа</button>
        </figure>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'speaker-highlight'">
      <div class="speaker-card" :class="speakerLayoutClass" :style="speakerCardStyle">
        <div class="speaker-content">
          <span v-if="textValue('badge_label')" class="speaker-badge" :style="{ background: speakerBadgeColor }">
            <InlineEditableField
              class="bare badge-field"
              label="Badge"
              :value="textValue('badge_label')"
              placeholder="Бейдж"
              @change="updateField('badge_label', $event)"
            />
          </span>
          <InlineEditableField
            class="bare eyebrow"
            label="Eyebrow"
            :value="textValue('eyebrow')"
            placeholder="Eyebrow"
            @change="updateField('eyebrow', $event)"
          />
          <InlineEditableField
            class="bare headline"
            label="Headline"
            :value="textValue('headline')"
            placeholder="Заголовок"
            @change="updateField('headline', $event)"
          />
          <InlineEditableField
            class="bare subtitle"
            label="Subtitle"
            :value="textValue('subtitle')"
            placeholder="Подзаголовок"
            @change="updateField('subtitle', $event)"
          />
          <InlineEditableField
            class="bare description"
            label="Description"
            :value="textValue('description')"
            placeholder="Описание"
            multiline
            @change="updateField('description', $event)"
          />
          <div v-if="speakerChipsList.length" class="speaker-chips">
            <span v-for="chip in speakerChipsList" :key="chip">{{ chip }}</span>
          </div>
          <div v-if="speakerTags.length" class="speaker-tags">
            <span v-for="(tag, index) in speakerTags" :key="`tag-${index}`">
              <strong>{{ stringValue(tag.icon) }}</strong>
              {{ stringValue(tag.title) }}
            </span>
          </div>
          <div class="speaker-cta">
            <button type="button">
              <InlineEditableField
                class="bare primary-cta"
                label="Primary CTA"
                :value="textValue('cta_primary_label')"
                placeholder="Главная кнопка"
                @change="updateField('cta_primary_label', $event)"
              />
            </button>
            <button type="button" class="ghost">
              <InlineEditableField
                class="bare secondary-cta"
                label="Secondary CTA"
                :value="textValue('cta_secondary_label')"
                placeholder="Вторая кнопка"
                @change="updateField('cta_secondary_label', $event)"
              />
            </button>
          </div>
          <div v-if="speakerStats.length" class="speaker-stats">
            <article v-for="(stat, index) in speakerStats" :key="`stat-${index}`">
              <strong>{{ stringValue(stat.value) }}</strong>
              <small>{{ stringValue(stat.label) }}</small>
            </article>
          </div>
        </div>
        <div class="speaker-avatar" :class="speakerAvatarShape" @click.stop="requestAsset('avatar', 'Фото спикера')">
          <img :src="textValue('avatar') || avatarPlaceholder" :alt="textValue('headline') || 'speaker avatar'" />
        </div>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'aurora-showcase'">
      <section class="aurora-preview">
        <div class="aurora-card" :style="auroraCardStyle">
          <span v-if="textValue('badge_label')" class="aurora-badge" :style="{ background: auroraBadgeColor }">
            <InlineEditableField
              class="bare"
              label="Badge"
              :value="textValue('badge_label')"
              placeholder="Badge"
              @change="updateField('badge_label', $event)"
            />
          </span>
          <InlineEditableField
            class="bare eyebrow"
            label="Eyebrow"
            :value="textValue('eyebrow')"
            placeholder="Eyebrow"
            @change="updateField('eyebrow', $event)"
          />
          <InlineEditableField
            class="bare aurora-headline"
            label="Headline"
            :value="textValue('headline')"
            placeholder="Заголовок"
            @change="updateField('headline', $event)"
          />
          <InlineEditableField
            class="bare aurora-description"
            label="Description"
            :value="textValue('description')"
            placeholder="Описание"
            multiline
            @change="updateField('description', $event)"
          />
          <div class="aurora-cta">
            <button type="button" class="primary">
              <InlineEditableField
                class="bare"
                label="Primary CTA"
                :value="textValue('primary_cta_label')"
                placeholder="Primary CTA"
                @change="updateField('primary_cta_label', $event)"
              />
            </button>
            <button type="button" class="ghost">
              <InlineEditableField
                class="bare"
                label="Secondary CTA"
                :value="textValue('secondary_cta_label')"
                placeholder="Secondary CTA"
                @change="updateField('secondary_cta_label', $event)"
              />
            </button>
          </div>
          <div class="aurora-stats" v-if="auroraStats.length">
            <article v-for="(stat, index) in auroraStats" :key="`aurora-stat-${index}`">
              <InlineEditableField
                class="bare stat-value"
                label="Value"
                :value="stringValue(stat.value)"
                placeholder="+120%"
                @change="updateListField('stats', index, 'value', $event)"
              />
              <InlineEditableField
                class="bare stat-label"
                label="Label"
                :value="stringValue(stat.label)"
                placeholder="Metric"
                @change="updateListField('stats', index, 'label', $event)"
              />
            </article>
          </div>
        </div>
        <figure
          class="aurora-media"
          :class="`shape-${auroraImageShape}`"
          @click.stop="requestAsset('image_url', 'Aurora media')"
        >
          <img :src="assetValue('image_url')" alt="Aurora media" />
          <button type="button">Сменить медиа</button>
        </figure>
      </section>
    </template>

    <template v-else-if="block.definition_key === 'feature-grid'">
      <div class="feature-grid">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="Название блока"
          @change="updateField('title', $event)"
        />
        <div class="grid">
          <article v-for="(feature, index) in listValue('features')" :key="`feature-${index}`">
            <InlineEditableField
              class="bare feature-title"
              label="Feature title"
              :value="stringValue(feature.title)"
              placeholder="Заголовок"
              @change="updateListField('features', index, 'title', $event)"
            />
            <InlineEditableField
              class="bare feature-description"
              label="Feature description"
              :value="stringValue(feature.description)"
              placeholder="Описание"
              multiline
              @change="updateListField('features', index, 'description', $event)"
            />
          </article>
        </div>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'media-gallery'">
      <div class="media-gallery">
        <figure v-for="(item, index) in listValue('images')" :key="`image-${index}`">
          <img :src="stringValue(item.url) || placeholderImage" :alt="stringValue(item.alt) || 'preview image'" />
          <figcaption>
            <InlineEditableField
              class="bare caption"
              label="Caption"
              :value="stringValue(item.caption)"
              placeholder="Подпись"
              @change="updateListField('images', index, 'caption', $event)"
            />
            <button type="button" @click.stop="requestListAsset('images', index, 'url', 'Gallery image')">
              Выбрать медиа
            </button>
          </figcaption>
        </figure>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'cta'">
      <div class="cta-block">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="Призыв"
          @change="updateField('title', $event)"
        />
        <InlineEditableField
          class="bare description"
          label="Description"
          :value="textValue('description')"
          placeholder="Дополнительный текст"
          multiline
          @change="updateField('description', $event)"
        />
        <div class="cta-actions">
          <InlineEditableField
            class="bare action-label"
            label="Action label"
            :value="textValue('action_label')"
            placeholder="Подпись кнопки"
            @change="updateField('action_label', $event)"
          />
          <InlineEditableField
            class="bare action-url"
            label="Action url"
            :value="textValue('action_url')"
            placeholder="https://"
            @change="updateField('action_url', $event)"
          />
        </div>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'form'">
      <div class="form-block">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="Название формы"
          @change="updateField('title', $event)"
        />
        <InlineEditableField
          class="bare description"
          label="Description"
          :value="textValue('description')"
          placeholder="Описание"
          multiline
          @change="updateField('description', $event)"
        />
        <div class="form-fields">
          <label v-for="(field, index) in listValue('fields')" :key="`field-${index}`">
            <span>Поле #{{ index + 1 }}</span>
            <InlineEditableField
              class="bare field-label"
              :label="`Field ${index}`"
              :value="stringValue(field)"
              placeholder="Название поля"
              @change="updateListValue('fields', index, $event)"
            />
          </label>
        </div>
        <InlineEditableField
          class="bare success"
          label="Success message"
          :value="textValue('success_message')"
          placeholder="Сообщение об успехе"
          @change="updateField('success_message', $event)"
        />
      </div>
    </template>

    <template v-else-if="block.definition_key === 'price-list'">
      <div class="price-list">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="Заголовок"
          @change="updateField('title', $event)"
        />
        <div class="plans">
          <article v-for="(plan, index) in listValue('plans')" :key="`plan-${index}`">
            <InlineEditableField
              class="bare plan-name"
              label="Plan name"
              :value="stringValue(plan.name)"
              placeholder="Название тарифа"
              @change="updateListField('plans', index, 'name', $event)"
            />
            <InlineEditableField
              class="bare plan-price"
              label="Plan price"
              :value="stringValue(plan.price)"
              placeholder="Цена"
              @change="updateListField('plans', index, 'price', $event)"
            />
            <ul>
              <li v-for="(feature, featIndex) in arrayValue(plan.features)" :key="`plan-${index}-feature-${featIndex}`">
                <InlineEditableField
                  class="bare plan-feature"
                  :label="`Feature ${featIndex}`"
                  :value="stringValue(feature)"
                  placeholder="Преимущество"
                  @change="updateNestedListValue(['plans', index, 'features'], featIndex, $event)"
                />
              </li>
            </ul>
          </article>
        </div>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'schedule'">
      <div class="schedule">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="Расписание"
          @change="updateField('title', $event)"
        />
        <ul>
          <li v-for="(item, index) in listValue('items')" :key="`schedule-${index}`">
            <InlineEditableField
              class="bare time"
              label="Time"
              :value="stringValue(item.time)"
              placeholder="09:00"
              @change="updateListField('items', index, 'time', $event)"
            />
            <div>
              <InlineEditableField
                class="bare topic"
                label="Topic"
                :value="stringValue(item.topic)"
                placeholder="Тема"
                @change="updateListField('items', index, 'topic', $event)"
              />
              <InlineEditableField
                class="bare speaker"
                label="Speaker"
                :value="stringValue(item.speaker)"
                placeholder="Спикер"
                @change="updateListField('items', index, 'speaker', $event)"
              />
            </div>
          </li>
        </ul>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'team'">
      <div class="team">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="Команда"
          @change="updateField('title', $event)"
        />
        <div class="members">
          <article v-for="(member, index) in listValue('members')" :key="`member-${index}`">
            <div class="avatar" @click.stop="requestListAsset('members', index, 'photo', 'Фото участника')">
              <img :src="stringValue(member.photo) || avatarPlaceholder" alt="" />
              <button type="button">Сменить</button>
            </div>
            <InlineEditableField
              class="bare member-name"
              label="Name"
              :value="stringValue(member.name)"
              placeholder="Имя"
              @change="updateListField('members', index, 'name', $event)"
            />
            <InlineEditableField
              class="bare member-role"
              label="Role"
              :value="stringValue(member.role)"
              placeholder="Роль"
              @change="updateListField('members', index, 'role', $event)"
            />
          </article>
        </div>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'testimonials'">
      <div class="testimonials">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="Отзывы"
          @change="updateField('title', $event)"
        />
        <div class="quotes">
          <blockquote v-for="(item, index) in listValue('testimonials')" :key="`quote-${index}`">
            <InlineEditableField
              class="bare quote"
              label="Quote"
              :value="stringValue(item.quote)"
              placeholder="Текст отзыва"
              multiline
              @change="updateListField('testimonials', index, 'quote', $event)"
            />
            <InlineEditableField
              class="bare author"
              label="Name"
              :value="stringValue(item.name)"
              placeholder="Автор"
              @change="updateListField('testimonials', index, 'name', $event)"
            />
          </blockquote>
        </div>
      </div>
    </template>

    <template v-else-if="block.definition_key === 'faq'">
      <div class="faq">
        <InlineEditableField
          class="bare title"
          label="Title"
          :value="textValue('title')"
          placeholder="FAQ"
          @change="updateField('title', $event)"
        />
        <div class="items">
          <details v-for="(item, index) in listValue('items')" :key="`faq-${index}`" open>
            <summary>
              <InlineEditableField
                class="bare question"
                label="Question"
                :value="stringValue(item.question)"
                placeholder="Вопрос"
                @change="updateListField('items', index, 'question', $event)"
              />
            </summary>
            <InlineEditableField
              class="bare answer"
              label="Answer"
              :value="stringValue(item.answer)"
              placeholder="Ответ"
              multiline
              @change="updateListField('items', index, 'answer', $event)"
            />
          </details>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="generic">
        <strong>{{ fallbackTitle }}</strong>
        <p>Этот блок пока отображается в виде заглушки.</p>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import InlineEditableField from "@/components/InlineEditableField.vue";
import type { AssetItem, BlockDefinition, BlockInstance } from "@/types/blocks";

const props = defineProps<{
  block: BlockInstance;
  definition?: BlockDefinition | null;
  activeLocale: string;
  defaultLocale: string;
  quickAssets?: AssetItem[];
  theme?: Record<string, string>;
}>();

const emit = defineEmits<{
  "inline-edit": [{ blockId: number; fieldKey: string; value: string; path?: (string | number)[] }];
  "request-asset": [{ blockId: number; fieldKey: string; label: string; path: (string | number)[] }];
}>();

const payload = computed(() => localizedConfig());
const placeholderImage = "https://placehold.co/600x400/e2e8f0/94a3b8?text=media";
const avatarPlaceholder = "https://placehold.co/160x160/fff/94a3b8?text=avatar";

const fallbackTitle = computed(() => props.definition?.name ?? props.block.definition_key);
const speakerCardStyle = computed(() => {
  const bg = textValue("bg_color") || "#111827";
  const start = textValue("gradient_start");
  const end = textValue("gradient_end");
  const gradient = start && end ? `linear-gradient(135deg, ${start}, ${end})` : null;
  return {
    background: gradient || bg,
    color: textValue("text_color") || "#f8fafc",
    boxShadow: textValue("card_shadow") || "0 30px 70px rgba(15, 23, 42, 0.4)"
  };
});
const speakerBadgeColor = computed(() => textValue("badge_color") || "#f9769b");
const speakerLayoutClass = computed(() => {
  const layout = textValue("layout").toLowerCase();
  return layout === "right" ? "layout-right" : "layout-left";
});
const speakerChipsList = computed(() => {
  const raw = textValue("chips");
  if (!raw) return [];
  return raw.split(",").map((chip) => chip.trim()).filter(Boolean);
});
const speakerAvatarShape = computed(() => {
  const shape = textValue("avatar_shape").toLowerCase();
  return shape === "square" ? "shape-square" : "shape-circle";
});
const speakerStats = computed(() => listValue("stats"));
const speakerTags = computed(() => listValue("tags"));
const auroraGradient = computed(() => {
  const start = textValue("gradient_start") || "#312e81";
  const end = textValue("gradient_end") || "#111827";
  return `linear-gradient(135deg, ${start}, ${end})`;
});
const auroraCardStyle = computed(() => ({
  background: auroraGradient.value,
  color: textValue("card_text_color") || "#ffffff",
  boxShadow: "0 25px 55px rgba(15, 23, 42, 0.35)"
}));
const auroraBadgeColor = computed(() => textValue("badge_color") || "#f472b6");
const auroraStats = computed(() => listValue("stats"));
const auroraImageShape = computed(() => {
  const shape = textValue("image_shape").toLowerCase();
  return shape === "circle" ? "circle" : "rounded";
});

function localizedConfig() {
  const config = props.block.config ?? {};
  if (props.activeLocale === props.defaultLocale) {
    return config;
  }
  return props.block.translations?.[props.activeLocale] ?? config;
}

function textValue(key: string) {
  const value = (payload.value as Record<string, unknown>)[key];
  return typeof value === "string" ? value : "";
}

function stringValue(input: unknown) {
  if (typeof input === "string") return input;
  return "";
}

function assetValue(key: string) {
  return textValue(key) || placeholderImage;
}

function listValue(key: string) {
  const value = (payload.value as Record<string, unknown>)[key];
  return Array.isArray(value) ? value : [];
}

function arrayValue(value: unknown) {
  return Array.isArray(value) ? value : [];
}

function updateField(fieldKey: string, value: string, path: (string | number)[] = [fieldKey]) {
  emit("inline-edit", {
    blockId: props.block.id,
    fieldKey,
    value,
    path
  });
}

function updateListField(listKey: string, index: number, subKey: string, value: string) {
  updateField(`${listKey}.${subKey}`, value, [listKey, index, subKey]);
}

function updateListValue(listKey: string, index: number, value: string) {
  updateField(`${listKey}[${index}]`, value, [listKey, index]);
}

function updateNestedListValue(basePath: (string | number)[], index: number, value: string) {
  updateField(basePath.join("."), value, [...basePath, index]);
}

function requestAsset(fieldKey: string, label: string, path: (string | number)[] = [fieldKey]) {
  emit("request-asset", {
    blockId: props.block.id,
    fieldKey,
    label,
    path
  });
}

function requestListAsset(listKey: string, index: number, subKey: string, label: string) {
  requestAsset(`${listKey}.${subKey}`, label, [listKey, index, subKey]);
}
</script>

<style scoped>
.preview-block {
  border-radius: 32px;
  padding: 32px;
  background: #fff;
  box-shadow: 0 25px 55px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-block :deep(.label) {
  display: none;
}

.preview-block :deep(.editable) {
  background: transparent;
  border: none;
  padding: 0;
  min-height: 0;
  font-size: inherit;
  color: inherit;
}

.preview-block :deep(.editable.empty::before) {
  color: rgba(15, 23, 42, 0.35);
}

.preview-block :deep(.editable.focused) {
  outline: 2px solid rgba(99, 102, 241, 0.35);
  border-radius: 8px;
  padding: 2px 4px;
}

.hero {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 32px;
  align-items: center;
}

.hero-copy .eyebrow :deep(.editable) {
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-size: 0.85rem;
  color: #94a3b8;
}

.hero-copy .headline :deep(.editable) {
  font-size: 2.4rem;
  font-weight: 700;
  line-height: 1.15;
}

.hero-copy .subheading :deep(.editable) {
  font-size: 1.1rem;
  line-height: 1.5;
  color: #475569;
}

.cta-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hero-media {
  position: relative;
  margin: 0;
}

.hero-media img {
  width: 100%;
  border-radius: 28px;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.2);
  display: block;
}

.hero-media button {
  position: absolute;
  right: 16px;
  bottom: 16px;
  border: none;
  border-radius: 999px;
  padding: 10px 16px;
  background: rgba(15, 23, 42, 0.8);
  color: #fff;
  cursor: pointer;
}

.feature-grid .grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 18px;
}

.feature-grid article {
  border-radius: 20px;
  padding: 18px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.media-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.media-gallery figure {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.media-gallery img {
  width: 100%;
  border-radius: 18px;
  object-fit: cover;
  min-height: 180px;
}

.media-gallery button {
  align-self: flex-start;
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 999px;
  padding: 6px 12px;
  background: transparent;
  color: #4f46e5;
  cursor: pointer;
}

.cta-block {
  text-align: center;
}

.cta-block :deep(.editable) {
  text-align: center;
}

.form-block .form-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-block label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 12px;
}

.price-list .plans {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}

.price-list article {
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 20px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: center;
}

.price-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.schedule ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.schedule li {
  display: flex;
  gap: 12px;
  justify-content: space-between;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 12px 16px;
}

.team .members {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.team article {
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 20px;
  padding: 16px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.team .avatar {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto;
}

.team .avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.team .avatar button {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  border: none;
  border-radius: 999px;
  padding: 4px 10px;
  background: rgba(15, 23, 42, 0.8);
  color: #fff;
  cursor: pointer;
}

.testimonials .quotes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.testimonials blockquote {
  margin: 0;
  padding: 14px 18px;
  border-left: 4px solid rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.08);
  border-radius: 12px;
}

.faq .items details {
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 16px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.generic {
  text-align: center;
  color: #94a3b8;
}

.speaker-card {
  border-radius: 32px;
  padding: 32px;
  display: flex;
  gap: 32px;
  align-items: center;
  flex-wrap: wrap;
}

.speaker-card.layout-right .speaker-avatar {
  order: -1;
}

.speaker-content {
  flex: 1;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.speaker-badge {
  align-self: flex-start;
  padding: 4px 12px;
  border-radius: 999px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.85rem;
}

.speaker-card .headline :deep(.editable) {
  font-size: 2.2rem;
  font-weight: 700;
}

.speaker-card .subtitle :deep(.editable) {
  font-size: 1.1rem;
  opacity: 0.85;
}

.speaker-card .description :deep(.editable) {
  opacity: 0.9;
  line-height: 1.5;
}

.speaker-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.speaker-chips span {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  font-size: 0.85rem;
}

.speaker-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.9rem;
}

.speaker-tags strong {
  font-size: 1rem;
}

.speaker-cta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.speaker-cta button {
  border: none;
  border-radius: 999px;
  padding: 10px 18px;
  font-weight: 600;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.9);
  color: #0f172a;
}

.speaker-cta button.ghost {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.7);
  color: inherit;
}

.speaker-cta button :deep(.editable) {
  color: inherit;
}

.speaker-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.speaker-stats article {
  min-width: 120px;
  padding: 12px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  text-align: center;
}

.speaker-stats strong {
  font-size: 1.4rem;
  display: block;
}

.speaker-avatar {
  width: 260px;
  flex-shrink: 0;
  text-align: center;
  cursor: pointer;
}

.speaker-avatar img {
  width: 100%;
  height: 320px;
  object-fit: cover;
  border-radius: 999px;
  box-shadow: 0 25px 45px rgba(0, 0, 0, 0.35);
}

.speaker-avatar.shape-square img {
  border-radius: 32px;
}

.aurora-preview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  align-items: stretch;
}

.aurora-card {
  border-radius: 28px;
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.aurora-card .eyebrow :deep(.editable) {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.8;
}

.aurora-badge {
  align-self: flex-start;
  padding: 6px 14px;
  border-radius: 999px;
  font-weight: 600;
  color: #0f172a;
}

.aurora-cta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.aurora-cta button {
  border-radius: 999px;
  border: none;
  padding: 10px 18px;
  font-weight: 600;
  cursor: pointer;
}

.aurora-cta button.ghost {
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: transparent;
}

.aurora-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.aurora-stats article {
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 12px;
  text-align: center;
  background: rgba(0, 0, 0, 0.08);
}

.aurora-media {
  border-radius: 32px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  box-shadow: 0 25px 55px rgba(15, 23, 42, 0.35);
}

.aurora-media.shape-circle {
  border-radius: 999px;
}

.aurora-media img {
  width: 100%;
  display: block;
  height: auto;
}

.aurora-media button {
  position: absolute;
  bottom: 12px;
  right: 12px;
  border: none;
  border-radius: 999px;
  padding: 6px 12px;
  background: rgba(15, 23, 42, 0.75);
  color: #fff;
  cursor: pointer;
}
</style>
