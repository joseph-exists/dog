  # Platform Branch Strategy

  ## Shadow Repos (shadow/*)

  Shadow repos use **single-branch architecture**:
  - All commits go to `main`
  - No branch switching needed (append-only audit log)
  - Worker always commits to HEAD of default branch
  - Read API always reads from default branch
  - Branch support: **deferred indefinitely** (not needed)

  ## User Repos (dog/*)

  User repos use **server-managed branching**:
  - Default branch: `main`
  - Additional branches: [user-created && platform-created]
  - Branch lifecycle: Dependent on future design.
  - Branch naming: Dependent on future design. As long as we have an association where these can be found & mapped - which does exist in the ShadowVersion* code - we are fine here for now.  Assume that we will at some point allow branch-naming: use best practices and be thoughtful - use existing coolname api route if we default to slug.

  ## Worktrees

  Worktrees are a **deployment-time concern**, not user-facing:
   - no worktree at this time.  


  ---

  Next Phase

  User repo branch support - This is where branching actually matters

  Deferred:

  5. Worktrees 