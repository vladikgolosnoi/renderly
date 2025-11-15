from pathlib import Path
path = Path('apps/api/app/services/publisher.py')
data = path.read_bytes()
old_hero = '''            {% if cta_label %}

            <a href="{{ cta_url or '#' }}" onclick="return false;">

              <button data-block-id="{{ block_id }}" data-field-path="cta_label">{{ cta_label or "" }}</button>

            </a>

            {% endif %}
'''.encode('utf-8')
new_hero = '''            {% if cta_label %}

            <a href="{{ cta_url or '#' }}">

              <button data-block-id="{{ block_id }}" data-field-path="cta_label">{{ cta_label or "" }}</button>

            </a>

            {% endif %}
'''.encode('utf-8')
old_cta = '''          <p data-block-id="{{ block_id }}" data-field-path="description">{{ description or "" }}</p>

          <button data-block-id="{{ block_id }}" data-field-path="action_label">{{ action_label or "" }}</button>
'''.encode('utf-8')
new_cta = '''          <p data-block-id="{{ block_id }}" data-field-path="description">{{ description or "" }}</p>

          {% if action_label %}

          <a href="{{ action_url or '#' }}">

            <button data-block-id="{{ block_id }}" data-field-path="action_label">{{ action_label or "" }}</button>

          </a>

          {% endif %}
'''.encode('utf-8')
old_input = ' placeholder="{{ field|capitalize }}" disabled />'.encode('utf-8')
new_input = ' placeholder="{{ field|capitalize }}" />'.encode('utf-8')
old_button = '<button type="submit" disabled>Отправить заявку</button>'.encode('utf-8')
new_button = '<button type="submit">Отправить заявку</button>'.encode('utf-8')
for old, new in [(old_hero, new_hero), (old_cta, new_cta), (old_input, new_input), (old_button, new_button)]:
    if old not in data:
        raise SystemExit('pattern not found')
    data = data.replace(old, new, 1)
path.write_bytes(data)
