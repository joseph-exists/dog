
we need to refactor the following components to use the new architecture, while simultaneously cutting away unnecessary duplication and complexity within the src/components/Agents directory and subdirectories.  We will retain the feature sets, but ensure that these components are not doing more work than they should, and that we're not repeating ourselves or doing work on the frontend that is already handled by the backend or other services.  Please review and provide an analysis that contains a new, slimmed down, Agents component set with clearer lines of separation.  This analysis should ensure better adherence to our engineering principles - and the practices outlined in frontend/docs/frontend-dev-skills.md.  if you have questions or strong branching concerns, please place them in the new analysis doc so we can discuss.

Errors  Files
     1  src/components/Agents/AgentCloneButton.tsx:89
     1  src/components/Agents/AgentDetailDialog.tsx:69
     3  src/components/Agents/AgentForm.tsx:48
     5  src/components/Agents/AgentProviderSelector.tsx:22
     1  src/components/Agents/CreateAgentDialog.tsx:128
     2  src/components/Agents/EditAgentDialog.tsx:146
     1  src/components/Agents/ProviderSelect.tsx:31
     1  src/components/Agents/ProviderStatusBadge.tsx:11
     4  src/components/Agents/providers/ProviderModelSelector.tsx:34
     1  src/components/Agents/providers/ProviderStatusBadge.tsx:20


AgentConfig feature list:

CreateAgentDialog: create an agent.
AgentCloneButton: clone an agentconfig - this will be used for cloning your own created agentconfigs, system agentconfigs, and other users shared/cloneable agent configs.
EditAgentDialog: update an agent

src/components/Agents/providers/ProviderModelSelector:
    needs extracted and rewritten, along with it's duplications: Agents/AgentProviderSelector, Agents/ProviderSelect

src/components/Agents/providers/ModelCombobox.tsx:
    searchable combobox for selecting LLM models to associate with an AgentConfig- currently non-functional due to limitations of LLM catalog service and breaks user ability to create new agentconfigs
    catalog models grouped by provider
    user's custom models
    inline creation of new custom models

    planned extensibility - we need this functionality, but need it to work correctly based on our architecture and current limitations.  we need a user to be able to edit the name manually (ie type in gpt-5-nano) and save without it throwing an error, and then they can modify - until the catalog service is designed, implemented, and functional.

decorations:
- providers/ModelBadge.tsx 
    - badge with tooltips (shows api provider type, custom model status, default, display name)

- Agents/ProviderStatusBadge
    - badge to show if a useraccessprovider is verified/not-tested/failing.  good feature, needs refactored.
