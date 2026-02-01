

> frontend@0.0.0 build
> tsc -p tsconfig.build.json && vite build

src/components/Agents/Dialogs/AgentCloneButton.tsx:75:23 - error TS1110: Type expected.

75       const payload:  = {
                         ~

src/components/Agents/Dialogs/CreateAgentDialog.tsx:27:19 - error TS1005: '{' expected.

27 import AgentForm, from "../Forms/AgentForm"
                     ~~~~

src/components/Agents/Dialogs/CreateAgentDialog.tsx:36:23 - error TS1110: Type expected.

36   onSuccess?: (agent: ) => void
                         ~


Found 3 errors in 2 files.

Errors  Files
     1  src/components/Agents/Dialogs/AgentCloneButton.tsx:75
     2  src/components/Agents/Dialogs/CreateAgentDialog.tsx:27