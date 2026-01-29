
We have replaced the LLMProvider.provider_type string with a provider_type_id FK and introduced the provider_type reference table plus canonical lookup helpers (see models.py:171‑235).

-> alembic revision, autogenerate, and upgrade are complete, and manual seeding has been completed.


tables look as follows:


```sql
tinyfoot=# \d provider_type
tinyfoot=# \d provider_type
                    Table "public.provider_type"
  Column   |          Type          | Collation | Nullable | Default
-----------+------------------------+-----------+----------+---------
 name      | character varying(30)  |           | not null |
 details   | character varying(500) |           |          |
 validated | boolean                |           | not null |
 is_system | boolean                |           | not null |
 id        | uuid                   |           | not null |
Indexes:
    "provider_type_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "llmprovider" CONSTRAINT "llmprovider_provider_type_id_fkey" FOREIGN KEY (provider_type_id) REFERENCES provider_type(id)
    TABLE "userllmprovider" CONSTRAINT "userllmprovider_provider_type_id_fkey" FOREIGN KEY (provider_type_id) REFERENCES provider_type(id)


tinyfoot=# \d llmprovider
                            Table "public.llmprovider"
       Column       |            Type             | Collation | Nullable | Default
--------------------+-----------------------------+-----------+----------+---------
 name               | character varying(100)      |           | not null |
 base_url           | character varying(500)      |           |          |
 description        | character varying(500)      |           |          |
 is_enabled         | boolean                     |           | not null |
 is_system          | boolean                     |           | not null |
 id                 | uuid                        |           | not null |
 is_deleted         | boolean                     |           | not null |
 deleted_at         | timestamp without time zone |           |          |
 created_at         | timestamp without time zone |           | not null |
 updated_at         | timestamp without time zone |           | not null |
 created_by_user_id | uuid                        |           |          |
 provider_type_id   | uuid                        |           |          |
Indexes:
    "llmprovider_pkey" PRIMARY KEY, btree (id)
    "ix_llmprovider_is_deleted" btree (is_deleted)
Foreign-key constraints:
    "llmprovider_created_by_user_id_fkey" FOREIGN KEY (created_by_user_id) REFERENCES "user"(id)
    "llmprovider_provider_type_id_fkey" FOREIGN KEY (provider_type_id) REFERENCES provider_type(id)
Referenced by:
    TABLE "llmmodel" CONSTRAINT "llmmodel_provider_id_fkey" FOREIGN KEY (provider_id) REFERENCES llmprovider(id)


tinyfoot=# \d userllmprovider
                          Table "public.userllmprovider"
      Column       |            Type             | Collation | Nullable | Default
-------------------+-----------------------------+-----------+----------+---------
 name              | character varying(100)      |           | not null |
 is_enabled        | boolean                     |           | not null |
 is_default        | boolean                     |           | not null |
 base_url          | character varying(500)      |           |          |
 description       | character varying(500)      |           |          |
 id                | uuid                        |           | not null |
 user_id           | uuid                        |           | not null |
 api_key_encrypted | character varying(1000)     |           | not null |
 created_at        | timestamp without time zone |           | not null |
 updated_at        | timestamp without time zone |           | not null |
 last_tested_at    | timestamp without time zone |           |          |
 last_test_success | boolean                     |           |          |
 provider_type_id  | uuid                        |           |          |
Indexes:
    "userllmprovider_pkey" PRIMARY KEY, btree (id)
    "ix_userllmprovider_user_id" btree (user_id)
Foreign-key constraints:
    "userllmprovider_provider_type_id_fkey" FOREIGN KEY (provider_type_id) REFERENCES provider_type(id)
    "userllmprovider_user_id_fkey" FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
Referenced by:
    TABLE "agent_configs" CONSTRAINT "agent_configs_user_provider_fkey" FOREIGN KEY (user_provider) REFERENCES userllmprovider(id)
    TABLE "room_participant_bindings" CONSTRAINT "room_participant_bindings_user_llm_provider_id_fkey" FOREIGN KEY (user_llm_provider_id) REFERENCES userllmprovider(id)

```

done: bound Relationship attributes after every class so providers/models can eagerly load their type row instead of re-querying by name.

all models changes, including bound relationship attributes follow patterns listed in backend/docs/DATA_MODEL_RULES.md

## current status

all models should mirror the catalog pattern introduced for LLMProviderBase (FK) and LLMProviderPublic (denormalized string).

provider_type in responses, is only on public/response models, not in base/table fields.

B) Reference example: post‑definition relationships (UserLLMProvider + ProviderType)
Per DATA_MODEL_RULES.md, bind after all classes exist:

# backend/app/models.py (post-definition section)

# LLMProviderType <-> UserLLMProvider relationship
LLMProviderType.user_providers = Relationship(
    back_populates="provider_type",
    sa_relationship_kwargs={"lazy": "selectin"},
)

UserLLMProvider.provider_type = Relationship(
    back_populates="user_providers",
    sa_relationship_kwargs={"lazy": "selectin"},
)
This matches the pattern already used for LLMProviderType <-> LLMProvider in models.py (line 3906).



Details

Replaced provider_type: str with provider_type_id: uuid.UUID | None in UserLLMProviderBase and added the same FK field to UserLLMProviderUpdate.
Added denormalized provider_type: str | None to UserLLMProviderPublic for response convenience.
Bound LLMProviderType.user_providers ↔ UserLLMProvider.provider_type in the post‑definition relationships block.

### REFERENCE NOTES BELOW - NOT PART OF RUNBOOK
Catalog/Provider Refactor Plan

done:
bind Relationship attributes after every class so providers/models can eagerly load their type row instead of re-querying by name.

active:   CRUD filters/serializers - update crud.py so get_llm_providers, get_llm_models, and get_llm_models_grouped accept either a type ID or use a single join (and user models join providers to pull type info in one go), then have the routes in llm_catalog.py (lines 36-393) pass along those IDs and emit provider_type.name in LLMProviderPublic/LLMModelPublic so the frontend still sees the same label without the redundant lookups we currently do per row.

believe this is done - need to validate.  Streamlined custom-model endpoints. When create_custom_model and list_custom_models call crud.get_llm_provider/get_user_models, loads the provider/ type in one query (e.g., selectinload or explicit joins) so we can populate provider_type + provider_name in the response without hitting the DB repeatedly for each model.

need to verify/review.
llm_providers routes in sync. Any route in llm_providers.py that filters by provider type should be respecting the new relationships when encrypting/validating API keys.


We adjusted the schema model, then updated CRUD helpers/routes to rely on it, and finally optimized the custom-model helpers so catalog responses stay efficient. 


refactor requirements:


done: llm_providers.py
done: llm_catalog.py
done: crud.py
done: relationship bindings  




we'll need to do a deeper dive on:

useLlmCatalog.ts hook
useLlmProviders.ts hook
llmCatalogService.ts 
llmProviderService.ts 

then and review/test:
ModelBadge.tsx
ModelCombobox.tsx
ProviderModelSelector.tsx


will need to update the provider-model-reference-card.md (will want to do a deep review of all docs to make sure the old pattern is scrubbed) - anything that references LLMProviderType or provider_type should be updated.


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
