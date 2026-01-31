OpenAI-compatible Models
Many providers and models are compatible with the OpenAI API, and can be used with OpenAIChatModel in Pydantic AI. Before getting started, check the installation and configuration instructions above.

To use another OpenAI-compatible API, you can make use of the base_url and api_key arguments from OpenAIProvider:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://<openai-compatible-api-endpoint>', api_key='your-api-key'
    ),
)
agent = Agent(model)
```

Various providers also have their own provider classes so that you don't need to specify the base URL yourself and you can use the standard <PROVIDER>_API_KEY environment variable to set the API key. When a provider has its own provider class, you can use the Agent("<provider>:<model>") shorthand, e.g. Agent("deepseek:deepseek-chat") or Agent("moonshotai:kimi-k2-0711-preview"), instead of building the OpenAIChatModel explicitly. Similarly, you can pass the provider name as a string to the provider argument on OpenAIChatModel instead of building instantiating the provider class explicitly.


Model Profile
Sometimes, the provider or model you're using will have slightly different requirements than OpenAI's API or models, like having different restrictions on JSON schemas for tool definitions, or not supporting tool definitions to be marked as strict.

When using an alternative provider class provided by Pydantic AI, an appropriate model profile is typically selected automatically based on the model name. If the model you're using is not working correctly out of the box, you can tweak various aspects of how model requests are constructed by providing your own ModelProfile (for behaviors shared among all model classes) or OpenAIModelProfile (for behaviors specific to OpenAIChatModel):

```python
from pydantic_ai import Agent, InlineDefsJsonSchemaTransformer
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://<openai-compatible-api-endpoint>.com', api_key='your-api-key'
    ),
    profile=OpenAIModelProfile(
        json_schema_transformer=InlineDefsJsonSchemaTransformer,  # Supported by any model class on a plain ModelProfile
        openai_supports_strict_tool_definition=False  # Supported by OpenAIModel only, requires OpenAIModelProfile
    )
)
agent = Agent(model)
```

DeepSeek
To use the DeepSeek provider, first create an API key by following the Quick Start guide.

You can then set the DEEPSEEK_API_KEY environment variable and use DeepSeekProvider by name:

```python
from pydantic_ai import Agent

agent = Agent('deepseek:deepseek-chat')

```
Or initialise the model and provider directly:

```python

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

model = OpenAIChatModel(
    'deepseek-chat',
    provider=DeepSeekProvider(api_key='your-deepseek-api-key'),
)
agent = Agent(model)

```

You can also customize any provider with a custom http_client:

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

custom_http_client = AsyncClient(timeout=30)
model = OpenAIChatModel(
    'deepseek-chat',
    provider=DeepSeekProvider(
        api_key='your-deepseek-api-key', http_client=custom_http_client
    ),
)
agent = Agent(model)
```

Alibaba Cloud Model Studio (DashScope)
To use Qwen models via Alibaba Cloud Model Studio (DashScope), you can set the ALIBABA_API_KEY (or DASHSCOPE_API_KEY) environment variable and use AlibabaProvider by name:


from pydantic_ai import Agent

agent = Agent('alibaba:qwen-max')
...
Or initialise the model and provider directly:


from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.alibaba import AlibabaProvider

model = OpenAIChatModel(
    'qwen-max',
    provider=AlibabaProvider(api_key='your-api-key'),
)
agent = Agent(model)
...
The AlibabaProvider uses the international DashScope compatible endpoint https://dashscope-intl.aliyuncs.com/compatible-mode/v1 by default. You can override this by passing a custom base_url:


from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.alibaba import AlibabaProvider

model = OpenAIChatModel(
    'qwen-max',
    provider=AlibabaProvider(
        api_key='your-api-key',
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',  # China region
    ),
)
agent = Agent(model)
...
Ollama
Pydantic AI supports both self-hosted Ollama servers (running locally or remotely) and Ollama Cloud.

For servers running locally, use the http://localhost:11434/v1 base URL. For Ollama Cloud, use https://ollama.com/v1 and ensure an API key is set.

You can set the OLLAMA_BASE_URL and (optionally) OLLAMA_API_KEY environment variables and use OllamaProvider by name:


from pydantic_ai import Agent

agent = Agent('ollama:gpt-oss:20b')
...
Or initialise the model and provider directly:


from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider


class CityLocation(BaseModel):
    city: str
    country: str


ollama_model = OpenAIChatModel(
    model_name='gpt-oss:20b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),  
)
agent = Agent(ollama_model, output_type=CityLocation)

result = agent.run_sync('Where were the olympics held in 2012?')
print(result.output)
#> city='London' country='United Kingdom'
print(result.usage())
#> RunUsage(input_tokens=57, output_tokens=8, requests=1)