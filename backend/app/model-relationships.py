
# User <-> UserLLMProvider relationship (both sides must be defined together)
User.llm_providers = Relationship(
    back_populates="owner",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
UserLLMProvider.owner = Relationship(back_populates="llm_providers")

# LLMProvider <-> LLMModel relationship (catalog models)
LLMProvider.models = Relationship(
    back_populates="provider",
    sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
)
LLMModel.provider = Relationship(back_populates="models")

# LLMProviderType <-> LLMProvider relationship
LLMProviderType.providers = Relationship(
    back_populates="provider_type",
    sa_relationship_kwargs={"lazy": "selectin"},
)
LLMProvider.provider_type = Relationship(
    back_populates="providers",
    sa_relationship_kwargs={"lazy": "selectin"},
)

# LLMProviderType <-> UserLLMProvider relationship
LLMProviderType.user_providers = Relationship(
    back_populates="provider_type",
    sa_relationship_kwargs={"lazy": "selectin"},
)
UserLLMProvider.provider_type = Relationship(
    back_populates="user_providers",
    sa_relationship_kwargs={"lazy": "selectin"},
)