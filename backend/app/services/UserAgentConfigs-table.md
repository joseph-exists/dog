tinyfoot=# \d user_agent_configs
                          Table "public.user_agent_configs"
        Column        |            Type             | Collation | Nullable | Default 
----------------------+-----------------------------+-----------+----------+---------
 name                 | character varying(100)      |           |          | 
 slug                 | character varying(50)       |           |          | 
 description          | character varying(500)      |           |          | 
 user_access_provider | uuid                        |           |          | 
 provider_type        | character varying(30)       |           |          | 
 model_id             | uuid                        |           |          | 
 model_name           | character varying           |           |          | 
 system_prompt        | character varying           |           |          | 
 custom_system_prompt | character varying           |           |          | 
 instructions         | character varying           |           |          | 
 tool_config          | json                        |           |          | 
 deps_config          | json                        |           |          | 
 agent_metadata       | json                        |           |          | 
 is_enabled           | boolean                     |           |          | 
 is_clonable          | boolean                     |           |          | 
 is_visible           | boolean                     |           |          | 
 scope                | character varying           |           |          | 
 participation_mode   | character varying           |           |          | 
 is_coordinator       | boolean                     |           |          | 
 max_tool_iterations  | integer                     |           |          | 
 capabilities         | json                        |           |          | 
 id                   | uuid                        |           | not null | 
 owner_id             | uuid                        |           |          | 
 created_at           | timestamp without time zone |           | not null | 
 updated_at           | timestamp without time zone |           |          | 
 version              | integer                     |           | not null | 
 model                | character varying(20)       |           |          | 
 provider_type_id     | uuid                        |           | not null | 