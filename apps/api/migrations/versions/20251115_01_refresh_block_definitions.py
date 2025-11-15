"""refresh block definitions text"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import json
from pathlib import Path

revision = '20251115_01_refresh_block_df'
down_revision = '20251113_03'
branch_labels = None
depends_on = None


SEED_PATH = Path(__file__).resolve().parents[2] / 'app' / 'seeds' / 'block_definitions.json'


def _load_definitions() -> list[dict[str, object]]:
    with SEED_PATH.open(encoding='utf-8') as f:
        return json.load(f)


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("block_definition"):
        # Skip on fresh environments where the base schema hasn't been created yet.
        return

    stmt = sa.text(
        """
        INSERT INTO block_definition
            (key, name, category, description, version, schema, default_config, ui_meta, created_at, updated_at)
        VALUES
            (:key, :name, :category, :description, :version, :schema::jsonb, :config::jsonb, :ui_meta::jsonb, now(), now())
        ON CONFLICT (key) DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            description = EXCLUDED.description,
            version = EXCLUDED.version,
            schema = EXCLUDED.schema,
            default_config = EXCLUDED.default_config,
            ui_meta = EXCLUDED.ui_meta,
            updated_at = now()
        """
    )
    for definition in _load_definitions():
        conn.execute(
            stmt,
            {
                'key': definition['key'],
                'name': definition.get('name'),
                'category': definition.get('category'),
                'description': definition.get('description'),
                'version': definition.get('version'),
                'schema': json.dumps(definition.get('schema', [])),
                'config': json.dumps(definition.get('default_config', {})),
                'ui_meta': json.dumps(definition.get('ui_meta', {})),
            },
        )


def downgrade() -> None:
    pass
