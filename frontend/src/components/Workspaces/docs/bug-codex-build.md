if we use the frontend to provision a workspace using the following settings we are unable to launch codex from either the root user (default login to terminal) or the dev user (after using su - dev command in terminal.)

Runtime Preset: codex
Flavour: dev
Kind: Persistent
(everything else using defaults:)
Install Intent: None
Startup Intent: Terminal Only 

If we use the frontend to provision a workspace with 

Runtime Preset: codex
Flavour: dev
Kind: Persistent
Startup Intent: Agent Runtime
Agent Runtime Profile: codex

the following error is returned:

-bash: line 1: cd: /home/dev/workspace: No such file or directory -bash: line 1: kill: (225) - No such process


backend workspace record for Agent Runtime profile:
{
  "name": "codex-winderfalls",
  "flavour": "dev",
  "kind": "persistent",
  "status": "failed",
  "kennel_name": "env-cb1a4011",
  "kennel_job": null,
  "ws_token": null,
  "failure_message": "-bash: line 1: cd: /home/dev/workspace: No such file or directory\n-bash: line 1: kill: (225) - No such process",
  "last_transition_at": "2026-03-30T18:37:10.170053",
  "requested_at": "2026-03-30T18:37:05.859122",
  "started_at": "2026-03-30T18:37:08.888902",
  "ready_at": null,
  "stopped_at": null,
  "destroyed_at": null,
  "meta": {
    "repo_url": null,
    "ssh_pubkey": null,
    "env_vars": {},
    "bootstrap_intent": {
      "repo_source": null,
      "workspace_path": null,
      "install_intent": {
        "mode": "none"
      },
      "startup_intent": {
        "mode": "agent_service",
        "agent_profile": "codex"
      },
      "env_vars": {},
      "ssh_pubkey": null,
      "bootstrap_profile": null,
      "runtime_files": {}
    },
    "bootstrap_plan": {
      "workspace_path": "/home/dev/workspace",
      "steps": [
        {
          "type": "run_command",
          "phase": "starting_services",
          "label": "Start Codex Runtime",
          "command": "export DOG_WORKSPACE_AGENT_PROFILE=\"codex\"; export DOG_WORKSPACE_AGENT_HOST=\"${DOG_WORKSPACE_AGENT_CODEX_HOST:-0.0.0.0}\"; export DOG_WORKSPACE_AGENT_PORT=\"${DOG_WORKSPACE_AGENT_CODEX_PORT:-4317}\"; export DOG_WORKSPACE_AGENT_PLATFORM_SERVICES_JSON=\"${DOG_AGENT_PLATFORM_SERVICES_JSON:-}\"; export DOG_WORKSPACE_AGENT_PLATFORM_SERVICE_ACCESS_ISSUED_AT=\"${DOG_AGENT_PLATFORM_SERVICE_ACCESS_ISSUED_AT:-}\"; export DOG_WORKSPACE_AGENT_PLATFORM_SERVICE_ACCESS_EXPIRES_AT=\"${DOG_AGENT_PLATFORM_SERVICE_ACCESS_EXPIRES_AT:-}\"; export DOG_WORKSPACE_AGENT_PLATFORM_SERVICES_PATH=\"${DOG_AGENT_PLATFORM_SERVICES_PATH:-$HOME/.dog/platform-services/agent-runtime.json}\"; export DOG_WORKSPACE_AGENT_AFFORDANCE_URL=\"${DOG_AGENT_PLATFORM_SERVICE_AFFORDANCE_URL:-}\"; export DOG_WORKSPACE_AGENT_STORY_URL=\"${DOG_AGENT_PLATFORM_SERVICE_STORY_URL:-}\"; AGENT_CMD=\"${DOG_WORKSPACE_AGENT_CODEX_CMD:-codex}\"; echo \"Starting Codex Runtime using: $AGENT_CMD\"; if [ -f \"${DOG_WORKSPACE_AGENT_PLATFORM_SERVICES_PATH}\" ]; then echo \"Platform services file: $DOG_WORKSPACE_AGENT_PLATFORM_SERVICES_PATH\"; fi; if [ -n \"${DOG_WORKSPACE_AGENT_AFFORDANCE_URL:-}\" ]; then echo \"Affordance MCP: $DOG_WORKSPACE_AGENT_AFFORDANCE_URL\"; fi; if [ -n \"${DOG_WORKSPACE_AGENT_STORY_URL:-}\" ]; then echo \"Story MCP: $DOG_WORKSPACE_AGENT_STORY_URL\"; fi; if command -v \"${AGENT_CMD%% *}\" >/dev/null 2>&1; then exec bash -lc \"$AGENT_CMD\"; fi; echo \"Agent command not found: $AGENT_CMD; keeping runtime alive for operator inspection.\"; exec tail -f /dev/null",
          "cwd": "/home/dev/workspace",
          "background": true,
          "service_name": "codex"
        }
      ]
    },
    "runtime_preset": "codex",
    "bootstrap_progress": {
      "phase": "failed",
      "message": "Bootstrap plan execution failed.",
      "step_count": 1,
      "completed_steps": 0,
      "failure_message": "-bash: line 1: cd: /home/dev/workspace: No such file or directory\n-bash: line 1: kill: (225) - No such process"
    },
    "inject_errors": [
      "run_command: -bash: line 1: cd: /home/dev/workspace: No such file or directory\n-bash: line 1: kill: (225) - No such process"
    ],
    "declared_services": [
      {
        "id": "codex",
        "service_name": "codex",
        "label": "Codex Runtime",
        "kind": "agent_runtime",
        "protocol": "ws",
        "port": 4500,
        "path": "/",
        "source": "bootstrap_profile",
        "workspace_path": "/home/dev/workspace",
        "pid_path": "/tmp/codex.pid",
        "log_path": "/tmp/codex.log",
        "service_name_hint": "codex"
      }
    ],
    "bootstrap_step_results": [
      {
        "index": 0,
        "type": "run_command",
        "phase": "starting_services",
        "label": "Start Codex Runtime",
        "status": "failed",
        "error": "-bash: line 1: cd: /home/dev/workspace: No such file or directory\n-bash: line 1: kill: (225) - No such process",
        "service_name": "codex"
      }
    ],
    "bootstrap_started_services": [],
    "bootstrap_workspace_path": "/home/dev/workspace",
    "platform_service_projection": [
      {
        "consumer_kind": "workspace_runtime",
        "service_ids": [
          "affordance",
          "story"
        ],
        "issued_at": "2026-03-30T18:37:08.892175+00:00",
        "expires_at": "2026-03-30T18:47:08.892175+00:00"
      },
      {
        "consumer_kind": "agent_runtime",
        "service_ids": [
          "affordance",
          "story"
        ],
        "issued_at": "2026-03-30T18:37:08.892382+00:00",
        "expires_at": "2026-03-30T18:47:08.892382+00:00"
      }
    ],
    "kennel_create_request": {
      "name": "env-cb1a4011",
      "kind": "persistent",
      "flavour": "dev",
      "runtime_preset": "codex"
    },
    "kennel_inject_request": {
      "user": "dev",
      "repo_url": null,
      "runtime_preset": "codex",
      "bootstrap_profile": null,
      "env_var_keys": [
        "DOG_AGENT_PLATFORM_SERVICES_JSON",
        "DOG_AGENT_PLATFORM_SERVICES_PATH",
        "DOG_AGENT_PLATFORM_SERVICE_ACCESS_EXPIRES_AT",
        "DOG_AGENT_PLATFORM_SERVICE_ACCESS_ISSUED_AT",
        "DOG_AGENT_PLATFORM_SERVICE_AFFORDANCE_AUTH_MODE",
        "DOG_AGENT_PLATFORM_SERVICE_AFFORDANCE_GRANT_ID",
        "DOG_AGENT_PLATFORM_SERVICE_AFFORDANCE_SCOPES",
        "DOG_AGENT_PLATFORM_SERVICE_AFFORDANCE_TAGS",
        "DOG_AGENT_PLATFORM_SERVICE_AFFORDANCE_TRANSPORT",
        "DOG_AGENT_PLATFORM_SERVICE_AFFORDANCE_URL",
        "DOG_AGENT_PLATFORM_SERVICE_COUNT",
        "DOG_AGENT_PLATFORM_SERVICE_STORY_AUTH_MODE",
        "DOG_AGENT_PLATFORM_SERVICE_STORY_GRANT_ID",
        "DOG_AGENT_PLATFORM_SERVICE_STORY_SCOPES",
        "DOG_AGENT_PLATFORM_SERVICE_STORY_TAGS",
        "DOG_AGENT_PLATFORM_SERVICE_STORY_TRANSPORT",
        "DOG_AGENT_PLATFORM_SERVICE_STORY_URL",
        "DOG_PLATFORM_SERVICES_JSON",
        "DOG_PLATFORM_SERVICES_PATH",
        "DOG_PLATFORM_SERVICE_ACCESS_EXPIRES_AT",
        "DOG_PLATFORM_SERVICE_ACCESS_ISSUED_AT",
        "DOG_PLATFORM_SERVICE_AFFORDANCE_AUTH_MODE",
        "DOG_PLATFORM_SERVICE_AFFORDANCE_GRANT_ID",
        "DOG_PLATFORM_SERVICE_AFFORDANCE_SCOPES",
        "DOG_PLATFORM_SERVICE_AFFORDANCE_TAGS",
        "DOG_PLATFORM_SERVICE_AFFORDANCE_TRANSPORT",
        "DOG_PLATFORM_SERVICE_AFFORDANCE_URL",
        "DOG_PLATFORM_SERVICE_COUNT",
        "DOG_PLATFORM_SERVICE_STORY_AUTH_MODE",
        "DOG_PLATFORM_SERVICE_STORY_GRANT_ID",
        "DOG_PLATFORM_SERVICE_STORY_SCOPES",
        "DOG_PLATFORM_SERVICE_STORY_TAGS",
        "DOG_PLATFORM_SERVICE_STORY_TRANSPORT",
        "DOG_PLATFORM_SERVICE_STORY_URL"
      ],
      "runtime_file_paths": [
        "/home/dev/.dog/platform-services/agent-runtime.json",
        "/home/dev/.dog/platform-services/workspace-runtime.json"
      ],
      "has_bootstrap_plan": true
    }
  },
  "id": "9bd93a0a-2277-419a-b1e0-83751bb477aa",
  "owner_id": "228d7ff2-960d-48b3-91a0-979034859cfe",
  "bootstrap": {
    "intent": {
      "repo_source": null,
      "workspace_path": null,
      "install_intent": {
        "mode": "none"
      },
      "startup_intent": {
        "mode": "agent_service",
        "agent_profile": "codex"
      },
      "env_vars": {},
      "ssh_pubkey": null,
      "bootstrap_profile": null,
      "runtime_files": {}
    },
    "progress": {
      "phase": "failed",
      "message": "Bootstrap plan execution failed.",
      "step_count": 1,
      "completed_steps": 0,
      "failure_message": "-bash: line 1: cd: /home/dev/workspace: No such file or directory\n-bash: line 1: kill: (225) - No such process"
    }
  },
  "readiness_summary": {
    "terminal_ready": false,
    "bootstrap_complete": false,
    "services_ready": false,
    "service_count": 0,
    "ready_service_count": 0
  },
  "connectivity_summary": {
    "terminal_ready": false,
    "bootstrap_complete": false,
    "services_ready": false,
    "service_count": 0,
    "ready_service_count": 0
  },
  "services": [],
  "flavour_health": {
    "flavour": "dev",
    "snapshot_ready": false,
    "latest_rebuild_status": null,
    "latest_rebuild_job_id": null
  },
  "allowed_actions": [
    "destroy"
  ],
  "visibility": "private",
  "project_id": null,
  "project_summary": null,
  "terminal_status": "unavailable",
  "created_at": "2026-03-30T18:37:05.859166",
  "updated_at": "2026-03-30T18:37:10.170106",
  "terminal_url": null
}


Note that running the following command:

curl -s -X POST "http://localhost:8090/envs" -H "Content-Type: application/json" -H "x-kennel-secret: woohoo" -d '{ "kind": "persistent", "runtime_preset": "codex"}'

Creates the job, which creates the environment in a ready state: this environment is immediately available over lxc-attach, has home/dev and the dev user, and codex can be launched immediately.

