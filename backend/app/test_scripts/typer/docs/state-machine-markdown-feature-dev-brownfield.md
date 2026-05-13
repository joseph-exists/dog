
***

# Feature PRD – LLM-Assisted Change in Brownfield Monolith

> **Feature Request ID:**  
> **Title:**  
> **Owner:**  
> **Date:**  

***

## 1. Context & Goals

### 1.1 Business context

- **Business goal:**  
- **Motivation / problem statement:**  
- **Target users / personas:**  
- **Success metrics (KPIs):**  

### 1.2 Constraints & guardrails

- **Risk tolerance (low/med/high):**  
- **Time constraints:**  
- **Tech constraints (e.g., no schema change, no downtime):**  

***

## 2. N0 – Intake

**Objective:** Capture the requested feature and basic constraints.

#### 2.1 Feature Request

- **Title:**  
- **Summary (1–3 paragraphs):**  
- **Primary user journeys impacted:**  
- **Business goal (restate succinctly):**  
- **Urgency (low/med/high) & why:**  
- **Known constraints:**  
  - 
- **Non-goals (explicitly out of scope):**  
  - 

#### 2.2 Repository / Environment Context

- **Monolith / service name:**  
- **Code repo URL / identifier:**  
- **Environments available (dev/stage/prod):**  
- **Anything special about deployment / infra here:**  

***

## 3. N0a – Clarify Request

**Objective:** Resolve ambiguity, record open questions and assumptions.

#### 3.1 Open questions

- Q1:  
- Q2:  

#### 3.2 Answers & decisions

- A1:  
- A2:  

#### 3.3 Assumptions

> Only list assumptions you’re willing to live with.

- Assumption 1:  
- Assumption 2:  

***

## 4. N1 – System Recon

**Objective:** Map the affected slice of the monolith.

#### 4.1 Candidate modules & entrypoints

- **Modules / packages likely involved:**  
  - 
- **Entry points (routes, jobs, CLIs):**  
  - 

#### 4.2 Call paths & data models

- **Key call paths (high level):**  
  - 
- **Primary data models / tables:**  
  - 

#### 4.3 Integrations & ownership

- **External integrations (APIs, queues, files):**  
  - 
- **Ownership signals (teams, codeowners, SMEs):**  
  - 

#### 4.4 Existing docs

- **Relevant docs / ADRs / diagrams:**  
  - 

#### 4.5 Unknowns & confidence

- **Unknowns / questions about the system:**  
  - 
- **Dependency map confidence (0–1):**  

***

## 5. N1a – Context Recovery (if needed)

**Objective:** Close critical gaps in understanding.

#### 5.1 Documentation gaps

- Missing docs / diagrams:  

#### 5.2 Tribal knowledge & production signals

- People to talk to / questions to ask:  
- Logs / metrics / traces to gather:  

#### 5.3 Notes & updated confidence

- Key notes from code reading / interviews:  
- Updated dependency map confidence (0–1):  

***

## 6. N2 – Baseline Behavior

**Objective:** Describe what the system does today.

#### 6.1 Current behavior

- **Narrative description of current behavior:**  

#### 6.2 Observed flows

- **User / system flow summary:**  
- **(Optional) Link to sequence / activity diagram:**  

#### 6.3 Invariants & non-functional constraints

- **Behavioral invariants (must remain true):**  
  - 
- **Non-functional constraints (latency, throughput, SLOs, compliance):**  
  - 

#### 6.4 Existing tests & gaps

- **Existing tests relevant to this area:**  
  -  
- **Known baseline failures / existing bugs:**  
  -  
- **Missing test areas:**  
  -  
- **Characterization coverage (0–1, justification):**  

***

## 7. N2a – Safety-Net Build (if needed)

**Objective:** Build tests/observability to support safe change.

#### 7.1 New characterization tests

- New test cases (name + brief scenario):  
  -  

#### 7.2 E2E paths, fixtures, golden outputs

- E2E paths to cover:  
- Fixtures / test data:  
- Golden outputs (snapshot of behavior):  

#### 7.3 Logging & coverage

- New logging / tracing added:  
- Coverage on touched area (0–1, justification):  

***

## 8. N3 – Change Spec

**Objective:** Specify the change as a delta to current behavior.

#### 8.1 Current vs target behavior

- **Current behavior (short summary):**  
- **Target behavior (short summary):**  

#### 8.2 Scope boundary

- **In scope:**  
  -  
- **Out of scope (exclude explicitly):**  
  -  

#### 8.3 Spec invariants

- **Invariants that must still hold after change:**  
  -  

#### 8.4 Acceptance criteria

> Each should be testable and ideally references tests or flows.

- AC1:  
- AC2:  

#### 8.5 Rollback plan (high level)

- **Rollback strategy:**  
- **Dependencies for rollback (flags, scripts, backups):**  

***

## 9. N4 – Feasibility & Risk Gate

**Objective:** Decide if the change is feasible and safe.

#### 9.1 Blast radius & coupling

- **Blast radius (modules, tables, integrations touched):**  
- **Coupling hotspots / scary areas:**  

#### 9.2 Risk assessment

- **Risk level (low/med/high):**  
- **Security impact:**  
- **Data integrity risk:**  
- **Migration needed? (Y/N and why):**  

#### 9.3 Guardrails

- **Feature flag strategy (per env):**  
- **Rollback thresholds (error rate, latency, KPI deltas):**  

#### 9.4 Decision

- Proceed as-is / require seam / abort:  

***

## 10. N4a – Seam Creation Plan (if needed)

**Objective:** Plan façade/adapter/boundary before main feature.

#### 10.1 Seam concept

- **Seam type (facade/adapter/ACL/flag/etc.):**  
- **Adapter contract (interface, responsibilities):**  

#### 10.2 Integration points & intermediate state

- **Where seam intercepts calls:**  
- **Intermediate state plan (old and new path coexistence):**  

#### 10.3 Deployability steps

- Step 1:  
- Step 2:  

***

## 11. N5 – Task Decomposition

**Objective:** Turn spec into bounded tasks.

> Use a table for clarity.

| Task ID | Title | Description | Related Modules | DoD (summary) | Review Checkpoint? |
|--------|-------|-------------|-----------------|---------------|--------------------|
| T-1 |  |  |  |  |  |
| T-2 |  |  |  |  |  |

- **Dependencies between tasks:**  

***

## 12. N6 – Prompt & Context Assembly

**Objective:** Prepare task-specific LLM context.

> Repeat per task as needed.

### For Task: `T-__`

#### 12.1 Selected context files

- Code / config / docs included:  

#### 12.2 Architecture notes & conventions

- Key architecture notes for this task:  
- Coding conventions:  
- Forbidden changes (modules/contracts not to touch):  

#### 12.3 Spec excerpt & success checks

- Spec excerpt relevant to this task:  
- Success checks (how we know this task is done):  

#### 12.4 Task prompt

- Prompt text to use with LLM:  

***

## 13. N7 – Implementation

**Objective:** Capture the patch and rationale.

> Repeat per patch / iteration on a task.

### Patch for Task: `T-__`

- **Patch ID:**  
- **Files changed:**  
- **High-level summary of change:**  
- **Rationale / reasoning:**  
- **Assumptions made while coding:**  
- **TODO flags / future cleanups:**  
- **Unexpected findings (e.g., hidden coupling, weird behavior):**  

***

## 14. N8 – Local Validation

**Objective:** Validate the patch technically.

### For Patch: `Patch ID`

- **Lint results:**  
- **Build results:**  
- **Test results (which tests, outcomes):**  
- **Coverage notes (any significant changes):**  
- **Contract checks (APIs, schema):**  
- **Performance smoke results:**  
- **Validation failures (if any):**  
- **Overall status (pass/fail):**  

***

## 15. N9 – Review

**Objective:** Human review of correctness, architecture, and maintainability.

### For Patch: `Patch ID`

- **Reviewers:**  
- **Summary:**  
- **Architecture conformance (notes):**  
- **Security findings:**  
- **Scope drift observed? (Y/N with details):**  
- **Maintainability notes (future readability, patterns):**  
- **Decision (approved / changes requested):**  
- **Key comments (bulleted, optionally link to code):**  
  - 

***

## 16. N10 – Integration & Flagging

**Objective:** Prepare merge and rollout.

- **Merge readiness (Y/N and why):**  
- **Feature flag configuration (flags, default values per env):**  
- **Migration steps (if any):**  
- **Release notes (dev-facing):**  
- **Release notes (user-facing, if relevant):**  
- **Operational checks / dashboards to watch:**  
- **Deployable decision (Y/N):**  

***

## 17. N11 – Runtime Verification

**Objective:** Observe behavior in real environments.

- **Environment (staging / canary / prod):**  
- **Staging results (if applicable):**  
- **Canary metrics (summary):**  
- **Error rate vs baseline:**  
- **Latency delta vs baseline:**  
- **Business KPI movement:**  
- **User feedback / support signals:**  
- **Did any rollback thresholds trigger? (Y/N, details):**  
- **Overall health (healthy / unhealthy):**  

***

## 18. N10a – Rollback / Contain (if needed)

**Objective:** Record incident and rollback decisions.

- **Incident ID:**  
- **Summary of issue:**  
- **Impact assessment:**  
- **Timeline of events:**  
- **Rollback / containment actions taken:**  
- **Root cause hypothesis:**  
- **Follow-up actions (tests, docs, refactors, etc.):**  

***

## 19. N12 – Learn & Update Memory

**Objective:** Persist knowledge for future work.

- **Docs updated (links):**  
- **Tests added/updated (IDs + what they cover):**  
- **Agent notes for future LLM work (what to remember next time):**  
- **Known traps / recurring patterns identified:**  
- **Changes to long-lived specs / ADRs:**  
- **Governance snapshot (key decisions, assumptions worth memorializing):**  
- **Final verification timestamp:**  

***

