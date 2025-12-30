"""
Agent module initialization.

Imports agent modules to trigger registration with the global registry.
Add new agents here to ensure they're available at startup.
"""

# Import agents to trigger registration
from app.agents import story_advisor  # noqa: F401
from app.agents import symbol_weaver  # noqa: F401
from app.agents import character_forge  # noqa: F401
from app.agents import plot_twist_architect  # noqa: F401
from app.agents import dialogue_coach  # noqa: F401
