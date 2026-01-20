
## THIS WILL BE ADDED INTO MODELS.PY FILE ##
## THIS WILL NOT EXIST AS A SEPARATE FILE ##
## DON'T DUPLICATE IMPORTS OR EXISTING MODELS ##



class AgentPersonaBase(SQLModel):
    """Base model for Agents's instance of a Persona"""

    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    # what other customization fields should we add?


class AgentPersonaCreate(AgentPersonaBase):
    persona_id: uuid.UUID


class AgentPersonaUpdate(SQLModel):
    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)


class AgentPersona(AgentPersonaBase, table=True):
    """Database model for User's instance of a Persona"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: uuid.UUID = Field(
        foreign_key="agent.id", nullable=False, ondelete="CASCADE"
    )
    persona_id: uuid.UUID = Field(foreign_key="persona.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )

class AgentPersonaPublic(UserPersonaBase):
    """Public model for UserPersona API responses"""

    id: uuid.UUID
    agent_id: uuid.UUID
    persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AgentPersonasPublic(SQLModel):
    """Collection model for AgentPersona API responses"""

    data: list[AgentPersonaPublic]
    count: int


