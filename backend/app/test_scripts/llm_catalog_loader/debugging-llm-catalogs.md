
tinyfoot=# select alpha_provider_type_id from user_access_provider where base_url='https://api.openai.com/v1' limit 1;
        alpha_provider_type_id        
--------------------------------------
 673f1787-8474-4e1c-986c-8e19f14c989c

tinyfoot=# select name from provider_type where id ='673f1787-8474-4e1c-986c-8e19f14c989c';
  name  
--------
 openai

tinyfoot=# select model_id from llmmodel where primary_provider_type_id='673f1787-8474-4e1c-986c-8e19f14c989c';
   model_id    
---------------
 gpt-3.5-turbo
 gpt-4-turbo
 gpt-4o
 gpt-4o-mini
 o1
 o1-mini
(6 rows)






select name from provider_type where id ='673f1787-8474-4e1c-986c-8e19f14c989c';


tinyfoot=# \d llmmodel;
                                 Table "public.llmmodel"
             Column             |          Type          | Collation | Nullable | Default 
--------------------------------+------------------------+-----------+----------+---------
 model_id                       | character varying(100) |           | not null | 
 display_name                   | character varying(100) |           | not null | 
 description                    | character varying(500) |           |          | 
 context_window                 | integer                |           |          | 
 is_default                     | boolean                |           | not null | 
 is_enabled                     | boolean                |           | not null | 
 is_deprecated                  | boolean                |           | not null | 
 sort_order                     | integer                |           | not null | 
 has_vision                     | boolean                |           |          | 
 has_function_calling           | boolean                |           |          | 
 has_streaming                  | boolean                |           |          | 
 has_json_mode                  | boolean                |           |          | 
 id                             | uuid                   |           | not null | 
 secondary_capabilities         | jsonb                  |           |          | 
 is_system                      | boolean                |           | not null | 
 multiple_provider_type_support | boolean                |           | not null | 
 primary_provider_type_id       | uuid                   |           | not null | 
 owner_id                       | uuid                   |           | not null | 
Indexes:
    "llmmodel_pkey" PRIMARY KEY, btree (id)
    "ix_llmmodel_is_system" btree (is_system)
    "ix_llmmodel_primary_provider_type_id" btree (primary_provider_type_id)
    "uq_llmmodel_provider_model" UNIQUE CONSTRAINT, btree (primary_provider_type_id, model_id)
Foreign-key constraints:
    "llmmodel_primary_provider_type_id_fkey" FOREIGN KEY (primary_provider_type_id) REFERENCES provider_type(id)


Task:
we need to load the models in models-original.csv into the llmmodel table.
we can do this directly in psql using insert statements, or we can load it using a script.


for models-original.csv, we can apply the following mapping:

provider_name, primary_provider_type_id
OpenAI, 673f1787-8474-4e1c-986c-8e19f14c989c
Anthropic, 008dc763-4309-43cd-ba5f-1eb1323a0964
OpenAI Compatible, e09ade10-8563-4748-8deb-1a6c87c97134
Custom, 186672e2-f50a-4457-a7dd-a50084077ff7
Empty, 37520103-0644-4d29-99b6-583eb0996370
Google, ae07eb0b-929e-4844-8b75-4fe6abca09df

## Seeding models-original.csv

**Python script (recommended):**
```bash
cd backend && uv run python app/test_scripts/llm_catalog_loader/seed_models.py
# or with docker:
docker compose exec backend uv run python app/test_scripts/llm_catalog_loader/seed_models.py
```

**psql script:**
```bash
# From host (replace with your connection string):
psql $DATABASE_URL -f app/test_scripts/llm_catalog_loader/seed_models_psql.sql

# Or via docker (pipe SQL from host into db container):
docker compose exec -T db psql -U postgres -d app < app/test_scripts/llm_catalog_loader/seed_models_psql.sql
```