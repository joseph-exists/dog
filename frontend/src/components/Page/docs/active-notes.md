Below is the CLI that we have:

(app) josep@asimov:~/dog/backend/app/test_scripts/typer$ python main.py pages --help

 Usage: main.py pages [OPTIONS] COMMAND [ARGS]...

 Page layout management

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ list     List persisted page layouts.                                                                                    │
│ get      Get the page layout for a specific entity.                                                                      │
│ upsert   Create or overwrite a page layout for an entity.                                                                │
│ update   Update an existing page layout by page ID.                                                                      │
│ delete   Delete a persisted page layout.       


python main.py pages list -t user --json

returns all user pages for users in json blobs

 Usage: main.py pages list [OPTIONS]

 List persisted page layouts.

 Supports filtering by entity type/ID and prefix matching.
 Examples:     python main.py pages list     python main.py pages list --type story     python main.py pages list
 --type-prefix room --json

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --type         -t      TEXT     Filter by entity type                                                                    │
│ --entity-id    -e      TEXT     Filter by entity ID                                                                      │
│ --type-prefix          TEXT     Filter by entity type prefix                                                             │
│ --id-prefix            TEXT     Filter by entity ID prefix                                                               │
│ --limit                INTEGER  Maximum items to list [default: 20]                                                      │
│ --skip                 INTEGER  Pagination offset [default: 0]                                                           │
│ --json                          Output as JSON                                                                           │
│ --verbose      -v               Verbose output                                                                           │
│ --help                          Show this message and exit.                


here we have the page model (in a models.py on the backend)


# ============================================================================
# Page Layout Models 
# ============================================================================


class PageBase(SQLModel):
    """Shared properties for persisted page layouts."""

    entity_type: str = Field(max_length=50, index=True)
    entity_id: str = Field(max_length=255, index=True)
    layout_version: int = Field(default=1)
    layout_json: list[dict[str, Any]] = Field(sa_column=Column(JSONB))


class PageCreate(PageBase):
    """Input model for creating a page layout."""

    owner_id: uuid.UUID


class PageLayoutUpdate(SQLModel):
    """Update model for page layout."""

    layout_json: list[dict[str, Any]]
    layout_version: int | None = None


class Page(PageBase, table=True):
    """
    Persisted page layouts for entities.

    One layout per entity_type/entity_id pair.
    """

    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("entity_type", "entity_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PagePublic(PageBase):
    """Public response model for pages."""

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class PagesPublic(SQLModel):
    """Paginated collection of pages."""
    data: list[PagePublic]
    count: int



and we have pages_crud.py :


"""
CRUD operations for persisted page layouts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Page


async def get_page_by_entity(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> Page | None:
    """Fetch a page layout by entity type/id."""
    statement = select(Page).where(
        Page.entity_type == entity_type,
        Page.entity_id == entity_id,
    )
    result = await session.exec(statement)
    return result.one_or_none()


async def get_page_by_id(session: AsyncSession, page_id: UUID) -> Page | None:
    """Fetch a page layout by page ID."""
    return await session.get(Page, page_id)


async def search_pages(
    session: AsyncSession,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    entity_type_prefix: str | None = None,
    entity_id_prefix: str | None = None,
    owner_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Page], int]:
    """Search page layouts with optional entity filters."""
    filters = []
    if entity_type:
        filters.append(Page.entity_type == entity_type)
    if entity_id:
        filters.append(Page.entity_id == entity_id)
    if entity_type_prefix:
        filters.append(Page.entity_type.startswith(entity_type_prefix))
    if entity_id_prefix:
        filters.append(Page.entity_id.startswith(entity_id_prefix))
    if owner_id:
        filters.append(Page.owner_id == owner_id)

    statement = (
        select(Page)
        .where(*filters)
        .order_by(desc(Page.updated_at))
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    pages = result.all()

    count_statement = select(func.count()).select_from(Page).where(*filters)
    count_result = await session.exec(count_statement)
    count = count_result.one()
    return list(pages), count


async def create_page_layout(
    session: AsyncSession,
    *,
    owner_id: UUID,
    entity_type: str,
    entity_id: str,
    layout_json: list[dict[str, Any]],
    layout_version: int = 1,
) -> Page:
    """Create a new page layout for an entity."""
    page = Page(
        owner_id=owner_id,
        entity_type=entity_type,
        entity_id=entity_id,
        layout_json=layout_json,
        layout_version=layout_version,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(page)
    await session.flush()
    await session.refresh(page)
    return page


async def update_page_layout(
    session: AsyncSession,
    page: Page,
    *,
    layout_json: list[dict[str, Any]],
    layout_version: int | None = None,
) -> Page:
    """Update an existing page layout."""
    page.layout_json = layout_json
    if layout_version is not None:
        page.layout_version = layout_version
    page.updated_at = datetime.utcnow()
    session.add(page)
    await session.flush()
    await session.refresh(page)
    return page


async def delete_page_layout(session: AsyncSession, page: Page) -> None:
    """Delete a persisted page layout."""
    await session.delete(page)
    await session.flush()


 need: 
 CodeBlock?
 StoryPlayerBlock?

 What am I trying to ask.  What do I want to see.

 I want:

 A cli exposed which enables:
 	- create a page
 		- ok, what kind?
 	- what kind of pages can I make?
 		- pages for these kinds of entities! 
 	- oh, ok, I want to make a page for entity type X. (js: review entity types, might not meet ontol-frame)
 		- ok, your page is created for entity type X.  do you want to use a template?
 	- what templates are there for entity type X.
 		- here they are!

 		yes, let's use a template
 		no thanks! (x)
 	- what operations do i have available now?
 		- here you can do these things!
 			list of available things they can do, structured by class or type


 	I want to make a Page for a Story!
		ok! story-id or create one?
		story-id: zoom zoom zipper

		command:typer page new --story --new -f story.json
		command typer page new --story --id 'storyid'

			zippie doodah, here's your new page for your story with a brand new slug and id and here's the link for it!