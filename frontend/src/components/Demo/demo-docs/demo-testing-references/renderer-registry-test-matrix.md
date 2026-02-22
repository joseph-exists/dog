# Renderer Registry Test Matrix

**Last updated:** 2026-02-22  
**Primary suite:** `frontend/tests-unit/demo-renderer-registry.spec.tsx`
**Runtime behavior suite:** `frontend/tests-unit/demo-runtime-block-behavior.spec.ts`

## Purpose
1. Make renderer mapping coverage explicit and auditable.
2. Identify behavior combinations that still need deeper tests.
3. Keep Workstream 3 and Workstream 4 validation sequencing crisp.

## Covered in Current Unit Suite

### Panel mapping matrix
1. `storyRuntime` -> `DemoStoryPanel`
2. `chat` -> `DemoChatPanel`
3. `participantPanel` -> `ParticipantPanel`
4. `canvas` -> `CanvasPanel`
5. `a2ui` -> `A2UIPanel`
6. `storyEditor` -> `StoryEditorPanel`
7. `storyPlayer` -> `StoryPlayerPanel`
8. `debug` -> `DebugPanel`
9. `content` -> callback dispatch (`renderContentPayload`)
10. unknown panel kind -> non-fatal fallback
11. `storyEditor` with `roomStoryId=null` -> explicit fallback messaging

### Block mapping matrix
1. `storyMetadata` -> `StoryMetadataBlock`
2. `agentRoster` -> `AgentRosterBlock`
3. `orchestratorState` -> `OrchestratorStateBlock`
4. `toolCapability` -> `ToolCapabilityBlock`
5. `contributionFeed` -> `ContributionFeedBlock`
6. `gitView` -> `GitViewBlock`
7. `fileExplorer` -> `FileExplorerBlock`
8. `context` -> callback dispatch (`renderContentPayload`)
9. `content` -> callback dispatch (`renderContentPayload`)
10. `story` -> structured fallback path
11. unknown block type -> non-fatal fallback

### Runtime-coupled behavior permutations
1. `StoryMetadataBlock` derived state:
- runtime missing + route fallback present
- runtime projection present and authoritative
- runtime precedence over route fallback
- loading state and raw-config toggle behavior
2. `OrchestratorStateBlock` derived state:
- default config behavior
- explicit config flag behavior
- active-only agent filtering summary
- unfiltered summary including inactive orchestrators
3. `ContributionFeedBlock` derived state:
- default config behavior and `max_items` normalization
- internal-message filter on/off permutations
- recency sort + truncation behavior
- sender-type formatting permutations

## Combinatorial Axes Exercised
1. Kind/type dispatch axis:
- active panel kinds
- active block kinds
- unknown fallback kinds/types
2. Payload routing axis:
- callback path (`content`/`context` block types and `content` panel kind)
- dedicated component path
- structured fallback path (`story`)
3. Contract resilience axis:
- missing story context fallback (`storyEditor` when `roomStoryId=null`)
- unsupported kind/type non-fatal behavior

## Gaps Requiring More Attention
1. Visibility-mode integration (`visible` vs `hidden_mounted` vs `hidden_unmounted`) at route + `DemoShell` render level.
2. Runtime-coupled block behavior under async state transitions:
- `storyMetadata` with runtime loading/error/started/not-started transitions
- `orchestratorState` with socket connectivity flips
- `contributionFeed` with streaming message updates
3. Agent/capability data edge cases:
- ambiguous agent matching precedence (`id` vs `slug` vs `name`)
- very large capability sets and truncation behavior
- empty/malformed `config_json` across dedicated blocks
4. Theme and presentation override interactions:
- composition-level theme vs block `presentation_json` behavior
5. Deferred compatibility kinds:
- `storyPlayerPanel`
- `strange` (panel and block)

## Suggested Next Test Layers
1. Component-level rendering tests for dedicated blocks with realistic `config_json` permutations.
2. Route-level mapping tests for visibility semantics and block region ordering.
3. Browser-level acceptance scripts for A/B/C/D that include runtime transitions and error paths.
