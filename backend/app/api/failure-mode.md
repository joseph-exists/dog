
... |       INFO   - "GET /api/v1/llm-providers/?skip=0&limit=50
... |              HTTP/1.1" 500
... |      ERROR   Exception in ASGI application


... |   File "/app/app/api/routes/llm_providers.py", line 48, in list_providers
... |     return UserLLMProvidersPublic(data=providers, count=count)

... | pydantic_core._pydantic_core.ValidationError: 3 validation errors for UserLLMProvidersPublic
... | data.0.provider_type
... |   Input should be a valid string [type=string_type, input_value=RelationshipInfo(back_pop...gs={'lazy': 'selectin'}), input_type=RelationshipInfo]

... | data.1.provider_type
... |   Input should be a valid string [type=string_type, input_value=RelationshipInfo(back_pop...gs={'lazy': 'selectin'}), input_type=RelationshipInfo]

... | data.2.provider_type
... |   Input should be a valid string [type=string_type, input_value=RelationshipInfo(back_pop...gs={'lazy': 'selectin'}), input_type=RelationshipInfo]
b
... |   File "/app/app/api/routes/llm_providers.py", line 48, in list_providers
... |     return UserLLMProvidersPublic(data=providers, count=count)

...

... | pydantic_core._pydantic_core.ValidationError: 3 validation errors for UserLLMProvidersPublic
... | data.0.provider_type
... |   Input should be a valid string [type=string_type, input_value=RelationshipInfo(back_pop...gs={'lazy': 'selectin'}), input_type=RelationshipInfo]
... |     For further information visit https://errors.pydantic.dev/2.12/v/string_type
... | data.1.provider_type
... |   Input should be a valid string [type=string_type, input_value=RelationshipInfo(back_pop...gs={'lazy': 'selectin'}), input_type=RelationshipInfo]
... |     For further information visit https://errors.pydantic.dev/2.12/v/string_type
... | data.2.provider_type
... |   Input should be a valid string [type=string_type, input_value=RelationshipInfo(back_pop...gs={'lazy': 'selectin'}), input_type=RelationshipInfo]
... |     For further information visit https://errors.pydantic.dev/2.12/v/string_type
