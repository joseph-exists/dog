The current frontend stack exposes two different repository models.

The  user_repo workspace path is documented in [user-repo-frontend-reference.md](/home/josep/dog/backend/app/services/service-docs/user-repo-frontend-reference.md) and [user-repo-viewer-v1-execution-plan.md](/home/josep/dog/backend/app/services/service-docs/user-repo-viewer-v1-execution-plan.md)

: import a repo, list repos, get repo detail, read tree, read file, read README, and consume capability flags. On the frontend, that powers the repo workspace route plus `repoExplorer` and `fileViewer` panels.

So, today, a user can effectively:
- import an external repository into a platform-managed `user_repo`
- view repo metadata and import status
- browse the file tree
- open files and README content
- configure multiple explorer/viewer panels with different local panel configs

Today, they cannot, based on the currently exposed contracts:

- create a second user repo derived from an existing user repo as a first-class operation

- scrub history, refs, or branches as a supported platform action

- manage private repo sharing/collaborator ACLs through the repo frontend contract

- perform platform-mediated branch workflows on `user_repo`

- treat demos/stories/pages as fully repo-native editors; `GitViewBlock` is still shadow-repo oriented in Demo - but will need extensibility if/when migrated to other contexts.  We need functionality to express both.

the backend will need to expose:

- A derived-repo creation contract
  Example: “create new user repo from existing user repo”
  
  Note: this explicitly excludes lineage metadata.  we do not want this operation to 'carry over' any refs, heads, branches, etc from the existing repo being cloned from.

  Note: this already exists with minimal mutation. If we can clone an external repo by giving the UI a link, then cloning an internal repo shouldn't be a stretch. 

- A long-running repo operation model exists - we can leverage/reuse our import functionality here.

  For derive/scrub/minimize jobs, with job status and failure payloads similar to import.




- A scrub/minimize contract


- Repo privacy and sharing contracts
  Private-by-default visibility, explicit user/user-team grants, read/write/admin roles.

- Collaboration contracts for platform-native git behavior



- History/search/activity contracts
  These are called out as later-stage needs in [user-repo-viewer-backend-handoff-checklist.md](/home/josep/dog/backend/app/services/service-docs/user-repo-viewer-backend-handoff-checklist.md).


- Clear repo identity semantics
  Imported source, derived-from lineage, current default branch, and whether the repo is detached from upstream permanently.

The most critical immediate gap is not frontend rendering. It is repo lifecycle semantics. Before more synthesis with `GitViewBlock` or repo-native blocks, the backend needs to define what a “secondary scrubbed repo” actually is in platform terms. Right now the platform has `imported repo` semantics; it does not yet have `derived private working repo` semantics.

My recommendation for sequencing is:

1. Define backend contracts for `derive`, `scrub/minimize`, and `share/access`.

TODO: this is explained in detail above.  Create a concise reference card that will enable you to remember this directly, and put it as a top level AGENTS.md in the Repo directory for review. 

2. Add lineage and capability fields to `user_repo` payloads so the frontend can distinguish imported repos from derived repos.
3. Decide whether collaboration is branch-based inside one shared repo or clone-based across multiple related repos.


If you want, the next useful step is for me to turn this into a concrete backend prerequisite matrix: `current contract`, `needed contract`, `frontend consumer`, and `priority`.