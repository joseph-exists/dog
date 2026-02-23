# Demo Builder Pack Registration Reference Card

## Purpose

Use capability packs to extend or override DemoBuilder composition/panel/block capabilities without changing persisted composition contract shape.

## Key APIs

Source: `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- `buildCapabilityRegistry(options)`
- `resolveBuilderCapabilityPacks(options)`
- `getBuilderCapabilityPackRegistrationInventory()`
- `getBuilderRequirementCompatibilityGaps(registry?)`
- `getBuilderRuntimeCompatibilityGaps(registry?)`
- `getBuilderRuntimeExpectationGaps(registry?)`
- `getBuilderCapabilitySafetyGaps(registry?)`

## Registration Model

1. Pack registrations are declared in `BUILDER_CAPABILITY_PACK_REGISTRATIONS`.
2. Each registration defines:
- `id`
- `description`
- `createPack()`
3. Pack activation is selected by:
- `VITE_DEMO_BUILDER_PACKS` (comma-separated pack ids)
- legacy compatibility flag `VITE_DEMO_BUILDER_ENABLE_INTERNAL_PLUGIN_PACK`

## Pack Authoring Contract

`BuilderCapabilityRegistryPack` supports:

- `id`
- `order`
- `compositionCapabilities`
- `panelCapabilities`
- `blockCapabilities`

Conflict behavior is controlled by `conflictPolicy`:

- `keep_existing` (default)
- `replace_existing`
- `error`

## Recommended Engineer Workflow

1. Add/adjust pack registration in `BUILDER_CAPABILITY_PACK_REGISTRATIONS`.
2. Enable pack in local env:
- `VITE_DEMO_BUILDER_PACKS=<pack_id>`
3. Validate:
- `npm run test:unit -- demo-builder-capability-registry.spec.ts`
- `npm run build`
4. Run compatibility checks in tests:
- runtime kind drift: `getBuilderRuntimeCompatibilityGaps(registry)`
- requirement drift: `getBuilderRequirementCompatibilityGaps(registry)`
- runtime-coupled expectation drift: `getBuilderRuntimeExpectationGaps(registry)`
- plugin safety constraints: `getBuilderCapabilitySafetyGaps(registry)`

## Safety/Compatibility Gates

Use these gates before enabling any new pack for shared environments:

1. Runtime kind compatibility:
- no missing runtime panel/block kinds
2. Requirement compatibility:
- no unexpected requirement drift unless explicitly approved
3. Runtime-coupled expectation compatibility:
- runtime-coupled capabilities keep required hooks:
  - `editorComponent`
  - `normalizeCompositionPatch`
  - `semanticValidators`
4. Plugin safety constraints:
- no unsupported composition controls (for current builder UI surface)
- no accidental requirement escalations without explicit rollout decision

## What DemoBuilder Users Get

Capability packs can safely change what authors see and can configure in builder UI:

- add/override panel kinds in add-controls
- add/override block kinds in add-controls
- swap display names/editor component identifiers
- attach normalization hooks for safe patch shaping
- attach semantic warning/error hooks for authoring guidance

All of the above remain contract-safe as long as resulting composition still conforms to canonical backend/OpenAPI schema.

## Current Built-In Pack

- `internal.plugin.demo-builder.v1`
- currently demonstrates:
  - `participantPanel` extension
  - `toolCapability` extension
