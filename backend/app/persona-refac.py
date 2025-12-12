

class UserPersonaBase(SQLModel):
    """Base model for User's instance of a Persona"""

    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)


class UserPersona(UserPersonaBase, table=True):
    """Database model for User's instance of a Persona"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    persona_id: uuid.UUID = Field(foreign_key="persona.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )  

class UserPersonaPublic(UserPersonaBase):
    """Public model for UserPersona API responses"""

    id: uuid.UUID
    user_id: uuid.UUID
    persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserPersonasPublic(SQLModel):
    """Collection model for UserPersona API responses"""

    data: list[UserPersonaPublic]
    count: int

class PersonaBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    long_description: str | None = Field(default=None)
    general_domain: str | None = Field(default=None, max_length=255)
    specific_domain: str | None = Field(default=None, max_length=255)
    general_domain_high: str | None = Field(default=None, max_length=255)
    specific_domain_high: str | None = Field(default=None, max_length=255)
