# Workspaces Engineering Reference Guide

## Purpose

This document is the current-state engineering reference for the Workspaces
milestone.

It is intended to be the most concise source of truth for:

- what is implemented now
- how the major cross-stack seams fit together
- which MVP requirements are satisfied
- which follow-up slices remain intentionally open

Use this guide as the primary orientation artifact. Use the linked roadmap and
decision documents for deeper rationale and implementation history.

## Current System Shape

The Workspaces system now provides a cross-stack operational flow with four
connected parts:

1. workspace lifecycle and readiness
2. repo/bootstrap and runtime/service startup
3. project-aware sharing and access semantics
4. room/workspace and workspace/platform trust paths

In practical terms, the platform now supports:

- provisioning a workspace with typed bootstrap intent
- materializing a repo-backed runtime slice for the currently supported source
  and startup profiles
- discovering workspace services and agent runtimes
- associating a workspace with a project through the canonical
  `ProjectResource(resource_type="workspace")` attachment model
- exposing project-aware visibility and allowed actions for shared workspaces
- issuing room/workspace connection descriptors and holding a room-side current
  connection as a narrow convenience projection
- issuing workspace-to-platform service access through canonical runtime config
  and runtime-facing environment projection

## Functional Slice Status

### 1. Workspace Domain Contract

Status: implemented for the current MVP slice

Current shape:

- canonical lifecycle states are explicit
- failure semantics are explicit
- allowed actions are backend-owned
- terminal and service readiness are projected clearly
- project visibility and project summary are projected into workspace detail and
  list responses

Primary references:

- [workspace-domain-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-domain-contract.md)
- [domain-contract-implementation-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/domain-contract-implementation-roadmap.md)

### 2. Repo And Bootstrap Contract

Status: implemented for the current MVP slice, with selective completeness
follow-up still open

Current shape:

- typed bootstrap intent and progress are live
- backend-generated bootstrap plans are live
- backend public workspace create now supports:
  - top-level `runtime_preset`
  - nested `bootstrap.bootstrap_profile`
  - nested `bootstrap.runtime_files`
- the normalized backend to kennel seam now carries:
  - preset selection
  - explicit bootstrap profile overrides
  - projected and explicit env vars
  - projected and explicit runtime files
- first service and agent-runtime startup profiles are supported
- service readiness and discovery are live
- workspace detail and list surfaces expose bootstrap and readiness state

Current supported operational profiles:

- install profiles: `npm`, `pnpm`, `yarn`, `uv`, `pip`
- service startup profiles: `vite`, `nextjs`, `fastapi`
- agent runtime profiles: `codex`, `claude_code`, `hermes`

Current frontend integration note:

- the frontend create form and submission helpers now expose `runtime_preset`, `bootstrap_profile`, and `runtime_files`
- the initial frontend path is preset-first with advanced operator controls in a separate collapsed section
- the frontend now includes `hermes-agent` as a runtime preset option so the next runtime slice can land without reshaping the form again

Current kennel validation note:

- [validate_provisioning.py](/home/josep/dog/kennel/scripts/validate_provisioning.py) is currently passing for the kennel-owned Codex preset path
- that validated path uses `runtime_preset: "codex"` for both create and inject and expects a healthy `codex` websocket service on port `4500`

Primary references:

- [repo-bootstrap-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-contract.md)
- [frontend-create-form-shape.md](/home/josep/dog/frontend/src/components/Workspaces/docs/frontend-create-form-shape.md)
- [repo-bootstrap-implementation-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-implementation-roadmap.md)
- [service-readiness-discovery-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/service-readiness-discovery-roadmap.md)
- [agent-service-runtime-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/agent-service-runtime-roadmap.md)

### 3. Project Sharing And Management Semantics

Status: implemented for the current MVP slice

Current shape:

- workspace/project relationship is canonical through `ProjectResource`
- the near-term zero-or-one project rule is enforced for workspaces
- workspace visibility is project-aware
- workspace allowed actions are actor-aware
- frontend surfaces distinguish `view`, `use`, and `manage`

Primary references:

- [project-workspace-relationship.md](/home/josep/dog/frontend/src/components/Workspaces/docs/project-workspace-relationship.md)
- [project-management-access-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/project-management-access-roadmap.md)

### 4. Room And Workspace Connectivity

Status: implemented for the current MVP slice

Current shape:

- room-aware workspace candidate selection is live
- backend-issued descriptors are the canonical room/workspace trust primitive
- room-side current connection is backend-backed and intentionally narrow
- descriptor freshness and historical/unavailable connection state are visible
  in room UX
- room runtime consumption is descriptor-backed rather than inferred from
  generic workspace URLs

Primary references:

- [room-workspace-connectivity.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connectivity.md)
- [room-workspace-connection-service-reference.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connection-service-reference.md)
- [room-workspace-execution-layer-mvp-plan.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-execution-layer-mvp-plan.md)
- [room-workspace-execution-layer-sequenced-implementation.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-execution-layer-sequenced-implementation.md)
- [room-workspace-descriptor-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-descriptor-roadmap.md)
- [room-workspace-current-connection-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-current-connection-roadmap.md)
- [concurrent-many-to-many.md](/home/josep/dog/frontend/src/components/Workspaces/docs/concurrent-many-to-many.md)

### 5. Workspace To Platform Service Access

Status: implemented for the current MVP slice

Current shape:

- explicit platform-service grants are backend-issued
- canonical runtime config is available for `workspace_runtime` and
  `agent_runtime`
- runtime-facing env projection is live
- projected runtime files are materialized in the workspace
- current agent runtime profiles actively consume projected platform-service
  access
- workspace detail exposes grant inspection, runtime-config inspection,
  projection refresh, projection freshness, runtime file paths, and inject notes

Primary references:

- [workspace-platform-service-access-decision.md](/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-platform-service-access-decision.md)

## MVP Definition Of Done Check

### Provision an instance with a repository

Status: satisfied for the current supported repo/bootstrap slice

### Install packages from that repository

Status: satisfied for the current supported install profiles

### Launch services on the instance, especially coding agents

Status: satisfied for the current supported service and agent-runtime profiles

### Associate that instance with a project

Status: satisfied

### Launch a room with agents

Status: already part of the platform and integrated with the workspace slice

### Allow room agents to connect to workspace services over websocket connections

Status: satisfied for the current descriptor-backed room/workspace trust slice

### Allow agents running on the provisioned instance to call platform services after access is granted and authenticated

Status: satisfied for the current canonical runtime-config and environment
projection slice

## Important Boundaries

These boundaries should remain explicit in future work:

- backend-issued descriptors are the canonical room/workspace trust primitive
- room-side current connection is a convenience default, not the long-term
  relationship model
- backend-issued runtime config is the canonical workspace/platform service
  access model
- environment projection is a convenience adapter derived from canonical runtime
  config
- create and inject precedence should be documented at the interface seam, not inferred from whichever layer happened to populate a field first
- bootstrap profiles are operational profiles, not the final domain ontology
- metadata-backed details should keep graduating into typed contract space when
  they become central to orchestration or policy

## Current Follow-Up Work

The MVP-critical vertical slices are now in place. The remaining work is
selective follow-through rather than foundational architecture.

The most likely follow-up slices are:

- repo/bootstrap completeness where it blocks real usage
  - especially `shadow_repo` and any remaining `user_repo` bridge pressure
- operator-facing management and classification polish
  - tags, grouping, and capability markers
- transport and policy hardening where a concrete surface benefits from it
  - expiry, refresh, proxy-aware transport, or stronger audit hooks

## Linked Artifacts

- [planning.md](/home/josep/dog/frontend/src/components/Workspaces/docs/planning.md)
- [mvp-closing-sequence.md](/home/josep/dog/frontend/src/components/Workspaces/docs/mvp-closing-sequence.md)
- [workspace-domain-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-domain-contract.md)
- [repo-bootstrap-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-contract.md)
- [project-workspace-relationship.md](/home/josep/dog/frontend/src/components/Workspaces/docs/project-workspace-relationship.md)
- [room-workspace-connectivity.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connectivity.md)
- [workspace-platform-service-access-decision.md](/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-platform-service-access-decision.md)
