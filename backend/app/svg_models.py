# models/svg_asset.py
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

## UNDER REVIEW FOR IMPORT TO MODELS.PY
## NEEDS REVIEW AGAINST DATA_MODEL_RULES PRIOR TO INTEGRATION.


class SVGVisibility(str):
    PRIVATE = "private"
    PUBLIC = "public"


class SvgAssetBase(SQLModel):
    owner_id: uuid.UUID = Field(index=True)
    # 'visibility' lets you query quickly; enforce semantics in service layer
    visibility: str = Field(default=SVGVisibility.PRIVATE, index=True)

    name: str = Field(index=True)  # user-level name or label
    description: Optional[str] = None

    # strong semantic tagging: you said you already have a tags solution,
    # so this is just an FK list placeholder
    # e.g. many-to-many via svg_asset_tags table (not expanded here)

    # link to original private asset when this is a public copy
    source_private_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="svgasset.id",
        index=True,
    )


class SvgAsset(SvgAssetBase, table=True):
    __tablename__ = "svgasset"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # current storage choice: store SVG inline as text
    svg_markup: str

    # arbitrary metadata: prompt, model, style, etc.
    metadata: Optional[dict] = Field(default=None, sa_column_kwargs={"nullable": True})

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # relationships (will need to be added after based on data model rules)
    source_private: Optional["SvgAsset"] = Relationship(
        back_populates="public_copies",
        sa_relationship_kwargs=dict(remote_side="SvgAsset.id"),
    )
    public_copies: List["SvgAsset"] = Relationship(
        back_populates="source_private"
    )


class SvgAssetBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str] = None
    visibility: str  # "private" | "public"
    # tags come from your existing solution; assume list of tag IDs or names
    tags: List[str] = []


class SvgAssetCreatePrivate(BaseModel):
    name: str
    description: Optional[str] = None
    svg_markup: str
    tags: List[str] = []  # or tag IDs
    metadata: Optional[dict] = None


class SvgAssetCreatePublicFromPrivate(BaseModel):
    # ID of the user's private asset to copy from
    source_private_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None  # override or extend tags


class SvgAssetUpdatePrivate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    svg_markup: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class SvgAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    visibility: str
    name: str
    description: Optional[str] = None
    svg_markup: str  # if you later move to object storage, this can become a URL
    metadata: Optional[dict] = None
    tags: List[str]

    source_private_id: Optional[UUID] = None

    created_at: datetime
    updated_at: datetime