from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_revision import ProjectRevision
from app.models.block_definition import BlockDefinition
from app.models.block_instance import BlockInstance
from app.services.publisher import snapshot_project


def record_revision(
    db: Session,
    project: Project,
    user_id: int | None,
    action: str,
) -> ProjectRevision:
    snapshot = snapshot_project(project)
    previous = (
        db.query(ProjectRevision)
        .filter(ProjectRevision.project_id == project.id)
        .order_by(ProjectRevision.created_at.desc())
        .first()
    )
    diff = compute_diff(previous.snapshot if previous else None, snapshot)
    revision = ProjectRevision(
        project_id=project.id,
        user_id=user_id,
        action=action,
        snapshot=snapshot,
        diff=diff,
        created_at=datetime.utcnow(),
    )
    db.add(revision)
    db.commit()
    db.refresh(revision)
    return revision


def _block_identifier(block: dict) -> str:
    return str(block.get("id") or f"{block.get('definition_key')}:{block.get('order_index')}")


def compute_diff(previous: dict | None, current: dict) -> dict:
    if not previous:
        return {
            "block_count": {"before": 0, "after": len(current["blocks"])},
            "added": [block.get("definition_key") for block in current["blocks"]],
            "removed": [],
            "changed": [],
            "theme_changed": True,
        }
    prev_blocks = {_block_identifier(block): block for block in previous.get("blocks", [])}
    curr_blocks = {_block_identifier(block): block for block in current.get("blocks", [])}
    added = [block.get("definition_key") for key, block in curr_blocks.items() if key not in prev_blocks]
    removed = [block.get("definition_key") for key, block in prev_blocks.items() if key not in curr_blocks]
    changed = []
    for key in curr_blocks.keys() & prev_blocks.keys():
        if curr_blocks[key].get("config") != prev_blocks[key].get("config"):
            changed.append(curr_blocks[key].get("definition_key"))
    prev_sequence = [
        _block_identifier(block)
        for block in previous.get("blocks", [])
        if _block_identifier(block) in curr_blocks
    ]
    curr_sequence = [
        _block_identifier(block)
        for block in current.get("blocks", [])
        if _block_identifier(block) in prev_blocks
    ]
    order_changed = prev_sequence != curr_sequence
    theme_changed = previous["project"].get("theme") != current["project"].get("theme")
    return {
        "block_count": {"before": len(prev_blocks), "after": len(curr_blocks)},
        "added": added,
        "removed": removed,
        "changed": changed,
        "order_changed": order_changed,
        "theme_changed": theme_changed,
    }


def restore_revision(db: Session, project: Project, revision: ProjectRevision) -> Project:
    snapshot = revision.snapshot
    project_data = snapshot.get("project", {})
    project.title = project_data.get("title", project.title)
    project.description = project_data.get("description")
    project.theme = project_data.get("theme") or {}
    project.settings = project_data.get("settings") or {}

    for block in list(project.blocks):
        db.delete(block)
    db.flush()

    definitions = {
        d.key: d
        for d in db.query(BlockDefinition)
        .filter(BlockDefinition.key.in_([b.get("definition_key") for b in snapshot.get("blocks", [])]))
        .all()
    }
    for order, block_data in enumerate(snapshot.get("blocks", [])):
        definition = definitions.get(block_data.get("definition_key"))
        if not definition:
            continue
        db.add(
            BlockInstance(
                project_id=project.id,
                definition_id=definition.id,
                order_index=block_data.get("order_index", order),
                config=block_data.get("config") or definition.default_config,
                translations=block_data.get("translations") or {},
            )
        )
    db.commit()
    db.refresh(project)
    return project
