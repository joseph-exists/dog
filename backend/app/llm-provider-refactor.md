
Catalog/Provider Refactor Plan

1. Strengthen the type table link. Replace the string provider_type columns in models.py (lines 177-230) with a provider_type_id foreign key to LLMProviderType ( (lines 140-170)), expose the new relationship there, and bind Relationship attributes after every class so providers/models can eagerly load their type row instead of re-querying by name.
2. Align CRUD filters/serializers. Update crud.py so get_llm_providers, get_llm_models, and get_llm_models_grouped accept either a type ID or use a single join against LLMProviderType (and user models join providers to pull type info in one go), then have the routes in llm_catalog.py (lines 36-393) pass along those IDs and emit provider_type.name in LLMProviderPublic/LLMModelPublic so the frontend still sees the same label without the redundant lookups we currently do per row.
3. Streamline custom-model endpoints. When create_custom_model and list_custom_models call crud.get_llm_provider/get_user_models, load the provider/ type in one query (e.g., selectinload or explicit joins) so you can populate provider_type + provider_name in the response without hitting the DB repeatedly for each model.
4. Keep llm_providers routes in sync. Any route in llm_providers.py that filters by provider type should look up the LLMProviderType row first (so switching to the table-based structure is seamless) and continue to respect the new relationships when encrypting/validating API keys.
This gives you a sequential refactor path: first adjust the schema model, then update CRUD helpers/routes to rely on it, and finally optimize the custom-model helpers so catalog responses stay efficient. Let me know if you’d like a branch-ready set of commits for each step.


refactor requirements:


update llm_providers.py
update llm_catalog.py
update crud.py
review relationship bindings for existing LLMProviderType table (if any) - review in both db and in models.py file

services review:
agent_instance.py
agent_registry_service.py


operational:
build & then alembic:
    alembic ->
        should drop the LLMProviderType table/indexes
        will need to review all schemas

update backend/app/test_scripts/llm_catalog_loader/load_catalog.py

may need to drop all existing agents - will pull down for recreating first - then re-seed.

will need to update the provider-model-reference-card.md (will want to do a deep review of all docs to make sure the old pattern is scrubbed)

then frontend:
review/test:
ModelBadge.tsx
ModelCombobox.tsx
ProviderModelSelector.tsx
useLlmCatalog.ts hook (do we need this hook?)
useLlmProviders.ts hook
llmCatalogService.ts (service and multiple hooks?)
llmProviderService.ts (another service - this one with downcase?)



as a user, I have an account with an llm access provider. i have 34 models available to me in my account, across 13 different llm providers.  not all accounts with this llm access provider will have this level of access. additionally, i have multiple API keys with this LLM access provider account, and those access keys give me access to different subsets of models and llm providers for those models.

as the same user, I have an account with OpenAI, an account with Google, etc.  These are my other llm access provider accounts, and within these accounts, each will have a set of API keys.  

as this user, I want to:

- Add an llm access provider account with a 1:1 relationship between that llm access provider and an API key.
	- name this account
    - add notes/details to this account (short text field)
	- add an API key for this named account (while we may branch in the future to enable more association between llm access provider accounts and API keys, we are limiting scope at this time.  however, we need to support the case where a user has three distinct named llm access provider accounts within our system for the same llm access provider - each with their own API key.  So I could have three OpenAI accounts, and they are represented as distinct accounts in our UI, and each have their own API key.)
	- with quick-add, link, or other method, add the llm provider types which are associated with accounts
		- sometimes, there is a 1:1 association with llm access providers and llm provider types.  this is the case with Anthropic, OpenAI, Gemini, etc. 
		- we need to explicitly support as a first class feature set adding those llm access providers which enable multiple llm provider types.  IE: using the PydanticAI Gateway allows for a very large superset.
		- some llm access providers supply an endpoint to request models which are available for a specific API key.  for the frontier llm access providers, this is a documented and available endpoint.  for other llm access providers, we will add them as we can, and/or we will allow the user to add when they have it.

	- validate (test API key.)
	- save to account with name.

as this user, I will want to:

Select this LLMAccessProvider/key when creating an agent, and see the list of available models.
Change an agent to use this key during all agent modification dialogs.

Know that if I use this agent in a room with other agents or users, my account settings or access provider details - including the name i've specified for the llm access provider - will not be exposed to other users.

Know that if I enable this as a public or shared agent, my llm access provider details will not be exposed to other users.

Know that if other users 'test-drive' or clone my public or shared agent, they will not be able to see or use my llm access provider details.
