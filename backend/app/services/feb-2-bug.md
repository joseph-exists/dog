backend-1  | 20:49:12.594           agent.instantiate_with_tools
backend-1  | INFO:app.services.agent_instance:[AGENT_INSTANCE.get_agent_config] slug=tested-scarlet-rabbit-of-champagne result=row=present type=Row id=? slug=? is_enabled=? model_name=? name=?
backend-1  | INFO:app.services.agent_instance:[AGENT_INSTANCE.get_agent_instance_with_tools] slug=tested-scarlet-rabbit-of-champagne config=present type=Row id=? slug=? is_enabled=? model_name=? name=?
backend-1  | ERROR:app.services.agent_runner_streaming:Agent tested-scarlet-rabbit-of-champagne streaming error in room 2ca99f0f-e47d-441b-be27-82d9ee630c0e: system_prompt

backend-1  |     raise KeyError(key) from err
backend-1  | KeyError: 'system_prompt'
backend-1  | 
backend-1  | The above exception was the direct cause of the following exception:
backend-1  | 
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/services/agent_runner_streaming.py", line 90, in run
backend-1  |     agent = await self._get_agent_instance_with_tools(
backend-1  |   File "/app/app/services/agent_instance.py", line 231, in get_agent_instance_with_tools
backend-1  |     system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"
backend-1  |     raise AttributeError(ke.args[0]) from ke
backend-1  | AttributeError: system_prompt
backend-1  | INFO:app.services.realtime_publisher:Published room_message.agent to Redis channel room:2ca99f0f-e47d-441b-be27-82d9ee630c0e, subscribers: 1
backend-1  | INFO:app.api.routes.rooms:list_messages success
backend-1  |       INFO   172.24.0.1:56026 - "GET                                            
backend-1  |              /api/v1/rooms/2ca99f0f-e47d-441b-be27-82d9ee630c0e/messages?limit=5
backend-1  |              0&include_internal=false HTTP/1.1" 200
backend-1  | DEBUG:urllib3.connectionpool:https://logfire-us.pydantic.dev:443 "POST /v1/traces HTTP/1.1" 200 0


tinyfoot=# select * from user_agent_configs where slug='tested-scarlet-rabbit-of-champagne';
   name    |                slug                |                description                |         user_access_provider         | provider_type | model_id |              model_name              |                  system_prompt                   | custom_system_prompt | instructions | tool_config | deps_config | agent_metadata | is_enabled | is_clonable | is_visible |  scope   | participation_mode | is_coordinator | max_tool_iterations | capabilities |                  id                  |               owner_id               |         created_at         |         updated_at         | version | model |           provider_type_id           
-----------+------------------------------------+-------------------------------------------+--------------------------------------+---------------+----------+--------------------------------------+--------------------------------------------------+----------------------+--------------+-------------+-------------+----------------+------------+-------------+------------+----------+--------------------+----------------+---------------------+--------------+--------------------------------------+--------------------------------------+----------------------------+----------------------------+---------+-------+--------------------------------------
 beep-beep | tested-scarlet-rabbit-of-champagne | scenic route of testing agents and agency | 36150057-1c9c-4441-b0d1-4edbab1e438b |               |          | c7fbbbe4-643c-422b-8aa4-4b4d1753c6cb | You are a fun assistant with fancy things to do. |                      |              | null        | null        | null           | t          | f           | f          | personal | always             | f              |                  10 | []           | 60eec55a-bcf5-4d9c-84f8-d521e03c70eb | 228d7ff2-960d-48b3-91a0-979034859cfe | 2026-02-02 19:06:01.417407 | 2026-02-02 19:09:03.702853 |       1 |       | 673f1787-8474-4e1c-986c-8e19f14c989c


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
Indexes:
    "user_agent_configs_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "user_agent_configs_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES "user"(id)
Referenced by:
    TABLE "agent_personas" CONSTRAINT "agent_personas_agent_id_fkey" FOREIGN KEY (agent_id) REFERENCES user_agent_configs(id) ON DELETE CASCADE
    TABLE "room_participant_bindings" CONSTRAINT "room_participant_bindings_agent_id_fkey" FOREIGN KEY (agent_id) REFERENCES user_agent_configs(id)


