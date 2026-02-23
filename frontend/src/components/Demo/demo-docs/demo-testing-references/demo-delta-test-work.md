### Delta 2: COMPLETE:  Validate Renderer + Acceptance Behavior
1. Add renderer tests for registry selection, unknown-kind fallback, and visibility mode behavior.
2. Add QA evidence for A/B/C/D compositions using current active panel/block mappings.
3. Add targeted checks for runtime-coupled blocks (`storyMetadata`, `orchestratorState`, `contributionFeed`) and agent-coupled blocks (`agentRoster`, `toolCapability`).


To validate:

### Validation run
1. `cd frontend && npm run test:unit`
2. `cd frontend && npm run build` 


Implemented a renderer-focused, combinatorial unit suite and documented the coverage matrix/gaps.

### Added test harness
1. New unit test command: `frontend/package.json`
- `test:unit`: `playwright test -c playwright.unit.config.ts`

2. New unit Playwright config: `frontend/playwright.unit.config.ts`
- Isolated from E2E (`tests-unit` only, no webserver/auth setup).

3. TS config updates:
- `frontend/tsconfig.json` includes `tests-unit` + `playwright.unit.config.ts`
- `frontend/tsconfig.build.json` excludes `tests-unit/**/*` so prod builds stay clean

### Added combinatorial suite
1. `frontend/tests-unit/demo-renderer-registry.spec.tsx`
- 22 tests covering:
  - Active panel kind dispatch (`storyRuntime`, `chat`, `content`, `participantPanel`, `canvas`, `a2ui`, `storyEditor`, `storyPlayer`, `debug`)
  - Active block type dispatch (`context`, `content`, `story`, `storyMetadata`, `agentRoster`, `orchestratorState`, `toolCapability`, `contributionFeed`, `gitView`, `fileExplorer`)
  - Unknown kind/type non-fatal fallback behavior
  - Callback routing verification for content paths
  - Story-panel missing-story fallback behavior

### Added coverage/gap documentation
1. `frontend/src/components/Demo/demo-docs/demo-testing-references/renderer-registry-test-matrix.md`
- Explicit matrix of covered combinations
- Enumerated “needs more attention” areas:
  - visibility-mode integration
  - runtime-coupled transitions
  - capability edge cases
  - theme/presentation interactions
  - deferred compatibility kinds



The next layer : targeted component behavior tests for the runtime-coupled blocks (`storyMetadata`, `orchestratorState`, `contributionFeed`) using config/state permutations from the matrix.

--

Added the next test layer for runtime-coupled block behavior, with config/state permutations and coverage docs.

### What I implemented

1. Exported deterministic behavior helpers from runtime-coupled blocks:
- `frontend/src/components/Demo/blocks/StoryMetadataBlock.tsx`
  - `deriveStoryMetadataRuntimeState(...)`
  - `shouldShowRawStoryMetadataConfig(...)`
- `frontend/src/components/Demo/blocks/OrchestratorStateBlock.tsx`
  - `parseOrchestratorStateConfig(...)`
  - `summarizeOrchestratorState(...)`
- `frontend/src/components/Demo/blocks/ContributionFeedBlock.tsx`
  - `parseContributionFeedConfig(...)`
  - `selectContributionFeedMessages(...)`
  - `formatContributionSenderType(...)`

2. Added targeted permutation suite:
- `frontend/tests-unit/demo-runtime-block-behavior.spec.ts`
- Covers:
  - `storyMetadata`: loading/runtime fallback/precedence/config-toggle permutations
  - `orchestratorState`: defaults/flags/filtering/orchestrator-count permutations
  - `contributionFeed`: default config, max normalization, internal filtering on/off, recency+max truncation, sender-type normalization

3. Updated matrix documentation:
- `frontend/src/components/Demo/demo-docs/demo-testing-references/renderer-registry-test-matrix.md`
- Added the new runtime behavior suite and explicitly listed covered permutations.

### Validation

- `cd frontend && npm run test:unit`  
  - Result: **35 passed**
- `cd frontend && npm run build`  
  - Result: **passed**

Next Section:

visibility-mode integration tests at route + `DemoShell` level (`visible` / `hidden_mounted` / `hidden_unmounted`).

...

Closed that visibility test gap.

### Implemented

1. Extracted shared visibility semantics helpers:
- `frontend/src/components/Demo/blockVisibility.ts`
  - `normalizeBlockVisibility(...)`
  - `resolveDemoBlockRegion(...)`
  - `getRenderableDemoBlocks(...)`

2. Wired route mapping to shared helper:
- `frontend/src/routes/_layout/demo.$slug.tsx`
  - Replaced inline visibility normalization/filter/sort logic with `getRenderableDemoBlocks(...)`.

3. Added explicit `DemoShell` visibility-class helper:
- `frontend/src/components/Demo/DemoShell.tsx`
  - `getDemoBlockContainerClassName(...)`
  - All block containers now call this helper for consistent `hidden_mounted` behavior.

4. Added dedicated visibility integration test suite:
- `frontend/tests-unit/demo-visibility-semantics.spec.ts`
  - Covers:
    - v2 visibility normalization (`visible`, `hidden_unmounted`, `hidden_mounted`, invalid fallback)
    - region normalization/fallback
    - route renderability semantics (`hidden_unmounted` filtered, `hidden_mounted` retained)
    - ordering/default-order behavior
    - `DemoShell` class behavior for `hidden_mounted` vs `visible`

5. Updated testing matrix docs:
- `frontend/src/components/Demo/demo-docs/demo-testing-references/renderer-registry-test-matrix.md`
  - Added visibility suite and updated remaining-gap list.

...

Updated and synced both QA reference docs for Delta 2 A/B/C validation.

**Patched**
1. Added explicit A/B/C validation framing and payload coverage in `backend/app/test_scripts/demo/qa-demo-composition-reference.md:12`.
2. Added new composition examples:
- Composition B runtime-coupled coverage in `backend/app/test_scripts/demo/qa-demo-composition-reference.md:196`
- Composition C visibility semantics coverage in `backend/app/test_scripts/demo/qa-demo-composition-reference.md:266`
3. Expanded validation checklist + block type domains + combinatoric matrix in `backend/app/test_scripts/demo/qa-demo-composition-reference.md:417`, `backend/app/test_scripts/demo/qa-demo-composition-reference.md:477`, `backend/app/test_scripts/demo/qa-demo-composition-reference.md:512`.
4. Added walkthroughs for B and C in `backend/app/test_scripts/demo/qa-demo-composition-reference.md:666` and `backend/app/test_scripts/demo/qa-demo-composition-reference.md:693`.
5. Added Example 6 for hidden-mounted/runtime-coupled browser QA in `backend/app/test_scripts/demo/qa-content-block-browser-reference.md:311`.
6. Mirrored backend doc updates into frontend copies:
- `frontend/src/components/Demo/demo-docs/demo-testing-references/qa-demo-composition-reference.md`
- `frontend/src/components/Demo/demo-docs/demo-testing-references/qa-content-block-browser-reference.md`

**Gap Analysis (Current vs Needed)**
1. Current: A/B/C manual validation is now documented with concrete payloads and walkthroughs.
Needed: automate these as repeatable scripted checks in your external harness (session create + composition apply + assertions) to reduce manual drift.

2. Current: Runtime-coupled blocks (`storyMetadata`, `orchestratorState`, `contributionFeed`) have dedicated components and behavior-focused unit tests.
Needed: add behavior tests for `gitView`, `fileExplorer`, `toolCapability`, `agentRoster` (currently mostly mapping/parse coverage, less scenario-depth).

3. Current: Visibility semantics (`visible`, `hidden_mounted`, `hidden_unmounted`) are implemented and unit-tested at helper/class contract level.
Needed: add DOM-level component tests that explicitly verify mounted-hidden state retention across runtime/message updates.

4. Current: Composition docs now include expanded block type domains.
Needed: confirm QA harness includes negative/contract tests (invalid `story_id`, unknown region/type, malformed config payloads) as first-class regression cases.

5. Current: `story` block type still uses structured fallback renderer path (`frontend/src/components/Demo/rendererRegistry.tsx`).
Needed: decide whether `story` gets a dedicated renderer in Delta 2 or stays intentionally deferred.


...

**Findings (ordered by severity)**

1. `test_qa_demo_baseline.py` can report success without validating the resolved contract (high false-positive risk).  
`backend/app/test_scripts/demo/test_qa_demo_baseline.py:895`, `backend/app/test_scripts/demo/test_qa_demo_baseline.py:967`, `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1131`  
It only checks HTTP status codes for `PUT`/`POST` and never asserts returned composition/runtime semantics (panel kinds/order, block visibility defaults, composition source, runtime policy behavior).

2. Session response key usage is stale for current payload shape (`demo_session_id` vs `session_id`).  
`backend/app/test_scripts/demo/test_qa_demo_baseline.py:972`, `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1543`  
Current backend/frontend contract uses `demo_session_id`; script reads `session_id`, so logs/results are wrong (`N/A`), masking regressions.

3. Default `story_id` is hardcoded and environment-fragile; this is likely the main “won’t work” failure mode.  
`backend/app/test_scripts/demo/test_qa_demo_baseline.py:165`, `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1214`  
If that UUID does not exist in a target env, session resolve fails with 400. For multi-env QA this is brittle.

4. Script is baseline-only and does not cover Delta 2 A/B/C scenarios now documented.  
`backend/app/test_scripts/demo/test_qa_demo_baseline.py:229`  
No path for Composition B (`storyMetadata`, `orchestratorState`, `contributionFeed`) or Composition C visibility permutations (`hidden_mounted`, `hidden_unmounted`).

5. No validation that `composition_source`, `room`, and `runtime` fields are structurally correct.  
`backend/app/test_scripts/demo/test_qa_demo_baseline.py:975`  
`composition_source` is read but never asserted/used; no checks for required nested fields.

6. Missing argument validation for panel sizes can create invalid payloads that fail late.  
`backend/app/test_scripts/demo/test_qa_demo_baseline.py:1242`, `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1250`, `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1264`  
No enforcement of `1..100` or sensible split constraints.

7. Output URL is hardcoded to localhost frontend and may mislead QA in non-local environments.  
`backend/app/test_scripts/demo/test_qa_demo_baseline.py:1540`, `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1564`

**What to change**

1. Add strict response assertions after each API call:
- `PUT composition`: assert returned composition contains expected panels/blocks and story binding.
- `POST session`: assert `demo_session_id`, `composition`, `composition_source`, `room`, `runtime` are present and typed.
- If story is bound, assert runtime-relevant fields reflect policy.

2. Update session-id handling:
- use `demo_session_id` primarily, fallback to `session_id` only for backward compatibility.

3. Remove hardcoded default story dependency:
- default `--story-id` to `None`.
- add `--require-story` flag (fail fast if not supplied).
- optionally add `--story-id-from-env` (`QA_STORY_ID`).

4. Extend script modes beyond baseline:
- add `--composition baseline|b|c`.
- implement payload builders for B and C from `qa-demo-composition-reference.md`.

5. Add semantic checks tied to A/B/C:
- baseline: constant top block + story/chat.
- B: runtime-coupled block presence/config.
- C: visibility config values present and accepted by API.

6. Add local arg validation and clearer fail-fast messages:
- enforce size range and sum sanity before API calls.

7. Parameterize hosts:
- `--api-base-url` (default current value),
- `--frontend-base-url` for printed links/results.

If you want, I can patch `test_qa_demo_baseline.py` now with a minimal hardening pass (items 1–3) first, then add composition modes B/C as a second pass.

...

Implemented both passes in `backend/app/test_scripts/demo/test_qa_demo_baseline.py`.

**What I patched**

1. Hardening + contract validation
- Added response contract checks for persisted composition and resolve-session payload (`_validate_persisted_composition`, `_validate_session_payload`) at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:972`.
- Added strict required-field assertions (panels/blocks, room/runtime/composition/composition_source) and mode-specific expectations.
- Fixed session ID handling to current contract (`demo_session_id`) with fallback to `session_id` via `resolve_session_identifier` at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:223`.
- Added panel size validation (`validate_size_range`) at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:233`.

2. Story/runtime safety
- Removed brittle hardcoded story default; now default comes from optional env `QA_STORY_ID` at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:168`.
- Added `--require-story` fail-fast behavior at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1559`.
- Added explicit guard that composition modes `b`/`c` require a story ID at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1648`.

3. Environment flexibility
- Added configurable API/frontend bases:
  - `--api-base-url` (`QA_API_BASE_URL`) at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1592`
  - `--frontend-base-url` (`QA_FRONTEND_BASE_URL`) at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1599`
- Builder now uses these URLs for all API calls and output links.

4. Second pass: composition modes
- Added mode selector `--composition baseline|b|c` at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:1534`.
- Added payload builders:
  - Composition B (`get_runtime_coupled_composition`) at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:650`
  - Composition C (`get_visibility_semantics_composition`) at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:723`
  - shared selector (`get_composition_for_mode`) at `backend/app/test_scripts/demo/test_qa_demo_baseline.py:781`
- `set_composition()` now uses selected mode and validates persisted composition.

5. Output updates
- Success summary now reports composition mode and uses configured frontend URL.
- Session summary uses normalized session id resolver.

**Validation run**
- Syntax check passed: `python3 -m py_compile backend/app/test_scripts/demo/test_qa_demo_baseline.py`

If you want, next I can add a small `--validate-only` mode that runs contract checks against an existing slug without creating/updating resources.


...

