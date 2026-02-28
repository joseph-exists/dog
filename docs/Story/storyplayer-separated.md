**Conclusion**
The system currently has one canonical room runtime, and most surfaces are aligned to it. The main remaining drift vector is the local `storyPlayer` panel.

Any panel that assumes `storyPlayer` reflects the same canonical story state as `storyRuntime` will enter failure modes.


**Runtime Review**
Most important finding:
- `storyPlayer` is not authoritative room runtime state. It maintains a separate local client-side state machine and only emits synthetic chat messages like `[Story: chose "..."]` via WebSocket in [StoryPlayerPanel.tsx:162](/home/josep/dog/frontend/src/components/Room/panels/StoryPlayerPanel.tsx:162), [StoryPlayerPanel.tsx:174](/home/josep/dog/frontend/src/components/Room/panels/StoryPlayerPanel.tsx:174), and [r.$roomId.tsx:356](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx:356). That can drift from the actual room runtime.


**UI**
- Added owner-facing room prompt settings dialog in [RoomPromptSettingsDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/RoomPromptSettingsDialog.tsx:1)
  - room default PromptConfig bind/unbind
  - per-agent override bind/unbind
  - current binding inspection
  - inline overlay inspection when present
- Wired it into the room header/settings flow in [r.$roomId.tsx:16](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx:16), [r.$roomId.tsx:72](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx:72), [r.$roomId.tsx:447](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx:447), [r.$roomId.tsx:484](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx:484)
- Added live invalidation for room prompt setting events in [useRoomStream.ts:66](/home/josep/dog/frontend/src/hooks/useRoomStream.ts:66) and [useRoomStream.ts:248](/home/josep/dog/frontend/src/hooks/useRoomStream.ts:248)
- Updated readiness tracking in [demo-readiness.md:98](/home/josep/dog/frontend/demo-readiness.md:98)




Authoritative hierarchy today:
1. Backend room runtime authority is `RoomStoryProgress.active_progress_id -> UserStoryProgress` in [crud.py:1971](/home/josep/dog/backend/app/crud.py:1971), [crud.py:2009](/home/josep/dog/backend/app/crud.py:2009), [crud.py:2150](/home/josep/dog/backend/app/crud.py:2150), [crud.py:2291](/home/josep/dog/backend/app/crud.py:2291), [crud.py:2453](/home/josep/dog/backend/app/crud.py:2453)
2. Agent prompt/context reads that runtime projection in [context_provider.py:183](/home/josep/dog/backend/app/services/context_provider.py:183)
3. Room `storyRuntime` panel is a projection/mutation client over that authority in [useRoomRuntime.ts:72](/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts:72) and [StoryPanel.tsx:30](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx:30)
4. WebSocket events invalidate runtime and messages, keeping chat/runtime panels coherent in [useRoomStream.ts:197](/home/josep/dog/frontend/src/hooks/useRoomStream.ts:197) and [useRoomStream.ts:242](/home/josep/dog/frontend/src/hooks/useRoomStream.ts:242)

What is coherent now:
- chat messages
- agent invocations/prompt resolution
- room runtime panel
- runtime-aware agent context
- room prompt settings dialog state







3. If sandbox/local, label it clearly and keep it out of any stateful runtime assumptions or panel/block integrations.