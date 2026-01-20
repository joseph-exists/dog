
## THIS WILL BE ADDED INTO MODELS.PY FILE ##
## THIS WILL NOT EXIST AS A SEPARATE FILE ##
## DON'T DUPLICATE IMPORTS OR EXISTING MODELS ##



class AgentPersonaBase(SQLModel):
    """Base model for an agent's library entry of a Persona."""

    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    # what other customization fields should we add?


class AgentPersonaCreate(AgentPersonaBase):
    persona_id: uuid.UUID


class AgentPersonaUpdate(SQLModel):
    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)


class AgentPersona(AgentPersonaBase, table=True):
    """Database model for an agent's library entry of a Persona."""

    __tablename__ = "agent_personas"
    __table_args__ = (
        UniqueConstraint("agent_id", "persona_id", name="uq_agent_personas_agent_persona"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: uuid.UUID = Field(
        foreign_key="agent_configs.id", nullable=False, ondelete="CASCADE"
    )
    persona_id: uuid.UUID = Field(
        foreign_key="persona.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )


class AgentPersonaPublic(AgentPersonaBase):
    """Public model for AgentPersona API responses."""

    id: uuid.UUID
    agent_id: uuid.UUID
    persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AgentPersonasPublic(SQLModel):
    """Collection model for AgentPersona API responses."""

    data: list[AgentPersonaPublic]
    count: int


# Post-definition relationship binding (per DATA_MODEL_RULES.md)
AgentConfig.agent_personas = Relationship(
    back_populates="agent_config",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)
AgentPersona.agent_config = Relationship(back_populates="agent_personas")

Persona.agent_personas = Relationship(back_populates="persona")
AgentPersona.persona = Relationship(back_populates="agent_personas")
