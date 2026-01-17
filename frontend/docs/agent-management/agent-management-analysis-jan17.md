● Agent Management Deep Dive Analysis



  │ No Frontend Processing      │ ⚠️ Warning   │ Inline model name transformation in AgentCard.tsx:139-143 │
  └─────────────────────────────┴──────────────┴───────────────────────────────────────────────────────────┘
  ---
  Critical Issue: Missing Service Layer

  The agent components directly use AgentConfigPublic from the auto-generated client:

  // Current (violates pattern)
  import type { AgentConfigPublic } from "@/client/types.gen"

  function AgentCard({ agent }: { agent: AgentConfigPublic }) {
    // Direct API type usage
  }

  Should be:
  // Compliant pattern
  import type { AgentViewModel } from "@/services/agentService"

  function AgentCard({ agent }: { agent: AgentViewModel }) {
    // ViewModel with transformed data
  }

  The docs mention AgentData interface in the components themselves, but there's no src/services/agentService.ts with proper
  ViewModels.

  ---
  defect:

  1. AgentCard.tsx:139-143 - Frontend Processing
  // remove this transform
  const displayModel = modelName
    ?.split(":")
    .pop()
    ?.replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())

  ---
  tasks:

  2. finish src/services/agentService.ts with:
    - AgentViewModel interface
    - transformAgent() function
    - Service methods wrapping API calls

  3. review components again & create list of needed updates


  
  4. Update docs to reference the service layer pattern
