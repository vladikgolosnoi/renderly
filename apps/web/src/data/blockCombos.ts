export type BlockComboStep = {
  definitionKey: string;
  config: Record<string, unknown>;
};

export interface BlockComboPreset {
  slug: string;
  title: string;
  description: string;
  tags: string[];
  accent: string;
  blocks: BlockComboStep[];
}

const PREVIEW_PLACEHOLDER =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 100'><rect width='160' height='100' rx='14' fill='%23f5f3ff'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='14' font-family='Inter,Arial,sans-serif' fill='%238181f5'>preview</text></svg>";

export const comboPresets: BlockComboPreset[] = [
  {
    slug: "lead-flow",
    title: "Лид-лендинг",
    description: "Hero + преимущества + форма — классический сценарий сбора заявок.",
    tags: ["Hero", "Features", "Form"],
    accent: "#6366f1",
    blocks: [
      {
        definitionKey: "hero",
        config: {
          eyebrow: "Платформа №1",
          headline: "Запустите сайт за вечер",
          subheading: "Готовые блоки, темы и автопубликация на ваш домен.",
          cta_label: "Создать проект",
          cta_url: "#lead",
          image_url: PREVIEW_PLACEHOLDER
        }
      },
      {
        definitionKey: "feature-grid",
        config: {
          title: "Почему Renderly",
          features: [
            { title: "Блоки", description: "Hero, сетки, формы и медиагалереи." },
            { title: "Темы", description: "Цветовые схемы и шрифты на один клик." },
            { title: "CDN", description: "Автопубликация на CDN или ваш домен." }
          ]
        }
      },
      {
        definitionKey: "form",
        config: {
          title: "Получите демо",
          description: "Оставьте контакты и мы покажем редактор в деле.",
          fields: ["Имя", "Компания", "Email", "Телефон"],
          webhook_url: "https://hooks.renderly.dev/demo",
          success_message: "Спасибо! Свяжемся в течение суток."
        }
      }
    ]
  },
  {
    slug: "product-drop",
    title: "Запуск продукта",
    description: "Герой с визуалом, галерея и CTA для мгновенных продаж.",
    tags: ["Hero", "Media", "CTA"],
    accent: "#0ea5e9",
    blocks: [
      {
        definitionKey: "hero",
        config: {
          eyebrow: "Новый релиз",
          headline: "Представляем коллекцию Flow 2.0",
          subheading: "Тонкие анимации, живые обложки и готовые интеграции.",
          cta_label: "Скачать медиакит",
          cta_url: "#assets",
          image_url: PREVIEW_PLACEHOLDER
        }
      },
      {
        definitionKey: "media-gallery",
        config: {
          images: [
            {
              url: PREVIEW_PLACEHOLDER,
              alt: "Экран конструктора",
              caption: "Редактор блоков"
            },
            {
              url: PREVIEW_PLACEHOLDER,
              alt: "Готовая страница",
              caption: "Лендинг курса"
            },
            {
              url: PREVIEW_PLACEHOLDER,
              alt: "Интерфейс настроек",
              caption: "Темы и цвета"
            }
          ]
        }
      },
      {
        definitionKey: "cta",
        config: {
          title: "Готовы к запуску?",
          description: "Подключите собственный домен и начните принимать заявки.",
          action_label: "Начать бесплатно",
          action_url: "https://renderly.app/signup"
        }
      }
    ]
  },
  {
    slug: "pricing-funnel",
    title: "Воронка с тарифами",
    description: "Hero, прайс-лист и форма заявки — отлично для студий и сервисов.",
    tags: ["Hero", "Pricing", "Form"],
    accent: "#f97316",
    blocks: [
      {
        definitionKey: "hero",
        config: {
          eyebrow: "Готовые решения",
          headline: "Соберём сайт и подключим интеграции",
          subheading: "Команда Renderly настроит домен, формы и автоматизацию.",
          cta_label: "Получить предложение",
          cta_url: "#plans",
          image_url: PREVIEW_PLACEHOLDER
        }
      },
      {
        definitionKey: "price-list",
        config: {
          title: "Тарифы",
          plans: [
            {
              name: "Старт",
              price: "19 000 ₽",
              features: ["1 страница", "Базовые блоки", "Поддержка 7/7"]
            },
            {
              name: "Бизнес",
              price: "39 000 ₽",
              features: ["До 5 страниц", "Свои домены", "Интеграции и формы"]
            },
            {
              name: "Проект",
              price: "Индивидуально",
              features: ["Дизайн под ключ", "Аналитика и n8n", "Поддержка 24/7"]
            }
          ]
        }
      },
      {
        definitionKey: "form",
        config: {
          title: "Получить расчёт",
          description: "Расскажите о задаче — вышлем точную смету в течение дня.",
          fields: ["Имя", "Компания", "Email", "Телефон", "Комментарий"],
          webhook_url: "https://hooks.renderly.dev/estimate",
          success_message: "Спасибо! Менеджер ответит в ближайшее время."
        }
      }
    ]
  }
];
