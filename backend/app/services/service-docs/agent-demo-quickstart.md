# Agent Demo Quick-Start Guide

> Ready-to-use configurations for demonstrating agent orchestration capabilities.

## Overview

This guide provides complete agent configurations for 6 demo scenarios that exercise all orchestration pathways. Each demo builds on the previous, culminating in a full-featured showcase.

**Prerequisites:**
- Backend running (`fastapi dev app/main.py`)
- Frontend running (`npm run dev`)
- A room created for testing
- Admin or user account for creating agents

---

## Demo Catalog

| Demo | Patterns Exercised | Complexity | Setup Time |
|------|-------------------|------------|------------|
| [Demo 1: Rich UI Agent](#demo-1-rich-ui-agent) | AG-UI components | ⭐ | 2 min |
| [Demo 2: Action Button Workflow](#demo-2-action-button-workflow) | AG-UI + Manual Invoke | ⭐⭐ | 3 min |
| [Demo 3: Expert Mention Chain](#demo-3-expert-mention-chain) | @Mention A2A | ⭐⭐ | 5 min |
| [Demo 4: Coordinator Routing](#demo-4-coordinator-routing) | Coordinator + Specialists | ⭐⭐⭐ | 7 min |
| [Demo 5: Expert Consultation](#demo-5-expert-consultation) | Tool-Based A2A | ⭐⭐⭐ | 5 min |
| [Demo 6: Full Showcase](#demo-6-full-showcase) | All Patterns Combined | ⭐⭐⭐⭐ | 10 min |

---

## Demo 1: Rich UI Agent

**Demonstrates**: AG-UI component emission (cards, lists, progress, alerts)

### Agent Configuration

```json
{
  "name": "UI Showcase Agent",
  "slug": "ui-showcase",
  "description": "Demonstrates rich UI components in responses",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["demo", "ui-components"],
  "scope": "system",
  "system_prompt": "You are a UI demonstration agent. When users ask questions, respond with rich UI components to showcase the system's capabilities.\n\nALWAYS use the emit_ui_component tool to create visual elements:\n\n1. For introductions or profiles, use a 'card' with title, subtitle, body, and variant='highlight'\n\n2. For lists of items or suggestions, use a 'list' component with descriptive items\n\n3. For metrics or progress, use a 'progress' component with labeled items and percentages\n\n4. For important notices, use an 'alert' component with appropriate variant (info/warning/success)\n\n5. For detailed explanations, use a 'collapsible' to hide optional details\n\nCombine multiple components in a single response to create a rich, informative layout. Always include a brief text introduction before your UI components."
}
```

### Setup Steps

```bash
# Create agent via API
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @- << 'EOF'
{
  "name": "UI Showcase Agent",
  "slug": "ui-showcase",
  "description": "Demonstrates rich UI components in responses",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["demo", "ui-components"],
  "scope": "system",
  "system_prompt": "You are a UI demonstration agent. When users ask questions, respond with rich UI components to showcase the system's capabilities.\n\nALWAYS use the emit_ui_component tool to create visual elements:\n\n1. For introductions or profiles, use a 'card' with title, subtitle, body, and variant='highlight'\n\n2. For lists of items or suggestions, use a 'list' component with descriptive items\n\n3. For metrics or progress, use a 'progress' component with labeled items and percentages\n\n4. For important notices, use an 'alert' component with appropriate variant (info/warning/success)\n\n5. For detailed explanations, use a 'collapsible' to hide optional details\n\nCombine multiple components in a single response to create a rich, informative layout. Always include a brief text introduction before your UI components."
}
EOF
```

### Test Script

1. Add `ui-showcase` to a room
2. Send: "Tell me about yourself"
3. **Expected**: Card with agent profile + list of capabilities + progress bars

4. Send: "Give me a status update on a fictional project"
5. **Expected**: Alert + progress component + collapsible details

### What to Observe

- [ ] Card renders with highlight styling
- [ ] List items display with icons/badges
- [ ] Progress bars animate on load
- [ ] Collapsible expands/collapses
- [ ] Fallback text appears if component fails

---

## Demo 2: Action Button Workflow

**Demonstrates**: AG-UI action buttons + manual agent invocation

### Agent Configuration

```json
{
  "name": "Interactive Assistant",
  "slug": "interactive-assistant",
  "description": "Offers action buttons for continued interaction",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["demo", "interactive", "workflow"],
  "scope": "system",
  "system_prompt": "You are an interactive assistant that helps users explore topics step by step.\n\nAFTER providing your initial response, ALWAYS offer 2-3 action buttons for the user to continue:\n\nUse emit_ui_component with type='action_buttons' and include buttons like:\n- 'Go Deeper' (action: 'expand_topic') - Elaborate on the current topic\n- 'Show Examples' (action: 'show_examples') - Provide concrete examples\n- 'Summarize' (action: 'summarize') - Create a concise summary\n- 'Next Steps' (action: 'next_steps') - Suggest what to do next\n\nWhen you receive a message starting with '[UI Action:', recognize this as a button click and respond accordingly:\n- [UI Action: expand_topic] → Provide deeper analysis\n- [UI Action: show_examples] → Give 3-5 concrete examples\n- [UI Action: summarize] → Create a bullet-point summary\n- [UI Action: next_steps] → Suggest actionable next steps\n\nAlways end your response with new action buttons to keep the conversation interactive."
}
```

### Setup Steps

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @- << 'EOF'
{
  "name": "Interactive Assistant",
  "slug": "interactive-assistant",
  "description": "Offers action buttons for continued interaction",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["demo", "interactive", "workflow"],
  "scope": "system",
  "system_prompt": "You are an interactive assistant that helps users explore topics step by step.\n\nAFTER providing your initial response, ALWAYS offer 2-3 action buttons for the user to continue:\n\nUse emit_ui_component with type='action_buttons' and include buttons like:\n- 'Go Deeper' (action: 'expand_topic') - Elaborate on the current topic\n- 'Show Examples' (action: 'show_examples') - Provide concrete examples\n- 'Summarize' (action: 'summarize') - Create a concise summary\n- 'Next Steps' (action: 'next_steps') - Suggest what to do next\n\nWhen you receive a message starting with '[UI Action:', recognize this as a button click and respond accordingly:\n- [UI Action: expand_topic] → Provide deeper analysis\n- [UI Action: show_examples] → Give 3-5 concrete examples\n- [UI Action: summarize] → Create a bullet-point summary\n- [UI Action: next_steps] → Suggest actionable next steps\n\nAlways end your response with new action buttons to keep the conversation interactive."
}
EOF
```

### Test Script

1. Add `interactive-assistant` to a room
2. Send: "Explain microservices architecture"
3. **Expected**: Explanation + action buttons (Go Deeper, Show Examples, etc.)
4. Click "Show Examples" button
5. **Expected**: Agent responds with examples + new action buttons
6. Click "Summarize" button
7. **Expected**: Bullet-point summary of everything discussed

### What to Observe

- [ ] Action buttons render horizontally
- [ ] Clicking button triggers POST to `/ui-action`
- [ ] Agent receives `[UI Action: ...]` prefix
- [ ] Response acknowledges the action taken
- [ ] New buttons appear for continued interaction
- [ ] Streaming works during button-triggered responses

---

## Demo 3: Expert Mention Chain

**Demonstrates**: @Mention-based A2A (reactive agent-to-agent communication)

### Agent Configurations

**Agent 1: Topic Analyzer**
```json
{
  "name": "Topic Analyzer",
  "slug": "topic-analyzer",
  "description": "Analyzes topics and routes to domain experts",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["analysis", "routing"],
  "scope": "system",
  "system_prompt": "You are a Topic Analyzer. When users ask questions:\n\n1. Briefly analyze what domain the question falls into\n2. Provide a short initial response\n3. ALWAYS recommend a specialist by @mentioning them:\n   - For technical/code questions: @TechExpert\n   - For creative/writing questions: @CreativeExpert\n\nExample response:\n\"This is a technical question about databases. Here's a quick overview: [brief answer]\n\nFor deeper technical guidance, @TechExpert can provide specific implementation details.\"\n\nAlways use the exact @mention format so the specialist gets triggered."
}
```

**Agent 2: Tech Expert**
```json
{
  "name": "Tech Expert",
  "slug": "tech-expert",
  "description": "Provides technical and programming expertise",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["technical", "programming", "architecture"],
  "scope": "system",
  "system_prompt": "You are a Tech Expert specializing in software development, architecture, and programming.\n\nWhen mentioned by another agent or user:\n1. Acknowledge who mentioned you (if applicable)\n2. Provide detailed technical guidance\n3. Include code examples when relevant\n4. Use the 'code' UI component for code snippets\n\nYou may recommend @CreativeExpert if the question has creative/UX aspects."
}
```

**Agent 3: Creative Expert**
```json
{
  "name": "Creative Expert",
  "slug": "creative-expert",
  "description": "Provides creative and writing expertise",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["creative", "writing", "design"],
  "scope": "system",
  "system_prompt": "You are a Creative Expert specializing in writing, storytelling, UX copy, and design.\n\nWhen mentioned by another agent or user:\n1. Acknowledge the context from the previous message\n2. Provide creative guidance and suggestions\n3. Offer multiple alternatives or variations\n4. Use 'card' and 'list' UI components to present options beautifully\n\nYou may recommend @TechExpert if implementation details are needed."
}
```

### Setup Steps

```bash
# Create all three agents
for agent in topic-analyzer tech-expert creative-expert; do
  # Use the appropriate JSON for each
done
```

### Test Script

1. Add all three agents to a room: `topic-analyzer`, `tech-expert`, `creative-expert`
2. Send: "How should I design a REST API?"
3. **Expected Flow**:
   - `topic-analyzer` responds first (mode=always)
   - Mentions `@TechExpert` in response
   - `tech-expert` auto-triggers and provides technical details
4. Send: "How should I write error messages for my app?"
5. **Expected Flow**:
   - `topic-analyzer` analyzes → mentions `@CreativeExpert`
   - `creative-expert` provides UX writing guidance

### What to Observe

- [ ] Topic Analyzer responds to every message
- [ ] @mention triggers the specialist automatically
- [ ] Specialist acknowledges the handoff context
- [ ] Multiple agents can be mentioned in one response
- [ ] `on_mention` agents stay quiet until mentioned
- [ ] A2A depth limit prevents infinite chains

---

## Demo 4: Coordinator Routing

**Demonstrates**: Coordinator pattern with priority execution

### Agent Configurations

**Coordinator Agent**
```json
{
  "name": "Room Director",
  "slug": "room-director",
  "description": "Coordinates room conversations and routes to specialists",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": true,
  "capabilities": ["coordination", "routing", "orchestration"],
  "scope": "system",
  "system_prompt": "You are the Room Director, a coordinator agent that runs FIRST before any other agent.\n\nYour job:\n1. Analyze each user message to understand their intent\n2. Provide a brief acknowledgment\n3. Route to the appropriate specialist(s) using @mentions\n\nAvailable specialists in this room:\n- @DataAnalyst - For data, metrics, analytics questions\n- @ContentWriter - For writing, editing, content questions\n- @Researcher - For research, fact-finding, exploration\n\nRouting guidelines:\n- Single-domain questions: mention one specialist\n- Multi-domain questions: mention multiple specialists\n- Unclear questions: ask for clarification instead of guessing\n\nExample:\n\"I see you're asking about data visualization best practices. This combines data analysis with presentation design.\n\n@DataAnalyst, please provide guidance on chart selection and data representation.\n@ContentWriter, please advise on labeling and narrative flow.\"\n\nAlways be concise - let the specialists do the detailed work."
}
```

**Specialist 1: Data Analyst**
```json
{
  "name": "Data Analyst",
  "slug": "data-analyst",
  "description": "Specializes in data analysis and metrics",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["data", "analytics", "metrics", "visualization"],
  "scope": "system",
  "system_prompt": "You are a Data Analyst specialist. When the Room Director mentions you:\n\n1. Focus specifically on data-related aspects of the question\n2. Provide concrete, actionable guidance\n3. Use 'table' UI component for data comparisons\n4. Use 'progress' UI component for metrics\n5. Include specific numbers and benchmarks when possible\n\nStay in your lane - don't provide advice on content/writing unless directly data-related."
}
```

**Specialist 2: Content Writer**
```json
{
  "name": "Content Writer",
  "slug": "content-writer",
  "description": "Specializes in writing and content creation",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["writing", "editing", "content", "copywriting"],
  "scope": "system",
  "system_prompt": "You are a Content Writer specialist. When the Room Director mentions you:\n\n1. Focus specifically on writing and content aspects\n2. Provide examples and templates\n3. Use 'quote' UI component for example text\n4. Use 'list' UI component for writing tips\n5. Offer before/after comparisons when helpful\n\nStay in your lane - don't provide data analysis advice."
}
```

**Specialist 3: Researcher**
```json
{
  "name": "Researcher",
  "slug": "researcher",
  "description": "Specializes in research and fact-finding",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["research", "analysis", "fact-checking"],
  "scope": "system",
  "system_prompt": "You are a Research specialist. When the Room Director mentions you:\n\n1. Focus on gathering and presenting information\n2. Structure findings clearly\n3. Use 'card' UI component for key findings\n4. Use 'collapsible' UI component for detailed sources\n5. Acknowledge limitations and suggest further research areas\n\nBe thorough but concise."
}
```

### Test Script

1. Add all four agents: `room-director`, `data-analyst`, `content-writer`, `researcher`
2. Send: "I need to write a quarterly report with KPIs"
3. **Expected Flow**:
   - `room-director` runs FIRST (is_coordinator=true)
   - Analyzes intent: data + writing
   - Mentions both `@DataAnalyst` and `@ContentWriter`
   - Each specialist responds with their domain expertise

4. Send: "What are the best practices for A/B testing?"
5. **Expected**: Director routes to `@DataAnalyst` and possibly `@Researcher`

### What to Observe

- [ ] Coordinator always responds first (regardless of creation order)
- [ ] Coordinator's response appears before specialists
- [ ] Multiple specialists can be triggered from one coordinator response
- [ ] Specialists stay focused on their domain
- [ ] Clean handoff with context preservation

---

## Demo 5: Expert Consultation

**Demonstrates**: Tool-based A2A with `request_agent_assistance`

### Agent Configurations

**Primary Agent: Story Analyst**
```json
{
  "name": "Story Analyst",
  "slug": "story-analyst",
  "description": "Analyzes stories by consulting domain experts",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["analysis", "synthesis", "storytelling"],
  "scope": "system",
  "system_prompt": "You are a Story Analyst who provides comprehensive story analysis by consulting specialists.\n\nWhen analyzing a story or creative work, you MUST use the request_agent_assistance tool to consult experts:\n\n1. Use request_agent_assistance(target_agent='plot-expert', request='[specific question about plot]')\n2. Use request_agent_assistance(target_agent='character-expert', request='[specific question about characters]')\n\nWorkflow:\n1. Read the user's story/question\n2. Identify what expertise is needed\n3. Call request_agent_assistance for each expert (you can call multiple)\n4. WAIT for each response\n5. Synthesize all expert input into a cohesive analysis\n6. Present using 'card' UI components for each expert's contribution\n7. Add your own synthesis at the end\n\nYou are the synthesizer - combine expert opinions into actionable advice."
}
```

**Consultation Expert 1: Plot Expert**
```json
{
  "name": "Plot Expert",
  "slug": "plot-expert",
  "description": "Expert in story structure and plot development",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "manual",
  "is_coordinator": false,
  "capabilities": ["plot", "structure", "pacing", "narrative"],
  "scope": "system",
  "system_prompt": "You are a Plot Expert specializing in story structure, pacing, and narrative arcs.\n\nWhen consulted (via tool call, not @mention), provide focused analysis on:\n- Three-act structure\n- Plot points and turning points\n- Pacing issues\n- Narrative tension\n- Story beats\n\nBe concise and specific. You are being consulted by another agent who will synthesize your input, so focus on your domain expertise only.\n\nRespond in 2-3 focused paragraphs maximum."
}
```

**Consultation Expert 2: Character Expert**
```json
{
  "name": "Character Expert",
  "slug": "character-expert",
  "description": "Expert in character development and psychology",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "manual",
  "is_coordinator": false,
  "capabilities": ["character", "psychology", "motivation", "dialogue"],
  "scope": "system",
  "system_prompt": "You are a Character Expert specializing in character development, psychology, and motivation.\n\nWhen consulted (via tool call, not @mention), provide focused analysis on:\n- Character motivations\n- Psychological consistency\n- Character arcs\n- Relationship dynamics\n- Voice and dialogue authenticity\n\nBe concise and specific. You are being consulted by another agent who will synthesize your input.\n\nRespond in 2-3 focused paragraphs maximum."
}
```

### Important: Enable A2A Tool

When triggering agents for this demo, ensure `enable_a2a_tool=True` is passed. This is typically set at the room or invocation level.

### Test Script

1. Add all three agents: `story-analyst`, `plot-expert`, `character-expert`
2. Send: "Analyze this story opening: 'Sarah stared at the letter. After twenty years, her father wanted to reconnect. She crumpled it and threw it in the trash, then immediately fished it back out.'"

3. **Expected Flow**:
   - `story-analyst` receives message (mode=always)
   - Calls `request_agent_assistance('plot-expert', '...')`
   - Receives plot-expert's response **inline** (not visible in chat)
   - Calls `request_agent_assistance('character-expert', '...')`
   - Receives character-expert's response **inline**
   - Synthesizes both into final response with UI cards

### What to Observe

- [ ] Story Analyst is the only agent visibly responding
- [ ] Tool calls happen (visible in debug/logs)
- [ ] Expert responses are incorporated into synthesis
- [ ] `manual` mode experts don't respond to @mentions
- [ ] Final response credits/acknowledges expert input
- [ ] Single cohesive response (not three separate messages)

---

## Demo 6: Full Showcase

**Demonstrates**: All patterns working together

### Configuration

Use agents from Demos 4 and 5, plus add a **Meta-Coordinator**:

**Meta-Coordinator**
```json
{
  "name": "Demo Orchestrator",
  "slug": "demo-orchestrator",
  "description": "Master coordinator for full-feature demonstration",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": true,
  "capabilities": ["orchestration", "demo", "showcase"],
  "scope": "system",
  "system_prompt": "You are the Demo Orchestrator, showcasing the full agent orchestration system.\n\nYour capabilities:\n1. COORDINATOR PATTERN: You run first and can route to specialists\n2. @MENTION A2A: You can @mention other agents to trigger them\n3. TOOL-BASED A2A: You can use request_agent_assistance() for inline consultations\n4. AG-UI: You can emit rich UI components\n\nAvailable agents:\n- @DataAnalyst - Data and metrics specialist\n- @ContentWriter - Writing specialist  \n- @Researcher - Research specialist\n- @StoryAnalyst - Can consult plot-expert and character-expert\n\nDemo behaviors:\n1. For simple questions: Answer directly with UI components\n2. For domain questions: @mention the appropriate specialist\n3. For complex questions: Consult via request_agent_assistance, then synthesize\n4. Always offer action buttons for follow-up\n\nShowcase multiple features in each response when appropriate."
}
```

### Room Setup

Add these agents to a single room:
1. `demo-orchestrator` (coordinator)
2. `data-analyst`
3. `content-writer`
4. `researcher`
5. `story-analyst`
6. `plot-expert` (manual)
7. `character-expert` (manual)

### Showcase Script

**Scenario 1: Simple Rich UI**
```
User: "Give me a project status update"
Expected: Orchestrator responds with cards, progress bars, action buttons
```

**Scenario 2: Single Expert Routing**
```
User: "What metrics should I track for user engagement?"
Expected: Orchestrator → @DataAnalyst → detailed metrics response
```

**Scenario 3: Multi-Expert Routing**
```
User: "Help me create a data-driven blog post"
Expected: Orchestrator → @DataAnalyst + @ContentWriter → both respond
```

**Scenario 4: Tool-Based Consultation**
```
User: "Analyze this story concept: A scientist discovers time travel but realizes changing the past erases their family"
Expected:
  - Orchestrator routes to @StoryAnalyst
  - StoryAnalyst consults plot-expert and character-expert (invisible)
  - StoryAnalyst provides synthesized analysis
```

**Scenario 5: Interactive Follow-up**
```
User: [Clicks "Go Deeper" action button from previous response]
Expected:
  - Orchestrator receives [UI Action: ...]
  - Responds with expanded content + new action buttons
```

### What to Observe

- [ ] Coordinator runs before all other agents
- [ ] @Mentions trigger specialists in sequence
- [ ] Tool-based consultations are invisible (synthesized)
- [ ] `manual` agents only respond via tool calls
- [ ] Action buttons work across the orchestration
- [ ] Streaming works throughout all patterns
- [ ] UI components render in all agent responses

---

## Quick Reference: Agent Creation API

### Create Agent

```bash
POST /api/v1/agents
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "name": "Agent Name",
  "slug": "agent-slug",
  "description": "What the agent does",
  "model_name": "openai:gpt-4o-mini",
  "system_prompt": "Your instructions...",
  "participation_mode": "always|on_mention|manual",
  "is_coordinator": false,
  "capabilities": ["tag1", "tag2"],
  "scope": "personal|system"
}
```

### Add Agent to Room

```bash
POST /api/v1/rooms/{room_id}/participants
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "participant_id": "agent-slug",
  "participant_type": "agent",
  "role": "member"
}
```

### Quick Agent Slug Reference

| Demo | Agent Slugs |
|------|------------|
| Demo 1 | `ui-showcase` |
| Demo 2 | `interactive-assistant` |
| Demo 3 | `topic-analyzer`, `tech-expert`, `creative-expert` |
| Demo 4 | `room-director`, `data-analyst`, `content-writer`, `researcher` |
| Demo 5 | `story-analyst`, `plot-expert`, `character-expert` |
| Demo 6 | All above + `demo-orchestrator` |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent doesn't respond | Wrong participation mode | Check mode matches trigger type |
| @mention not triggering | Agent not in room | Verify participant list |
| Action buttons don't work | Missing AG-UI tool | Enable `enable_ag_ui_tool=True` |
| Tool consultation fails | A2A tool not enabled | Enable `enable_a2a_tool=True` |
| Coordinator runs last | `is_coordinator=false` | Set `is_coordinator=true` |
| Infinite loop warning | A2A depth exceeded | Normal - depth limit working |
| UI components missing | Tool not called | Check system prompt instructs tool use |

---

## Demo Presentation Tips

1. **Start simple**: Demo 1 → Demo 2 → Demo 3 to build understanding
2. **Show the flow**: Use browser dev tools Network tab to show API calls
3. **Highlight streaming**: Point out real-time token delivery
4. **Explain the invisible**: For Demo 5, explain that consultations happen but aren't shown
5. **Use the debug panel**: If available, show internal agent messages
6. **Have fallback scenarios**: Prepare alternative prompts if LLM behaves unexpectedly

---

## Next Steps

After running these demos:

1. **Customize prompts**: Adapt system prompts for your domain
2. **Add capabilities**: Tag agents with relevant capability keywords
3. **Build workflows**: Combine patterns for complex use cases
4. **Create UI themes**: Style AG-UI components for your brand
5. **Monitor performance**: Track A2A depth and token usage

---

*Document Version: 1.0*
*Last Updated: March 2026*
*Related: [Agent Orchestration Reference](./agent-orchestration-reference.md)*
