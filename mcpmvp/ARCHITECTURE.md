# MCP Server Architecture

This directory contains standalone MCP (Model Context Protocol) servers that provide specialized tooling for agents. Each server is self-contained with direct service imports (no HTTP dependencies on the main backend).

## Directory Structure

```
mcpmvp/
├── ARCHITECTURE.md          # This file
├── pyproject.toml           # Dependencies (fastmcp, pydantic, yaml)
├── main.py                  # Entry point for running servers
│
├── # Affordance System
├── affordance_server.py     # MCP server exposing introspection tools
├── affordance_service.py    # Core logic for affordance queries
├── demo-builder.yaml        # Affordance registry definition
│
├── # Future: Story System
├── story_server.py          # (planned) Story navigation & branching
├── story_service.py         # (planned) Story logic
│
├── # Future: Tesser System
├── tesser_server.py         # (planned) Vector/embedding operations
├── tesser_service.py        # (planned) Tesser logic
│
├── # Future: Canvas System
├── canvas_server.py         # (planned) Canvas rendering & composition
├── canvas_service.py        # (planned) Canvas logic
│
└── docs/                    # Additional documentation
```

## Design Principles

### 1. Direct Import (No HTTP)

MCP servers import service logic directly rather than calling HTTP APIs:

```python
# ✅ GOOD: Direct import
from affordance_service import get_affordance_service
_service = get_affordance_service()

@mcp.tool
def affordance_list():
    return _service.registry.affordances

# ❌ AVOID: HTTP dependency
async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/api/v1/...")
```

**Why:** Eliminates network latency, removes backend dependency, simpler deployment.

### 2. Self-Contained Services

Each service should:
- Load its own data (YAML, JSON, or embedded)
- Have no imports from `backend/app/`
- Use only standard library + pydantic + domain-specific deps
- Expose a singleton getter function

```python
# Service pattern
_service_instance: MyService | None = None

def get_my_service() -> MyService:
    global _service_instance
    if _service_instance is None:
        data_path = Path(__file__).parent / "my-data.yaml"
        _service_instance = MyService.from_yaml(data_path)
    return _service_instance
```

### 3. FastMCP Tool Structure

Tools should be synchronous when possible (simpler), async only when needed:

```python
from fastmcp import FastMCP

mcp = FastMCP(
    "Server Name",
    instructions="Brief description for agents...",
)

@mcp.tool
def simple_query(param: str) -> dict:
    """Docstring becomes the tool description for agents."""
    return {"result": ...}

@mcp.resource("resource://name")
def get_resource() -> str:
    """Resources return string content (often JSON)."""
    return json.dumps(data, indent=2)
```

### 4. Pydantic Models for API Surface

Use Pydantic models for:
- Complex input parameters
- Structured responses
- Validation

```python
class QueryContext(BaseModel):
    user_id: str = "agent"
    is_superuser: bool = False
    # ...

def build_context(**kwargs) -> Context:
    """Helper to build domain models from simple params."""
    return Context(user=UserContext(id=kwargs["user_id"]), ...)
```

## Migration Checklist

When extracting a system from the main backend:

### Phase 1: Identify Dependencies

- [ ] Check imports in the service file (`grep "^from app\." service.py`)
- [ ] Check imports in the route file
- [ ] Identify data files (YAML, JSON configs)
- [ ] Note any database dependencies (these require more thought)

### Phase 2: Copy Files

- [ ] Copy service file to `mcpmvp/`
- [ ] Copy any data files (YAML, JSON)
- [ ] Update file paths if service loads data via `Path(__file__).parent`

### Phase 3: Create MCP Server

- [ ] Create `{domain}_server.py` using the FastMCP pattern
- [ ] Import service directly
- [ ] Convert HTTP endpoints to MCP tools
- [ ] Add resources for bulk data access

### Phase 4: Update Typer CLI

- [ ] Update `backend/app/test_scripts/typer/commands/{domain}.py`
- [ ] Add mcpmvp to path: `sys.path.insert(0, str(Path(__file__).parents[5] / "mcpmvp"))`
- [ ] Replace HTTP calls with direct service imports

### Phase 5: Clean Up Backend

- [ ] Remove route file from `backend/app/api/routes/`
- [ ] Remove service file from `backend/app/services/`
- [ ] Remove registration from `backend/app/api/main.py`
- [ ] Remove any data files that were copied

### Phase 6: Test

- [ ] Test MCP server: `python -c "from {domain}_server import ..."`
- [ ] Test Typer CLI: `python main.py {domain} --help`
- [ ] Verify no HTTP dependencies remain

## Running MCP Servers

### Development

```bash
cd mcpmvp
source .venv/bin/activate

# Run a specific server
fastmcp run affordance_server.py

# Or directly
python affordance_server.py
```

### With Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "demo-builder": {
      "command": "python",
      "args": ["/path/to/mcpmvp/affordance_server.py"]
    }
  }
}
```

## Upcoming Integrations

### Story System

**Current location:** `backend/app/api/routes/stories.py`, `storynodes.py`

**Potential scope:**
- Story structure navigation
- Node branching logic
- Choice evaluation
- Progress tracking

**Dependencies to evaluate:**
- Database models (Story, StoryNode, UserStoryProgress)
- May need to remain partially in backend if DB-heavy

### Tesser System

**Current location:** `backend/app/api/routes/tesser.py`

**Potential scope:**
- Embedding generation
- Vector similarity queries
- Semantic search

**Dependencies to evaluate:**
- External embedding APIs
- Vector store (if used)

### Canvas System

**Current location:** (new development)

**Potential scope:**
- Canvas composition rendering
- Demo layout computation
- Presentation JSON validation

**Dependencies to evaluate:**
- Panel/block schema definitions
- Theme resolution

## Integration with Typer CLI

The Typer CLI in `backend/app/test_scripts/typer/` can import directly from mcpmvp:

```python
import sys
from pathlib import Path

# Add mcpmvp to path
MCPMVP_PATH = Path(__file__).parents[5] / "mcpmvp"
sys.path.insert(0, str(MCPMVP_PATH))

from my_service import get_my_service
```

This allows CLI testing without HTTP and keeps the agent tooling consistent.

## Questions for Future Integrations

When planning a new MCP server, consider:

1. **Does it need database access?**
   - If yes, may need to stay in backend or use a hybrid approach
   - If no, good candidate for mcpmvp

2. **Is it read-heavy or write-heavy?**
   - Read-heavy introspection → mcpmvp
   - Write-heavy mutations → probably backend

3. **Does it need authentication?**
   - User-specific data → backend
   - Agent tooling / introspection → mcpmvp

4. **What's the primary consumer?**
   - Agents (Claude) → MCP server
   - Frontend → REST API in backend
   - Both → Consider exposing both interfaces
