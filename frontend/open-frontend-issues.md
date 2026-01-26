● Here's the pre-close checklist status:
  Item: TypeScript
  Status: ✅ Pass
  Notes: No compilation errors
  ────────────────────────────────────────
  Item: Linting
  Status: ⚠️ Expected warning
  Notes: dangerouslySetInnerHTML flagged — but we use DOMPurify
  (same
     pattern as original StoryPreview.tsx)
  ────────────────────────────────────────
  Item: OpenAPI client regen
  Status: 🔄 Optional
  Notes: Backend endpoint changed (include_inactive param). I
    bypassed the generated client with __request, so it works,
    but keeping in sync is good hygiene
  ────────────────────────────────────────
  Item: participation_mode
  Status: ❓ Needs your verification
  Notes: Run the psql query to confirm if it's a DB issue or still
    frontend
  ────────────────────────────────────────
  Item: Smoke test
  Status: 🧪 Needs manual test
  Notes: Toggle agents, play a story, verify events emit to chat
  ---
  Remaining actions for you:

  1. Verify participation_mode — Run this in psql:
  SELECT name, participation_mode FROM agent_configs ORDER BY name;
 

  3. Smoke test these scenarios:
    - Toggle an agent OFF → should dim but stay visible
    - Toggle back ON → should reactivate
    - Add storyPlayer panel to a room with a story attached
    - Make story choices → verify [Story: chose "X" → Y] messages
  appear in chat
    - Undo/restart → verify events emit

  
