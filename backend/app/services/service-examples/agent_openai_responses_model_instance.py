from pydantic_ai import Agent
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import UserAgentConfig
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
"""
using OpenAIResponsesModel by name:

from pydantic_ai import Agent
agent = Agent('openai-responses:gpt-5')


Or initialise the model directly with just the model name:

model = OpenAIResponsesModel('gpt-5')
agent = Agent(model)
"""

model=OpenAIResponsesModel()
agent = Agent(model)

model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[
        ComputerToolParam(
            type='computer_use',
        )
    ],
)
model = OpenAIResponsesModel('gpt-5')
agent = Agent(model=model, model_settings=model_settings)

result = agent.run_sync('Open a new browser tab')
print(result.output)

result = agent.run_sync('The secret is 1234')
model_settings = OpenAIResponsesModelSettings(
    openai_previous_response_id=result.all_messages()[-1].provider_response_id
)
result = agent.run_sync('What is the secret code?', model_settings=model_settings)
print(result.output)

"""
Referencing earlier responses
The Responses API supports referencing earlier model responses in a new request using a previous_response_id parameter, to ensure the full conversation state including reasoning items are kept in context. This is available through the openai_previous_response_id field in OpenAIResponsesModelSettings.


from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5')
agent = Agent(model=model)

result = agent.run_sync('The secret is 1234')
model_settings = OpenAIResponsesModelSettings(
    openai_previous_response_id=result.all_messages()[-1].provider_response_id
)
result = agent.run_sync('What is the secret code?', model_settings=model_settings)
print(result.output)
#> 1234
By passing the provider_response_id from an earlier run, you can allow the model to build on its own prior reasoning without needing to resend the full message history.

Automatically referencing earlier responses
When the openai_previous_response_id field is set to 'auto', Pydantic AI will automatically select the most recent provider_response_id from message history and omit messages that came before it, letting the OpenAI API leverage server-side history instead for improved efficiency.


from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5')
agent = Agent(model=model)

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

# When set to 'auto', the most recent provider_response_id
# and messages after it are sent as request.
model_settings = OpenAIResponsesModelSettings(openai_previous_response_id='auto')
result2 = agent.run_sync(
    'Explain?',
    message_history=result1.new_messages(),
    model_settings=model_settings
)
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.
"""



