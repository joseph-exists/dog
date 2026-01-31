


<!-- # PREVIOUS GET AGENT INSTANCE FUNCTION
# async def get_agent_instance(
#     session: AsyncSession,
#     slug: str,
# ) -> Agent[Any, Any] | None:
#     """
#     Get basic agent instance from database UserAgentConfig (no tools).

#     Instantiates a PydanticAI Agent using the configuration stored in the database.
#     Uses the model_name and system_prompt from UserAgentConfig.

#     For agents with A2A tools, use get_agent_instance_with_tools() instead.
#     """
#     config = await get_agent_config(session, slug)



#     if config and config.is_enabled:
#         system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

#         agent = Agent(config.model_name, system_prompt=system_prompt)
#         logger.debug(
#             f"Instantiated database agent: {config.slug} with model {config.model_name}"
#         )
#         return agent

#     return None -->

<!-- # async def resolve_user_credentials(
#     session: AsyncSession,
#     user_id: uuid.UUID,
#     agent_config: UserAgentConfig,
# ) -> tuple[str, str | None, str | None, str | None]:
#     """
#     Resolve user's credentials for an agent.

#     Returns:
#         Tuple of (effective_model_name, decrypted_api_key, provider_type, base_url)
#     """



#     effective_model_name = agent_config.model_name
#     if settings and settings.model_name_override:
#         effective_model_name = settings.model_name_override
#         logger.debug(
#             f"Using model override '{effective_model_name}' for agent {agent_config.slug}"
#         )

#     provider_type_str = (
#         effective_model_name.split(":")[0] if ":" in effective_model_name else "openai"
#     )
#     normalized_type = provider_type_str.lower()
#     provider_type_stmt = await session.exec(
#         select(LLMProviderType).where(
#             func.lower(LLMProviderType.name) == normalized_type
#         )
#     )
#     provider_type = provider_type_stmt.one_or_none()
#     if not provider_type:
#         logger.warning(
#             f"Unknown provider type '{provider_type_str}' in model '{effective_model_name}'"
#         )
#         return effective_model_name, None, None, None
#     provider_type_name = provider_type.name
#     provider_type_id = provider_type.id

#     provider: UserAccessProvider | None = None

#     if settings and settings.provider_id:
#         provider_result = await session.exec(
#             select(UserAccessProvider).where(
#                 UserAccessProvider.id == settings.provider_id,
#                 UserAccessProvider.is_enabled,
#             )
#         )
#         provider_row = provider_result.one_or_none()
#         provider = (
#             provider_row[0]
#             if provider_row and not isinstance(provider_row, UserAccessProvider)
#             else provider_row
#         )
#         if provider:
#             logger.debug(
#                 f"Using explicit provider '{provider.name}' for agent {agent_config.slug}"
#             )
#             if not provider.provider_type_id:
#                 # Legacy payloads used provider_type name; fail fast and log loudly.
#                 logger.error(
#                     "provider_type_id missing on UserAccessProvider %s during agent resolution",
#                     provider.id,
#                 )

#     if not provider:
#         default_result = await session.exec(
#             select(UserAccessProvider).where(
#                 UserAccessProvider.user_id == user_id,
#                 UserAccessProvider.provider_type_id == provider_type_id,
#                 UserAccessProvider.is_default,
#                 UserAccessProvider.is_enabled,
#             )
#         )
#         provider_row = default_result.one_or_none()
#         provider = (
#             provider_row[0]
#             if provider_row and not isinstance(provider_row, UserAccessProvider)
#             else provider_row
#         )
#         if provider:
#             logger.debug(
#                 f"Using default provider '{provider.name}' for agent {agent_config.slug}"
#             )
#             if not provider.provider_type_id:
#                 # Legacy payloads used provider_type name; fail fast and log loudly.
#                 logger.error(
#                     "provider_type_id missing on UserAccessProvider %s during agent resolution",
#                     provider.id,
#                 )

#     if not provider:
#         logger.debug(
#             f"No user provider for agent {agent_config.slug}, using env vars"
#         )
#         return effective_model_name, None, provider_type_name, None

#     api_key = decrypt_api_key(provider.api_key_encrypted)
#     base_url = provider.base_url
#     logger.debug(
#         f"Resolved credentials: api_key=***{api_key[-4:] if api_key else 'None'}, base_url={base_url}"
#     )
#     return effective_model_name, api_key, provider_type_name, base_url


# def create_model_with_credentials(
#     model_name: str,
#     api_key: str | None,
#     provider_type: str | None,
#     base_url: str | None = None,
# ) -> Any:
#     """
#     Create a PydanticAI model with user credentials.

#     For openai_compatible providers, always creates an OpenAIProvider even
#     without an API key — some servers (Ollama, local vLLM) don't need one,
#     and PydanticAI doesn't recognize "openai_compatible" as a provider prefix.
#     """

#     if normalized_type == OPENAI_COMPATIBLE:
#         compat_provider = OpenAIProvider(
#             api_key=api_key or "not-needed",
#             base_url=base_url,
#         )
#         return OpenAIChatModel(model_id, provider=compat_provider)

#     if not api_key:
#         return model_name

#     if normalized_type == OPENAI:
#         openai_provider = OpenAIProvider(api_key=api_key, base_url=base_url)
#         return OpenAIChatModel(model_id, provider=openai_provider)

#     if normalized_type == ANTHROPIC:
#         anthropic_provider = AnthropicProvider(api_key=api_key, base_url=base_url)
#         return AnthropicModel(model_id, provider=anthropic_provider)

#     if normalized_type == GOOGLE:
#         google_provider = GoogleProvider(api_key=api_key)
#         return GoogleModel(model_id, provider=google_provider)

#     logger.warning(f"Unknown provider type '{provider_type}', using model name directly")
#     return model_name -->
