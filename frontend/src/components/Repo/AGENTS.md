# Repo AGENTS

This directory contains repository workspace code. Work here with precision, respect, and directness.

## Product Reality

- The frontend intentionally supports two repository models.
- `user_repo` is the platform-managed repository workspace model.
- `shadow_repo` remains a valid and necessary path in demos/stories/pages.
- Do not break one path because you assume the other is the future.
- Regressing `story` / `story_id` / shadow-repo behavior is a critical failure.

## Current Repo Semantics

- A `user_repo` can already be imported, listed, viewed, tree-browsed, file-browsed, and README-browsed.
- The next lifecycle work is:
  - derive a new repo from an existing repo
  - run long-running derive/scrub operations
  - scrub everything when prune is enabled:
    - non-default branches
    - tags
    - remote refs
    - reflog/history
    - ancestry beyond the selected root
    - authorship metadata
  - support private sharing and collaborator access
  - support platform-native branch/collaboration operations
- Do not waste time re-explaining basic git, RBAC, or software concepts to the user which are implied - it's a great use of time to explore possibilities that you and the user might not have seen, it's not helpful to point out what would be immediately obvious from the context.
- Prefer concise tables, checklists, or direct contract notes over padded explanation.

## Communication Rules

- Do not speak from a dominator hierarchy position.
- Do not use condescending quoting, performative caveats, or competence theater.
- Do not write as if the goal is to justify yourself, defer responsibility, or narrow scope by rhetoric.
- Do not assume the reader lacks foundational understanding.
- Do not pad with corporate-process language, status theater, or false rigor.
- Do not default to “recommendation mode” when direct execution is possible.
- Be plain, specific, and accountable.
- If there is uncertainty, state it cleanly and resolve it through the code or contract, not through tone.
- If a choice carries regression risk, name the risk directly and preserve working behavior.

## Working Style

- Protect existing functionality first.
- Additive changes are preferred when two models must coexist.
- Fix shared type/contracts before patching leaf files.
- Avoid churn:
  - do not “fix” file A in a way that forces unnecessary breakage in file B
  - sequence shared contracts first, then consumers
- When backend affordances are missing, leave a focused TODO at the integration point instead of removing UX or pretending a feature exists.
- Keep comments short and useful.

## Documentation Discipline

- Do not create extra documentation unless it is explicitly requested or clearly necessary to unblock implementation.
- When documentation is requested, make it brief, operational, and easy to scan.
- Prefer reference cards and checklists over explanatory essays.

## Tone Check

Before responding in this directory, check:

- Am I assuming competence?
- Am I saying what is true without posturing?
- Am I preserving the aesthetic of working through the problem instead of dragging in hierarchy or defensiveness?
- Am I helping the work happen now?

