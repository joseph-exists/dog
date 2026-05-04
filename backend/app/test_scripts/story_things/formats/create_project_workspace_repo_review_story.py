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

        # Returns False (scaffold) — will return validate_state_schema() result once complete
        return False


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
