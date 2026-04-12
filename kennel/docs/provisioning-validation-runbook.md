# Kennel Provisioning Validation Runbook

This runbook validates the current kennel-owned provisioning path for runtime-backed environments using local `curl` calls against kennel.

It is intended for:

- local developer validation,
- QA manual verification,
- automation test design.

It explicitly tests the kennel `runtime_preset` path, not the backend-owned `bootstrap_plan` path.

## Automated Validator

The machine-checkable version of this runbook lives at [scripts/validate_provisioning.py](/home/josep/dog/kennel/scripts/validate_provisioning.py).

Basic usage:

```bash
python3 scripts/validate_provisioning.py
```

Verbose usage:

```bash
python3 scripts/validate_provisioning.py --verbose
```

Full Codex runtime validation:

```bash
OPENAI_API_KEY=sk-... python3 scripts/validate_provisioning.py \
  --require-codex-ready \
  --verbose
```

Full Claude runtime validation:

```bash
python3 scripts/validate_provisioning.py \
  --require-claude-ready \
  --verbose
```

Output behavior:

- stdout emits a single JSON summary suitable for CI or test harness parsing,
- stderr emits verbose request/response traces when `--verbose` is enabled,
- per-step request/response artifacts are written under `artifacts/provisioning-validation` by default.

## Scope

This artifact validates the current kennel implementation for:

- flavour rebuild and base-container readiness,
- `runtime_preset` normalization on create,
- `runtime_preset` normalization on inject,
- runtime file materialization,
- service manifest generation,
- service readiness probing,
- force-rebuild safety guard behavior.

Current runtime presets covered here:

- `codex`
- `claude_code`

## Prerequisites

Set these shell variables first:

```bash
export KENNEL_BASE_URL="${KENNEL_BASE_URL:-http://localhost:8090}"
export KENNEL_SECRET="${KENNEL_SECRET:?set KENNEL_SECRET first}"
export TEST_REPO_URL="${TEST_REPO_URL:-https://github.com/octocat/Hello-World.git}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
```

Tooling assumed:

- `curl`
- `jq`

Optional but useful:

- `python3` for quick polling helpers

## Important Test Notes

### Codex

The Codex preset is suitable for a full positive-path validation if you provide a real `OPENAI_API_KEY`.

Without a valid key:

- create still validates,
- inject may still write config and declare services,
- runtime readiness may fail or stay pending depending on Codex startup behavior.

### Claude Code

The Claude Code preset currently depends on Claude account authentication and a supported subscription for `claude remote-control`.

So there are two valid Claude outcomes:

1. Contract-level pass:
   create succeeds, inject resolves the preset, and kennel declares the `claude_code` service even if startup fails due to auth.
2. Full runtime pass:
   the runtime process stays up and `/envs/{name}/services` reports the service as `ready`.

For unattended QA and automation, the contract-level pass is the safer default expectation unless the test environment is explicitly pre-authenticated for Claude Code.

## Step 1: Health Check

Command:

```bash
curl -s "$KENNEL_BASE_URL/health" | jq
```

Validates:

- kennel HTTP server is reachable,
- the process is accepting management requests.

Expected result:

```json
{
  "status": "ok"
}
```

## Step 2: Inspect Runtime Flavours

Command:

```bash
curl -s "$KENNEL_BASE_URL/flavours" \
  -H "x-kennel-secret: $KENNEL_SECRET" | jq
```

Validates:

- runtime-specific flavours are registered,
- kennel reports `base_container` and `base_ready`,
- snapshot-era reporting has been replaced by base-container readiness.

Expected keys of interest:

- `dev-codex`
- `dev-claude-code`
- `base_container`
- `base_ready`
- `hermes-agent`
- `hermes-agent-dev`
(note: the hermes were added after original documentation, so aren't reflected below. put on your thinking cap and figure it out - deduction and induction are both important.)

## Step 3: Rebuild Runtime Flavours If Needed

### 3A. Trigger Codex flavour rebuild

Command:

```bash
CODEX_REBUILD_JOB="$(
  curl -s -X POST "$KENNEL_BASE_URL/flavours/dev-codex/rebuild" \
    -H "x-kennel-secret: $KENNEL_SECRET" | jq -r '.job_id'
)"
echo "$CODEX_REBUILD_JOB"
```

curl -s X POST "kennel

Validates:

- kennel accepts rebuild for the runtime-specific flavour,
- the flavour exists as a first-class rebuild target.

### 3B. Poll Codex rebuild completion

Command:

```bash
while true; do
  curl -s "$KENNEL_BASE_URL/rebuild-jobs/$CODEX_REBUILD_JOB" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/dev-codex-rebuild.json | jq
  STATUS="$(jq -r '.status' /tmp/dev-codex-rebuild.json)"
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
```

Validates:

- layered rebuild completes for `base -> dev -> dev-codex`,
- provision script execution is wired into the rebuild worker,
- failures surface through the rebuild job API.

Pass criteria:

- `.status == "done"`

Repeat the same two-step sequence for `dev-claude-code`:

```bash
CLAUDE_REBUILD_JOB="$(
  curl -s -X POST "$KENNEL_BASE_URL/flavours/dev-claude-code/rebuild" \
    -H "x-kennel-secret: $KENNEL_SECRET" | jq -r '.job_id'
)"
echo "$CLAUDE_REBUILD_JOB"
```

```bash
while true; do
  curl -s "$KENNEL_BASE_URL/rebuild-jobs/$CLAUDE_REBUILD_JOB" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/dev-claude-code-rebuild.json | jq
  STATUS="$(jq -r '.status' /tmp/dev-claude-code-rebuild.json)"
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
```

Validates:

- `dev-claude-code` is rebuildable as a first-class flavour,
- its provision script is reachable and syntactically valid at runtime.


then hermes:
```
BASE_HERMES_REBUILD_JOB="$(
  curl -s -X POST "$KENNEL_BASE_URL/flavours/base-hermes-agent/rebuild" \
    -H "x-kennel-secret: $KENNEL_SECRET" | jq -r '.job_id'
)"
echo "$BASE_HERMES_REBUILD_JOB"

while true; do
  curl -s "$KENNEL_BASE_URL/rebuild-jobs/$BASE_HERMES_REBUILD_JOB" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/base-hermes-agent-rebuild.json | jq
  STATUS="$(jq -r '.status' /tmp/base-hermes-agent-rebuild.json)"
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
```


then hermes agent:
```
HERMES_AGENT_REBUILD_JOB="$(
  curl -s -X POST "$KENNEL_BASE_URL/flavours/hermes-agent-dev/rebuild" \
    -H "x-kennel-secret: $KENNEL_SECRET" | jq -r '.job_id'
)"
echo "$HERMES_AGENT_REBUILD_JOB"

while true; do
  curl -s "$KENNEL_BASE_URL/rebuild-jobs/$HERMES_AGENT_REBUILD_JOB" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/hermes-agent-dev-rebuild.json | jq
  STATUS="$(jq -r '.status' /tmp/hermes-agent-dev-rebuild.json)"
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
```


## Step 4: Confirm Base Containers Are Ready

Command:

```bash
curl -s "$KENNEL_BASE_URL/flavours" \
  -H "x-kennel-secret: $KENNEL_SECRET" | jq '{
    codex: ."dev-codex",
    claude_code: ."dev-claude-code"
  }'
```

Validates:

- `base-dev-codex` exists and is reported ready,
- `base-dev-claude-code` exists and is reported ready.

Pass criteria:

- `."dev-codex".base_ready == true`
- `."dev-claude-code".base_ready == true`

## Step 5: Negative Create Test For Preset Mapping

This step is optional if the flavours are already built, but it is the cleanest way to prove that create-time `runtime_preset` maps to runtime-specific base containers.

Temporarily skip this step if the flavour is already ready and you do not want to tear it down.

Command:

```bash
curl -s -X POST "$KENNEL_BASE_URL/envs" \
  -H "Content-Type: application/json" \
  -H "x-kennel-secret: $KENNEL_SECRET" \
  -d '{
    "kind": "persistent",
    "runtime_preset": "codex"
  }' | jq
```

Validates:

- create-time preset normalization runs before clone,
- kennel resolves `runtime_preset: "codex"` to `base-dev-codex`.

If the base is missing, expected failure detail contains:

- `Base container not ready: base-dev-codex`
- `Rebuild flavour 'dev-codex' first`

The same pattern applies to:

- `runtime_preset: "claude_code"` -> `base-dev-claude-code`

## Step 6: Create A Codex Environment

Command:

```bash
CODEX_CREATE_JSON="$(
  curl -s -X POST "$KENNEL_BASE_URL/envs" \
    -H "Content-Type: application/json" \
    -H "x-kennel-secret: $KENNEL_SECRET" \
    -d '{
      "kind": "persistent",
      "runtime_preset": "codex"
    }'
)"
echo "$CODEX_CREATE_JSON" | jq
export CODEX_ENV_NAME="$(echo "$CODEX_CREATE_JSON" | jq -r '.name')"
export CODEX_JOB_ID="$(echo "$CODEX_CREATE_JSON" | jq -r '.job_id')"
```

terminal local dev:
```
curl -s -X POST "http://localhost:8090/envs" -H "Content-Type: application/json" -H "x-kennel-secret: woohoo" -d '{

      "kind": "persistent",

      "runtime_preset": "codex"

    }'
```

Validates:

- `runtime_preset` create path is accepted,
- kennel can clone from the runtime-specific base container,
- environment creation is asynchronous and job-backed.

Pass criteria:

- a non-empty `name`,
- a non-empty `job_id`,
- initial `status == "pending"`.

### Poll Codex create completion

Command:

```bash
while true; do
  curl -s "$KENNEL_BASE_URL/jobs/$CODEX_JOB_ID" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/codex-create.json | jq
  STATUS="$(jq -r '.status' /tmp/codex-create.json)"
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
```

Validates:

- clone and start completed successfully,
- kennel job state transitions from `pending` to `done`.

Pass criteria:

- `.status == "done"`
- `.env_name == $CODEX_ENV_NAME`

## Step 7: Inject The Codex Runtime

Command:

```bash
CODEX_INJECT_BODY="$(jq -n \
  --arg repo "$TEST_REPO_URL" \
  --arg api_key "$OPENAI_API_KEY" '
  {
    runtime_preset: "codex",
    repo_url: $repo
  }
  + (if $api_key != "" then {env_vars: {OPENAI_API_KEY: $api_key}} else {} end)
')"

curl -s -X POST "$KENNEL_BASE_URL/envs/$CODEX_ENV_NAME/inject" \
  -H "Content-Type: application/json" \
  -H "x-kennel-secret: $KENNEL_SECRET" \
  -d "$CODEX_INJECT_BODY" | tee /tmp/codex-inject.json | jq
```

Validates:

- inject-time preset normalization resolves `codex_app_server`,
- kennel writes runtime files for Codex,
- kennel executes bootstrap steps,
- kennel declares the `codex` service,
- terminal token issuance still happens as part of inject.

Pass criteria:

- `.env == $CODEX_ENV_NAME`
- `.workspace_path == "/home/dev/workspace"`
- `.declared_services[0].service_name == "codex"`
- `.declared_services[0].protocol == "ws"`
- `.declared_services[0].port == 4500`

Stronger positive-path criteria:

- `.bootstrap_success == true`
- `.started_services` contains `codex`

## Step 8: Inspect Codex Service Readiness

Command:

```bash
curl -s "$KENNEL_BASE_URL/envs/$CODEX_ENV_NAME/services" \
  -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/codex-services.json | jq
```

Validates:

- service manifest was persisted,
- kennel can probe runtime readiness,
- the built-in `codex` service profile uses websocket metadata on port `4500`.

Pass criteria for full runtime validation:

- `.service_count >= 1`
- `.ready_service_count >= 1`
- `.services[] | select(.service_name == "codex") | .status == "ready"`
- `.services[] | select(.service_name == "codex") | .port == 4500`

Contract-level pass if auth is missing or startup is flaky:

- `.service_count >= 1`
- `.services[] | select(.service_name == "codex")` exists

## Step 9: Create And Inject A Claude Code Environment

### 9A. Create

Command:

```bash
CLAUDE_CREATE_JSON="$(
  curl -s -X POST "$KENNEL_BASE_URL/envs" \
    -H "Content-Type: application/json" \
    -H "x-kennel-secret: $KENNEL_SECRET" \
    -d '{
      "kind": "persistent",
      "runtime_preset": "claude_code"
    }'
)"
echo "$CLAUDE_CREATE_JSON" | jq
export CLAUDE_ENV_NAME="$(echo "$CLAUDE_CREATE_JSON" | jq -r '.name')"
export CLAUDE_JOB_ID="$(echo "$CLAUDE_CREATE_JSON" | jq -r '.job_id')"
```

CLAUDE_CREATE_JSON="$(
  curl -s -X POST "localhost:8090/envs" \
    -H "Content-Type: application/json" \
    -H "x-kennel-secret: woohoo" \
    -d '{
      "kind": "persistent",
      "runtime_preset": "claude_code"
    }'
)"
echo "$CLAUDE_CREATE_JSON" | jq
export CLAUDE_ENV_NAME="$(echo "$CLAUDE_CREATE_JSON" | jq -r '.name')"
export CLAUDE_JOB_ID="$(echo "$CLAUDE_CREATE_JSON" | jq -r '.job_id')"

curl -s POST "http://localhost:8090/jobs/job-3e617fdf" -H "x-kennel-secret: woohoo"

Validates:

- `claude_code` preset is accepted on create,
- kennel attempts clone from `base-dev-claude-code`.

Poll exactly as in Step 6.

Pass criteria:

- create job ends with `.status == "done"`.

### 9B. Inject

Command:

```bash
curl -s -X POST "$KENNEL_BASE_URL/envs/$CLAUDE_ENV_NAME/inject" \
  -H "Content-Type: application/json" \
  -H "x-kennel-secret: $KENNEL_SECRET" \
  -d "{
    \"runtime_preset\": \"claude_code\",
    \"repo_url\": \"$TEST_REPO_URL\"
  }" | tee /tmp/claude-inject.json | jq
```

Validates:

- inject-time preset normalization resolves `claude_code_remote_control`,
- kennel writes Claude runtime files,
- kennel attempts to start `claude remote-control`,
- kennel declares the `claude_code` service even though runtime auth may still be required.

Contract-level pass criteria:

- `.declared_services[] | select(.service_name == "claude_code")` exists
- `.started_services` contains `claude_code` or `.fatal_error` explains auth/startup failure

Full runtime pass criteria:

- `.bootstrap_success == true`
- `.started_services` contains `claude_code`

## Step 10: Inspect Claude Service Readiness

Command:

```bash
curl -s "$KENNEL_BASE_URL/envs/$CLAUDE_ENV_NAME/services" \
  -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/claude-services.json | jq
```

Validates:

- service manifest exists for the Claude runtime,
- kennel can report PID-based readiness for a portless runtime.

Contract-level pass criteria:

- `.service_count >= 1`
- `.services[] | select(.service_name == "claude_code")` exists

Full runtime pass criteria:

- `.ready_service_count >= 1`
- `.services[] | select(.service_name == "claude_code") | .status == "ready"`

Expected auth-gated behavior:

- if the environment is not pre-authenticated for Claude Code, `bootstrap_success` may be `false` and the service may be `failed`.

That still validates kennel’s preset mapping, bootstrap attempt, manifest generation, and readiness reporting.

## Step 11: Validate Force-Rebuild Safety Guard

Run this while either `CODEX_ENV_NAME` or `CLAUDE_ENV_NAME` still exists.

Command:

```bash
FORCE_JOB="$(
  curl -s -X POST "$KENNEL_BASE_URL/flavours/dev-codex/rebuild?force=true" \
    -H "x-kennel-secret: $KENNEL_SECRET" | jq -r '.job_id'
)"
echo "$FORCE_JOB"
```

Poll:

```bash
while true; do
  curl -s "$KENNEL_BASE_URL/rebuild-jobs/$FORCE_JOB" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/force-rebuild.json | jq
  STATUS="$(jq -r '.status' /tmp/force-rebuild.json)"
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
```

Validates:

- kennel blocks forced rebuilds while `env-*` containers exist,
- the new safety check is active before overlay ancestry is destroyed.

Pass criteria:

- `.status == "failed"`
- `.error` contains `force rebuild blocked while user env containers exist`

## Step 12: Cleanup

Commands:

```bash
curl -s -X DELETE "$KENNEL_BASE_URL/envs/$CODEX_ENV_NAME" \
  -H "x-kennel-secret: $KENNEL_SECRET" | jq
```

```bash
curl -s -X DELETE "$KENNEL_BASE_URL/envs/$CLAUDE_ENV_NAME" \
  -H "x-kennel-secret: $KENNEL_SECRET" | jq
```

Validates:

- destroy path works for runtime-backed environments,
- cleanup removes test containers so future forced rebuilds can succeed.

## Summary Of What A Good Test Run Proves

If the runbook passes:

- kennel can rebuild runtime-specific base layers,
- kennel reports base-container readiness correctly,
- `runtime_preset` selects the intended runtime base image at create time,
- `runtime_preset` selects the intended runtime bootstrap profile at inject time,
- Codex runtime config, service declaration, and readiness probing work,
- Claude runtime config and service declaration work, with full readiness depending on auth,
- forced rebuilds are safely blocked while user environments still exist.
