# TinyFoot Test Scripts

This directory contains test and utility scripts for the TinyFoot backend API.

## Prerequisites

1. **Backend server running** on `http://localhost:8000`
2. **Test credentials** in `test.env` file (see below)
3. **Python packages** installed (requests, etc.)

### Setting up test.env

Create a `test.env` file in this directory or in `backend/` with:

```bash
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=yourpassword
```

## Scripts

### 1. test_story_system.py

Tests the complete CYOA story system including event sourcing and timeline navigation.

**What it tests:**
- **Phase 1:** Story creation, nodes, choices
- **Phase 2:** Progress tracking and choice making
- **Phase 3:** Timeline navigation (undo/jump/breadcrumbs)
- **Validation:** Event sourcing foundations (parent pointers, head versioning, state replay)

**Usage:**
```bash
# Run full test suite (15 tests)
python test_story_system.py

# Run with verbose output
python test_story_system.py --verbose

# Run specific phase only
python test_story_system.py --phase 1  # Story/Node CRUD
python test_story_system.py --phase 2  # Progress & Choices
python test_story_system.py --phase 3  # Timeline Navigation

# Use existing persona
python test_story_system.py --persona-id YOUR-PERSONA-UUID
```

**Requirements:**
- Backend server running on `http://localhost:8000`
- Database with migrations applied (especially Phase 1-3 CYOA migrations)
- Test credentials in `test.env`
- User persona (created automatically if not specified)

**Output:**
- Console logs with detailed test results and bug hints
- `test_results_story_system.json` - Complete results with:
  - All 15 test results (pass/fail)
  - Created entity IDs (story, nodes, choices, progress)
  - Phase-by-phase breakdown
  - Success rate and timing

**Features:**
- ✅ Comprehensive CYOA validation (15 tests across 4 phases)
- ✅ Automatic bug detection with helpful hints
- ✅ Tests tree structure (parent_choice_id linkage)
- ✅ Tests optimistic concurrency (head_version)
- ✅ Tests state replay correctness
- ✅ Timeline navigation validation
- ✅ Exit codes (0 for success, 1 for failures)

**Example Output:**
```
======================================================================
  STORY SYSTEM TEST SUITE
  CYOA Phase 1-3 Validation
======================================================================

──────────────────────────────────────────────────────────────────────
  Test 1: Create Story
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: create_story
     Story created: "The Enchanted Forest" (ID: 12345678...)

[... more tests ...]

======================================================================
  TEST SUMMARY
======================================================================
  Total Tests:  15
  ✅ Passed:    15
  ❌ Failed:    0
  Success Rate: 100.0%
```

**See:** `STORY_TEST_SUITE.md` for complete documentation

---

### 2. test_quixote_agent.py

Tests the Quixote storytelling AI agent by running it 5 times with different topics.

**What it tests:**
- Agent initialization and execution
- Story generation with various topics (courage, wisdom, friendship, perseverance, compassion)
- Response handling and error management
- Logging and result compilation

**Usage:**
```bash
python test_quixote_agent.py
```

**Requirements:**
- OpenAI API key configured in environment (`OPENAI_API_KEY`)
- Backend server running (for environment/config access)
- `pydantic-ai` library (already in dependencies)

**Output:**
- Console logs with story previews (first 200 characters)
- `test_results_quixote_agent.json` - Complete results with:
  - All 5 stories generated
  - Story lengths and topics
  - Success/failure status for each test
  - Timestamps and summary statistics

**Features:**
- ✅ Async agent execution
- ✅ Detailed logging with timestamps
- ✅ Story preview in console output
- ✅ Comprehensive JSON results
- ✅ Error handling and recovery
- ✅ Exit codes (0 for success, 1 for failures)

**Example Output:**
```
[2025-01-15 10:30:45] INFO: Test #1: Requesting story about 'courage'
[2025-01-15 10:30:47] INFO: Test #1: Story received (342 characters)

--- Story Preview ---
Once upon a time, there was a man who loved courage more than anything 
else in the world. He faced dragons and demons, storms and shadows...
--- End Preview ---
```

---

### 3. populate_jungian_system.py

Creates a complete Jungian archetype-based character system with full relationship linking.

**What it creates:**
- 12 Jungian Archetypes (The Innocent, The Sage, The Explorer, etc.)
- 36 Traits (3 per archetype)
- 10 Universal Qualities (Strength, Intelligence, Charisma, etc.)
- 36 Personas (3 per archetype)
- Quality-Trait relationship links
- Persona-Quality relationship links
- Automatic Persona-Trait links (via archetype inheritance)

**Usage:**
```bash
python populate_jungian_system.py
```

**Output:**
- Console progress with emojis and status indicators
- `test_results_jungian_system.json` - Complete results with all created entity IDs

**Features:**
- ✅ Continues on error (doesn't stop at first failure)
- ✅ Tracks all successes and failures
- ✅ Pass/fail indication for each operation
- ✅ Detailed JSON output with entity IDs

---

### 4. assign_persona_attributes.py

Assigns attributes from a CSV file to personas missing data in specified fields.

**Supported Fields:**
- `general_domain` - General character domain
- `specific_domain` - Specific character domain
- `general_domain_high` - High-level general domain
- `specific_domain_high` - High-level specific domain
- `long_description` - Extended persona description

**Assignment Modes:**

1. **Sequential** (default) - Attributes used without replacement
   - Takes attributes from front of list
   - Each attribute used only once
   - Good for ensuring all personas get unique attributes

2. **Stochastic** - Attributes randomly selected with replacement
   - Random sampling from full attribute pool
   - Attributes can be reused across personas
   - Good for natural variation

**Usage Examples:**

```bash
# Dry run to preview changes
python assign_persona_attributes.py \\
    --file sample_attributes.csv \\
    --field general_domain \\
    --sample-size 2 \\
    --dry-run

# Sequential assignment (default)
python assign_persona_attributes.py \\
    --file sample_attributes.csv \\
    --field general_domain \\
    --sample-size 2

# Stochastic assignment with 3 attributes per persona
python assign_persona_attributes.py \\
    --file sample_attributes.csv \\
    --field specific_domain \\
    --sample-size 3 \\
    --mode stochastic

# Shuffle before sequential assignment
python assign_persona_attributes.py \\
    --file sample_attributes.csv \\
    --field general_domain \\
    --sample-size 2 \\
    --shuffle

# Assign to long_description with space separator
python assign_persona_attributes.py \\
    --file descriptions.csv \\
    --field long_description \\
    --sample-size 1 \\
    --separator " "
```

**CSV File Format:**

Comma-separated values, can span multiple rows:

```csv
funny,serious,professor,mohawk
loves oranges,afraid of the dark,heavily tattooed
quirky,methodical,spontaneous
```

**Command-line Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--file PATH` | CSV file with attributes (required) | - |
| `--field NAME` | Field to populate (required) | - |
| `--sample-size N` | Attributes per persona | 2 |
| `--mode MODE` | `sequential` or `stochastic` | `sequential` |
| `--separator STR` | Join separator for attributes | `", "` |
| `--shuffle` | Shuffle before sequential assignment | false |
| `--dry-run` | Preview without making changes | false |
| `--output FILE` | JSON output filename | `assignment_results.json` |

**Output:**
- Console progress with per-persona status
- JSON results file with:
  - All assignments made
  - Success/failure for each persona
  - Statistics and timing
  - Error details

---

## Helper Module: auth_helper.py

Provides authentication for test scripts.

**Functions:**
- `get_authenticated_session()` - Returns requests.Session with auth headers
- `get_auth_headers()` - Returns dict with auth headers
- `get_access_token()` - Returns just the JWT token

**Testing authentication:**
```bash
python auth_helper.py
```

---

## Workflow Example

### 1. Initial Setup - Create Character System

```bash
# Create the complete Jungian archetype system
python populate_jungian_system.py
```

This creates 36 personas, but they're missing domain and description attributes.

### 2. Add General Domains

```bash
# Create a CSV with general domain attributes
cat > general_domains.csv << EOF
magical,mundane,academic,artistic
spiritual,technological,natural,urban
historical,futuristic,mystical,practical
EOF

# Assign 2 general domains to each persona (sequential)
python assign_persona_attributes.py \\
    --file general_domains.csv \\
    --field general_domain \\
    --sample-size 2
```

### 3. Add Specific Domains

```bash
# Create CSV with more specific attributes
cat > specific_domains.csv << EOF
fire magic,water divination,earth healing,air prophecy
clockwork engineering,steam power,electrical mastery
ancient ruins,forgotten lore,lost civilizations
EOF

# Assign randomly (stochastic)
python assign_persona_attributes.py \\
    --file specific_domains.csv \\
    --field specific_domain \\
    --sample-size 2 \\
    --mode stochastic
```

### 4. Add Long Descriptions

```bash
# Create CSV with descriptive phrases
cat > descriptions.csv << EOF
A mysterious figure who walks between worlds
One who seeks truth in ancient texts
A wanderer of forgotten paths
A guardian of sacred knowledge
EOF

# Assign one description per persona
python assign_persona_attributes.py \\
    --file descriptions.csv \\
    --field long_description \\
    --sample-size 1 \\
    --separator " "
```

---

## Tips & Best Practices

### CSV File Tips
- Use plain text editors (not Excel) to avoid encoding issues
- One attribute per comma-separated value
- Attributes can span multiple rows
- Empty cells/lines are automatically skipped
- No header row needed

### Sequential vs Stochastic
- **Use Sequential when:**
  - You want to ensure all attributes get used
  - You want no duplicates across personas
  - You have exactly enough attributes for all personas

- **Use Stochastic when:**
  - You want more natural variation
  - You have fewer attributes than needed
  - You want some personas to share attributes
  - You're okay with some attributes not being used

### Sample Size Guidelines
- `general_domain`: 2-3 attributes
- `specific_domain`: 2-3 attributes  
- `general_domain_high`: 1-2 attributes
- `specific_domain_high`: 1-2 attributes
- `long_description`: 1 attribute (or use space separator for multi-phrase)

### Dry Run First
Always run with `--dry-run` first to:
- Verify your CSV file is formatted correctly
- See which personas will be affected
- Confirm the attribute assignments look good
- Check you have enough attributes

---

## Troubleshooting

### "Authentication Error"
- Check `test.env` file exists with correct credentials
- Verify backend server is running
- Test with: `python auth_helper.py`

### "No personas found missing field"
All personas already have that field populated. To re-assign:
1. Manually clear the field in the database, or
2. Use a different field

### "Ran out of attributes"
In sequential mode, you don't have enough attributes for all personas.
- Add more attributes to CSV
- Reduce `--sample-size`
- Use `--mode stochastic` instead

### "Failed to update persona"
- Check user has permission to update personas
- Verify persona IDs in error output
- Check API logs for details

---

## Output Files

### test_results_quixote_agent.json
Complete log of Quixote agent test runs with:
- All 5 stories generated (full text)
- Topics tested
- Story lengths (character counts)
- Success/failure status for each test
- Timestamps for each story generation
- Summary statistics (total tests, successful, failed, average length)

### test_results_jungian_system.json
Complete log of Jungian system creation with:
- All created entity IDs (qualities, traits, archetypes, personas)
- Link relationship IDs
- Success/failure status for each operation
- Error details

### assignment_results.json
Complete log of attribute assignment with:
- Which personas were updated
- What attributes were assigned to each
- Success/failure per persona
- Timing and statistics

---

## API Endpoints Used

Based on `dog-openapi.json`:

- `POST /api/v1/login/access-token` - Authentication
- `GET /api/v1/users/me` - User info
- `GET /api/v1/personas` - List personas
- `POST /api/v1/personas` - Create persona
- `PUT /api/v1/personas/{id}` - Update persona
- `POST /api/v1/personas/from-archetype/{id}` - Create with inheritance
- `POST /api/v1/archetypes` - Create archetype
- `POST /api/v1/traits` - Create trait
- `POST /api/v1/qualities` - Create quality
- `POST /api/v1/quality-trait-links` - Link quality to trait
- `POST /api/v1/personas/{id}/qualities/{quality_id}` - Link persona to quality

---

## Future Enhancements

Potential additions:
- Bulk update endpoint for efficiency
- Filter personas by missing field in API
- Undo/rollback functionality
- Import/export complete persona datasets
- Template system for common attribute sets
- Validation rules for field formats
