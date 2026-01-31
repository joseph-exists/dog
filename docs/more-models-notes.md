tinyfoot=# select model_name from user_agent_configs;
     model_name     
--------------------
 openai:gpt-4o-mini
 jeepers creepers
 openai:gpt-4o-mini
(3 rows)

tinyfoot=# select provider_type from user_agent_configs;
 provider_type 
---------------
 openai
 openai
 openai
(3 rows)

tinyfoot=# select model_id from user_agent_configs;
               model_id               
--------------------------------------
 
 3fa85f64-5717-4562-b3fc-2c963f66afa6
 
(3 rows)

tinyfoot=# select name, model_id from user_agent_configs;
          name          |               model_id               
------------------------+--------------------------------------
 nothing wrong here pal | 
 Malcolm                | 3fa85f64-5717-4562-b3fc-2c963f66afa6
 Fred                   | 

 a: updated model_name default constructor to gpt-4o-mini (from openai:gpt-4o-mini) (frontend/src/services/agentService.ts)


provider type determines the provider spec needs.

tinyfoot=# \d llmmodel
                                Table "public.llmmodel"
         Column         |            Type             | Collation | Nullable | Default 
------------------------+-----------------------------+-----------+----------+---------
 model_id               | character varying(100)      |           | not null | 
 display_name           | character varying(100)      |           | not null | 
 description            | character varying(500)      |           |          | 
 context_window         | integer                     |           |          | 
 is_default             | boolean                     |           | not null | 
 is_enabled             | boolean                     |           | not null | 
 is_deprecated          | boolean                     |           | not null | 
 sort_order             | integer                     |           | not null | 
 has_vision             | boolean                     |           |          | 
 has_function_calling   | boolean                     |           |          | 
 has_streaming          | boolean                     |           |          | 
 has_json_mode          | boolean                     |           |          | 
 id                     | uuid                        |           | not null | 
 provider_id            | uuid                        |           | not null | 
 deprecated_at          | timestamp without time zone |           |          | 
 sunset_at              | timestamp without time zone |           |          | 
 is_deleted             | boolean                     |           | not null | 
 deleted_at             | timestamp without time zone |           |          | 
 created_at             | timestamp without time zone |           | not null | 
 updated_at             | timestamp without time zone |           | not null | 
 secondary_capabilities | jsonb                       |           |          | 
 is_system              | boolean                     |           | not null | 
 created_by_user_id     | uuid                        |           |          | 
Indexes:
    "llmmodel_pkey" PRIMARY KEY, btree (id)
    "ix_llmmodel_is_deleted" btree (is_deleted)
    "ix_llmmodel_is_system" btree (is_system)
    "ix_llmmodel_provider_id" btree (provider_id)
Foreign-key constraints:
    "llmmodel_created_by_user_id_fkey" FOREIGN KEY (created_by_user_id) REFERENCES "user"(id)
    "llmmodel_provider_id_fkey" FOREIGN KEY (provider_id) REFERENCES provider_type(id)

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
    TABLE "llmmodel" CONSTRAINT "llmmodel_provider_id_fkey" FOREIGN KEY (provider_id) REFERENCES provider_type(id)


Ok.  User Access Providers -

Frontier Case : (OpenAI, Anthropic, etc.)
 enable fast entry because it's one of them. 
 once they enter their API, we test with the available-models for that API KEY - that's the test.
 We save the results to A: somewhere linked to that UAP and B: somewhere just for us for funsies and tagging
 These results are then loaded when they select that saved API key for a model.


OpenAICompatible Case:
Ollama Case:
Gateway Case:
 


 
tinyfoot=# \d llmmodel
                                Table "public.llmmodel"
         Column         |            Type             | Collation | Nullable | Default 
------------------------+-----------------------------+-----------+----------+---------
 model_id               | character varying(100)      |           | not null | 
 display_name           | character varying(100)      |           | not null | 
 description            | character varying(500)      |           |          | 
 context_window         | integer                     |           |          | 
 is_default             | boolean                     |           | not null | 
 is_enabled             | boolean                     |           | not null | 
 is_deprecated          | boolean                     |           | not null | 
 sort_order             | integer                     |           | not null | 
 has_vision             | boolean                     |           |          | 
 has_function_calling   | boolean                     |           |          | 
 has_streaming          | boolean                     |           |          | 
 has_json_mode          | boolean                     |           |          | 
 id                     | uuid                        |           | not null | 
 provider_id            | uuid                        |           | not null | 
 deprecated_at          | timestamp without time zone |           |          | 
 sunset_at              | timestamp without time zone |           |          | 
 is_deleted             | boolean                     |           | not null | 
 deleted_at             | timestamp without time zone |           |          | 
 created_at             | timestamp without time zone |           | not null | 
 updated_at             | timestamp without time zone |           | not null | 
 secondary_capabilities | jsonb                       |           |          | 
 is_system              | boolean                     |           | not null | 
 created_by_user_id     | uuid                        |           |          | 
Indexes:
    "llmmodel_pkey" PRIMARY KEY, btree (id)
    "ix_llmmodel_is_deleted" btree (is_deleted)
    "ix_llmmodel_is_system" btree (is_system)
    "ix_llmmodel_provider_id" btree (provider_id)
Foreign-key constraints:
    "llmmodel_created_by_user_id_fkey" FOREIGN KEY (created_by_user_id) REFERENCES "user"(id)
    "llmmodel_provider_id_fkey" FOREIGN KEY (provider_id) REFERENCES provider_type(id)

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
    TABLE "llmmodel" CONSTRAINT "llmmodel_provider_id_fkey" FOREIGN KEY (provider_id) REFERENCES provider_type(id)

steps: create 

FrontierAccessProviderBase(SQLModel)
FrontierAccessProvider(FrontierAccessProviderBase, Table=True;)




frontier_access_provider
