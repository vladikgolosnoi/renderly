const blockTitles: Record<string, string> = {
  hero: "Hero",
  "feature-grid": "Сетка преимуществ",
  "media-gallery": "Галерея",
  cta: "Призыв к действию",
  form: "Форма",
  "price-list": "Тарифы",
  schedule: "Расписание"
};

const fieldLabels: Record<string, string> = {
  eyebrow: "Эйброу",
  headline: "Заголовок",
  subheading: "Подзаголовок",
  cta_label: "Текст кнопки",
  cta_url: "Ссылка кнопки",
  image_url: "URL изображения",
  title: "Название",
  description: "Описание",
  features: "Преимущества",
  items: "Элементы",
  steps: "Шаги",
  schedule: "Расписание",
  success_message: "Сообщение об успехе",
  webhook_url: "Webhook URL",
  fields: "Поля",
  plans: "Тарифы",
  images: "Изображения",
  caption: "Подпись",
  alt: "ALT-текст"
};

const categoryLabels: Record<string, string> = {
  content: "Контент",
  media: "Медиа",
  form: "Форма",
  layout: "Макет",
  hero: "Hero"
};

function normalize(value: string | null | undefined) {
  return (value ?? "").toString().trim().toLowerCase();
}

function lookup<T extends Record<string, string>>(map: T, ...candidates: (string | null | undefined)[]) {
  for (const candidate of candidates) {
    const key = normalize(candidate);
    if (key && map[key]) return map[key];
  }
  return undefined;
}

export function localizedBlockName(definitionKey: string, fallback: string) {
  return lookup(blockTitles, definitionKey, fallback) ?? fallback;
}

export function localizedFieldLabel(fieldKey: string, fallback: string) {
  return lookup(fieldLabels, fieldKey, fallback) ?? fallback;
}

export function localizedCategoryLabel(category: string, fallback: string) {
  return lookup(categoryLabels, category, fallback) ?? fallback;
}
