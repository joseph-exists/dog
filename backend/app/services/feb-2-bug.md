 14:03:28.151           agent.instantiate_with_tools
backend-1  | --- Logging error ---

backend-1  |     await run_agents_for_message(
backend-1  |   File "/app/app/services/agent_runner.py", line 453, in run_agents_for_message
backend-1  |     response = await run_agent_for_room_streaming(
backend-1  |   File "/app/app/services/agent_runner.py", line 310, in run_agent_for_room_streaming
backend-1  |     result = await _get_streaming_runner().run(
backend-1  |   File "/app/app/services/agent_runner_streaming.py", line 90, in run
backend-1  |     agent = await self._get_agent_instance_with_tools(
backend-1  |   File "/app/app/services/agent_instance.py", line 96, in get_agent_instance_with_tools
backend-1  |     logger.info(
backend-1  | Message: '[AGENT_INSTANCE.get_agent_instance_with_tools] slug=%s config_present=%s'
backend-1  | Arguments: ('aboriginal-ginger-kagu-of-serendipity', UserAgentConfig(slug='aboriginal-ginger-kagu-of-serendipity', system_prompt='fsdfsdfsdf', is_visible=False, created_at=datetime.datetime(2026, 2, 3, 14, 2, 31, 911171), description='fillip', custom_system_prompt=None, scope='personal', user_access_provider=UUID('36150057-1c9c-4441-b0d1-4edbab1e438b'), instructions=None, participation_mode='always', updated_at=None, provider_type=UUID('673f1787-8474-4e1c-986c-8e19f14c989c'), tool_config=None, is_coordinator=False, version=1, model='gpt-4o-mini', deps_config=None, max_tool_iterations=10, name='fun', model_id=UUID('7dfa7ff3-b369-4ffd-9a6b-053fdbb0c51f'), agent_metadata=None, capabilities=[], model_name='gpt-4o-mini', is_enabled=True, id=UUID('632a1cda-e46a-4764-b6e9-dd623660866e'), is_clonable=False, owner_id=UUID('228d7ff2-960d-48b3-91a0-979034859cfe')), True)
backend-1  | ERROR:app.services.agent_runner_streaming:Agent aboriginal-ginger-kagu-of-serendipity streaming error in room b7f684ec-9f46-4299-9b06-f4713d580249: name 'model' is not defined
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/services/agent_runner_streaming.py", line 90, in run
backend-1  |     agent = await self._get_agent_instance_with_tools(
backend-1  |   File "/app/app/services/agent_instance.py", line 142, in get_agent_instance_with_tools
backend-1  |     "model": model,
backend-1  | NameError: name 'model' is not defined



tinyfoot=# \d user_agent_configs
                          Table "public.user_agent_configs"
        Column        |            Type             | Collation | Nullable | Default 
----------------------+-----------------------------+-----------+----------+---------
 name                 | character varying(100)      |           |          | 
 slug                 | character varying(50)       |           |          | 
 description          | character varying(500)      |           |          | 
 user_access_provider | uuid                        |           |          | 
 provider_type        | uuid                        |           |          | 
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




 fun     | aboriginal-ginger-kagu-of-serendipity | fillip                            | 36150057-1c9c-4441-b0d1-4edbab1e438b | 673f1787-8474-4e1c-986c-8e19f14c989c | 7dfa7ff3-b369-4ffd-9a6b-053fdbb0c51f | gpt-4o-mini | fsdfsdfsdf                                                                                                                                                                                                                                                                                                  |                      |              | null        | null        | null           | t          | f           | f          | personal | always             | f              |                  10 | []           | 632a1cda-e46a-4764-b6e9-dd623660866e | 228d7ff2-960d-48b3-91a0-979034859cfe | 2026-02-03 14:02:31.911171 |            |       1 | gpt-4o-mini