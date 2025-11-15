from __future__ import annotations



from datetime import datetime

from typing import Any



from jinja2 import Template



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

              <article class="plan">

                <h3 data-block-id="{{ block_id }}" data-field-path="plans.{{ loop.index0 }}.name">{{ plan.name or "" }}</h3>

                <strong data-block-id="{{ block_id }}" data-field-path="plans.{{ loop.index0 }}.price">{{ plan.price or "" }}</strong>

                <ul>

                  {% for feature in plan.features or [] %}

                    <li data-block-id="{{ block_id }}" data-field-path="plans.{{ loop.parent.index0 }}.features.{{ loop.index0 }}">{{ feature or "" }}</li>

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



def render_block(block: BlockInstance, locale: str, settings: dict[str, Any]) -> str:

    template = BLOCK_TEMPLATES.get(block.definition.key)

    payload: dict[str, Any] = (

        block_payload_for_locale(block, locale, settings) or block.definition.default_config or {}

    )

    payload = dict(payload)

    style_attr = _style_to_attr(payload.pop("style", None))

    if template is None:

        return f"<section style=\"{style_attr}\"><pre>{payload}</pre></section>"

    return template.render(style_attr=style_attr, block=block, is_video_url=is_video_url, **payload)





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

    content = "\n".join(

        render_block(block, selected_locale, settings)

        for block in sorted(project.blocks, key=lambda b: b.order_index)

    )

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

                "order_index": block.order_index,

                "config": block.config,

                "translations": block.translations or {},

            }

            for block in sorted(project.blocks, key=lambda b: b.order_index)

        ],

    }


