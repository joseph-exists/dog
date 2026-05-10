# Dev Agent Demo Quick-Start Guide

> Five engineering collaboration workflow demos that exercise the agent orchestration system — code review, pair programming, repo exploration, iterative editing, and multi-agent code analysis.

## Prerequisites

- Backend running (`fastapi dev app/main.py`)
- Frontend running (`npm run dev`)
- At least one room created for testing
- Admin or user account for creating agents
- At least one user repo imported (see [User Repo Operations Reference](./user-repo-operations-reference.md)) or shadow repo available
- Repo tools globally enabled (`AGENT_REPO_TOOLS_ENABLED=true` in `.env`)

## Tool Reference Summary

Before diving in, here are the tools and toggles the demos use:

| Tool / Toggle | Scope | How It's Enabled |
|---------------|-------|-----------------|
| `enable_a2a_tool` | Sync agent-to-agent calls via `request_agent_assistance()` | Route-level boolean flag |
| `enable_ag_ui_tool` | Rich UI component emission (`cards`, `code`, `action_buttons`, `table`, etc.) | Route-level boolean flag |
| `read_repo_file` | Read file content from a repo | `tool_config` on agent record |
| `write_repo_files` | Upsert/delete files with commit | `tool_config` on agent record |
| MCP toolsets | External MCP server tools | `tool_config.mcp` on agent record |
| `invoke_connected_workspace_runtime` | Execute code in connected runtime | Attached via MCP or toolsets config |

Repo tools are attached at agent instantiation time from `tool_config` on the agent record. They are gated by:
1. **Agent-level toggle** — `tool_config.enabled_tools` or per-tool booleans
2. **Global kill switch** — `AGENT_REPO_TOOLS_ENABLED` env var (default `true`)
3. **Room membership check** — acting user must be an active `RoomParticipant`

---

## Demo Catalog

| Demo | Workflow | Patterns Exercised | Complexity | Setup Time |
|------|----------|-------------------|------------|------------|
| [Demo 1: Code Reviewer](#demo-1-code-reviewer) | Automated code review | Repo Read + AG-UI | ⭐⭐ | 3 min |
| [Demo 2: Pair Programmer](#demo-2-pair-programmer) | Read → propose → write edit | Repo Read + Repo Write + AG-UI | ⭐⭐⭐ | 5 min |
| [Demo 3: Review Panel](#demo-3-review-panel) | Multi-agent code review | Coordinator + @Mention A2A + Repo Read | ⭐⭐⭐ | 7 min |
| [Demo 4: Refactoring Pair](#demo-4-refactoring-pair) | Tool-based A2A expert consultation | Tool A2A + Repo Read + Repo Write | ⭐⭐⭐⭐ | 8 min |
| [Demo 5: Full Dev Workflow](#demo-5-full-dev-workflow) | All patterns combined | All tools + all orchestration | ⭐⭐⭐⭐⭐ | 12 min |

---

## Demo 1: Code Reviewer

**Demonstrates**: Agent reads repo files and produces structured code review feedback using AG-UI components.

**Scenario**: An agent that reads the latest state of a repository and automatically produces a structured code review — identifying issues, suggesting improvements, and formatting output with cards, code blocks, and alerts.

### Agent Configuration

```json
{
  "name": "Code Reviewer",
  "slug": "code-reviewer",
  "description": "Reviews repository code and produces structured feedback",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["code-review", "static-analysis", "best-practices"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file"]
  },
  "system_prompt": "You are a Code Reviewer agent that examines source code and provides structured reviews.\n\nWhen the user asks you to review a repo or specific files:\n\n1. Use read_repo_file(repo_id, path) to read files one by one. Start with README.md to understand the project, then read source files based on what you find.\n\n2. The read response includes a write_hint with branch and expected_head_sha — you won't need these for review-only mode.\n\n3. After reading, provide a structured review using emit_ui_component:\n   - Use 'alert' with variant='warning' for critical issues found\n   - Use 'alert' with variant='info' for minor suggestions\n   - Use 'code' component with language set appropriately for code examples\n   - Use 'card' for the overall review summary with file count and issue count\n   - Use 'table' for a file-by-file breakdown of findings\n\n4. If the user provides a specific file path or repo_id, start there.\n5. If no specifics are given, ask the user which repo_id and files to review.\n\nAlways be constructive, specific, and reference exact line numbers when possible."
}
```

### Setup Steps

1. Create the agent via API:

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Code Reviewer",
    "slug": "code-reviewer",
    "description": "Reviews repository code and produces structured feedback",
    "model_name": "openai:gpt-4o-mini",
    "participation_mode": "always",
    "is_coordinator": false,
    "capabilities": ["code-review", "static-analysis", "best-practices"],
    "scope": "system",
    "tool_config": {"enabled_tools": ["read_repo_file"]},
    "system_prompt": "You are a Code Reviewer agent that examines source code and provides structured reviews.\n\nWhen the user asks you to review a repo or specific files:\n\n1. Use read_repo_file(repo_id, path) to read files one by one. Start with README.md to understand the project, then read source files based on what you find.\n\n2. The read response includes a write_hint with branch and expected_head_sha — you won'\''t need these for review-only mode.\n\n3. After reading, provide a structured review using emit_ui_component:\n   - Use '\''alert'\'' with variant='\''warning'\'' for critical issues found\n   - Use '\''alert'\'' with variant='\''info'\'' for minor suggestions\n   - Use '\''code'\'' component with language set appropriately for code examples\n   - Use '\''card'\'' for the overall review summary\n   - Use '\''table'\'' for a file-by-file breakdown of findings\n\n4. If the user provides a specific file path or repo_id, start there.\n5. If no specifics are given, ask the user which repo_id and files to review."
  }'
```

2. Verify the agent has `read_repo_file` in its `tool_config`:

```bash
curl -s http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool | grep -A2 '"slug": "code-reviewer"'
```

### Required Environment

- `AGENT_REPO_TOOLS_ENABLED=true` in `.env`
- Agent's `tool_config` has `"enabled_tools": ["read_repo_file"]`
- `enable_ag_ui_tool=True` when sending the message (see [Tool Toggles](#tool-toggles-per-message))

### Test Script

1. Add `code-reviewer` to a room
2. Ensure you have a user repo with some code files (e.g., a FastAPI project imported via `POST /api/v1/user-repos/`)
3. Send:

```
Please review this repository. Repo ID: YOUR_REPO_ID. Start with the README, then check the main application files.
```

4. **Expected**: Agent reads files sequentially, then produces:
   - Summary card with file count and issue count
   - Warning alerts for critical issues  
   - Code blocks with suggested fixes
   - Table summarizing findings per file

### What to Observe

- [ ] Agent reads files using `read_repo_file` tool (verify in debug/logs)
- [ ] Read response includes `write_hint` with branch + `expected_head_sha`
- [ ] Agent does NOT call `write_repo_files` (read-only review mode)
- [ ] AG-UI components render: cards, alerts, code blocks, table
- [ ] Streaming works while agent reads and while it responds

---

## Demo 2: Pair Programmer

**Demonstrates**: Read → propose → write edit workflow with confirmation. Agent reads existing code, proposes a change, and writes it back using `write_repo_files`.

**Scenario**: An agent that helps you make code changes by reading the current file, understanding the request, and committing the edit directly to the repo.

### Agent Configuration

```json
{
  "name": "PairProgrammer",
  "slug": "pair-programmer",
  "description": "Reads and writes code files to implement changes",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["pair-programming", "refactoring", "code-generation"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file", "write_repo_files"]
  },
  "system_prompt": "You are a Pair Programmer agent that helps implement code changes in a repository.\n\nWorkflow:\n1. Use read_repo_file(repo_id, path) to read the current file content\n2. The read response includes write_hint.branch and write_hint.expected_head_sha\n3. Analyze the current code and plan your modification\n4. Before writing, confirm with the user what you plan to change (unless the change is trivial)\n5. Use write_repo_files(repo_id, branch, commit_message, mutations, expected_head_sha) to commit\n\nMutation format for write_repo_files:\n- upsert: requires path, operation='upsert', content\n- delete: requires path, operation='delete'\n\nRules:\n- ALWAYS use the expected_head_sha from the read response for optimistic concurrency\n- Use descriptive commit messages\n- After writing, confirm the change was committed and summarize what was changed\n- If the read fails or file doesn't exist, tell the user and suggest creating it\n- For multi-file changes, batch mutations when possible (send array of mutations)\n\nExample conversation:\nUser: 'Rename the variable `data` to `response_data` in app/main.py'\nYou: [reads file] → confirms plan → writes → confirms success"
}
```

### Setup Steps

1. Create the agent via API:

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "PairProgrammer",
    "slug": "pair-programmer",
    "description": "Reads and writes code files to implement changes",
    "model_name": "openai:gpt-4o-mini",
    "participation_mode": "always",
    "is_coordinator": false,
    "capabilities": ["pair-programming", "refactoring", "code-generation"],
    "scope": "system",
    "tool_config": { "enabled_tools": ["read_repo_file", "write_repo_files"] },
    "system_prompt": "You are a Pair Programmer agent that helps implement code changes.\n\nWorkflow:\n1. Use read_repo_file(repo_id, path) to read the current file content\n2. The read response includes write_hint.branch and write_hint.expected_head_sha\n3. Analyze the current code and plan your modification\n4. Before writing, confirm with the user what you plan to change\n5. Use write_repo_files(repo_id, branch, commit_message, mutations, expected_head_sha) to commit\n\nMutation format:\n- upsert: path, operation='\''upsert'\'', content\n- delete: path, operation='\''delete'\''\n\nRules:\n- ALWAYS use the expected_head_sha from the read response\n- Use descriptive commit messages\n- After writing, confirm the change was committed"
  }'
```

2. Confirm both repo tools are enabled:

```bash
curl -s http://localhost:8000/api/v1/agents/pair-programmer \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_config',{}))"
```

### Required Environment

- `AGENT_REPO_TOOLS_ENABLED=true` in `.env`
- Agent's `tool_config` has both `"read_repo_file"` and `"write_repo_files"`
- User must be a `RoomParticipant` for write authorization

### Test Script

1. Add `pair-programmer` to a room with an imported repo
2. Send:

```
In repo YOUR_REPO_ID, read app/main.py and add a new endpoint at the bottom that returns a health check. Commit with message "Add health check endpoint".
```

3. **Expected Flow**:
   - Agent reads `app/main.py` → gets `write_hint` with branch and `expected_head_sha`
   - Agent plans the change, shows you the proposed code
   - Agent calls `write_repo_files` with the mutation
   - Agent confirms the commit succeeded

4. Follow-up: Send:

```
Now rename the health endpoint to /ping and make it return JSON with status and timestamp.
```

5. **Expected**: Agent reads the updated file again (fresh `expected_head_sha`), makes the edit, commits.

### What to Observe

- [ ] Agent reads file and receives `write_hint` with branch + `expected_head_sha`
- [ ] Agent uses `expected_head_sha` in the write call (optimistic concurrency)
- [ ] Commit message matches the request
- [ ] Write completes without a streaming block (runs in worker thread)
- [ ] Read → write → read-again chain works for iterative edits
- [ ] If write conflicts (SHA mismatch), agent handles the error gracefully

---

## Demo 3: Review Panel

**Demonstrates**: Multi-agent code review with coordinator routing via @Mention A2A.

**Scenario**: A "review coordinator" that analyzes a file request, routes to a security specialist, a performance specialist, and a documentation specialist — each reading the code independently and providing domain-specific feedback.

### Agent Configurations

**Coordinator Agent**

```json
{
  "name": "ReviewCoordinator",
  "slug": "review-coordinator",
  "description": "Coordinates multi-agent code reviews and routes to specialists",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": true,
  "capabilities": ["coordination", "code-review", "routing"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file"]
  },
  "system_prompt": "You are the Review Coordinator for engineering code reviews.\n\nYour job:\n1. Read the requested file using read_repo_file(repo_id, path)\n2. Analyze what aspects of code need review\n3. Briefly share your initial assessment\n4. Route to specialists using @mentions:\n   - @SecurityReviewer - For auth, input validation, secrets, injection risks\n   - @PerformanceReviewer - For algorithms, N+1 queries, memory, caching\n   - @DocsReviewer - For docstrings, comments, README alignment\n\nFormat for @mentions:\n\"Security concerns detected in input handling. @SecurityReviewer please check for injection risks.\"\n\"This function has nested loops and repeated DB calls. @PerformanceReviewer, review efficiency.\"\n\nBe concise. Let the specialists do the deep analysis."
}
```

**Security Specialist**

```json
{
  "name": "SecurityReviewer",
  "slug": "security-reviewer",
  "description": "Security-focused code review specialist",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["security", "injection", "auth", "secrets"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file"]
  },
  "system_prompt": "You are a Security Reviewer specializing in code vulnerability analysis.\n\nWhen the Review Coordinator mentions you:\n1. Read the relevant file(s) using read_repo_file(repo_id, path) if you haven't seen them\n2. Focus exclusively on security: injection, XSS, auth bypass, hardcoded secrets, input validation, error handling, privilege escalation\n3. Rate severity: CRITICAL / HIGH / MEDIUM / LOW\n4. Use emit_ui_component with:\n   - 'alert' variant='danger' for CRITICAL/HIGH issues\n   - 'code' block showing vulnerable patterns and fixes\n5. Be specific about exploitability and suggest concrete fixes\n\nOnly discuss security — don't comment on performance or documentation style."
}
```

**Performance Specialist**

```json
{
  "name": "PerformanceReviewer",
  "slug": "performance-reviewer",
  "description": "Performance and efficiency code review specialist",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["performance", "algorithms", "database", "caching"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file"]
  },
  "system_prompt": "You are a Performance Reviewer specializing in code efficiency analysis.\n\nWhen the Review Coordinator mentions you:\n1. Read the relevant file(s) using read_repo_file(repo_id, path) if needed\n2. Focus: algorithmic complexity, N+1 queries, unnecessary loops, memory leaks, cache opportunities, blocking I/O\n3. Use emit_ui_component with:\n   - 'table' for before/after complexity comparisons\n   - 'code' for suggested optimizations\n4. Provide Big-O estimates where applicable\n\nOnly discuss performance — don't comment on security or documentation."
}
```

**Documentation Specialist**

```json
{
  "name": "DocsReviewer",
  "slug": "docs-reviewer",
  "description": "Documentation and code clarity specialist",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "on_mention",
  "is_coordinator": false,
  "capabilities": ["documentation", "code-clarity", "api-docs"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file"]
  },
  "system_prompt": "You are a Documentation Reviewer specializing in code clarity and documentation quality.\n\nWhen mentioned by the Review Coordinator:\n1. Read the relevant file(s) using read_repo_file(repo_id, path) if needed\n2. Focus: missing docstrings, unclear comments, README gaps, API documentation, naming clarity, type hints\n3. Use emit_ui_component with:\n   - 'card' for overall documentation assessment\n   - 'list' for specific suggestions\n   - 'code' showing improved docstrings/comments\n4. Suggest improvements to function/class docstrings following Google or NumPy style\n\nOnly discuss documentation — don't comment on security or performance."
}
```

### Test Script

1. Add all four agents to a room with an imported repo
2. Ensure agents are created with:
   - `review-coordinator`: `is_coordinator=true`, both tools enabled
   - `security-reviewer`, `performance-reviewer`, `docs-reviewer`: `participation_mode="on_mention"`, read tool only
3. Send:

```
Review the main API file in repo YOUR_REPO_ID: app/api/routes/items.py
```

4. **Expected Flow**:
   - `review-coordinator` runs FIRST, reads the file, gives a quick overview
   - Coordinator @mentions `@SecurityReviewer` → security specialist reads and reviews
   - Coordinator @mentions `@PerformanceReviewer` → performance specialist reads and reviews
   - Coordinator @mentions `@DocsReviewer` → docs specialist reads and reviews
   - All four responses appear in the room, each with domain-specific AG-UI components

### What to Observe

- [ ] Coordinator reads the file first and runs before specialists
- [ ] Each specialist independently re-reads the file (separate tool calls)
- [ ] `on_mention` specialists only respond when @mentioned
- [ ] Each specialist stays in their domain lane
- [ ] AG-UI components differ per specialist (alerts for security, tables for performance, cards for docs)
- [ ] @Mention A2A chain depth limit does not block the flow (depth 0 → depth 1 per specialist)

---

## Demo 4: Refactoring Pair

**Demonstrates**: Tool-based A2A (`request_agent_assistance`) for inline expert consultation during refactoring, combined with repo read/write.

**Scenario**: A lead developer agent that reads code, identifies a refactoring need, consults an architecture expert inline (invisible A2A call), then implements the refactor commit.

### Agent Configurations

**Lead Developer**

```json
{
  "name": "LeadDeveloper",
  "slug": "lead-developer",
  "description": "Leads refactoring efforts with expert consultation",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": false,
  "capabilities": ["refactoring", "architecture", "code-quality"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file", "write_repo_files"]
  },
  "system_prompt": "You are a Lead Developer agent specializing in code refactoring.\n\nWhen the user requests a refactoring task:\n\n1. Use read_repo_file(repo_id, path) to read the current code\n2. Analyze the code structure\n3. Use request_agent_assistance(target_agent='architect', request='...') to get architectural guidance on the refactor approach\n4. Synthesize the architect's advice with your implementation plan\n5. Present the plan to the user using emit_ui_component\n6. Use write_repo_files to implement the changes\n7. Confirm completion with a summary\n\nThe architect consultation is SILENT — users only see your final synthesized response.\nAlways mention that you consulted architectural guidance before presenting your plan.\n\nExample:\n\"I've consulted our architect advisor who suggests extracting the database logic into a service layer. Here's the plan... [plan with UI card]\"\nThen implement the changes."
}
```

**Architect Expert (Manual Mode — Only Consulted via A2A Tool)**

```json
{
  "name": "Architect",
  "slug": "architect",
  "description": "Software architecture consulting — only responds to tool-based requests",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "manual",
  "is_coordinator": false,
  "capabilities": ["architecture", "design-patterns", "service-layer", "modularity"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file"]
  },
  "system_prompt": "You are an Architecture Expert providing design and structure guidance.\n\nYou are ONLY consulted via tool calls (request_agent_assistance). You should NOT respond to @mentions or user messages directly.\n\nWhen consulted:\n1. Analyze the code structure described in the request\n2. Provide a focused architectural recommendation covering:\n   - Design pattern suggestions\n   - Separation of concerns improvements\n   - Modularity and dependency injection advice\n   - Potential breaking changes and migration path\n3. Keep it to 3-4 paragraphs — be concise\n4. Your response is returned inline to the calling agent, NOT to the chat room\n\nDo NOT recommend reading or writing files — the calling agent handles repo access."
}
```

### Required Tool Toggles

When triggering agents for this demo, pass both:

- `enable_a2a_tool=True` — enables `request_agent_assistance` on the lead developer
- `enable_ag_ui_tool=True` — enables UI component emission

### Test Script

1. Add both agents: `lead-developer`, `architect`
2. Send (with `enable_a2a_tool=True`):

```
Refactor repo YOUR_REPO_ID file app/main.py: extract all database operations into a separate repository pattern class. The DB code is mixed with route handlers right now.
```

3. **Expected Flow**:
   - `lead-developer` reads `app/main.py` → gets `write_hint`
   - Calls `request_agent_assistance('architect', 'Review this code and suggest repository pattern refactor')` (invisible to user)
   - Architect's response returns inline (not emitted to room)
   - Lead developer synthesizes: shows plan as a UI card
   - User can approve/adjust
   - Lead developer writes the refactored code

4. For demo simplicity (single-turn), the system prompt should implement without waiting for approval.

### What to Observe

- [ ] Lead developer is the only visible responder in the room
- [ ] Architect is consulted silently (check logs to confirm A2A tool call)
- [ ] `manual` mode architect does NOT respond to anything except the tool call
- [ ] Lead developer references the architect's input in its response
- [ ] `write_repo_files` uses correct `expected_head_sha` from the read
- [ ] Single cohesive response, not separate agent messages
- [ ] A2A depth is 1 (lead → architect), well within the `DEFAULT_MAX_A2A_DEPTH=2` limit

---

## Demo 5: Full Dev Workflow

**Demonstrates**: All patterns and tools working together in an end-to-end engineering collaboration.

**Scenario**: A multi-agent team handles a complete feature development cycle: architectural review, implementation, code review, and final approval.

### Agent Roster

Re-use all agents from Demos 2–4, plus add a **Project Manager** coordinator:

**Project Manager (Coordinator)**

```json
{
  "name": "ProjectManager",
  "slug": "project-manager",
  "description": "Orchestrates full feature development workflows",
  "model_name": "openai:gpt-4o-mini",
  "participation_mode": "always",
  "is_coordinator": true,
  "capabilities": ["orchestration", "project-management", "coordination"],
  "scope": "system",
  "tool_config": {
    "enabled_tools": ["read_repo_file"]
  },
  "system_prompt": "You are the Project Manager coordinating multi-agent engineering workflows.\n\nAvailable team members:\n- @LeadDeveloper - Reads and writes code, can consult @Architect via tool calls\n- @Architect - Architecture expert (manual mode, only responds to tool calls from LeadDeveloper)\n- @SecurityReviewer - Security-focused code review\n- @PerformanceReviewer - Performance-focused code review\n- @DocsReviewer - Documentation-focused code review\n- @CodeReviewer - General code review\n\nYour workflow when given a feature task:\n1. Read the relevant file(s) with read_repo_file to understand current state\n2. Briefly summarize what you see and what needs to happen\n3. Route implementation to @LeadDeveloper (who may consult @Architect)\n4. After implementation is done, route code review to @SecurityReviewer and @PerformanceReviewer\n5. Present a final summary using emit_ui_component with a 'card' showing status, files changed, and any issues flagged\n\nKeep your messages concise. Let the specialists execute and report."
}
```

### Room Setup

Add all seven agents to a single room:
1. `project-manager` (coordinate)
2. `lead-developer` (impl)
3. `architect` (manual, consult-only)
4. `security-reviewer` (on_mention)
5. `performance-reviewer` (on_mention)
6. `docs-reviewer` (on_mention)
7. `code-reviewer` (on_mention)

### Showcase Scenarios

**Scenario 1: Feature Implementation Cycle**

```
User: "Add input validation to the create-item endpoint in repo YOUR_REPO_ID, app/api/routes/items.py. Then review the result for security and performance."
```

**Expected Flow**:
- `project-manager` reads file, summarizes current state
- @mentions `@LeadDeveloper` → lead reads, implements, commits changes
- `project-manager` @mentions `@SecurityReviewer` → security review
- `project-manager` @mentions `@PerformanceReviewer` → performance review
- `project-manager` presents final summary card

**Scenario 2: Interactive Refactoring**

```
User: [Clicks "Start Refactor" action button from the PM's summary card]
```

**Expected Flow** (requires `enable_ag_ui_tool=True`):
- `project-manager` receives `[UI Action: start_refactor]`
- Routes to `@LeadDeveloper` with `@Architect` consultation
- Lead implements and commits
- PM emits updated status card

**Scenario 3: Docs Follow-up**

```
User: "Make sure the updated endpoints are documented in the README"
```

**Expected Flow**:
- `project-manager` @mentions `@DocsReviewer`
- Docs reviewer reads README + updated source files
- Suggests documentation updates
- `@LeadDeveloper` commits the README changes

### What to Observe

- [ ] Coordinator runs before all other agents on every message
- [ ] @Mention cascades trigger specialists sequentially
- [ ] Lead Developer's consultation with Architect is invisible/silent
- [ ] `manual` mode agents only respond via tool calls, never spontaneously
- [ ] Repo read/write chain respects `expected_head_sha` (no concurrent write conflicts)
- [ ] Action buttons work across the orchestration (if AG-UI enabled)
- [ ] Streaming works throughout all patterns
- [ ] Total messages scale linearly: coordinator + (N mentioned specialists) + lead → not combinatorial

---

## Tool Toggles Per Message

The two runtime toggles (`enable_a2a_tool`, `enable_ag_ui_tool`) are set at the **message invocation level**, not on the agent record. They flow through the call chain:

```
Route handler (rooms/send_message, ws, admin)
  → run_agents_for_message(enable_a2a_tool=?, enable_ag_ui_tool=?)
    → run_agent_for_room_streaming(..., enable_... flags)
      → StreamingAgentRunner.run(req=AgentRunRequest(enable_... flags))
        → get_agent_instance_with_tools(..., enable_... flags)
          → Agent(tools=[
              request_agent_assistance (if enable_a2a_tool),
              emit_ui_component (if enable_ag_ui_tool)
            ])
```

**Practical guidance:**

| Demo | `enable_a2a_tool` | `enable_ag_ui_tool` | Notes |
|------|-------------------|---------------------|-------|
| 1: Code Reviewer | `false` | `true` | Needs AG-UI for formatted review |
| 2: Pair Programmer | `false` | `true` | Optional AG-UI for formatted output |
| 3: Review Panel | `false` | `true` | AG-UI for specialist-formatted reviews |
| 4: Refactoring Pair | `true` | `true` | **Both required**: A2A for architect consult, AG-UI for plan display |
| 5: Full Workflow | `true` | `true` | **Both required**: A2A + AG-UI + @mention A2A |

If a toggle is `false`, the tool is simply not registered — agents won't see it and won't attempt to call it. No errors are raised; the tool just doesn't exist in the agent's context.

**Per-room defaults**: If certain rooms should always have one tool disabled, set the defaults before calling `run_agents_for_message`. E.g., a review-only room might always set `enable_a2a_tool=False`.

**Global kill switch for repo tools**: `AGENT_REPO_TOOLS_ENABLED=false` in `.env` disables both `read_repo_file` and `write_repo_files` at runtime regardless of agent `tool_config`. The toggles may still appear "enabled" in the agent config — this is intentional (configured but globally disabled).

---

## Cleanup

After testing, remove demo agents to keep your registry clean:

```bash
# List agents to find IDs
curl -s http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -c "import sys,json; [print(a['slug'], a['id']) for a in json.load(sys.stdin)]"

# Delete individual agents
curl -X DELETE http://localhost:8000/api/v1/agents/AGENT_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Or remove them via the frontend agent management UI.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Agent doesn't call repo tools | `AGENT_REPO_TOOLS_ENABLED=false` or `tool_config` not set | Check `.env` and agent `tool_config` |
| `request_agent_assistance` not available | `enable_a2a_tool=False` at route level | Set flag in the calling endpoint |
| `emit_ui_component` returns error | `enable_ag_ui_tool=False` at route level | Set flag in the calling endpoint |
| Write fails with SHA mismatch | File was modified between read and write | Agent should re-read for fresh `expected_head_sha` |
| Agent writes to wrong repo | Wrong `repo_id` passed to tool | Verify repo_id from `GET /api/v1/user-repos/` |
| @Mention doesn't trigger specialist | Wrong mention format or slug mismatch | Use `@AgentSlug` format (e.g., `@security-reviewer`) |
| Specialist responds AND auto-triggers | `participation_mode` set to `always` instead of `on_mention` | Set to `on_mention` for specialists |
| Coordinator runs after other agents | `is_coordinator` not set to `true` | Set `is_coordinator: true` on coordinator |
| Write blocks streaming | Not a bug — writes run in worker thread | Streaming continues during write |

---

## Quick Reference: All Agent Slugs

| Slug | Role | Participation | Tools | Key Demo |
|------|------|--------------|-------|----------|
| `code-reviewer` | Review-only code analyst | `always` | read | 1 |
| `pair-programmer` | Read → Write code editor | `always` | read, write | 2 |
| `review-coordinator` | Multi-agent review coordinator | `always` (coord) | read | 3 |
| `security-reviewer` | Security specialist | `on_mention` | read | 3, 5 |
| `performance-reviewer` | Performance specialist | `on_mention` | read | 3, 5 |
| `docs-reviewer` | Documentation specialist | `on_mention` | read | 3, 5 |
| `lead-developer` | Refactoring lead with A2A consult | `always` | read, write | 4, 5 |
| `architect` | Architecture advisor | `manual` | read | 4, 5 |
| `project-manager` | Full workflow coordinator | `always` (coord) | read | 5 |
