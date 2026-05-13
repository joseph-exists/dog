class ShadowUserBase(SQLModel):
    """
    Base model for Shadow Forgejo user profile mappings.

    Maps application users to their shadow profile repository.
    This is system-managed and invisible to end users - they never
    interact with Forgejo directly. Acts like a CMS for user profiles.
    """
    forgejo_repo_name: str = Field(max_length=255)
    forgejo_repo_id: int | None = Field(default=None)


class ShadowUserCreate(ShadowUserBase):
    """Input model for creating ShadowUser mapping (system use only)"""
    user_id: uuid.UUID


class ShadowUserUpdate(SQLModel):
    """Update model for ShadowUser"""
    forgejo_repo_id: int | None = None


class ShadowUser(ShadowUserBase, table=True):
    """
    Database model for user profile shadow tracking.

    System-managed mapping between application User and their
    shadow profile repository. Users don't see or control this -
    all operations happen automatically via service accounts.

    The shadow-users service account owns all user profile repos.
    Repo naming: user-{uuid}
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        unique=True,
        nullable=False,
        ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ShadowUserPublic(ShadowUserBase):
    """Public API response model for ShadowUser (admin use only)"""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class ShadowUsersPublic(SQLModel):
    """Collection response for ShadowUsers"""
    data: list[ShadowUserPublic]
    count: int

# ==================== ShadowRepo Models ====================

class ShadowRepoBase(SQLModel):
    """
    Base model for entity-to-repository mappings.

    Each versioned entity (agent, story, etc.) gets its own
    Forgejo repository following repo-per-entity pattern.

    Repos are owned by service accounts (shadow-agents, shadow-stories)
    not by individual users. This is invisible to end users.
    """
    entity_type: str = Field(max_length=50)  # 'agent', 'story', 'user'
    entity_id: uuid.UUID
    forgejo_repo_name: str = Field(max_length=255)
    forgejo_repo_id: int | None = Field(default=None)


class ShadowRepoCreate(ShadowRepoBase):
    """Input model for creating ShadowRepo (system use only)"""
    owner_id: uuid.UUID  # User who owns this entity
    forked_from_id: uuid.UUID | None = None


class ShadowRepoUpdate(SQLModel):
    """Update model for ShadowRepo"""
    forgejo_repo_id: int | None = None
    forked_from_id: uuid.UUID | None = None


class ShadowRepo(ShadowRepoBase, table=True):
    """
    Database model for entity-to-repo mapping.

    Repo naming convention: {entity_type}-{entity_id_short}
    e.g., agent-550e8400

    Service account ownership by entity_type:
    - 'agent' → shadow-agents service account
    - 'story' → shadow-stories service account
    - 'user'  → shadow-users service account

    forked_from_id enables clone/fork tracking for branching.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
        description="Application user who owns this entity"
    )
    forked_from_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="shadowrepo.id",
        description="Source repo if this is a fork/clone"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ShadowRepoPublic(ShadowRepoBase):
    """Public API response model for ShadowRepo (admin use only)"""
    id: uuid.UUID
    owner_id: uuid.UUID
    forked_from_id: uuid.UUID | None
    created_at: datetime


class ShadowReposPublic(SQLModel):
    """Collection response for ShadowRepos"""
    data: list[ShadowRepoPublic]
    count: int

# ==================== ShadowVersion Models ====================

class ShadowVersionBase(SQLModel):
    """
    Base model for version/commit records.
    
    Each save operation creates a new version with full
    JSON snapshot of entity state.
    """
    commit_sha: str = Field(max_length=40)
    version_number: int
    message: str = Field(max_length=500)


class ShadowVersionCreate(ShadowVersionBase):
    """Input model for creating ShadowVersion"""
    shadow_repo_id: uuid.UUID
    snapshot_json: dict[str, Any]  # Full entity state
    created_by_id: uuid.UUID


class ShadowVersionUpdate(SQLModel):
    """Update model for ShadowVersion (immutable - not used)"""
    pass  # Versions are immutable


class ShadowVersion(ShadowVersionBase, table=True):
    """
    Database model for version records.
    
    Stores complete JSON snapshot of entity at each save.
    Pretty-printed JSON for git diff readability.
    Immutable once created - never updated.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    shadow_repo_id: uuid.UUID = Field(
        foreign_key="shadowrepo.id",
        nullable=False,
        ondelete="CASCADE"
    )
    snapshot_json: dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="Full entity state at this version"
    )
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        description="User who created this version"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ShadowVersionPublic(ShadowVersionBase):
    """Public API response model for ShadowVersion"""
    id: uuid.UUID
    shadow_repo_id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    # Note: snapshot_json excluded by default (large), use detail endpoint


class ShadowVersionDetail(ShadowVersionPublic):
    """Detailed response including full snapshot"""
    snapshot_json: dict[str, Any]


class ShadowVersionsPublic(SQLModel):
    """Collection response for ShadowVersions"""
    data: list[ShadowVersionPublic]
    count: int

# ============================================================================
# Shadow Forgejo Relationships
# ============================================================================

# ShadowUser → User (many-to-one)
ShadowUser.user = Relationship(
    back_populates="shadow_user",
    sa_relationship_kwargs={"lazy": "joined"}
)

# User → ShadowUser (one-to-one, reverse)
User.shadow_user = Relationship(
    back_populates="user",
    sa_relationship_kwargs={
        "uselist": False,  # One-to-one
        "lazy": "select"
    }
)

# ShadowRepo → User (many-to-one, entity owner)
ShadowRepo.owner = Relationship(
    back_populates="shadow_repos",
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.owner_id]",
        "lazy": "joined"
    }
)

# User → ShadowRepo (one-to-many, entities owned by user)
User.shadow_repos = Relationship(
    back_populates="owner",
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.owner_id]",
        "cascade": "all, delete-orphan",
        "lazy": "select"
    }
)

# ShadowRepo self-referential (forked_from)
ShadowRepo.forked_from = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.forked_from_id]",
        "remote_side": "[ShadowRepo.id]"
    }
)

ShadowRepo.forks = Relationship(
    back_populates="forked_from",
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.forked_from_id]"
    }
)

# ShadowVersion → ShadowRepo (many-to-one)
ShadowVersion.repo = Relationship(
    back_populates="versions",
    sa_relationship_kwargs={"lazy": "joined"}
)

# ShadowRepo → ShadowVersion (one-to-many)
ShadowRepo.versions = Relationship(
    back_populates="repo",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "lazy": "select",
        "order_by": "ShadowVersion.version_number.desc()"
    }
)

# ShadowVersion → User (many-to-one, created_by)
ShadowVersion.created_by = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowVersion.created_by_id]",
        "lazy": "joined"
    }
)