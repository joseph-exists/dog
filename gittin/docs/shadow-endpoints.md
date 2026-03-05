 ---
  Shadow Repo Read API - Complete ✅

  ★ Insight ─────────────────────────────────────
  The v1 Shadow Repo Read API is now fully implemented and tested:
  - All endpoints working with proper authorization
  - Path traversal attempts safely rejected via git's own protections
  - Superuser bypass verified
  - Frontend component wired and functional
  ─────────────────────────────────────────────────

  Test Coverage Summary
  ┌───────────────────────────────────────────────┬─────────────────────────────┬─────────┐
  │                     Test                      │           Purpose           │ Status  │
  ├───────────────────────────────────────────────┼─────────────────────────────┼─────────┤
  │ test_shadow_repo_view_returns_repo_projection │ Owner can view their repo   │ ✅ Pass │
  ├───────────────────────────────────────────────┼─────────────────────────────┼─────────┤
  │ test_shadow_repo_file_returns_file_content    │ Owner can read files        │ ✅ Pass │
  ├───────────────────────────────────────────────┼─────────────────────────────┼─────────┤
  │ test_shadow_repo_access_denied_is_opaque_404  │ Non-owner gets 404          │ ✅ Pass │
  ├───────────────────────────────────────────────┼─────────────────────────────┼─────────┤
  │ test_superuser_can_access_any_shadow_repo     │ Superuser can view any repo │ ✅ Pass │
  ├───────────────────────────────────────────────┼─────────────────────────────┼─────────┤
  │ test_shadow_repo_file_rejects_path_traversal  │ Path traversal blocked      │ ✅ Pass │
  ├───────────────────────────────────────────────┼─────────────────────────────┼─────────┤
  │ test_shadow_repo_nonexistent_returns_404      │ Missing repo returns 404    │ ✅ Pass │
  └───────────────────────────────────────────────┴─────────────────────────────┴─────────┘
  Architecture Recap

  ┌─────────────────┐     ┌───────────────────────┐     ┌─────────────────┐
  │   GitViewBlock  │────▶│  ShadowReposService   │────▶│  shadow_repos   │
  │   (React)       │     │  (Generated SDK)      │     │  routes.py      │
  └─────────────────┘     └───────────────────────┘     └────────┬────────┘
                                                                 │
                                                                 ▼
                                                        ┌────────────────────┐
                                                        │ shadow_repo_view   │
                                                        │ _service.py        │
                                                        └────────┬───────────┘
                                                                 │
                          ┌──────────────────────────────────────┼─────────────┐
                          │                                      │             │
                          ▼                                      ▼             ▼
                   ┌─────────────┐                       ┌─────────────┐  ┌─────────┐
                   │ ShadowRepo  │                       │ Git CLI     │  │ Files   │
                   │ (DB)        │                       │ (subprocess)│  │ on disk │
                   └─────────────┘                       └─────────────┘  └─────────┘

  What's Now Available

  Backend Endpoints:
  - GET /api/v1/shadow-repos/{entity_type}/{entity_id}/view - repo summary, commits, tree
  - GET /api/v1/shadow-repos/{entity_type}/{entity_id}/file?path=... - file content
