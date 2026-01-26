# Agent User Guide

> Quick reference for working with AI agents in rooms

---

## What Are Agents?

Agents are AI assistants that participate in your chat rooms. Each agent has a unique personality, expertise, and way of responding to messages. You can add multiple agents to a room to get different perspectives and specialized help.

---

## Quick Start

### Adding Agents to a Room

1. Open a room
2. Click the **Party Picker** (participant menu)
3. Browse available agents
4. Click an agent to add them to the room
5. The agent will join and respond based on their participation mode

### Talking to Agents

| Method | How It Works | Example |
|--------|--------------|---------|
| **@Mention** | Type `@` followed by agent name | `@Donald what do you think?` |
| **Direct message** | Just type if agent is in "always" mode | Agent responds to every message |
| **Quoted names** | Use quotes for names with spaces | `@"Alice Muldoon" help me please` |

---

## Agent Behaviors

### Participation Modes

Agents respond differently based on their configured mode:

| Mode | Behavior | Best For |
|------|----------|----------|
| **On Mention** | Responds only when you @mention them | Most agents - keeps conversations focused |
| **Always** | Responds to every message in the room | Primary assistants, room monitors |
| **Manual** | Never auto-responds | Background agents, API-only tools |

### Coordinator Agents

Some agents are marked as **coordinators**. These special agents:
- Always respond first (before other agents)
- Analyze your message intent
- Route requests to specialist agents
- Can orchestrate multi-agent workflows

*Example: A "Room Coordinator" might receive your message, determine you need permissions help, and ask @PermissionsTechAdvisor for assistance.*

---


---

## Creating Your Own Agents

### Personal Agents

You can create agents customized for your needs:

1. Go to **Settings → Agents**
2. Click **Create Agent**
3. Fill in the details:
   - **Name**: Display name (e.g., "My Writing Coach")
   - **Description**: What the agent does
   - **System Prompt**: Instructions for how the agent behaves
   - **Provider** - the access gateway, user fills in.
   - **Model**: Which AI model powers it (e.g., GPT-4o-mini)

### Agent Settings

| Setting | What It Does |
|---------|--------------|
| **Participation Mode** | When the agent responds (always/on_mention/manual) |
| **Is Coordinator** | Whether agent runs first as orchestrator |
| **Capabilities** | Tags describing expertise (helps other agents find them) |
| **Enabled** | Toggle agent on/off without deleting |

---

## Agent Interactions

### Agents Talking to Each Other (A2A)

Agents can collaborate! When one agent needs help from another:

1. Agent A receives your message
2. Agent A realizes it needs @AgentB's expertise
3. Agent A asks Agent B for input
4. Agent B responds to Agent A
5. Agent A incorporates the response

*You'll see this as a natural conversation flow in the room.*

### Rich UI Components (AG-UI)

Agents can display more than just text:

| Component | Use Case |
|-----------|----------|
| **Cards** | Highlighted information, character profiles |
| **Lists** | Suggestions, options, checklists |
| **Tables** | Comparisons, structured data |
| **Progress Bars** | Story completion, metrics |
| **Code Blocks** | Technical examples, scripts |
| **Alerts** | Warnings, tips, important notes |
| **Quotes** | Dialogue examples, excerpts |
| **Collapsible** | Hidden details, spoilers |
| **Tabs** | Organized alternatives |
| **Action Buttons** | Quick actions to take |

---

## Customizing Agent Behavior

### Per-Agent Settings

You can customize how agents work for you specifically:

1. Go to **Settings → Agents**
2. Click on an agent
3. Adjust **My Settings**:
   - **AI Provider**: Use your own API key
   - **Custom Prompt**: Add personal instructions
   - **Favorite**: Bookmark for quick access

*Your settings don't affect other users.*

---

## Tips & Best Practices

### Getting the Best Responses

1. **Be specific** - "Help with chapter 3's pacing" > "Help with my story"
2. **Provide context** - Agents see recent room messages
3. **Use the right agent** - Match expertise to your need
4. **Mention multiple agents** - `@StoryAdvisor and @DialogueCoach` for combined input

### Room Organization

- **Focus rooms**: One topic + relevant agents
- **Creative rooms**: Multiple specialist agents for collaboration
- **Work rooms**: Coordinator + specialists for complex projects

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not responding | Check if you @mentioned them (on_mention mode) |
| Wrong agent responding | Use specific @mentions instead of general messages |
| Agent seems confused | Provide more context or start a new topic |
| Agent unavailable | Check if agent is enabled in settings |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `@` | Start mentioning an agent |
| `Tab` | Autocomplete agent name |
| `↑` `↓` | Navigate agent suggestions |
| `Enter` | Select agent |

---

## Privacy & Data

- Agents only see messages in rooms they're added to
- Your personal agent settings are private
- API keys are encrypted and never shared
- Conversation history stays in your rooms

---

## Next Steps

- **Explore agents**: Try each system agent to understand their style
- **Create a personal agent**: Customize one for your workflow
- **Build a dream team**: Add complementary agents to a room
- **Experiment with coordinators**: Try orchestrated multi-agent workflows
