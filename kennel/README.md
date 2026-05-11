The clean path from here is:

1. Confirm kennel is up.
2. Rebuild the base/flavour layers.
3. Create one test environment from a rebuilt flavour.
4. Inject workspace/runtime config.
5. Verify services.
6. Only then wire backend/frontend traffic through it.

Important naming note: `base-noble` is the startup bootstrap container from `kennel/scripts/init.sh`. The rebuild API uses separate flavour-layer containers like `base-base`, `base-dev`, `base-dev-codex`, etc. So after `base-noble` succeeds, it is still normal for `/flavours` to show `base_ready: false` until you run the rebuild API.

Use this from repo root:

```bash
export KENNEL_BASE_URL=http://localhost:8090
export KENNEL_SECRET=woohoo
```

Health and current flavour state:

```bash
curl -s "$KENNEL_BASE_URL/health" | jq

curl -s "$KENNEL_BASE_URL/flavours" \
  -H "x-kennel-secret: $KENNEL_SECRET" | jq
```

Rebuild the main runtime flavours one at a time. Rebuilding `dev-codex` will build `base -> dev -> dev-codex`; later rebuilds will skip existing layers unless `force=true` is passed.

```bash
JOB="$(
  curl -s -X POST "$KENNEL_BASE_URL/flavours/dev-codex/rebuild" \
    -H "x-kennel-secret: $KENNEL_SECRET" | jq -r '.job_id'
)"

while true; do
  curl -s "$KENNEL_BASE_URL/rebuild-jobs/$JOB" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/kennel-rebuild.json | jq
  STATUS="$(jq -r '.status' /tmp/kennel-rebuild.json)"
  [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ] && break
  sleep 2
done
```

Then repeat for the other desired targets:

```bash
dev-claude-code
hermes-agent-dev
cuda
```

For Hermes, use `hermes-agent` or `hermes-agent-dev` as the flavour name. The doc bit saying `base-hermes-agent` is stale; that is the generated container name, not the rebuild API target.

After rebuilds, smoke-test a container:

```bash
CREATE_JOB="$(
  curl -s -X POST "$KENNEL_BASE_URL/envs" \
    -H "Content-Type: application/json" \
    -H "x-kennel-secret: $KENNEL_SECRET" \
    -d '{"kind":"persistent","runtime_preset":"codex"}' | jq -r '.job_id'
)"

while true; do
  curl -s "$KENNEL_BASE_URL/jobs/$CREATE_JOB" \
    -H "x-kennel-secret: $KENNEL_SECRET" | tee /tmp/kennel-create.json | jq
  STATUS="$(jq -r '.status' /tmp/kennel-create.json)"
  [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ] && break
  sleep 2
done

ENV_NAME="$(jq -r '.env_name' /tmp/kennel-create.json)"
```

Then inject:

```bash
curl -s -X POST "$KENNEL_BASE_URL/envs/$ENV_NAME/inject" \
  -H "Content-Type: application/json" \
  -H "x-kennel-secret: $KENNEL_SECRET" \
  -d '{
    "runtime_preset": "codex",
    "repo_url": "https://github.com/octocat/Hello-World.git"
  }' | jq
```

Verify services:

```bash
curl -s "$KENNEL_BASE_URL/envs/$ENV_NAME/services" \
  -H "x-kennel-secret: $KENNEL_SECRET" | jq
```

There is also an automated runner:

```bash
cd kennel
KENNEL_BASE_URL=http://localhost:8090 \
KENNEL_SECRET=woohoo \
python3 scripts/validate_provisioning.py --verbose
```

I would avoid `force=true` until you have deleted any `env-*` containers, because the implementation intentionally blocks force rebuilds while user env overlays exist.