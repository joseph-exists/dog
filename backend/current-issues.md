when using the 'add participant' functionality to add an agent to a room:

 | pydantic_core._pydantic_core.ValidationError: 17 validation errors for AgentConfigsPublic
backend-1  | data.0.capabilities
backend-1  |   Input should be a valid list [type=list_type, input_value=None, input_type=NoneType]
backend-1  |     For further information visit https://errors.pydantic.dev/2.12/v/list_type
backend-1  | data.1.capabilities
backend-1  |   Input should be a valid list [type=list_type, input_value=None, input_type=NoneType]
backend-1  |     For further information visit https://errors.pydantic.dev/2.12/v/list_type