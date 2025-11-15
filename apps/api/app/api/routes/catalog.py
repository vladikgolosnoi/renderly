from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_db
from app.models.block_definition import BlockDefinition
from app.schemas.block import (
    BlockDefinitionSchema,
    BlockDefinitionCreate,
    BlockDefinitionUpdate,
)
from app.models.user import User

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/blocks", response_model=list[BlockDefinitionSchema])
def list_blocks(db: Session = Depends(get_db)) -> list[BlockDefinition]:
    return db.query(BlockDefinition).order_by(BlockDefinition.category, BlockDefinition.name).all()


@router.post(
    "/blocks",
    response_model=BlockDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_block_definition(
    payload: BlockDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> BlockDefinition:
    if db.query(BlockDefinition).filter(BlockDefinition.key == payload.key).first():
        raise HTTPException(status_code=400, detail="Block key already exists")
    obj = BlockDefinition(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/blocks/{block_id}", response_model=BlockDefinitionSchema)
def update_block_definition(
    block_id: int,
    payload: BlockDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> BlockDefinition:
    obj = db.query(BlockDefinition).filter(BlockDefinition.id == block_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Block definition not found")
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(obj, key, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_block_definition(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> Response:
    obj = db.query(BlockDefinition).filter(BlockDefinition.id == block_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Block definition not found")
    db.delete(obj)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
