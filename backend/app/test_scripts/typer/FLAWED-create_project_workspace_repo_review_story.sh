#!/usr/bin/env bash
# Creates the "Project workspace repository review" story and, by default,
# a demo composition bound to that story via metadata_json.story_id.

set -e

TYPER_DIR="/home/josep/dog/backend/app/test_scripts/typer"
cd "$TYPER_DIR"

source /home/josep/dog/backend/.venv/bin/activate

PY="python main.py"

CREATE_DEMO=true
PUBLISH_STORY=false
DEMO_TITLE="Project Workspace Repository Review"
DEMO_SLUG="project-workspace-repo-review"
DEMO_SCOPE="personal"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-demo)
      CREATE_DEMO=false
      shift
      ;;
    --publish)
      PUBLISH_STORY=true
      shift
      ;;
    --demo-title)
      DEMO_TITLE="$2"
      shift 2
      ;;
    --demo-slug)
      DEMO_SLUG="$2"
      shift 2
      ;;
    --demo-scope)
      DEMO_SCOPE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--no-demo] [--publish] [--demo-title TITLE] [--demo-slug SLUG] [--demo-scope personal|shared|system]" >&2
      exit 1
      ;;
  esac
done

extract_id() {
    python -c "
import json
import re
import sys

raw = sys.stdin.read()
start = raw.find('{')
if start >= 0:
    try:
        obj = json.loads(raw[start:])
        print(obj.get('id', ''))
        raise SystemExit
    except Exception:
        pass

match = re.search(r'^\s*ID:\s*([0-9a-fA-F-]+)\s*$', raw, re.MULTILINE)
if match:
    print(match.group(1))
"
}

require_id() {
  local label="$1"
  local value="$2"
  if [ -z "$value" ]; then
    echo "Failed to extract $label from CLI output" >&2
    exit 1
  fi
}

echo "=== Step 1: Create story ==="
STORY_ID=$($PY stories create "Project workspace repository review" \
  --desc "A human-in-the-loop workflow story for scaffolding a Project, preparing its dev environment workspace, reviewing attached repositories, initializing agent docs, and guiding safe repository updates." \
  | extract_id)
require_id "story id" "$STORY_ID"
echo "STORY_ID=$STORY_ID"

echo ""
echo "=== Step 2: Add state variables ==="

$PY stories add-state-var $STORY_ID --key project_context_captured --type boolean --default false --category project --desc "The target Project purpose, owner, constraints, and demo goals have been captured"
$PY stories add-state-var $STORY_ID --key workspace_available --type boolean --default false --category workspace --desc "A dev environment workspace exists and can be inspected by the room agents"
$PY stories add-state-var $STORY_ID --key repositories_attached --type boolean --default false --category repositories --desc "One or more repositories are attached to the Project or Room"
$PY stories add-state-var $STORY_ID --key repo_write_available --type boolean --default false --category repositories --desc "The Orchestrator has repo_write tool access for the attached repository"
$PY stories add-state-var $STORY_ID --key repository_inventory_complete --type boolean --default false --category repositories --desc "Attached repositories, branches, remotes, service boundaries, and ownership hints have been inventoried"
$PY stories add-state-var $STORY_ID --key agent_docs_initialized --type boolean --default false --category docs --desc "Agent-facing docs such as AGENTS.md, README notes, or workspace instructions have been created or confirmed"
$PY stories add-state-var $STORY_ID --key analysis_complete --type boolean --default false --category analysis --desc "Repository structure, project scaffolding gaps, and dev environment requirements have been analyzed"
$PY stories add-state-var $STORY_ID --key question_set_answered --type boolean --default false --category analysis --desc "The required repository review questions have answers or explicit unknowns"
$PY stories add-state-var $STORY_ID --key summary_ready --type boolean --default false --category communication --desc "A concise project/workspace/repository summary is ready for the human"
$PY stories add-state-var $STORY_ID --key human_review_requested --type boolean --default false --category human --desc "The Orchestrator has asked the user to review findings and choose whether to proceed, rewind, or reset"
$PY stories add-state-var $STORY_ID --key human_plan_approved --type boolean --default false --category human --desc "A human explicitly approved the repository update plan"
$PY stories add-state-var $STORY_ID --key rewind_requested --type boolean --default false --category human --desc "A human requested that the Story rewind to an earlier analysis point"
$PY stories add-state-var $STORY_ID --key reset_requested --type boolean --default false --category human --desc "A human requested a Story reset"
$PY stories add-state-var $STORY_ID --key update_plan_ready --type boolean --default false --category execution --desc "A bounded repository update plan with files, risks, and verification steps is ready"
$PY stories add-state-var $STORY_ID --key repo_updates_applied --type boolean --default false --category execution --desc "Approved repository updates have been written to the repo"
$PY stories add-state-var $STORY_ID --key validation_complete --type boolean --default false --category validation --desc "Relevant checks, tests, or manual verification have completed"
$PY stories add-state-var $STORY_ID --key validation_passed --type boolean --default false --category validation --desc "Validation completed successfully"
$PY stories add-state-var $STORY_ID --key review_evidence_ready --type boolean --default false --category review --desc "Diff summary, test output, residual risks, and next-step evidence are ready for review"
$PY stories add-state-var $STORY_ID --key demo_ready --type boolean --default false --category demo --desc "The Project, workspace notes, repository review, and update evidence are ready for the demo"
$PY stories add-state-var $STORY_ID --key blocked --type boolean --default false --category governance --desc "The workflow is blocked by missing access, missing repositories, unresolved risk, or human reset"

echo ""
echo "=== Step 3: Create nodes ==="

N0=$($PY stories add-node $STORY_ID \
  --title "Project Intake" \
  --content "Capture the Project purpose, user goal, participating Room, expected Demo outcome, known repositories, and dev environment expectations.

Orchestrator guidance: ask only for missing essentials. Agents may gather context and update the user, but they do not advance Story State by choosing for the human.

Exit when: project_context_captured is true." \
  --node-type task \
  --content-format markdown \
  --start \
  --json | extract_id)
echo "N0=$N0"

N1=$($PY stories add-node $STORY_ID \
  --title "Workspace Readiness" \
  --content "Confirm the dev environment workspace for this Project.

Review: workspace path, available commands, dependency managers, runtime services, environment variables, project-level docs, and any sandbox or credential constraints.

Exit when: workspace_available is true, or blocked is true with a clear access request." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N1=$N1"

N2=$($PY stories add-node $STORY_ID \
  --title "Repository Attachment Check" \
  --content "Verify which repositories are attached to the Project and visible in the Room context.

Collect: repository names, local paths, remotes, default branches, dirty worktree status, ownership signals, and whether repo_write is available to the Orchestrator.

Exit when: repositories_attached is true and repository_inventory_complete is true, or blocked is true." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N2=$N2"

N3=$($PY stories add-node $STORY_ID \
  --title "Agent Docs Initialization" \
  --content "Initialize or verify agent-facing repository documentation before deeper work.

Required proof: agent_docs_initialized indicates that repo instructions, workspace notes, or AGENTS.md-style guidance exists or the absence is intentionally documented.

The Orchestrator may use repo_write to create or update docs, then report exactly what changed." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N3=$N3"

N4=$($PY stories add-node $STORY_ID \
  --title "Repository Review Questions" \
  --content "Answer the repository review question set.

Questions:
- What is the Project scaffold and where are the primary entrypoints?
- How should the dev environment be started, tested, and reset?
- Which repositories or directories are authoritative for agents in this Room?
- What docs are missing or stale?
- What changes are safe for the Orchestrator to make now?
- What requires human confirmation before proceeding?

Exit when: analysis_complete and question_set_answered are true." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N4=$N4"

N5=$($PY stories add-node $STORY_ID \
  --title "Summary and Human Review Gate" \
  --content "Prepare a user-facing summary of Project scaffold, workspace readiness, repository inventory, docs initialization, open risks, and recommended next action.

Human-in-the-loop constraint: Orchestrators and Agents may perform tasks, write approved repository updates, and give detailed updates. They cannot make the Story-progressing choice for the user.

The update must explicitly offer: proceed with a bounded update plan, rewind to repository review, reset the Story, or stop because blocked.

Exit when: summary_ready and human_review_requested are true." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N5=$N5"

N6=$($PY stories add-node $STORY_ID \
  --title "Update Plan" \
  --content "Create a bounded repository update plan after human approval.

Plan contents: target files, intended edits, risks, verification commands, rollback notes, and what will be reported back to the user.

Exit when: human_plan_approved and update_plan_ready are true." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N6=$N6"

N7=$($PY stories add-node $STORY_ID \
  --title "Apply Repository Updates" \
  --content "Apply only the approved repository updates.

The Orchestrator may use repo_write tool access. Preserve unrelated user changes, keep edits scoped, and report changed files with rationale.

Exit when: repo_updates_applied is true, or blocked is true with the reason." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N7=$N7"

N8=$($PY stories add-node $STORY_ID \
  --title "Validate and Collect Evidence" \
  --content "Run targeted validation for the repository updates.

Collect: command outputs, test status, lint/build status, manual checks, skipped checks with reasons, and remaining risks.

Exit when: validation_complete is true." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N8=$N8"

N9=$($PY stories add-node $STORY_ID \
  --title "Review Evidence" \
  --content "Prepare final review evidence for the user and demo.

Include: repository diff summary, docs initialized or changed, commands run, validation result, remaining choices, and whether the demo is ready.

Exit when: review_evidence_ready is true." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N9=$N9"

N10=$($PY stories add-node $STORY_ID \
  --title "Demo Ready" \
  --content "The Project scaffold, workspace context, repository review, docs initialization, and update evidence are ready to be shown in the Demo.

Agents in the Room will receive this Story and Story State as context when called via API." \
  --node-type succeed \
  --content-format markdown \
  --end \
  --json | extract_id)
echo "N10=$N10"

N_rewind=$($PY stories add-node $STORY_ID \
  --title "Human Requested Rewind" \
  --content "A human requested a rewind. Return to repository review with the new instruction, retaining useful evidence already gathered." \
  --node-type task \
  --content-format markdown \
  --json | extract_id)
echo "N_rewind=$N_rewind"

N_reset=$($PY stories add-node $STORY_ID \
  --title "Human Requested Reset" \
  --content "A human requested a reset. Stop automated progression and ask the user or host system to reset Story State before restarting the demo path." \
  --node-type fail \
  --content-format markdown \
  --end \
  --json | extract_id)
echo "N_reset=$N_reset"

N_blocked=$($PY stories add-node $STORY_ID \
  --title "Blocked" \
  --content "The workflow is blocked by missing access, missing repositories, missing workspace, or unresolved risk.

The Orchestrator should explain the blocker, list the exact proof or permission needed, and ask the user whether to rewind, reset, or provide the missing input." \
  --node-type fail \
  --content-format markdown \
  --end \
  --json | extract_id)
echo "N_blocked=$N_blocked"

echo ""
echo "=== Step 4: Create choices (transitions) ==="

$PY stories add-choice $N0 $N1 \
  --text "Project context captured - check workspace readiness" \
  --requires-state '{"project_context_captured": true}' \
  --order 1

$PY stories add-choice $N0 $N_blocked \
  --text "Project context unavailable - block and request missing context" \
  --requires-state '{"blocked": true}' \
  --order 2

$PY stories add-choice $N1 $N2 \
  --text "Workspace available - inspect attached repositories" \
  --requires-state '{"workspace_available": true}' \
  --order 1

$PY stories add-choice $N1 $N_blocked \
  --text "Workspace unavailable - block and request access or setup details" \
  --requires-state '{"blocked": true}' \
  --order 2

$PY stories add-choice $N2 $N3 \
  --text "Repositories inventoried and repo_write availability known - initialize agent docs" \
  --requires-state '{"repositories_attached": true, "repository_inventory_complete": true}' \
  --order 1

$PY stories add-choice $N2 $N_blocked \
  --text "No attached repository or repository access missing - block" \
  --requires-state '{"blocked": true}' \
  --order 2

$PY stories add-choice $N3 $N4 \
  --text "Agent docs initialized or confirmed - answer repository review questions" \
  --requires-state '{"agent_docs_initialized": true}' \
  --order 1

$PY stories add-choice $N3 $N_blocked \
  --text "Agent docs cannot be initialized safely - block for human input" \
  --requires-state '{"blocked": true}' \
  --order 2

$PY stories add-choice $N4 $N5 \
  --text "Analysis and question set complete - prepare human review summary" \
  --requires-state '{"analysis_complete": true, "question_set_answered": true}' \
  --order 1

$PY stories add-choice $N4 $N_blocked \
  --text "Review cannot be completed with available context - block" \
  --requires-state '{"blocked": true}' \
  --order 2

$PY stories add-choice $N5 $N6 \
  --text "Human approved a bounded repository update plan - draft the plan" \
  --requires-state '{"summary_ready": true, "human_review_requested": true, "human_plan_approved": true}' \
  --order 1

$PY stories add-choice $N5 $N_rewind \
  --text "Human requested rewind - return to repository review" \
  --requires-state '{"rewind_requested": true}' \
  --order 2

$PY stories add-choice $N5 $N_reset \
  --text "Human requested reset - stop and await Story State reset" \
  --requires-state '{"reset_requested": true}' \
  --order 3

$PY stories add-choice $N5 $N_blocked \
  --text "Human review identifies a blocker - stop automated progression" \
  --requires-state '{"blocked": true}' \
  --order 4

$PY stories add-choice $N_rewind $N4 \
  --text "Rewind accepted - re-run repository review with updated instruction" \
  --requires-state '{"rewind_requested": false}' \
  --order 1

$PY stories add-choice $N6 $N7 \
  --text "Update plan ready and approved - apply repository updates" \
  --requires-state '{"human_plan_approved": true, "update_plan_ready": true, "repo_write_available": true}' \
  --order 1

$PY stories add-choice $N6 $N_blocked \
  --text "Update plan missing approval or repo_write access - block" \
  --requires-state '{"blocked": true}' \
  --order 2

$PY stories add-choice $N7 $N8 \
  --text "Approved repository updates applied - validate" \
  --requires-state '{"repo_updates_applied": true}' \
  --order 1

$PY stories add-choice $N7 $N_blocked \
  --text "Repository update blocked - report exact blocker" \
  --requires-state '{"blocked": true}' \
  --order 2

$PY stories add-choice $N8 $N9 \
  --text "Validation complete - prepare evidence for review" \
  --requires-state '{"validation_complete": true, "validation_passed": true}' \
  --order 1

$PY stories add-choice $N8 $N7 \
  --text "Validation failed - revise approved repository updates" \
  --requires-state '{"validation_complete": true, "validation_passed": false}' \
  --order 2

$PY stories add-choice $N9 $N10 \
  --text "Review evidence ready and validation passed - demo is ready" \
  --requires-state '{"review_evidence_ready": true, "validation_passed": true, "demo_ready": true}' \
  --order 1

$PY stories add-choice $N9 $N5 \
  --text "Review evidence ready but more human direction is needed" \
  --requires-state '{"review_evidence_ready": true, "demo_ready": false}' \
  --order 2

$PY stories add-choice $N9 $N_blocked \
  --text "Review evidence exposes a blocker - stop and request direction" \
  --requires-state '{"blocked": true}' \
  --order 3

echo ""
echo "=== Step 5: Validate state schema ==="
$PY stories validate-state-schema $STORY_ID

echo ""
echo "=== Step 6: Validate graph structure ==="
$PY stories validate $STORY_ID

echo ""
echo "=== Step 7: Display story tree ==="
$PY stories tree $STORY_ID

if [ "$PUBLISH_STORY" = true ]; then
  echo ""
  echo "=== Step 8: Publish story ==="
  $PY stories publish $STORY_ID
fi

if [ "$CREATE_DEMO" = true ]; then
  echo ""
  echo "=== Step 9: Create demo bound to story ==="
  DEMO_ID=$($PY demos create "$DEMO_TITLE" --slug "$DEMO_SLUG" --scope "$DEMO_SCOPE" | extract_id)
  require_id "demo id" "$DEMO_ID"
  echo "DEMO_ID=$DEMO_ID"

  COMPOSITION_FILE=$(mktemp /tmp/project-workspace-repo-review-composition.XXXXXX.json)
  python - "$COMPOSITION_FILE" "$STORY_ID" "$DEMO_TITLE" <<'PY'
import json
import sys

path, story_id, title = sys.argv[1:4]
composition = {
    "schema_version": 1,
    "layout_mode": "panels",
    "runtime_policy": "auto",
    "persona_policy": "first_available",
    "chat_mode": "participant",
    "presentation_json": {
        "typography": {
            "size": "sm",
            "line_height": "relaxed",
            "heading_font": "Inter",
            "body_font": "Inter",
        },
        "callouts": {
            "header": {
                "style": "runtime-banner",
                "text": "Project Workspace Repository Review",
                "icon": "git-branch",
            }
        },
        "tokens": {
            "--demo-accent-primary": "#2563eb",
            "--demo-accent-secondary": "#10b981",
        },
    },
    "panels": [
        {
            "id": "story-runtime",
            "kind": "storyRuntime",
            "prominence": "primary",
            "order": 1,
            "title": "Story State",
            "default_size": 46,
            "min_size": 30,
            "viewport_mode": "panel",
            "options": {
                "show_state": True,
                "show_choices": True,
                "mode": "orchestrator",
            },
        },
        {
            "id": "chat",
            "kind": "chat",
            "prominence": "primary",
            "order": 2,
            "title": "Room",
            "default_size": 54,
            "min_size": 35,
            "viewport_mode": "panel",
            "options": {
                "mode": "participant",
            },
        },
    ],
    "blocks": [],
    "metadata_json": {
        "story_id": story_id,
        "workflow_template": "project_workspace_repo_review",
        "orchestrator_pattern": True,
        "human_in_the_loop": True,
        "title": title,
    },
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(composition, handle, indent=2)
PY

  $PY demos compose "$DEMO_ID" "$COMPOSITION_FILE"
  echo "Composition file: $COMPOSITION_FILE"
fi

echo ""
echo "=== Done! ==="
echo "Story ID: $STORY_ID"
if [ "$CREATE_DEMO" = true ]; then
  echo "Demo ID: $DEMO_ID"
  echo "Demo slug: $DEMO_SLUG"
fi
if [ "$PUBLISH_STORY" = false ]; then
  echo "To publish: python main.py stories publish $STORY_ID"
fi
