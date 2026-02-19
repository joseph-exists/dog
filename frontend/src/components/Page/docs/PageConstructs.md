Page
├── BlockWrapper.tsx
                # BlockWrapper - Wraps blocks to add click-to-select and toolbar in edit mode
                # UI for modifying which blocks appear on the page
├── Dialogs
│   ├── CreatePageDialog.tsx
            # does a lookup by entitytype and returns available page templates -
            # uses Page/registry getTemplatesForEntityType and pageTemplates
            # UI 'intended' for Users when they visit their own User Page for the first time.
│   └── PanelLayoutDialog.tsx
         # drives panel configuration and integration for that Page.
         # slightly clunky here, more intended to be used for Page clones
         # large import set - one of the primary UI drivers for a significant functionality set
├── Forms
│   └── FormSelectors
│       └── LayoutSourceSelector.tsx
                # enables users to customize their panel config for a specific instantiation of Page, whether system or entity level.  IE Rooms, or Story, or Users - or a specific Room.  

├── InteractivePreview.tsx
        # used by PanelLayoutDialog for panel reordering - flashy, well-liked by users

├── PageHeader.tsx
        # header for page. default has breadcrumb, timestamps, action buttons - heavily customizable for Page clones,
        # less useful for entity level Pages
├── PageLayout.tsx
 

├── PageShell.tsx
           # main orchestrator for viewing and editing an entity page.

├── blocks *(current - not final, not even representative.)
│   ├── ActivityFeedBlock.tsx
│   ├── BioBlock.tsx
│   ├── ChartBlock.tsx
│   ├── ContactBlock.tsx
│   ├── DataTableBlock.tsx
│   ├── DomainsBlock.tsx
│   ├── GalleryBlock.tsx
│   ├── IdentityBlock.tsx
│   ├── LinksBlock.tsx
│   ├── PersonasBlock.tsx
│   ├── ProfileImageBlock.tsx
│   ├── QualitiesBlock.tsx
│   ├── RelationshipsBlock.tsx
│   ├── TraitsBlock.tsx
│   ├── UsedByBlock.tsx
│   └── index.ts

├── editor
│   ├── BlockEditorSheet.tsx
│   ├── BlockPalette.tsx
│   ├── BlockPaletteItem.tsx
│   ├── forms *(current - not final, not even representative.)
│   │   ├── BioForm.tsx
│   │   ├── ContactForm.tsx
│   │   ├── DomainsForm.tsx
│   │   ├── GalleryForm.tsx
│   │   ├── IdentityForm.tsx
│   │   ├── LinksForm.tsx
│   │   ├── ProfileImageForm.tsx
│   │   ├── QualitiesForm.tsx
│   │   ├── RelationshipsForm.tsx
│   │   ├── TraitsForm.tsx
│   │   └── index.ts
│   └── index.ts
├── index.ts
├── panels (these are some of the objects that can be added/removed to a Page)
│   ├── A2UIPanel.tsx 
            # AgentUI panel - agents can create objects (buttons, forms, etc) if Panel is on a Page where they are active, through A2UI tool use
│   ├── CanvasPanel.tsx
            # pending integration - advanced a2ui over gRPC using letsDraw/tiptap
│   ├── ChatPanel.tsx
            # talk talk window window
│   ├── DebugPanel.tsx
            # advanced, complex panel - refined, but not refined enough. needs more tests before any changes are made.
│   ├── ParticipantPanel.tsx
            # Page participants added - agents/users w/ management controls
│   ├── RoomDebugPanel.tsx
            # specialized debug panel for chat/story room integrated Page (Room)
│   ├── StoryEditorPanel.tsx
            # where a story is edited
│   ├── StoryPanel
│   │   ├── ChoiceItem.tsx
│   │   ├── ChoiceList.tsx
│   │   ├── NodeChainCollapsible.tsx
│   │   ├── NodeDisplay.tsx
│   │   ├── RuntimeControls.tsx
│   │   ├── StoryPanel.tsx
│   │   ├── StoryRuntimeStartDialog.tsx
│   │   ├── StoryStateCollapsible.tsx
│   │   └── index.ts
│   ├── StoryPlayerPanel.tsx
│   └── index.ts
├── primitives
│   ├── ActionBar.tsx
│   ├── BlockContainer.tsx
│   ├── CollapsiblePanel.tsx
│   ├── ContentRenderer
│   │   ├── ContentRenderer.tsx
│   │   ├── components
│   │   │   ├── CodeHighlight.tsx
│   │   │   └── FallbackRenderer.tsx
│   │   ├── current-build-failures.md
│   │   ├── hooks
│   │   │   ├── useMDXCompiler.ts
│   │   │   └── useThemeResolution.ts
│   │   ├── index.ts
│   │   ├── open-errors.md
│   │   ├── pluginRegistry.ts
│   │   ├── registry.ts
│   │   ├── renderers
│   │   │   ├── CodeRenderer.tsx
│   │   │   ├── HTMLRenderer.tsx
│   │   │   ├── ImageRenderer.tsx
│   │   │   ├── JSONRenderer.tsx
│   │   │   ├── MDXRenderer.tsx
│   │   │   ├── MarkdownRenderer.tsx
│   │   │   ├── SVGRenderer.tsx
│   │   │   └── TextRenderer.tsx
│   │   └── types.ts
│   ├── DraggablePanel.tsx
│   ├── EntityCard.tsx
│   ├── KeyboardShortcutProvider.tsx
│   ├── MiniPreview.tsx
│   ├── PanelContainer.tsx
│   ├── ParticipantStack.tsx
│   ├── PlaceholderContent.tsx
│   ├── PresetPicker.tsx
│   └── index.ts
├── registry
│   ├── blockTypes.ts
│   ├── dataSources.ts
│   ├── entityTypes.ts
│   ├── index.ts
│   ├── pageTemplates.ts
│   ├── panelTypes.ts
│   └── relationshipTypes.ts

16 directories, 110 files
