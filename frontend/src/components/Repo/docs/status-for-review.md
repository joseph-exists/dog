I finished both UI/keyboard improvements and documented the preview-config reuse pattern.

In [RepoPanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Repo/Dialogs/RepoPanelLayoutDialog.tsx), the lightweight dialog now exposes visible shortcut hints on the relevant controls:
- `Ctrl/Cmd+Shift+A` for `Add Panel`
- `Ctrl/Cmd+Alt+L` for `Advanced Editor`
- row-level hints for prominence toggling
- inline shortcut guidance for move/remove/insert behavior

It also now supports keyboard-driven panel insertion and removal:
- `Ctrl/Cmd+Shift+A` toggles the add-panel section
- `ArrowUp` / `ArrowDown` move through addable panel options when that section is open
- `Enter` confirms the focused add-panel option
- `Alt+A` inserts the currently selected add-panel option directly
- `Delete` / `Backspace` removes the focused panel row
- existing `Alt+Arrow` movement shortcuts remain in place

I also documented the repo preview-config pattern in [RepoViewer-Alpha.md](/home/josep/dog/frontend/src/components/Repo/docs/RepoViewer-Alpha.md), pointing engineers to [previewConfig.ts](/home/josep/dog/frontend/src/components/Repo/panels/previewConfig.ts) and spelling out that future block-layout previews should use repo-owned label/color mappings passed into the shared preview primitives rather than hardcoding repo semantics into Page-level components.

Verification: `npm run build` passed in `/home/josep/dog/frontend`.

Natural next steps:
1. Add a small shortcut legend or help popover in the repo detail header so layout shortcuts are discoverable even before the dialog is opened.
2. When repo blocks land, create a companion repo block preview config beside [previewConfig.ts](/home/josep/dog/frontend/src/components/Repo/panels/previewConfig.ts) instead of extending the panel-only mapping ad hoc.