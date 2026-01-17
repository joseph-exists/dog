
  Files Requiring Changes (2 total)
  ┌───────────────────────────┬───────┬───────────┬────────────┬──────────────────┐
  │           File            │ Lines │ SDK Calls │ Type Props │    Complexity    │
  ├───────────────────────────┼───────┼───────────┼────────────┼─
  ├───────────────────────────┼───────┼───────────┼────────────┼──────────────────┤
  │ AgentModelSettings.tsx    │ 383   │ 2         │ No         │ Medium           │
  ├───────────────────────────┼───────┼───────────┼────────────┼──────────────────┤
  │ AgentProviderSelector.tsx │ 227   │ 2         │ No         │ Medium           │
  └───────────────────────────┴───────┴───────────┴────────────┴──────────────────┘
  Files Using AgentData (no changes needed)
  ┌──────────────────────┬──────────────────────────────┐
  │         File         │            Notes             │
  ├──────────────────────┼──────────────────────────────┤
  │ AgentCarousel.tsx    │ Uses internal AgentData type │
  ├──────────────────────┼──────────────────────────────┤
  │ AgentPartyPicker.tsx │ Uses internal AgentData type │
  ├──────────────────────┼──────────────────────────────┤
  │ AgentQuickAdd.tsx    │ Uses internal AgentData type │
  ├──────────────────────┼──────────────────────────────┤
  │ RoomAgentList.tsx    │ Uses internal AgentData type │
  ├──────────────────────┼──────────────────────────────┤
  │ AgentCard.tsx        │ Props-based, no SDK imports  │
  ├──────────────────────┼──────────────────────────────┤
  │ AgentAvatar.tsx      │ Pure UI, no types            │
  ├──────────────────────┼──────────────────────────────┤
  │ AgentBadge.tsx       │ Pure UI, exports own types   │
  └──────────────────────┴──────────────────────────────┘


  ---
  Quick Review Commands

  # See all direct SDK imports in one view
  grep -n "from \"@/client" src/components/Agents/*.tsx src/routes/_layout/agents.tsx

  # See all AgentConfigPublic usages
  grep -n "AgentConfigPublic" src/components/Agents/*.tsx src/routes/_layout/agents.tsx

  # See inline transforms to replace
  grep -n "split.*pop.*replace" src/components/Agents/*.tsx

  ---
  Suggested Migration Order

  7. AgentModelSettings.tsx - Uses settings endpoints (separate concern)
  8. AgentProviderSelector.tsx - Uses settings endpoints (separate concern)
