from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict, validator


class BlockFieldSchema(BaseModel):
    key: str
    label: str
    type: Literal["text", "richtext", "media", "list", "button", "stats"]
    required: bool = False
    description: str | None = None
    default: Any | None = None


class BlockDefinitionSchema(BaseModel):
    id: int | None = None
    key: str
    name: str
    category: str
    description: str | None = None
    version: str
    schema: list[BlockFieldSchema] = Field(default_factory=list)
    default_config: dict[str, Any] = Field(default_factory=dict)
    ui_meta: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class BlockDefinitionCreate(BaseModel):
    key: str
    name: str
    category: str = "content"
    description: str | None = None
    version: str = "1.0.0"
    schema: list[BlockFieldSchema] = Field(default_factory=list)
    default_config: dict[str, Any] = Field(default_factory=dict)
    ui_meta: dict[str, Any] = Field(default_factory=dict)


class BlockDefinitionUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    version: str | None = None
    schema: list[BlockFieldSchema] | None = None
    default_config: dict[str, Any] | None = None
    ui_meta: dict[str, Any] | None = None


class BlockInstanceBase(BaseModel):
    definition_key: str
    order_index: int = 0
    config: dict[str, Any] = Field(default_factory=dict)
    translations: dict[str, dict[str, Any]] = Field(default_factory=dict)


class BlockInstanceCreate(BlockInstanceBase):
    ...


class BlockInstanceUpdate(BaseModel):
    order_index: int | None = None
    config: dict[str, Any] | None = None
    translations: dict[str, dict[str, Any]] | None = None


class BlockInstanceRead(BlockInstanceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
