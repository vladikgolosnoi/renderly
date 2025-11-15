from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.db import base  # noqa: F401  # ensure all models are registered
from app.models.block_definition import BlockDefinition
from app.models.block_instance import BlockInstance
from app.models.project import Project
from app.models.user import User
from app.models.theme_template import ThemeTemplate

SEED_PATH = Path(__file__).with_name("block_definitions.json")


def seed_block_definitions(db: Session) -> None:
    definitions = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for data in definitions:
        if db.query(BlockDefinition).filter(BlockDefinition.key == data["key"]).first():
            continue
        db.add(BlockDefinition(**data))
    db.commit()


DEFAULT_DEMO_EMAIL = "demo@renderly.dev"
ADMIN_EMAIL = "admin@renderly.dev"


def seed_default_user(db: Session) -> User:
    user = db.query(User).filter(User.email == DEFAULT_DEMO_EMAIL).first()
    if user:
        return user
    user = User(
        email=DEFAULT_DEMO_EMAIL,
        full_name="Demo User",
        hashed_password=get_password_hash("renderly123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_admin_user(db: Session) -> None:
    if db.query(User).filter(User.email == ADMIN_EMAIL).first():
        return
    admin = User(
        email=ADMIN_EMAIL,
        full_name="Renderly Admin",
        hashed_password=get_password_hash("renderlyAdmin123"),
        is_admin=True,
    )
    db.add(admin)
    db.commit()


def seed_sample_project(db: Session, owner: User) -> None:
    if db.query(Project).filter(Project.slug == "demo-landing").first():
        return
    project = Project(
        owner_id=owner.id,
        title="Renderly демо",
        slug="demo-landing",
        description="Демо-лендинг с базовыми блоками",
        theme={
            "page_bg": "#f8fafc",
            "text_color": "#0f172a",
            "accent": "#6366f1",
            "header_bg": "#ffffff",
            "header_text": "#0f172a",
            "footer_bg": "#0f172a",
            "footer_text": "#ffffff",
        },
        settings={"footer_text": "Renderly • No-code редактор"},
    )
    db.add(project)
    db.flush()

    definitions = {d.key: d for d in db.query(BlockDefinition).all()}
    blocks = [
        BlockInstance(
            project_id=project.id, definition_id=definitions["hero"].id, order_index=0, config=definitions["hero"].default_config
        ),
        BlockInstance(
            project_id=project.id,
            definition_id=definitions["feature-grid"].id,
            order_index=1,
            config=definitions["feature-grid"].default_config,
        ),
        BlockInstance(
            project_id=project.id,
            definition_id=definitions["cta"].id,
            order_index=2,
            config=definitions["cta"].default_config,
        ),
    ]
    db.add_all(blocks)
    db.commit()


def seed_default_theme_template(db: Session) -> None:
    if db.query(ThemeTemplate).filter(ThemeTemplate.slug == "renderly-default").first():
        return
    db.add(
        ThemeTemplate(
            name="Renderly Default",
            slug="renderly-default",
            description="Базовая тема Renderly",
            palette={
                "page_bg": "#f8fafc",
                "text_color": "#0f172a",
                "accent": "#6366f1",
                "header_bg": "#ffffff",
                "header_text": "#0f172a",
                "footer_bg": "#0f172a",
                "footer_text": "#ffffff",
            },
        )
    )
    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        seed_block_definitions(db)
        user = seed_default_user(db)
        seed_sample_project(db, user)
        seed_default_theme_template(db)
        seed_admin_user(db)
        print("Seed data applied.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
