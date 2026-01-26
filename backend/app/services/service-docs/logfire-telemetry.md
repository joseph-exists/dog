# Logfire telemetry config

Telemetry tuning for every service in `backend/app/services` is centralized in `logfire_config.toml` alongside the `logfire_config` loader.

## Schema recap

- `version`: bump this when you make incompatible config changes.
- `[defaults]`: baseline values; `enabled` defaults to `false`, `level` is the minimum event level (`debug` → `error`), and `telemetry` gates spans (`traces`) vs events (`events`).
- `[bundles.<name>]`: reusable groups of services. `services` lists service IDs, `enabled`/`level` override defaults, and `[telemetry]` can toggle traces/events. A bundle name can be referenced directly from a service override via `services.<service_id>.bundles`.
- `[services.<service_id>]`: per-service overrides. Set `enabled`, `level`, or `telemetry` to tweak the bundle-derived values. Use the `bundles` list to opt a service into a bundle without editing the bundle’s service list.

Bundles are not mutually exclusive; the loader merges them by OR-ing `enabled/telemetry` flags and picking the most verbose `level` (debug wins over info). Explicit service overrides always win.

## How the helper enforces the config

`app.services.logfire_client.ServiceLogfire` wraps the real `logfire` client. Each service instantiates it with its canonical `service_id` (e.g., `ServiceLogfire("agent_runner")`). The wrapper checks `get_service_logfire_config` before emitting spans or events: spans only run when `traces` is enabled and event logs obey both `telemetry.events` and the configured `level`.

## Adding or updating a bundle/service

1. Add or extend `[bundles.<bundle_name>]` in `logfire_config.toml`, list all services affected, and configure `enabled`, `level`, and `[telemetry]`.
2. If a service needs to join without editing the bundle list, point its `[services.<id>]` entry at the bundle name via `bundles = ["<bundle_name>"]`.
3. Override a specific service by adding `[services.<id>]` with `enabled`, `level`, or `[telemetry]` keys.
4. Call `app.services.logfire_config.reload_logfire_config()` if you need the running process to pick up file changes (the loader is cached by default).

## Example

The current sample config enables the `agent_runners` bundle at `level = "debug"` with spans on, and turns on all events + traces for `event_emitter`, `event_replay`, and `realtime_publisher`. Add a new bundle like `background_workers` for `shadow_outbox_worker` if you later want to capture its telemetry separately; just add `[bundles.background_workers]` with `services = ["shadow_outbox_worker"]`.
