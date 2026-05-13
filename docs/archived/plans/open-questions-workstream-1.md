# Workstream 1 Open Questions and Decisions

**Last updated:** 2026-02-22  
**Scope:** `docs/plans/active-hardening-implementation.md` Workstream 1

## Purpose
1. Track contract decisions that affect backend model hardening order.
2. Prevent backend/frontend drift by locking behavior before OpenAPI/client regeneration checkpoints.

## Decision Log

### D-001 Visibility semantics sequencing
1. **Decision:** frontend-first sequencing for new hidden visibility modes.
2. **Why:** current frontend behavior treats `hidden` as the only hidden state; backend-only enum expansion risks incorrect rendering.
3. **Implementation order:**
- Document semantics in this file and implementation plan.
- Update frontend renderer/mapping behavior for `hidden_unmounted` and `hidden_mounted`.
- Then expand backend contract and validators.
- Then regenerate OpenAPI/client artifacts.
4. **Status:** accepted.

### D-002 Per-kind options strictness strategy
1. **Decision:** strict options enforcement in v2 contract mode, starting now.
2. **Why:** this migration explicitly allows contract-breaking cleanup and does not require preserving legacy payload compatibility.
3. **Implementation order:**
- Inventory real option keys by kind.
- Add typed options + constrained `extras` for explicit extension points only.
- Reject unknown keys immediately in strict validators.
4. **Status:** accepted.

## Questions and Resolutions

### Q-001 Hidden mode API compatibility with legacy `hidden`
1. Should legacy `hidden` map to:
- `hidden_unmounted` by default, or
- remain a first-class accepted value during transition?
2. **Recommendation:** do not keep `hidden` as an accepted compatibility value in v2 contract mode.
3. **Owner:** backend + frontend.
4. **Due before:** Slice 1.5 backend enum change.
5. **Decision:** accepted. v2 will use explicit visibility values only (`visible`, `hidden_unmounted`, `hidden_mounted`) with no legacy alias.

### Q-002 `hidden_mounted` runtime guarantees
1. What is guaranteed to remain active when node is hidden-mounted?
- local UI state only
- subscriptions/listeners
- agent/runtime side effects
2. **Recommendation:** support runtime-state use cases directly by preserving subscriptions/listeners and intentional side effects while hidden-mounted.
3. **Owner:** frontend.
4. **Due before:** frontend Slice 1.5 implementation.
5. **Decision:** accepted. hidden-mounted semantics must preserve runtime stateful behavior, not only visual state.

### Q-003 Unknown options handling policy per phase
1. During transition, should unknown keys be:
- allowed silently
- allowed with warnings/logging
- rejected for specific kinds only?
2. **Recommendation:** reject unknown options keys in strict mode immediately.
3. **Owner:** backend.
4. **Due before:** Slice 1.6 validators.
5. **Decision:** accepted. strict rejection starts now.


### Q-004 `strange` and `storyPlayerPanel` lifecycle
1. Are these production contract values or temporary compatibility values?
2. **Recommendation:** treat both as compatibility values until renderer ownership and acceptance coverage are documented.
3. **Owner:** product + frontend + backend.
4. **Due before:** Workstream 3 mapping lock.
5. **Decision:** accepted as deferred compatibility kinds for minimal rework.
6. **Execution note:** exclude `storyPlayerPanel` and `strange` from current Workstream 3 renderer implementation checklist; retain contract support and fallback behavior.

## Action Checklist (Completed Slices)
1. Slice 1.5:
- finalized Q-001 and Q-002
- implemented frontend hidden-mode behavior
- implemented backend visibility expansion with explicit v2 values only (no legacy `hidden` alias)
- regenerated OpenAPI/client artifacts
2. Slice 1.6:
- finalized Q-003 and Q-004
- completed options key inventory by kind
- enforced strict unknown-key rejection in validators
- added typed options + constrained extras only where explicitly allow-listed
- regenerated OpenAPI/client artifacts

## Next Work (After Workstream 1)
1. Workstream 3 renderer coverage for active kinds is complete (panel + block mapping with dedicated block components).
2. Keep compatibility fallback behavior for deferred kinds:
- `storyPlayerPanel`
- `strange` (panel and block)
3. Prioritize WS3/WS4 validation work:
- add renderer selection/fallback/visibility tests
- run acceptance validation for demos A/B/C/D
- update `active-demo-integration-snapshot.md` with completed coverage and remaining risks
4. Revisit deferred kinds after renderer ownership and acceptance scope are defined.

## Evidence Required at Review
1. OpenAPI schema diff showing visibility/options contract changes.
2. Generated client diff in:
- `frontend/src/client/schemas.gen.ts`
- `frontend/src/client/types.gen.ts`
- `frontend/src/client/sdk.gen.ts`
3. Validation tests proving:
- discriminators reject invalid branches
- hidden mode explicit-value rules hold (`visible`/`hidden_unmounted`/`hidden_mounted`)
- options policy enforces strict unknown-key rejection.
