┌─────────────────────────────────────────────────────┐
│  Layer 0: base-noble                                 │
│  Raw ubuntu:noble + system essentials only           │
│  (ca-certs, curl, git, openssh, sudo, locales)       │
└────────────────────┬────────────────────────────────┘
                     │ lxc-snapshot
┌────────────────────▼────────────────────────────────┐
│  Layer 1: base-dev                                   │
│  + build tools, python, node, common runtimes        │
│  + your platform agent/tooling                       │
│  + user skeleton, dotfiles scaffold                  │
└──────┬─────────────┬────────────────┬───────────────┘
       │             │                │
  lxc-snapshot  lxc-snapshot    lxc-snapshot
       │             │                │
┌──────▼───┐  ┌──────▼───┐  ┌────────▼──────┐
│ python   │  │  node    │  │  other        │
│ flavour  │  │  flavour │  │  flavour      │
└──────────┘  └──────────┘  └───────────────┘
       │
  lxc-copy -s (COW clone — ~2s)
       │
┌──────▼───────────────┐
│  env-abc123          │
│  user workspace      │
│  (ephemeral or       │
│   persistent)        │
└──────────────────────┘

Each layer is a snapshot of the one above. Cloning from a snapshot is copy-on-write so it's nearly instant and only stores the delta.

See kennel/provision/ for the base and dev scripts.

the builtin snapshots are located in server.py - we do need to review list_flavours and clean it up (redundant create_env.)

TODO: add BackgroundTasks for snapshots/rebuild.

Workspace injection will happen on spawn for actual user/session - 
we'll inject it at spawn time via lxc-attach.  this is how we will populate specific instances with repos, libraries, etc. super simple. (see example-spawn-injection.md for rudimentary git example)



POST /snapshots/rebuild?flavour=base — provision Layer 0, snapshot it
POST /snapshots/rebuild?flavour=dev — provision Layer 1 on top, snapshot it
POST /envs {"flavour": "dev", "kind": "ephemeral"} — clone from dev snapshot (~2s)
Backend calls _inject_workspace with user context
WebSocket terminal is live