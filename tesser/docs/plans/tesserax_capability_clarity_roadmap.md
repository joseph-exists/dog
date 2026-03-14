# Tesserax Capability Clarity Roadmap

## Context

The immediate goal is not to redesign `tesser` in the abstract. The goal is to understand what is already present in this repository, what parts are already functional, what parts are hard to discover or use, and what sequence of work would make the advanced `tesserax` capabilities understandable and usable from the broader `dog` system.

Current working assumptions based on repository review:

- The `builtin` render path is operational and already serving simple SVG output.
- The external example registry is now functioning again after the path fix.
- The advanced capability surface is substantial and already present in the codebase.
- The main problems are discoverability, organization, service metadata, and confidence about how these examples should be treated as product-facing capabilities.
- `examples-other` is a functional requirement, not incidental sample code.

This roadmap is meant to support two parallel outcomes:

1. Documentation that accurately describes the current system.
2. A practical path to make the `tesserax` capability surface easier to discover, reason about, and expose.

## What We Know Now

The current registry now exposes a broad set of example-backed scripts:

- Static examples
- Animation examples
- Runners
- Utility scripts

That means the repository does already contain a meaningful capability catalog. The remaining problem is that the catalog is not yet easy to understand at a human level or consume at a system level.

There are also still signs of structural ambiguity:

- Top-level `examples-other/` is treated in docs and tests as a primary discovery surface.
- Service-owned script sources currently live under `src/tesserax_service/scripts/examples-other/`.
- The manifest and docs describe a taxonomy, but the service contract exposes only a thin script listing.
- Some example families appear ready for productization, while others are clearly tooling, review, or migration support.

## Problem Statement

The problem to solve is:

How do we turn the existing `tesserax` example and script surface into a clear, documented, and intentionally exposed capability layer for `tesser`, without making premature structural decisions before the intended integration model is understood?

## Desired Outcomes

### Outcome 1: Accurate Project Understanding

Anyone reviewing this repository should be able to answer:

- What is core `tesserax` library code?
- What is `tesserax_service` execution infrastructure?
- What is product-facing example capability?
- What is tooling, migration support, or review scaffolding?
- Which scripts are intended to be callable from `dog`?

### Outcome 2: Capability Discoverability

A developer integrating from `dog` should be able to answer:

- What scripts are available?
- Which are static vs animation vs utility?
- What inputs do they take?
- What formats do they return?
- Which ones are suitable for synchronous SVG use?
- Which ones require export dependencies or worker-backed execution?

### Outcome 3: Safer Documentation Updates

Documentation work should describe reality, not aspirations. Before broad documentation changes, the project needs a stable interpretation of:

- source of truth
- capability taxonomy
- intended service contract
- operator-facing run paths

## API and Interface Questions To Resolve

These are design questions, not yet implementation directives.

### Service Discovery Surface

The current script listing is enough to enumerate IDs, but not enough to describe them meaningfully.

Questions:

- Should `/v1/scripts` become the canonical capability catalog?
- Should the catalog include taxonomy fields such as `domain`, `tier`, and `kind`?
- Should it expose supported formats and runtime profile hints?
- Should it expose parameter metadata directly, or only references to docs/manifests?

### Product-Facing Script Definition

Not every script in the repository should necessarily be treated the same.

Questions:

- Which examples are intended as end-user or frontend-facing capabilities?
- Which scripts are internal tooling only?
- Are runner scripts ever part of the product surface, or only operator workflows?
- Is `dataset_storyboard` intended to be promoted from utility to renderable capability?

### Artifact Delivery Contract

SVG is straightforward because it can be inlined. Other outputs need a clearer contract.

Questions:

- How should GIF/MP4/PNG/PDF outputs be retrieved by `dog`?
- Should the service return filesystem paths only, or stable fetchable artifact references?
- Is there an existing artifact-serving pattern elsewhere in `dog` that `tesser` should follow?

## Implementation Plan

### Phase 1: Clarify the Current Capability Surface

Purpose:
Produce a factual inventory of what exists and what role each script plays.

Work:

- Review all registered scripts and classify them by intent:
  - product-facing render
  - exploratory render
  - runner
  - utility
  - migration or review support
- Compare manifest taxonomy with what the service currently exposes.
- Identify high-value scripts that should be considered first-class capabilities.
- Identify ambiguous scripts that need product decisions before exposure.

Files likely involved:

- `src/tesserax_service/scripts/external_examples.py`
- `src/tesserax_service/scripts/examples-other/examples_manifest.yaml`
- `examples-other/reference/index.md`
- `docs/tesserax_guide.md`
- `docs/advanced_tesserax_summary.md`

Deliverable:

- A written capability inventory and shortlist of first-class candidate scripts.

### Phase 2: Clarify Documentation Source of Truth

Purpose:
Make the repository understandable without yet committing to a major restructure.

Work:

- Document the distinction between:
  - core library
  - service infrastructure
  - example capability catalog
  - tooling and review scripts
- Reconcile the mismatch between documented run paths and actual source locations.
- Decide what top-level `examples-other/` is meant to be:
  - executable source surface
  - documentation surface
  - compatibility surface
  - or some combination with explicit rules

Files likely involved:

- `README.md`
- `examples-other/README.md`
- `examples-other/reference/index.md`
- a new architecture or glossary document if needed

Deliverable:

- Documentation update plan with explicit definitions and no ambiguous directory narratives.

### Phase 3: Define the Capability Catalog Contract

Purpose:
Decide how `dog` should discover and reason about the `tesserax` capability surface.

Work:

- Define the metadata needed for each script in the service listing.
- Decide whether manifest fields should flow through to API consumers.
- Decide whether parameter schema should be surfaced as service metadata.
- Separate renderable capabilities from tooling-only entries in the public listing.

Files likely involved:

- `src/tesserax_service/api.py`
- `src/tesserax_service/registry.py`
- `src/tesserax_service/contracts.py`
- `src/tesserax_service/redis_bridge.py`
- `src/tesserax_service/scripts/examples-other/examples_manifest.yaml`

Deliverable:

- A documented target shape for script discovery and capability metadata.

### Phase 4: Define the Integration Path for Non-SVG Outputs

Purpose:
Make animation and export-heavy examples realistically usable from `dog`.

Work:

- Review how artifact paths are produced today.
- Determine how the consuming frontend or backend should retrieve generated media.
- Align with any existing artifact-serving or job-result conventions in `dog`.
- Identify whether the current manifest and worker result payloads are sufficient.

Files likely involved:

- `src/tesserax_service/runtime.py`
- `src/tesserax_service/redis_messages.py`
- `src/tesserax_service/worker.py`
- `src/tesserax_service/redis_bridge.py`

Deliverable:

- A concrete integration contract for SVG and non-SVG outputs.

### Phase 5: Only Then Revisit Structural Changes

Purpose:
Avoid making file-layout changes before the intended operating model is agreed.

Work:

- Review whether current directory boundaries are actually blocking clarity after documentation and metadata work.
- If still needed, evaluate small structural changes with a clear migration path.
- Preserve compatibility where practical.

Deliverable:

- A scoped structural proposal only if the earlier phases show it is necessary.

## Suggested Sequence of Work

1. Produce a capability inventory from the registered script set.
2. Mark likely first-class capabilities versus tooling/support scripts.
3. Update documentation to describe the current reality in precise terms.
4. Define the service metadata shape needed by `dog`.
5. Define artifact retrieval expectations for non-SVG outputs.
6. Reassess whether repository restructuring is still necessary.

## Risks and Unknowns

- The intended consumer behavior inside `dog` is not yet described in this repository.
- Some examples may be technically renderable but not product-appropriate.
- A documentation pass done too early could harden the wrong mental model.
- A directory restructure done too early could create churn without improving actual integration.

## Review Questions

Before implementation work begins, these are the most useful questions to settle:

1. Which `examples-other` scripts do you already view as product-facing or strategically important?
2. Is the next milestone primarily:
   documentation clarity,
   service capability exposure,
   or frontend integration?
3. Should the service catalog aim to describe all scripts, or only an approved subset?
4. Is there already a preferred artifact delivery pattern elsewhere in `dog` that `tesser` should align to?
