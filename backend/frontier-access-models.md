class FrontierAccessProviderBase(SQLModel):
    """Model for holding frontier model access providers for cloning and updates"""
    base_url: str | None = Field(default=None, max_length=100, description="Endpoint URL")
    testing_api_key: str = Field(min_length=1, description="Plain text API key for testing endpoint (will be encrypted)")
    name: str = Field(max_length=100, description="should be directly mappable to provider_type - not going to enforce it.")
    is_enabled: bool = Field(default=True, description="Whether this provider is active")
    is_visible: bool = Field(default=False, description="is this shared for people to clone?")
    is_deprecated: bool =   Field(default=False, description="are people still allowed to clone")
    description: str | None = Field(default=None, max_length=500)

class FrontierAccessProviderCreate(FrontierAccessProviderBase):
    """Input model for creating provider - accepts plain API key."""
    name: str = Field(max_length=100, description="should be directly mappable to provider_type - not going to enforce it.")
    testing_api_key: str = Field(min_length=1, description="Plain text API key for testing endpoint (will be encrypted)")
    base_url: str | None = Field(default=None, max_length=100, description="Endpoint URL")
    is_enabled: bool = Field(default=True, description="Whether this provider is active")
    is_visible: bool = Field(default=False, description="is this shared for people to clone?")
    description: str | None = Field(default=None, max_length=500, description="reason for this to exist")

class FrontierAccessProviderUpdate(FrontierAccessProviderBase):
    """Update model - all fields optional."""
    name: str | None = Field(default=None, max_length=100)
    is_enabled: bool | None = None
    is_default: bool | None = None
    is_validated: bool | None = None
    # users validate an access provider by pushing the 'Test' button on the front end
    base_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=500)
    api_key: str | None = Field(default=None, description="New API key to encrypt, if changing")


class FrontierAccessProvider(FrontierAccessProviderBase, table=True):
    """
    Database model for frontier access provider configurations.

    Stores encrypted frontier access keys for test and validation.

    """
    __tablename__ = "frontier_access_provider"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    provider_id: uuid.UUID = Field(
        foreign_key="provider_type.id",
        nullable=False,
        index=True,
        description="API base (anthropic, google, openai, openai_compatible, multiple, custom, empty)"
    )

    # Encrypted API key (never store plain text)
    api_key_encrypted: str = Field(max_length=1000, description="Fernet-encrypted API key")

    # Audit timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Connection test tracking
    last_tested_at: datetime | None = Field(default=None)
    last_test_success: bool | None = Field(default=None)

class FrontierAccessProviderPublic(FrontierAccessProviderBase):
    """Public API response - NEVER includes API key."""
    id: uuid.UUID
    base_url: str
    is_enabled: bool
    is_validated: bool
    created_at: datetime
    updated_at: datetime
    last_tested_at: datetime | None
    last_test_success: bool | None


class FrontierAccessProvidersPublic(SQLModel):
    """Collection response for FrontierAccessProviders."""
    data: list[FrontierAccessProviderPublic]
    count: int
