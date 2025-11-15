from __future__ import annotations



from datetime import datetime
from dataclasses import dataclass
import hashlib
import logging

from typing import Any



from jinja2 import Environment, Template, TemplateError
from markupsafe import Markup, escape



from app.models.block_instance import BlockInstance

from app.models.project import Project

from app.services.localization import ensure_locales, resolve_locale, block_payload_for_locale





BASE_TEMPLATE = Template(

    """

<!doctype html>

<html lang="ru">

  <head>

    <meta charset="utf-8"/>

    <title>{{ title }}</title>

    <style>

      * { box-sizing: border-box; }

      body { font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 0; background: {{ background }}; color: {{ text_color }}; }

      header, footer { width: 100%; }

      header { padding: 20px 32px; background: {{ header_bg }}; color: {{ header_text }}; box-shadow: 0 1px 0 rgba(15, 23, 42, 0.08); }

      footer { padding: 32px; background: {{ footer_bg }}; color: {{ footer_text }}; text-align: center; }

      main { max-width: 960px; margin: 0 auto; padding: 32px 24px 96px; display: flex; flex-direction: column; gap: 32px; }

      section { border-radius: 24px; padding: 48px 32px; background: #fff; box-shadow: 0 25px 55px rgba(15, 23, 42, 0.06); border: 1px solid rgba(15, 23, 42, 0.06); }

      h1, h2, h3 { margin-top: 0; }

      .hero { display: grid; gap: 32px; align-items: center; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }

      .hero .eyebrow { text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px; display: inline-block; }

      .hero button { background: {{ accent }}; color: #fff; border: none; padding: 16px 32px; border-radius: 999px; font-size: 1.1rem; cursor: pointer; }

      .hero figure { margin: 0; text-align: center; }

      .hero figure img { width: 100%; border-radius: 24px; object-fit: cover; box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12); }

      .feature-grid .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }

      .feature-grid article { padding: 12px; border-radius: 18px; background: rgba(99, 102, 241, 0.08); }

      .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }

      .gallery figure { margin: 0; }

      .gallery img { width: 100%; border-radius: 18px; }

      .cta { text-align: center; }

      .cta button { background: {{ accent }}; color: #fff; border: none; padding: 16px 32px; border-radius: 16px; cursor: pointer; font-size: 1rem; }

      .form-block form { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }

      .form-block label { display: flex; flex-direction: column; text-align: left; gap: 4px; font-size: 0.95rem; }

      .form-block input { border-radius: 12px; border: 1px solid #cbd5f5; padding: 10px 12px; }

      .form-block button { align-self: flex-start; background: {{ accent }}; color: #fff; border: none; padding: 12px 20px; border-radius: 10px; cursor: pointer; }

      .price-list .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }

      .price-list .plan { border: 1px solid #e2e8f0; border-radius: 20px; padding: 16px; text-align: center; }

      .price-list ul { list-style: none; padding: 0; margin: 12px 0 0; }

      .schedule ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px; }

      .schedule li { padding: 12px 16px; border-radius: 14px; background: rgba(15, 23, 42, 0.05); display: flex; justify-content: space-between; gap: 12px; }

      .team .members { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; }

      .team figure { text-align: center; }

      .team img { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; }

      .testimonials blockquote { margin: 12px 0; padding: 16px; border-left: 4px solid {{ accent }}; background: rgba(99, 102, 241, 0.08); }

      .faq details { border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px 16px; margin-bottom: 12px; }

      .asset-placeholder { min-height: 220px; border: 2px dashed rgba(99, 102, 241, 0.35); border-radius: 18px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; text-align: center; color: #94a3b8; background: rgba(99, 102, 241, 0.05); padding: 24px; font-size: 0.95rem; }

      .asset-placeholder strong { color: #475569; font-weight: 600; }

      .asset-placeholder.small { min-height: 140px; padding: 16px; }

      .asset-placeholder.avatar { min-height: 120px; min-width: 120px; border-radius: 999px; }

    </style>

  </head>

  <body>

    {{ header }}

    <main>

      {{ content }}

    </main>

    {{ footer }}

  </body>

</html>

"""

)




logger = logging.getLogger(__name__)


CUSTOM_TEMPLATE_ENV = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
_CUSTOM_TEMPLATE_CACHE: dict[str, tuple[str, Template]] = {}


@dataclass
class RenderedBlock:
    html: str
    style_key: str | None = None
    style_rules: str | None = None


@dataclass
class TemplateListItem:
    base_key: str
    index: int
    value: Any

    def path(self, sub_key: str | None = None) -> str:
        if sub_key is None:
            return f"{self.base_key}.{self.index}"
        return f"{self.base_key}.{self.index}.{sub_key}"


class TemplateHelpers:
    def __init__(self, block: BlockInstance, payload: dict[str, Any]):
        self.block = block
        self.payload = payload
        self.block_id = block.id or block.order_index or 0
        self.definition_key = block.definition.key

    def text(
        self,
        key: str,
        tag: str = "p",
        classes: str = "",
        default: str = "",
        attrs: dict[str, str] | None = None,
    ) -> Markup:
        return self._field(key, tag, classes, default, attrs, allow_html=False)

    def richtext(
        self,
        key: str,
        tag: str = "div",
        classes: str = "",
        default: str = "",
        attrs: dict[str, str] | None = None,
    ) -> Markup:
        return self._field(key, tag, classes, default, attrs, allow_html=True)

    def field(
        self,
        path: str,
        tag: str = "span",
        classes: str = "",
        default: str = "",
        attrs: dict[str, str] | None = None,
        allow_html: bool = False,
    ) -> Markup:
        return self._field(path, tag, classes, default, attrs, allow_html)

    def value(self, path: str, default: str = "") -> str:
        data = self._raw_value(path)
        if data is None:
            return default
        if isinstance(data, (int, float)):
            return str(data)
        if isinstance(data, str):
            return data
        return default

    def list_items(self, key: str) -> list[TemplateListItem]:
        raw = self._raw_value(key)
        if not isinstance(raw, list):
            return []
        return [TemplateListItem(key, index, item) for index, item in enumerate(raw)]

    def items(self, key: str) -> list[TemplateListItem]:
        return self.list_items(key)

    def item_text(
        self,
        item: TemplateListItem,
        sub_key: str | None = None,
        tag: str = "span",
        classes: str = "",
        default: str = "",
        attrs: dict[str, str] | None = None,
    ) -> Markup:
        return self._field(item.path(sub_key), tag, classes, default, attrs, allow_html=False)

    def item_richtext(
        self,
        item: TemplateListItem,
        sub_key: str | None = None,
        tag: str = "div",
        classes: str = "",
        default: str = "",
        attrs: dict[str, str] | None = None,
    ) -> Markup:
        return self._field(item.path(sub_key), tag, classes, default, attrs, allow_html=True)

    def item_value(self, item: TemplateListItem, sub_key: str | None = None, default: str = "") -> str:
        return self.value(item.path(sub_key), default)

    def asset(
        self,
        key: str,
        classes: str = "",
        label: str | None = None,
        attrs: dict[str, str] | None = None,
    ) -> Markup:
        label = label or self._humanize(key)
        url = self.value(key, "")
        media_html: str
        if url and is_video_url(url):
            media_html = f'<video src="{escape(url)}" autoplay muted loop playsinline></video>'
        elif url:
            media_html = f'<img src="{escape(url)}" alt="{escape(label)}"/>'
        else:
            media_html = self._asset_placeholder(label)
        attr_map = dict(attrs or {})
        attr_map["data-field-kind"] = "asset"
        attr_map["data-field-label"] = label
        return Markup(
            f'<figure data-block-id="{self.block_id}" data-field-path="{key}"'
            f'{self._build_attr_string(classes, attr_map)}>{media_html}</figure>'
        )

    def item_asset(
        self,
        item: TemplateListItem,
        sub_key: str | None = None,
        classes: str = "",
        label: str | None = None,
        attrs: dict[str, str] | None = None,
    ) -> Markup:
        path = item.path(sub_key)
        label = label or self._humanize(sub_key or item.base_key)
        url = self.value(path, "")
        media_html: str
        if url and is_video_url(url):
            media_html = f'<video src="{escape(url)}" autoplay muted loop playsinline></video>'
        elif url:
            media_html = f'<img src="{escape(url)}" alt="{escape(label)}"/>'
        else:
            media_html = self._asset_placeholder(label)
        attr_map = dict(attrs or {})
        attr_map["data-field-kind"] = "asset"
        attr_map["data-field-label"] = label
        return Markup(
            f'<figure data-block-id="{self.block_id}" data-field-path="{path}"'
            f'{self._build_attr_string(classes, attr_map)}>{media_html}</figure>'
        )

    def field_path(self, path: str) -> str:
        return path

    def section_classes(self, *extra: str) -> str:
        classes = ["block", f"block-{self.definition_key}"]
        classes.extend(cls for cls in extra if cls)
        return " ".join(classes)

    def _field(
        self,
        path: str,
        tag: str,
        classes: str,
        default: str,
        attrs: dict[str, str] | None,
        allow_html: bool,
    ) -> Markup:
        value = self.value(path, default)
        content = value if allow_html else escape(value)
        attr_string = self._build_attr_string(classes, attrs)
        return Markup(
            f'<{tag} data-block-id="{self.block_id}" data-field-path="{path}"{attr_string}>{content}</{tag}>'
        )

    def _build_attr_string(self, classes: str, attrs: dict[str, str] | None) -> str:
        pairs: list[tuple[str, str]] = []
        if classes:
            pairs.append(("class", classes))
        if attrs:
            for key, value in attrs.items():
                if value is None:
                    continue
                pairs.append((key, str(value)))
        if not pairs:
            return ""
        return " " + " ".join(f'{key}="{escape(val)}"' for key, val in pairs)

    def _raw_value(self, path: str) -> Any:
        if not isinstance(self.payload, dict) or not path:
            return None
        normalized = []
        for segment in path.replace("]", "").split("."):
            normalized.extend(part for part in segment.split("[") if part)
        current: Any = self.payload
        for part in normalized:
            if isinstance(current, list):
                try:
                    index = int(part)
                except ValueError:
                    return None
                if index < 0 or index >= len(current):
                    return None
                current = current[index]
                continue
            if isinstance(current, dict):
                current = current.get(part)
                continue
            return None
        return current

    def _humanize(self, key: str) -> str:
        return key.replace("_", " ").title()

    def _asset_placeholder(self, label: str) -> str:
        return (
            '<div class="asset-placeholder">'
            f"<strong>{escape(label)}</strong>"
            "<span>Загрузите медиа</span>"
            "</div>"
        )


def _get_compiled_template(cache_key: str, markup: str) -> Template:
    checksum = hashlib.sha1(markup.encode("utf-8")).hexdigest()
    cached = _CUSTOM_TEMPLATE_CACHE.get(cache_key)
    if cached and cached[0] == checksum:
        return cached[1]
    template = CUSTOM_TEMPLATE_ENV.from_string(markup)
    _CUSTOM_TEMPLATE_CACHE[cache_key] = (checksum, template)
    return template


def _render_template_error(helpers: TemplateHelpers, message: str) -> str:
    attrs = [
        f'class="{helpers.section_classes("is-error")}"',
        f'data-block-section="{helpers.block_id}"',
        f'data-template-key="{helpers.definition_key}"',
    ]
    return f"<section {' '.join(attrs)}><pre>{escape(message)}</pre></section>"


def _render_dynamic_block(block: BlockInstance, payload: dict[str, Any], style_attr: str) -> RenderedBlock | None:
    markup = block.definition.template_markup
    if not markup:
        return None
    cache_key = str(block.definition.id or block.definition.key)
    try:
        template = _get_compiled_template(cache_key, markup)
    except TemplateError as exc:
        logger.warning("Failed to compile template for block %s: %s", block.definition.key, exc)
        helpers = TemplateHelpers(block, payload)
        return RenderedBlock(html=_render_template_error(helpers, f"Template error: {exc}"))
    helpers = TemplateHelpers(block, payload)
    context = {
        "block": block,
        "payload": payload,
        "helpers": helpers,
        "block_id": helpers.block_id,
        "style_attr": style_attr,
        "is_video_url": is_video_url,
    }
    try:
        inner = template.render(**context)
    except TemplateError as exc:
        logger.warning("Failed to render template for block %s: %s", block.definition.key, exc)
        return RenderedBlock(html=_render_template_error(helpers, f"Template error: {exc}"))
    section_attrs = [
        f'class="{helpers.section_classes()}"',
        f'data-block-section="{helpers.block_id}"',
        f'data-template-key="{block.definition.key}"',
    ]
    if style_attr:
        section_attrs.append(f'style="{style_attr}"')
    html = f"<section {' '.join(section_attrs)}>{inner}</section>"
    style_rules = (block.definition.template_styles or "").strip() or None
    style_key = block.definition.key if style_rules else None
    return RenderedBlock(html=html, style_key=style_key, style_rules=style_rules)



def _style_to_attr(style: dict[str, Any] | None) -> str:

    if not style or not isinstance(style, dict):

        return ""

    parts: list[str] = []

    background = style.get("background")

    padding = style.get("padding")

    border_color = style.get("border_color")

    border_radius = style.get("border_radius")

    if isinstance(background, str) and background:

        parts.append(f"background:{background}")

    if isinstance(padding, str) and padding:

        parts.append(f"padding:{padding}")

    if isinstance(border_color, str) and border_color:

        width = style.get("border_width") or "1px"

        parts.append(f"border:{width} solid {border_color}")

    if isinstance(border_radius, (int, float)):

        parts.append(f"border-radius:{border_radius}px")

    return ";".join(parts)





VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov", ".m4v", ".ogg")





def is_video_url(url: str | None) -> bool:

    if not isinstance(url, str):

        return False

    clean = url.split("?", 1)[0].split("#", 1)[0].lower()

    return clean.endswith(VIDEO_EXTENSIONS)





BLOCK_TEMPLATES: dict[str, Template] = {

    "hero": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="hero" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <div>

            <p class="eyebrow" data-block-id="{{ block_id }}" data-field-path="eyebrow">{{ eyebrow or "" }}</p>

            <h1 data-block-id="{{ block_id }}" data-field-path="headline">{{ headline or "" }}</h1>

            <p data-block-id="{{ block_id }}" data-field-path="subheading">{{ subheading or "" }}</p>

            {% if cta_label %}

            <a href="{{ cta_url or '#' }}">

              <button data-block-id="{{ block_id }}" data-field-path="cta_label">{{ cta_label or "" }}</button>

            </a>

            {% endif %}

          </div>

          <figure class="hero-media" data-block-id="{{ block_id }}" data-field-kind="asset" data-field-path="image_url" data-field-label="Hero media">

            {% if image_url %}

              {% if is_video_url(image_url) %}

                <video src="{{ image_url }}" playsinline muted loop controls></video>

              {% else %}

                <img src="{{ image_url }}" alt="{{ headline or '' }}" />

              {% endif %}

            {% else %}

                            <div class="asset-placeholder">
                <strong>Добавьте медиа</strong>
                <span>Нажмите, чтобы загрузить фото или видео</span>
              </div>

            {% endif %}

          </figure>

        </section>

        """

    ),
    "speaker-highlight": Template(
        """
        {% set block_id = block.id or block.order_index %}
        {% set layout_mode = (layout or "left").lower() %}
        {% set gradient = gradient_start and gradient_end %}
        {% set background = gradient and "linear-gradient(135deg, " ~ gradient_start ~ ", " ~ gradient_end ~ ")" or bg_color or "#111827" %}
        {% set text_col = text_color or "#f8fafc" %}
        {% set badge_col = badge_color or "#f9769b" %}
        {% set shadow = card_shadow or "0 30px 70px rgba(15, 23, 42, 0.4)" %}
        {% set chips_list = chips.split(",") if chips else [] %}
        {% set stats_list = stats or [] %}
        {% set tags_list = tags or [] %}
        <section class="speaker-highlight" data-block-section="{{ block_id }}" style="background: {{ background }}; color: {{ text_col }}; box-shadow: {{ shadow }}; border-radius: 32px; padding: 40px 32px;">
          <div style="display:flex; flex-wrap:wrap; gap:32px; align-items:center;">
            <div style="flex:1; min-width:260px; display:flex; flex-direction:column; gap:12px;">
              {% if badge_label %}
              <span style="display:inline-flex; align-items:center; padding:4px 12px; border-radius:999px; font-weight:600; letter-spacing:0.08em; background: {{ badge_col }};"
                    data-block-id="{{ block_id }}" data-field-path="badge_label">{{ badge_label }}</span>
              {% endif %}
              {% if eyebrow %}<p style="margin:0; text-transform:uppercase; letter-spacing:0.2em; font-size:0.8rem;"
                    data-block-id="{{ block_id }}" data-field-path="eyebrow">{{ eyebrow }}</p>{% endif %}
              {% if headline %}<h2 style="margin:0; font-size:2.2rem;"
                    data-block-id="{{ block_id }}" data-field-path="headline">{{ headline }}</h2>{% endif %}
              {% if subtitle %}<h3 style="margin:0; font-size:1.1rem; font-weight:500; opacity:0.85;"
                    data-block-id="{{ block_id }}" data-field-path="subtitle">{{ subtitle }}</h3>{% endif %}
              {% if description %}<div style="opacity:0.9; line-height:1.5;"
                    data-block-id="{{ block_id }}" data-field-path="description">{{ description | safe }}</div>{% endif %}
              {% if chips_list %}
              <div style="display:flex; flex-wrap:wrap; gap:8px;" data-block-id="{{ block_id }}" data-field-path="chips">
                {% for chip in chips_list %}
                <span style="padding:4px 10px; border-radius:999px; font-size:0.85rem; background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.3);">{{ chip.strip() }}</span>
                {% endfor %}
              </div>
              {% endif %}
              {% if tags_list %}
              <div style="display:flex; flex-direction:column; gap:6px;">
                {% for tag in tags_list %}
                <span style="display:flex; gap:8px; align-items:center;">
                  <strong data-block-id="{{ block_id }}" data-field-path="tags.{{ loop.index0 }}.icon">{{ tag.icon }}</strong>
                  <span data-block-id="{{ block_id }}" data-field-path="tags.{{ loop.index0 }}.title">{{ tag.title }}</span>
                </span>
                {% endfor %}
              </div>
              {% endif %}
              <div style="display:flex; flex-wrap:wrap; gap:12px; margin-top:6px;">
                {% if cta_primary_label %}
                <a href="{{ cta_primary_url or '#' }}" style="text-decoration:none; font-weight:600; padding:10px 22px; border-radius:999px; background:#fff; color:#111827; box-shadow:0 10px 20px rgba(0,0,0,0.25);"
                   data-block-id="{{ block_id }}" data-field-path="cta_primary_label">{{ cta_primary_label }}</a>
                {% endif %}
                {% if cta_secondary_label %}
                <a href="{{ cta_secondary_url or '#' }}" style="text-decoration:none; font-weight:600; padding:10px 22px; border-radius:999px; border:1px solid rgba(255,255,255,0.7); color:#fff;"
                   data-block-id="{{ block_id }}" data-field-path="cta_secondary_label">{{ cta_secondary_label }}</a>
                {% endif %}
              </div>
              {% if stats_list %}
              <div style="display:flex; flex-wrap:wrap; gap:16px; margin-top:12px;">
                {% for stat in stats_list %}
                <article style="min-width:120px; padding:10px 14px; border-radius:18px; background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.25); text-align:center;">
                  <strong style="display:block; font-size:1.4rem;"
                          data-block-id="{{ block_id }}" data-field-path="stats.{{ loop.index0 }}.value">{{ stat.value }}</strong>
                  <small style="opacity:0.75;"
                         data-block-id="{{ block_id }}" data-field-path="stats.{{ loop.index0 }}.label">{{ stat.label }}</small>
                </article>
                {% endfor %}
              </div>
              {% endif %}
            </div>
            <figure style="margin:0; width:260px; flex-shrink:0; text-align:center; {% if layout_mode == 'right' %}order:-1;{% endif %}">
              <img src="{{ avatar or 'https://placehold.co/300x360/222/eee?text=avatar' }}" alt="{{ headline or 'speaker' }}" style="width:100%; height:320px; object-fit:cover; border-radius:{% if avatar_shape and avatar_shape|lower == 'square' %}32px{% else %}999px{% endif %}; box-shadow:0 20px 45px rgba(0,0,0,0.35);"
                   data-block-id="{{ block_id }}" data-field-path="avatar" />
            </figure>
          </div>
        </section>
        """
    ),

    "feature-grid": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="feature-grid" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>

          <div class="grid">

            {% for feature in features %}

              <article>

                <h3 data-block-id="{{ block_id }}" data-field-path="features.{{ loop.index0 }}.title">{{ feature.title or "" }}</h3>

                <p data-block-id="{{ block_id }}" data-field-path="features.{{ loop.index0 }}.description">{{ feature.description or "" }}</p>

              </article>

            {% endfor %}

          </div>

        </section>

        """

    ),

    "media-gallery": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="gallery" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          {% set gallery = images or [] %}

          {% if gallery %}

            {% for image in gallery %}

              <figure data-block-id="{{ block_id }}" data-field-kind="asset" data-field-path="images.{{ loop.index0 }}.url" data-field-label="Gallery image #{{ loop.index }}">

                {% if image.url %}

                  {% if is_video_url(image.url) %}

                    <video src="{{ image.url }}" playsinline muted loop controls></video>

                  {% else %}

                    <img src="{{ image.url }}" alt="{{ image.alt or '' }}" />

                  {% endif %}

                {% else %}

                                    <div class="asset-placeholder small">
                    <strong>Добавьте медиа</strong>
                    <span>Нажмите, чтобы загрузить файл</span>
                  </div>

                {% endif %}

                <figcaption data-block-id="{{ block_id }}" data-field-path="images.{{ loop.index0 }}.caption">{{ image.caption or "" }}</figcaption>

              </figure>

            {% endfor %}

          {% else %}

            <figure data-block-id="{{ block_id }}" data-field-kind="asset" data-field-path="images.0.url" data-field-label="Gallery image #1">

                                <div class="asset-placeholder small">
                    <strong>Добавьте медиа</strong>
                    <span>Нажмите, чтобы загрузить файл</span>
                  </div>

              <figcaption data-block-id="{{ block_id }}" data-field-path="images.0.caption"></figcaption>

            </figure>

          {% endif %}

        </section>

        """

    ),

    "cta": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="cta" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>

          <p data-block-id="{{ block_id }}" data-field-path="description">{{ description or "" }}</p>

          {% if action_label %}

          <a href="{{ action_url or '#' }}">

            <button data-block-id="{{ block_id }}" data-field-path="action_label">{{ action_label or "" }}</button>

          </a>

          {% endif %}

        </section>

        """

    ),

    "form": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="form-block" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>

          <p data-block-id="{{ block_id }}" data-field-path="description">{{ description or "" }}</p>

          <form class="form-preview">

            {% for field in fields %}

              <label data-block-id="{{ block_id }}" data-field-path="fields.{{ loop.index0 }}">

                <span>{{ field|capitalize }}</span>

                <input type="text" name="{{ field }}" placeholder="{{ field|capitalize }}" />

              </label>

            {% endfor %}

            <button type="submit">Отправить заявку</button>

          </form>

          {% if success_message %}

          <small data-block-id="{{ block_id }}" data-field-path="success_message">{{ success_message or "" }}</small>

          {% endif %}

        </section>

        """

    ),

    "price-list": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="price-list" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>

          <div class="plans">

            {% for plan in plans %}
              {% set plan_index = loop.index0 %}
              <article class="plan">
                <h3 data-block-id="{{ block_id }}" data-field-path="plans.{{ plan_index }}.name">{{ plan.name or "" }}</h3>
                <strong data-block-id="{{ block_id }}" data-field-path="plans.{{ plan_index }}.price">{{ plan.price or "" }}</strong>
                <ul>
                  {% for feature in plan.features or [] %}
                    <li data-block-id="{{ block_id }}" data-field-path="plans.{{ plan_index }}.features.{{ loop.index0 }}">{{ feature or "" }}</li>
                  {% endfor %}
                </ul>
              </article>
            {% endfor %}

          </div>

        </section>

        """

    ),

    "schedule": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="schedule" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>

          <ul>

            {% for item in items %}

              <li>

                <span>

                  <strong data-block-id="{{ block_id }}" data-field-path="items.{{ loop.index0 }}.time">{{ item.time or "" }}</strong>

                  —

                  <span data-block-id="{{ block_id }}" data-field-path="items.{{ loop.index0 }}.topic">{{ item.topic or "" }}</span>

                </span>

                <small data-block-id="{{ block_id }}" data-field-path="items.{{ loop.index0 }}.speaker">{{ item.speaker or "" }}</small>

              </li>

            {% endfor %}

          </ul>

        </section>

        """

    ),

    "team": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="team" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>

          {% set team_members = members or [] %}

          <div class="members">

            {% if team_members %}

              {% for member in team_members %}

                <figure>

                  <div data-block-id="{{ block_id }}" data-field-kind="asset" data-field-path="members.{{ loop.index0 }}.photo" data-field-label="Фото участника #{{ loop.index }}">

                    {% if member.photo %}

                      {% if is_video_url(member.photo) %}

                        <video src="{{ member.photo }}" playsinline muted loop controls></video>

                      {% else %}

                        <img src="{{ member.photo }}" alt="{{ member.name or '' }}" />

                      {% endif %}

                    {% else %}

                                          <div class="asset-placeholder avatar">
                      <strong>Нет изображения</strong>
                      <span>Загрузите фото участника</span>
                    </div>

                    {% endif %}

                  </div>

                  <figcaption>

                    <strong data-block-id="{{ block_id }}" data-field-path="members.{{ loop.index0 }}.name">{{ member.name or "" }}</strong>

                    <span data-block-id="{{ block_id }}" data-field-path="members.{{ loop.index0 }}.role">{{ member.role or "" }}</span>

                  </figcaption>

                </figure>

              {% endfor %}

            {% else %}

              <figure>

                <div data-block-id="{{ block_id }}" data-field-kind="asset" data-field-path="members.0.photo" data-field-label="Фото участника #1">

                                      <div class="asset-placeholder avatar">
                      <strong>Нет изображения</strong>
                      <span>Загрузите фото участника</span>
                    </div>

                </div>

                <figcaption>

                  <strong data-block-id="{{ block_id }}" data-field-path="members.0.name">Имя участника</strong>

                  <span data-block-id="{{ block_id }}" data-field-path="members.0.role">Роль участника</span>

                </figcaption>

              </figure>

            {% endif %}

          </div>

        </section>

        """

    ),

    "testimonials": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="testimonials" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          <h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>

          {% for item in testimonials %}

            <blockquote>

              <p data-block-id="{{ block_id }}" data-field-path="testimonials.{{ loop.index0 }}.quote">{{ item.quote or "" }}</p>

              <strong data-block-id="{{ block_id }}" data-field-path="testimonials.{{ loop.index0 }}.name">{{ item.name or "" }}</strong>

            </blockquote>

          {% endfor %}

        </section>

        """

    ),

    "faq": Template(

        """

        {% set block_id = block.id or block.order_index %}

        <section class="faq" data-block-section="{{ block_id }}" {% if style_attr %}style="{{ style_attr }}"{% endif %}>

          {% if title %}<h2 data-block-id="{{ block_id }}" data-field-path="title">{{ title or "" }}</h2>{% endif %}

          {% for item in items %}

            <details open>

              <summary data-block-id="{{ block_id }}" data-field-path="items.{{ loop.index0 }}.question">{{ item.question or "" }}</summary>

              <p data-block-id="{{ block_id }}" data-field-path="items.{{ loop.index0 }}.answer">{{ item.answer or "" }}</p>

            </details>

          {% endfor %}

        </section>

        """

    ),

}



def render_block(block: BlockInstance, locale: str, settings: dict[str, Any]) -> RenderedBlock:

    template = BLOCK_TEMPLATES.get(block.definition.key)

    payload: dict[str, Any] = (

        block_payload_for_locale(block, locale, settings) or block.definition.default_config or {}

    )

    payload = dict(payload)

    style_attr = _style_to_attr(payload.pop("style", None))

    dynamic = _render_dynamic_block(block, payload, style_attr)
    if dynamic:
        return dynamic

    if template is None:

        block_id = block.id or block.order_index or 0

        attrs = [f'data-block-section="{block_id}"']

        if style_attr:

            attrs.append(f'style="{style_attr}"')

        return RenderedBlock(html=f"<section {' '.join(attrs)}><pre>{payload}</pre></section>")

    return RenderedBlock(

        html=template.render(style_attr=style_attr, block=block, is_video_url=is_video_url, **payload)

    )





def render_project_html(project: Project, locale: str | None = None) -> str:

    theme = project.theme or {}

    settings = project.settings or {}

    ensure_locales(settings)

    selected_locale = resolve_locale(settings, locale)

    header = Template(

        """

        <header style="padding:16px 24px;background:{{ background }};color:{{ color }};">

          <strong>{{ title }}</strong>

        </header>

        """

    ).render(

        title=project.title,

        background=theme.get("header_bg", "#ffffff"),

        color=theme.get("header_text", "#0f172a"),

    )

    footer = Template(

        """

        <footer style="padding:32px 24px;background:{{ background }};color:{{ color }};">

          <p>{{ footer_text }}</p>

        </footer>

        """

    ).render(

        footer_text=settings.get("footer_text", "Сделано на Renderly"),

        background=theme.get("footer_bg", "#0f172a"),

        color=theme.get("footer_text", "#ffffff"),

    )

    rendered_blocks = [
        render_block(block, selected_locale, settings)
        for block in sorted(project.blocks, key=lambda b: b.order_index)
    ]

    style_tags: dict[str, str] = {}
    content_parts: list[str] = []
    for rendered in rendered_blocks:
        content_parts.append(rendered.html)
        if rendered.style_key and rendered.style_rules and rendered.style_key not in style_tags:
            style_tags[rendered.style_key] = (
                f'<style data-block-style="{rendered.style_key}">\n{rendered.style_rules}\n</style>'
            )

    style_html = "\n".join(style_tags.values())
    content = "\n".join(part for part in ([style_html] if style_html else []) + content_parts)

    return BASE_TEMPLATE.render(

        title=project.title,

        background=theme.get("page_bg", "#f8fafc"),

        text_color=theme.get("text_color", "#0f172a"),

        accent=theme.get("accent", "#6366f1"),

        header_bg=theme.get("header_bg", "#ffffff"),

        header_text=theme.get("header_text", "#0f172a"),

        footer_bg=theme.get("footer_bg", "#0f172a"),

        footer_text=theme.get("footer_text", "#ffffff"),

        header=header,

        footer=footer,

        content=content,

    )





def version_for_project(project: Project) -> str:

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    return f"{project.id}-{timestamp}"





def snapshot_project(project: Project) -> dict[str, Any]:

    settings = project.settings or {}

    ensure_locales(settings)

    return {

        "project": {

            "title": project.title,

            "slug": project.slug,

            "description": project.description,

            "theme": project.theme,

            "settings": settings,

            "status": project.status,

            "visibility": getattr(project, "visibility", "private"),

        },

        "blocks": [

            {

                "id": block.id,

                "definition_key": block.definition.key,

                "definition": {

                    "key": block.definition.key,

                    "name": block.definition.name,

                    "category": block.definition.category,

                    "version": block.definition.version,

                    "schema": block.definition.schema,

                    "default_config": block.definition.default_config,

                    "template_markup": getattr(block.definition, "template_markup", None),

                    "template_styles": getattr(block.definition, "template_styles", None),

                },

                "order_index": block.order_index,

                "config": block.config,

                "translations": block.translations or {},

            }

            for block in sorted(project.blocks, key=lambda b: b.order_index)

        ],

    }


