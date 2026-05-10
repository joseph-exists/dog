#!/usr/bin/env python3
"""
DEMO-1: Project Workspace Repository Review — Story Seeder

Creates the "Project Workspace Repository Review" story for use in a team
workflow demo. This story guides an Orchestrator agent and a human collaborator
through scaffolding a Project, reviewing its dev environment, inventorying
attached repositories, initializing agent-facing documentation, and — with
human approval — making bounded repository updates.

KEY CONCEPTS DEMONSTRATED:
- Human-in-the-loop story progression (agents cannot make choices)
- State flows only through human choices (sets_state on choices)
- Orchestrator uses repo_write to initialize agent docs
- Six-question repository review framework
- Bounded update plan with validation evidence

STORY STRUCTURE:
- 12 nodes: intake → workspace review → docs init → questions → summary gate
  → (rewind loop) → update plan → apply → validate → demo ready
- 3 terminal nodes: demo_ready (succeed), blocked (fail), reset (fail)
- 21 choices with sets_state mutations; 4 choices with requires_state guards
- 14 state variables tracking human approvals and workflow phase

=============================================================================

Usage:
    python create_project_workspace_repo_review_story.py
    python create_project_workspace_repo_review_story.py --verbose

Output:
    test_results_project_workspace_repo_review.json
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError

BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_project_workspace_repo_review.json"

test_results = {
    "test_suite": "DEMO-1: Project Workspace Repository Review",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class ProjectWorkspaceRepoReviewBuilder:
    """Builds the Project Workspace Repository Review story for a team workflow demo."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.story_id = None
        self.nodes = {}
        self.choices = []
        self.state_vars = {}

    def log(self, message: str):
        print(f"  {message}")

    def debug(self, message: str):
        if self.verbose:
            print(f"  [DEBUG] {message}")

    # =========================================================================
    # API Helper Methods
    # =========================================================================

    def create_story(self, title: str, description: str) -> dict:
        response = self.session.post(f"{BASE_URL}/stories", json={
            "title": title,
            "description": description,
            "current_version": 1
        })
        if response.status_code != 200:
            raise Exception(f"Failed to create story: {response.text}")
        return response.json()

    def create_state_variable(self, key: str, value_type: str,
                              default_value=None, enum_values: list = None,
                              description: str = None, category: str = None) -> dict:
        payload = {
            "key": key,
            "value_type": value_type,
        }
        if default_value is not None:
            payload["default_value"] = default_value
        if enum_values:
            payload["enum_values"] = enum_values
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category

        response = self.session.post(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema",
            json=payload
        )
        if response.status_code != 200:
            raise Exception(f"Failed to create state variable '{key}': {response.text}")
        return response.json()

    def create_node(self, title: str, content: str,
                    is_start: bool = False, is_end: bool = False,
                    content_format: str = "markdown") -> dict:
        response = self.session.post(f"{BASE_URL}/storynodes", json={
            "story_id": self.story_id,
            "story_version": 1,
            "title": title,
            "content": content,
            "node_type": "text",
            "content_format": content_format,
            "is_start_node": is_start,
            "is_end_node": is_end
        })
        if response.status_code != 200:
            raise Exception(f"Failed to create node '{title}': {response.text}")
        return response.json()

    def create_choice(self, from_node_name: str, to_node_name: str,
                      text: str, order: int = 0,
                      requires_state: dict = None,
                      sets_state: dict = None) -> dict:
        from_node = self.nodes.get(from_node_name)
        to_node = self.nodes.get(to_node_name)

        if not from_node:
            raise Exception(f"From node '{from_node_name}' not found")
        if not to_node:
            raise Exception(f"To node '{to_node_name}' not found")

        payload = {
            "from_node_id": from_node["id"],
            "to_node_id": to_node["id"],
            "text": text,
            "order": order
        }
        if requires_state:
            payload["requires_state"] = requires_state
        if sets_state:
            payload["sets_state"] = sets_state

        response = self.session.post(f"{BASE_URL}/node-choices", json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to create choice '{text}': {response.text}")
        return response.json()

    def validate_state_schema(self) -> dict:
        response = self.session.get(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema/validate"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to validate: {response.text}")
        return response.json()

    # =========================================================================
    # Story Building
    # =========================================================================

    def build_story(self):
        """Build the Project Workspace Repository Review story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\nCreating story...")

        story = self.create_story(
            title="Project Workspace Repository Review",
            description=(
                "A human-in-the-loop demo story guiding an Orchestrator agent and a human "
                "collaborator through scaffolding a Project, reviewing its dev environment, "
                "inventorying attached repositories, initializing agent-facing documentation, "
                "and — with human approval — making bounded repository updates.\n\n"
                "Demonstrates: human-gated state progression, six-question repo review "
                "framework, rewind loops, and bounded update plans with validation evidence."
            )
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        self.log("\n📋 Creating state schema...")

        # Phase tracking
        self.state_vars["workflow_phase"] = self.create_state_variable(
            key="workflow_phase",
            value_type="enum",
            enum_values=["intake", "workspace_review", "docs_init", "analysis",
                         "summary", "update_plan", "applying", "validating",
                         "evidence", "complete", "blocked", "reset"],
            default_value="intake",
            category="phase",
            description="Current phase of the workflow"
        )
        self.debug("Created state var: workflow_phase")

        # Progress flags
        self.state_vars["workspace_reviewed"] = self.create_state_variable(
            key="workspace_reviewed",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="Human confirmed workspace reviewed and understood"
        )
        self.debug("Created state var: workspace_reviewed")

        self.state_vars["repos_inventoried"] = self.create_state_variable(
            key="repos_inventoried",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="Human confirmed repository inventory is complete"
        )
        self.debug("Created state var: repos_inventoried")

        self.state_vars["repo_write_confirmed"] = self.create_state_variable(
            key="repo_write_confirmed",
            value_type="boolean",
            default_value=False,
            category="access",
            description="Orchestrator has repo_write tool access to the attached repository"
        )
        self.debug("Created state var: repo_write_confirmed")

        self.state_vars["docs_initialized"] = self.create_state_variable(
            key="docs_initialized",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="Agent-facing docs created, updated, or confirmed present"
        )
        self.debug("Created state var: docs_initialized")

        self.state_vars["questions_answered"] = self.create_state_variable(
            key="questions_answered",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="All six repository review questions answered or explicitly flagged unknown"
        )
        self.debug("Created state var: questions_answered")

        # Human approval flags
        self.state_vars["summary_approved"] = self.create_state_variable(
            key="summary_approved",
            value_type="boolean",
            default_value=False,
            category="human",
            description="Human chose to proceed with a bounded repository update after reading the summary"
        )
        self.debug("Created state var: summary_approved")

        self.state_vars["update_plan_approved"] = self.create_state_variable(
            key="update_plan_approved",
            value_type="boolean",
            default_value=False,
            category="human",
            description="Human approved the specific bounded update plan"
        )
        self.debug("Created state var: update_plan_approved")

        # Execution flags
        self.state_vars["updates_applied"] = self.create_state_variable(
            key="updates_applied",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="Approved repository changes have been written"
        )
        self.debug("Created state var: updates_applied")

        self.state_vars["validation_passed"] = self.create_state_variable(
            key="validation_passed",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="Targeted validation checks passed after updates were applied"
        )
        self.debug("Created state var: validation_passed")

        self.state_vars["evidence_ready"] = self.create_state_variable(
            key="evidence_ready",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="Demo evidence (diff summary, test output, remaining risks) is collected and ready"
        )
        self.debug("Created state var: evidence_ready")

        # Control flags
        self.state_vars["rewind_requested"] = self.create_state_variable(
            key="rewind_requested",
            value_type="boolean",
            default_value=False,
            category="control",
            description="Human requested a return to analysis with new direction"
        )
        self.debug("Created state var: rewind_requested")

        self.state_vars["blocked"] = self.create_state_variable(
            key="blocked",
            value_type="boolean",
            default_value=False,
            category="control",
            description="Workflow stopped due to missing access, missing repo, or unresolved risk"
        )
        self.debug("Created state var: blocked")

        self.state_vars["reset_requested"] = self.create_state_variable(
            key="reset_requested",
            value_type="boolean",
            default_value=False,
            category="control",
            description="Human requested a full story reset"
        )
        self.debug("Created state var: reset_requested")

        self.log(f"  Created {len(self.state_vars)} state variables")
        test_results["state_variable_ids"] = {name: var["id"] for name, var in self.state_vars.items()}

        self.log("\n🎭 Creating story nodes...")

        # START node
        self.nodes["project_intake"] = self.create_node(
            title="Project Intake",
            content="""# Project Workspace Repository Review

Welcome to the Project Workspace Repository Review story. This workflow guides
an Orchestrator agent and a human collaborator through scaffolding a Project,
reviewing its dev environment, inventorying attached repositories, initializing
agent-facing documentation, and — with human approval — making bounded repository
updates.

## What the Orchestrator should do at this node

Ask the human for any missing essentials:

- **Project name and owner** — who owns this project and why does it exist?
- **Participating Room** — which Room are we working in?
- **Demo goal** — what should be demonstrable at the end of this story?
- **Known repositories** — which repos are attached or expected?
- **Dev environment expectations** — local, container, remote, sandbox?

Do not invent context. If the human has already provided this in the Room
conversation, summarize it back for confirmation rather than asking again.

## Human gate

*You are about to make the first choice in this story. Agents cannot choose for
you — their job is to gather and present information so you can decide.*

Choose **Begin** when you have a project, at least one repo to review, and a
workspace you can point the Orchestrator at.

Choose **Blocked** if something essential is missing and you need to resolve it
before starting.""",
            is_start=True
        )
        self.debug("Created node: project_intake")

        # Rewind loop node
        self.nodes["rewind"] = self.create_node(
            title="Human Requested Rewind",
            content="""# Rewind Requested

A human has requested a return to the analysis phase with new direction.

## What the Orchestrator should do at this node

1. Acknowledge the rewind clearly.
2. Ask the human what changed or what additional direction they want to provide.
3. Summarize the new instruction before proceeding.
4. Carry forward any useful evidence already gathered — do not discard prior
   analysis, annotate it as superseded if needed.

## Human gate

Choose **Direction given** when you have provided the Orchestrator with clear
updated instruction and are ready for it to re-run the analysis."""
        )
        self.debug("Created node: rewind")

        # END nodes
        self.nodes["demo_ready"] = self.create_node(
            title="Demo Ready",
            content="""# Demo Ready

The Project scaffold, workspace context, repository inventory, agent docs
initialization, and update evidence are all complete.

Agents in the Room associated with this Demo will receive this Story and Story
State as context when called via API. The Orchestrator can use this state to
orient new participants, summarize what happened, and describe what was changed
and why.

**Story complete.** No further choices are required.""",
            is_end=True
        )
        self.debug("Created node: demo_ready")

        self.nodes["blocked"] = self.create_node(
            title="Blocked",
            content="""# Blocked

The workflow has stopped because of a missing access, missing repository,
unresolved risk, or human request.

## What the Orchestrator should do at this node

1. State the exact blocker clearly — what is missing, what permission or input
   is needed, and from whom.
2. Do not attempt to work around the blocker or guess at missing context.
3. Offer the human specific options: provide the missing input, grant the
   required access, or reset the story.

**This is a terminal node.** Story State must be reset by a human or host
system before the workflow can restart.""",
            is_end=True
        )
        self.debug("Created node: blocked")

        self.nodes["reset"] = self.create_node(
            title="Human Requested Reset",
            content="""# Human Requested Reset

A human has requested a full story reset. Automated progression has stopped.

The Orchestrator should acknowledge the reset, summarize what was accomplished
before the reset point, and confirm that Story State will need to be cleared
by the human or host system before this workflow can be restarted.

**This is a terminal node.** No further choices are available.""",
            is_end=True
        )
        self.debug("Created node: reset")

        self.nodes["workspace_repo_review"] = self.create_node(
            title="Workspace and Repository Review",
            content="""# Workspace and Repository Review

## What the Orchestrator should do at this node

### Workspace review

Inspect and report on:

- Workspace path and type (local filesystem, container, remote, sandbox)
- Available CLI tools and dependency managers (`git`, `npm`, `uv`, `docker`, etc.)
- Runtime services (databases, queues, dev servers) and how to start them
- Relevant environment variables (names only — do not expose secret values)
- Project-level documentation already present (`README`, `CLAUDE.md`, `AGENTS.md`, etc.)
- Any credential or sandbox constraints that will limit what the Orchestrator can do

### Repository inventory

For each attached repository, collect:

- Repository name, local path, and remote URL
- Default and current branch
- Dirty worktree status (uncommitted changes)
- Top-level directory structure (one level deep)
- Ownership signals: `CODEOWNERS`, team references in docs, primary language
- Whether the Orchestrator has `repo_write` tool access to this repository

Report clearly if any repository is missing, inaccessible, or has an unexpected state.

## Human gate

*The Orchestrator has reported its findings. You are making the next choice.*

Choose the option that reflects what was discovered about `repo_write` access.
Choose **Blocked** if the workspace or repositories are unavailable or unusable."""
        )
        self.debug("Created node: workspace_repo_review")

        self.nodes["agent_docs_init"] = self.create_node(
            title="Agent Docs Initialization",
            content="""# Agent Docs Initialization

## What the Orchestrator should do at this node

Initialize or verify agent-facing documentation for the attached repository
before deeper analysis begins.

### If `repo_write_confirmed` is true

Using `repo_write` tool access, create or update the following as needed:

- **`AGENTS.md`** at the repository root — agent instructions, architecture
  overview, command reference, forbidden actions
- **Workspace notes** — how to start, test, and reset the dev environment
- **`README` section** — brief note that an Orchestrator is active in this Room

Report **exactly** what was created, what was updated (with the change), and
what was already present and confirmed correct. Do not make silent changes.

### If `repo_write_confirmed` is false

Document the absence explicitly:

- State that agent docs could not be initialized because `repo_write` is
  unavailable
- List what docs are missing and what they would contain
- Note this as a risk for downstream analysis steps

### In both cases

Confirm the result to the human before they make the next choice.

## Human gate

Choose **Agent docs initialized** when docs have been created, updated, or
confirmed present (or intentionally absent with the reason documented).

Choose **Blocked** if docs cannot be safely initialized and human input is needed."""
        )
        self.debug("Created node: agent_docs_init")

        self.nodes["repo_questions"] = self.create_node(
            title="Repository Review Questions",
            content="""# Repository Review Questions

## What the Orchestrator should do at this node

Answer all six repository review questions. For each question, provide a direct
answer or explicitly flag it as **Unknown** with the reason.

---

### Q1 — Project scaffold and primary entrypoints

What is the top-level structure of the project? Where are the primary entrypoints
(routes, CLIs, background jobs, event handlers)? What are the main service
boundaries, if any?

### Q2 — Dev environment: start, test, reset

What is the exact sequence of commands to:
- Start the dev environment from a clean state
- Run the test suite (unit, integration, E2E)
- Reset the environment to a known-good state

Include dependency installation, database migrations, and any required environment
variables.

### Q3 — Authoritative directories for agents in this Room

Which repositories, directories, or files should agents in this Room treat as
authoritative? Which areas are off-limits or require special care?

### Q4 — Missing or stale documentation

What docs are missing entirely? What docs are present but appear outdated,
inconsistent with the code, or insufficient for a new agent or developer to
get started?

### Q5 — Changes safe for the Orchestrator to make now

Based on the review, what changes could the Orchestrator make right now without
risk — documentation updates, minor config fixes, missing files, stale references?

### Q6 — Changes requiring human confirmation

What changes should *not* be made without explicit human approval? List specific
files, areas, or operations and explain why each requires confirmation.

---

## Human gate

Choose **Analysis complete** when all six questions have answers or explicit
unknowns. The Orchestrator should not proceed until every question is addressed.

Choose **Blocked** if the Orchestrator cannot complete the analysis with the
available context and needs human input or additional access."""
        )
        self.debug("Created node: repo_questions")

        self.nodes["summary_gate"] = self.create_node(
            title="Summary and Human Review Gate",
            content="""# Summary and Human Review Gate

## What the Orchestrator should do at this node

Prepare a structured summary covering everything gathered so far. Present it
clearly to the human before they make their choice.

### Summary format

**Project:** [name, owner, demo goal]

**Workspace:** [type, key tools, services, constraints]

**Repositories:** [list with branch status, write access, ownership]

**Agent docs:** [what was created/updated/confirmed, or why absent]

**Review findings:**
- Scaffold and entrypoints: [summary]
- Dev environment commands: [summary]
- Authoritative areas: [summary]
- Missing/stale docs: [list]
- Safe changes available now: [list]
- Changes requiring human approval: [list]

**Recommended update scope:** [what the Orchestrator proposes to change, bounded
and specific]

**Open risks:** [anything that could go wrong, with mitigation notes]

---

**Important:** The Orchestrator presents this summary and waits. It does not
make the next choice. The human decides whether to proceed, rewind, or stop.

## Human gate

Choose **Proceed** to approve a bounded repository update. The Orchestrator
will draft a specific plan for your review before making any changes.

Choose **Rewind** to send the Orchestrator back to the analysis phase with
new direction. Your instruction will be captured at the next node.

Choose **Reset** to stop the workflow entirely. Story State must be reset
before restarting.

Choose **Blocked** if the summary reveals a problem that requires external
input before proceeding."""
        )
        self.debug("Created node: summary_gate")

        self.nodes["update_plan"] = self.create_node(
            title="Update Plan",
            content="""# Update Plan

## What the Orchestrator should do at this node

Draft a bounded repository update plan based on the approved scope from the
summary. The plan must be specific enough that the human can approve it without
ambiguity.

### Plan format

**Target files:** [exact paths, one per line]

**Intended edits:** [for each file: what changes and why]

**Risk assessment:** [what could go wrong with each change]

**Verification commands:** [exact commands to confirm the changes worked]

**Rollback notes:** [how to undo each change if needed]

**Out of scope:** [explicitly list what will NOT be changed, to prevent drift]

**Reporting commitment:** [what the Orchestrator will report back after applying]

---

Present the plan and wait for the human to approve it before making any changes.

## Human gate

Choose **Plan approved** when you have reviewed the plan and are satisfied with
the scope, risk assessment, and verification approach. The Orchestrator will
then apply the changes.

Choose **Blocked** if the plan is missing approval, `repo_write` is unavailable,
or the plan scope is unacceptable. Clarify what needs to change before proceeding."""
        )
        self.debug("Created node: update_plan")

        self.nodes["apply_updates"] = self.create_node(
            title="Apply Repository Updates",
            content="""# Apply Repository Updates

## What the Orchestrator should do at this node

Apply only the changes listed in the approved update plan using `repo_write`
tool access.

### Constraints

- **Scope only** — do not make changes outside the approved plan
- **Preserve user changes** — do not overwrite uncommitted work in unrelated areas
- **Report everything** — for each file changed, state what was changed and why
- **Stop on unexpected state** — if a file is in an unexpected state (conflicts,
  missing, permissions error), stop and report rather than guessing

### After applying

Report to the human:

- Files changed (with a brief summary of each change)
- Files that were already in the desired state (no change needed)
- Any files that could not be changed and why
- Current worktree status

## Human gate

Choose **Updates applied** when all approved changes have been written and
reported. The Orchestrator will then run validation.

Choose **Blocked** if a change could not be applied safely and human input or
additional access is needed."""
        )
        self.debug("Created node: apply_updates")

        self.nodes["validate_evidence"] = self.create_node(
            title="Validate and Collect Evidence",
            content="""# Validate and Collect Evidence

## What the Orchestrator should do at this node

Run targeted validation for the repository updates and collect evidence for
the demo.

### Validation steps

Run each relevant check and capture its output:

- **Lint / format check** — report pass/fail and any new violations introduced
- **Build** — report pass/fail
- **Test suite** — run tests relevant to changed areas; report pass/fail and
  any new failures
- **Manual checks** — any checks that cannot be automated; describe what was
  verified and how
- **Skipped checks** — list any checks that were skipped and the reason

### Evidence collection

Assemble the following for the demo:

- Diff summary (files changed, lines added/removed)
- Docs initialized or modified
- Commands run and their outcomes
- Overall validation status
- Remaining open items or risks

Report all of this to the human before they make the next choice.

## Human gate

Choose **Validation passed** when checks pass and the demo evidence is complete.

Choose **Validation failed — revise** to send the Orchestrator back to apply
corrected changes. The update plan remains approved; only the execution is revised.

Choose **More direction needed** if the evidence reveals that a broader
conversation is needed before concluding. Returns to the summary gate."""
        )
        self.debug("Created node: validate_evidence")

        self.log(f"  Created {len(self.nodes)} nodes")
        test_results["node_ids"] = {name: node["id"] for name, node in self.nodes.items()}

        # =====================================================================
        # STEP 4: CREATE CHOICES
        # =====================================================================
        self.log("\n🔀 Creating choices...")

        # --- project_intake ---
        self.choices.append(self.create_choice(
            from_node_name="project_intake",
            to_node_name="workspace_repo_review",
            text="Begin — I have a project, workspace, and at least one repo to review",
            order=0,
            sets_state={"workflow_phase": "workspace_review"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="project_intake",
            to_node_name="blocked",
            text="Blocked — missing context, access, or a repo to attach",
            order=1,
            sets_state={"blocked": True, "workflow_phase": "blocked"}
        ))

        # --- workspace_repo_review ---
        self.choices.append(self.create_choice(
            from_node_name="workspace_repo_review",
            to_node_name="agent_docs_init",
            text="Reviewed — Orchestrator has repo_write access, proceed to docs",
            order=0,
            sets_state={
                "workspace_reviewed": True,
                "repos_inventoried": True,
                "repo_write_confirmed": True,
                "workflow_phase": "docs_init"
            }
        ))
        self.choices.append(self.create_choice(
            from_node_name="workspace_repo_review",
            to_node_name="agent_docs_init",
            text="Reviewed — Orchestrator does NOT have repo_write access",
            order=1,
            sets_state={
                "workspace_reviewed": True,
                "repos_inventoried": True,
                "repo_write_confirmed": False,
                "workflow_phase": "docs_init"
            }
        ))
        self.choices.append(self.create_choice(
            from_node_name="workspace_repo_review",
            to_node_name="blocked",
            text="Blocked — workspace or repositories are unavailable or unusable",
            order=2,
            sets_state={"blocked": True, "workflow_phase": "blocked"}
        ))

        # --- agent_docs_init ---
        self.choices.append(self.create_choice(
            from_node_name="agent_docs_init",
            to_node_name="repo_questions",
            text="Agent docs initialized or confirmed present — proceed to review questions",
            order=0,
            sets_state={"docs_initialized": True, "workflow_phase": "analysis"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="agent_docs_init",
            to_node_name="blocked",
            text="Blocked — cannot safely initialize docs, need human input",
            order=1,
            sets_state={"blocked": True, "workflow_phase": "blocked"}
        ))

        # --- repo_questions ---
        self.choices.append(self.create_choice(
            from_node_name="repo_questions",
            to_node_name="summary_gate",
            text="Analysis complete — all questions answered or explicitly flagged unknown",
            order=0,
            sets_state={"questions_answered": True, "workflow_phase": "summary"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="repo_questions",
            to_node_name="blocked",
            text="Blocked — cannot complete analysis with available context",
            order=1,
            sets_state={"blocked": True, "workflow_phase": "blocked"}
        ))

        # --- summary_gate ---
        self.choices.append(self.create_choice(
            from_node_name="summary_gate",
            to_node_name="update_plan",
            text="Proceed — I approve a bounded repository update plan",
            order=0,
            requires_state={"questions_answered": True},
            sets_state={"summary_approved": True, "workflow_phase": "update_plan"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="summary_gate",
            to_node_name="rewind",
            text="Rewind — return to analysis with new direction",
            order=1,
            sets_state={"rewind_requested": True, "workflow_phase": "analysis"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="summary_gate",
            to_node_name="reset",
            text="Reset — stop the workflow entirely and clear state before restarting",
            order=2,
            sets_state={"reset_requested": True, "workflow_phase": "reset"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="summary_gate",
            to_node_name="blocked",
            text="Blocked — summary reveals a problem requiring external input",
            order=3,
            sets_state={"blocked": True, "workflow_phase": "blocked"}
        ))

        # --- rewind ---
        self.choices.append(self.create_choice(
            from_node_name="rewind",
            to_node_name="repo_questions",
            text="Direction given — re-run analysis with updated instruction",
            order=0,
            requires_state={"rewind_requested": True},
            sets_state={
                "rewind_requested": False,
                "questions_answered": False,
                "workflow_phase": "analysis"
            }
        ))

        # --- update_plan ---
        self.choices.append(self.create_choice(
            from_node_name="update_plan",
            to_node_name="apply_updates",
            text="Plan approved — apply the bounded repository updates",
            order=0,
            requires_state={
                "$and": [
                    {"summary_approved": True},
                    {"repo_write_confirmed": True}
                ]
            },
            sets_state={"update_plan_approved": True, "workflow_phase": "applying"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="update_plan",
            to_node_name="blocked",
            text="Blocked — plan is missing approval or repo_write is unavailable",
            order=1,
            sets_state={"blocked": True, "workflow_phase": "blocked"}
        ))

        # --- apply_updates ---
        self.choices.append(self.create_choice(
            from_node_name="apply_updates",
            to_node_name="validate_evidence",
            text="Updates applied — run validation and collect evidence",
            order=0,
            requires_state={"update_plan_approved": True},
            sets_state={"updates_applied": True, "workflow_phase": "validating"}
        ))
        self.choices.append(self.create_choice(
            from_node_name="apply_updates",
            to_node_name="blocked",
            text="Blocked — update could not be applied safely",
            order=1,
            sets_state={"blocked": True, "workflow_phase": "blocked"}
        ))

        # --- validate_evidence ---
        self.choices.append(self.create_choice(
            from_node_name="validate_evidence",
            to_node_name="demo_ready",
            text="Validation passed — demo evidence is complete and ready",
            order=0,
            sets_state={
                "validation_passed": True,
                "evidence_ready": True,
                "workflow_phase": "complete"
            }
        ))
        self.choices.append(self.create_choice(
            from_node_name="validate_evidence",
            to_node_name="apply_updates",
            text="Validation failed — revise and re-apply the approved changes",
            order=1,
            sets_state={
                "validation_passed": False,
                "updates_applied": False,
                "workflow_phase": "applying"
            }
        ))
        self.choices.append(self.create_choice(
            from_node_name="validate_evidence",
            to_node_name="summary_gate",
            text="More direction needed — return to summary gate for human review",
            order=2,
            sets_state={"evidence_ready": True, "workflow_phase": "summary"}
        ))

        self.log(f"  Created {len(self.choices)} choices")
        test_results["choice_ids"] = [c["id"] for c in self.choices]

        # =====================================================================
        # STEP 5: VALIDATE STATE SCHEMA
        # =====================================================================
        self.log("\n✅ Validating state schema...")

        validation = self.validate_state_schema()

        if validation.get("is_valid"):
            self.log("  Schema is VALID — all state variables defined!")
        else:
            self.log("  Schema has issues:")
            for error in validation.get("errors", []):
                self.log(f"    - {error.get('variable_key')} in {error.get('used_in')}")

        return validation.get("is_valid", False)


def main():
    parser = argparse.ArgumentParser(description="Create the Project Workspace Repository Review story")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  DEMO-1: PROJECT WORKSPACE REPOSITORY REVIEW")
    print("  Human-in-the-loop story seeder")
    print("=" * 70)

    try:
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        builder = ProjectWorkspaceRepoReviewBuilder(session, verbose=args.verbose)
        is_valid = builder.build_story()

        print("\n" + "=" * 70)
        print("  STORY CREATION COMPLETE")
        print("=" * 70)
        print(f"\n  Story ID: {builder.story_id}")
        print(f"  Nodes created: {len(builder.nodes)}")
        print(f"  Choices created: {len(builder.choices)}")
        print(f"  State variables: {len(builder.state_vars)}")
        print(f"  Schema valid: {'Yes' if is_valid else 'No (in progress)'}")

        # Visual story structure
        print("\n  📋 STORY STRUCTURE:")
        print("  ┌─ project_intake (START)")
        print("  │   ├─→ workspace_repo_review")
        print("  │   │     ├─→ agent_docs_init")
        print("  │   │     │     ├─→ repo_questions")
        print("  │   │     │     │     ├─→ summary_gate")
        print("  │   │     │     │     │     ├─→ rewind → repo_questions (loop)")
        print("  │   │     │     │     │     ├─→ update_plan")
        print("  │   │     │     │     │     │     └─→ apply_updates")
        print("  │   │     │     │     │     │           └─→ validate_evidence")
        print("  │   │     │     │     │     │                 ├─→ demo_ready (END ✓)")
        print("  │   │     │     │     │     │                 ├─→ summary_gate (loop)")
        print("  │   │     │     │     │     │                 └─→ apply_updates (loop)")
        print("  │   │     │     │     │     ├─→ reset (END ✗)")
        print("  │   │     │     │     │     └─→ blocked (END ✗)")
        print("  │   │     │     │     └─→ blocked")
        print("  │   │     │     └─→ blocked")
        print("  │   │     └─→ blocked")
        print("  └─→ blocked")
        print("")
        print("  🔐 HUMAN-IN-THE-LOOP:")
        print("  Agents read node content and do work. Humans make all choices.")
        print("  No state variable is agent-settable — state flows through human decisions.")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  📊 Results saved to: {RESULTS_FILE}")

        return 0 if is_valid else 1

    except AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        test_results["errors"].append(str(e))
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        test_results["errors"].append(str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
