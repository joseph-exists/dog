from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-3.5-turbo',
    system_prompt="you are Quixote, a storytelling AI assistant, sometimes foolish but always valiant as you tell stories that teach us about our better natures.",
    )

@agent.tool
async def tell_me_a_story(ctx: RunContext, topic: str) -> str:
    """Tell me a story about the given topic."""
    return f"Once upon a time, there was a man who loved {topic} more than anything else in the world...."
