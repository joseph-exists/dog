
 
 ToolsMcTavishMakesToolsHappy | InternalMCP | null          | f           | aacdd0ce-f90a-43d6-8676-61c888ef43bb | 228d7ff2-960d-48b3-91a0-979034859cfe |              2 | 2026-03-20 13:44:46.535189 | 2026-03-20 13:45:09.395514 | perky-annoying-dodo-of-tempering

promptconfig:
tinyfoot=# \d prompt_configs;
                         Table "public.prompt_configs"
     Column     |            Type             | Collation | Nullable | Default
----------------+-----------------------------+-----------+----------+---------
 name           | character varying(150)      |           | not null |
 description    | character varying(1000)     |           |          |
 metadata_json  | json                        |           |          |
 is_archived    | boolean                     |           | not null |
 id             | uuid                        |           | not null |
 owner_id       | uuid                        |           |          |
 latest_version | integer                     |           | not null |
 created_at     | timestamp without time zone |           | not null |
 updated_at     | timestamp without time zone |           |          |
 slug           | character varying(100)      |           | not null |
Indexes:
    "prompt_configs_pkey" PRIMARY KEY, btree (id)
    "ix_prompt_configs_owner_id" btree (owner_id)
    "uq_prompt_config_slug" UNIQUE CONSTRAINT, btree (slug)
Foreign-key constraints:
    "prompt_configs_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES "user"(id)
Referenced by:
    TABLE "prompt_config_versions" CONSTRAINT "prompt_config_versions_prompt_config_id_fkey" FOREIGN KEY (prompt_config_id) REFERENCES prompt_configs(id) ON DELETE CASCADE
    TABLE "prompt_config_working_copies" CONSTRAINT "prompt_config_working_copies_prompt_config_id_fkey" FOREIGN KEY (prompt_config_id) REFERENCES prompt_configs(id) ON DELETE CASCADE
    TABLE "user_agent_configs" CONSTRAINT "user_agent_configs_prompt_config_id_fkey" FOREIGN KEY (prompt_config_id) REFERENCES prompt_configs(id)


 Tools | charming-crystal-anteater-of-art | validation of MCP server tools calls within the stack | ef8b71aa-89ac-41d4-bcbf-c2e75657b14d | 673f1787-8474-4e1c-986c-8e19f14c989c | 7dfa7ff3-b369-4ffd-9a6b-053fdbb0c51f | gpt-4o-mini | You are a planning agent for the Dog tech stack project. |                      | Use MCP affordance introspection before recommending composition actions. | null        | null        | null           | t          | f           | t          | personal | on_mention         | f              |                  10 | []           | a953bace-6656-48b2-8b9c-e33136b0108d | 228d7ff2-960d-48b3-91a0-979034859cfe | 2026-03-20 13:39:58.590933 | 2026-03-20 13:51:43.641746 |       1 | gpt-4o-mini | advisor    | null         |                  | latest                       |                              | f               | f


