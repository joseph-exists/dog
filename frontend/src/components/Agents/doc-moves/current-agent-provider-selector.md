
rough requirements:
users can add their provider API keys and URLs
    - working, see frontend/src/components/UserSettings/LLMProviders.tsx for initial implementation

users are able to have multiple API keys or none
if none, then defaults to system API key and system model

users are able to select from their available providers and models when creating, editing, or cloning an agent.

users can have N active LLM providers at any time, with the following case:

User has AgentBob and AgentAlice.  User sets AgentBob to use OpenAI GPT 5.1, and sets AgentAlice to use Gemini Flash Pro.  (different API keys, different providers, different models.)  These two agents can both be used in the same room at the same time.

Also needs to be supported (but should be if the following case works:)

User has AgentBob and AgentAlice.  AA uses GPT-5.1, AB uses GPT-nano.  same provider, two different models.

Users can switch providers and models at any time, as long as they have that provider in their UserSettings.

If a User makes an agent available to share publicly for other users to use or clone/edit, the agent will have the provider and model noted (GPT 5.1) that the User has used with it, but other users can clone and change as necessary.

Changing a model for an agent calls a ShadowClone and version update on that agent. (don't worry about this in the design, we will leave notes in the code.)

