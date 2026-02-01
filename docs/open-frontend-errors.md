
src/components/Agents/Dialogs/EditAgentDialog.tsx:28:8 - error TS2306: File '/home/josep/dog/frontend/src/services/agentService.ts' is not a module.

28 } from "@/services/agentService"
          ~~~~~~~~~~~~~~~~~~~~~~~~~

src/components/Agents/Dialogs/EditAgentDialog.tsx:70:34 - error TS18046: 'updatedAgent' is of type 'unknown'.

70       showSuccessToast(`Agent "${updatedAgent.name}" - wow. that actually worked?  neat.`)
                                    ~~~~~~~~~~~~

src/components/Agents/Display/ModelBadge.tsx:21:15 - error TS2614: Module '"@/services/llmCatalogService"' has no exported member 'LLMProviderType'. Did you mean to use 'import LLMProviderType from "@/services/llmCatalogService"' instead?

21 import type { LLMProviderType } from "@/services/llmCatalogService"
                 ~~~~~~~~~~~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:22:1 - error TS6133: 'AgentsService' is declared but its value is never read.

22 import { AgentsService } from "@/client"
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:41:10 - error TS2304: Cannot find name 'AgentViewModel'.

41   agent: AgentViewModel
            ~~~~~~~~~~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:45:5 - error TS2304: Cannot find name 'useAgentSettings'.

45     useAgentSettings({ agent })
       ~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:67:14 - error TS2304: Cannot find name 'ProviderStatusBadge'.

67             <ProviderStatusBadge status={provider.status} size="sm" />
                ~~~~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:78:3 - error TS2339: Property 'agent' does not exist on type 'AgentProviderSelectorProps'.

78   agent,
     ~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:90:7 - error TS2304: Cannot find name 'useAgentSettings'.

90   } = useAgentSettings({ agent })
         ~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:143:14 - error TS2304: Cannot find name 'ProviderStatusBadge'.

143             <ProviderStatusBadge status={provider.status} size="sm" />
                 ~~~~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/InlineProviderSelector.tsx:168:10 - error TS2304: Cannot find name 'AgentViewModel'.

168   agent: AgentViewModel
             ~~~~~~~~~~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:57:3 - error TS2339: Property 'placeholder' does not exist on type 'ModelComboboxProps'.

57   placeholder = "Select a model...",
     ~~~~~~~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:83:7 - error TS7053: Element implicitly has an 'any' type because expression of type 'string' can't be used to index type '{}'.
  No index signature with a parameter of type 'string' was found on type '{}'.

83     ? modelsByProvider[providerType] || []
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:87:35 - error TS2554: Expected 0 arguments, but got 1.

87   const selectedModel = findModel(value)
                                     ~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:88:39 - error TS2339: Property 'label' does not exist on type 'never'.

88   const displayValue = selectedModel?.label || formatModelName(value)
                                         ~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:93:6 - error TS7006: Parameter 'm' implicitly has an 'any' type.

93     (m) =>
        ~

src/components/Agents/Selectors/ModelCombobox.tsx:101:23 - error TS2552: Cannot find name 'suggestDisplayName'. Did you mean 'setNewDisplayName'?

101     setNewDisplayName(suggestDisplayName(searchQuery))
                          ~~~~~~~~~~~~~~~~~~

  src/components/Agents/Selectors/ModelCombobox.tsx:66:26
    66   const [newDisplayName, setNewDisplayName] = useState("")
                                ~~~~~~~~~~~~~~~~~
    'setNewDisplayName' is declared here.

src/components/Agents/Selectors/ModelCombobox.tsx:113:46 - error TS2554: Expected 0 arguments, but got 1.

113       const result = await createCustomModel({
                                                 ~
114         modelId: newModelId.trim(),
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
...
116         providerType: effectiveProviderType,
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
117       })
    ~~~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:115:47 - error TS2552: Cannot find name 'suggestDisplayName'. Did you mean 'setNewDisplayName'?

115         displayName: newDisplayName.trim() || suggestDisplayName(newModelId),
                                                  ~~~~~~~~~~~~~~~~~~

  src/components/Agents/Selectors/ModelCombobox.tsx:66:26
    66   const [newDisplayName, setNewDisplayName] = useState("")
                                ~~~~~~~~~~~~~~~~~
    'setNewDisplayName' is declared here.

src/components/Agents/Selectors/ModelCombobox.tsx:120:23 - error TS2339: Property 'value' does not exist on type 'void'.

120       onChange(result.value)
                          ~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:177:42 - error TS2339: Property 'isDefault' does not exist on type 'never'.

177                 {value && selectedModel?.isDefault && (
                                             ~~~~~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:208:39 - error TS2552: Cannot find name 'suggestDisplayName'. Did you mean 'setNewDisplayName'?

208                     setNewDisplayName(suggestDisplayName(e.target.value))
                                          ~~~~~~~~~~~~~~~~~~

  src/components/Agents/Selectors/ModelCombobox.tsx:66:26
    66   const [newDisplayName, setNewDisplayName] = useState("")
                                ~~~~~~~~~~~~~~~~~
    'setNewDisplayName' is declared here.

src/components/Agents/Selectors/ModelCombobox.tsx:273:18 - error TS7006: Parameter 'm' implicitly has an 'any' type.

273                 (m) =>
                     ~

src/components/Agents/Selectors/ModelCombobox.tsx:295:23 - error TS2304: Cannot find name 'LLMProviderType'.

295                       LLMProviderType,
                          ~~~~~~~~~~~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:296:23 - error TS2304: Cannot find name 'ModelOption'.

296                       ModelOption[],
                          ~~~~~~~~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:308:78 - error TS2554: Expected 0 arguments, but got 1.

308                       <CommandGroup key={type} heading={getProviderTypeLabel(type)}>
                                                                                 ~~~~

src/components/Agents/Selectors/ModelCombobox.tsx:378:10 - error TS2304: Cannot find name 'suggestDisplayName'.

378 export { suggestDisplayName }
             ~~~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:28:50 - error TS2306: File '/home/josep/dog/frontend/src/services/userAccessProviderService.ts' is not a module.

28 import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"
                                                    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:112:5 - error TS2339: Property 'hasAnyProvider' does not exist on type '{ providers: never[]; isLoading: boolean; }'.

112     hasAnyProvider,
        ~~~~~~~~~~~~~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:123:31 - error TS2339: Property 'id' does not exist on type 'never'.

123     ? providers.find((p) => p.id === providerId)
                                  ~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:187:37 - error TS2339: Property 'id' does not exist on type 'never'.

187                       key={provider.id}
                                        ~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:188:39 - error TS2339: Property 'id' does not exist on type 'never'.

188                       value={provider.id}
                                          ~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:189:43 - error TS2339: Property 'is_usable' does not exist on type 'never'.

189                       disabled={!provider.is_usable}
                                              ~~~~~~~~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:193:41 - error TS2339: Property 'name' does not exist on type 'never'.

193                         <span>{provider.name}</span>
                                            ~~~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:196:46 - error TS2339: Property 'status' does not exist on type 'never'.

196                             status={provider.status}
                                                 ~~~~~~

src/components/Agents/Selectors/ProviderModelSelector.tsx:224:13 - error TS2322: Type '{ value: string; onChange: (value: string) => void; placeholder: string; disabled: boolean; className: string; }' is not assignable to type 'IntrinsicAttributes & ModelComboboxProps'.
  Property 'placeholder' does not exist on type 'IntrinsicAttributes & ModelComboboxProps'.

224             placeholder={`Select model (default: ${formatModelName(agentDefaultModel)})`}
                ~~~~~~~~~~~

src/components/Agents/Settings/AgentDetailDialog.tsx:47:47 - error TS2304: Cannot find name 'AgentViewModel'.

47 function AgentViewContent({ agent }: { agent: AgentViewModel }) {
                                                 ~~~~~~~~~~~~~~

src/components/Agents/Settings/AgentDetailDialog.tsx:114:43 - error TS2345: Argument of type 'string' is not assignable to parameter of type 'AgentsGetAgentData'.

114     queryFn: () => AgentsService.getAgent(agentId),
                                              ~~~~~~~

src/components/Agents/Settings/AgentDetailDialog.tsx:127:24 - error TS2304: Cannot find name 'UpdateAgentInput'.

127     mutationFn: (data: UpdateAgentInput) =>
                           ~~~~~~~~~~~~~~~~

src/components/Agents/Settings/AgentDetailDialog.tsx:128:7 - error TS2552: Cannot find name 'AgentService'. Did you mean 'AgentsService'?

128       AgentService.updateAgent(agentId, data),
          ~~~~~~~~~~~~

src/components/Agents/Settings/AgentDetailDialog.tsx:130:34 - error TS18046: 'updatedAgent' is of type 'unknown'.

130       showSuccessToast(`Agent "${updatedAgent.name}" updated successfully.`)
                                     ~~~~~~~~~~~~

src/components/Agents/Settings/AgentDetailDialog.tsx:158:20 - error TS2304: Cannot find name 'UpdateAgentInput'.

158     const payload: UpdateAgentInput = {}
                       ~~~~~~~~~~~~~~~~

src/components/Agents/Settings/AgentDetailDialog.tsx:207:30 - error TS2322: Type 'string | null | undefined' is not assignable to type 'string'.
  Type 'undefined' is not assignable to type 'string'.

207                 <AgentAvatar name={agent.name} size="sm" />
                                 ~~~~

  src/components/Agents/Display/AgentAvatar.tsx:100:3
    100   name: string
          ~~~~
    The expected type comes from property 'name' which is declared here on type 'IntrinsicAttributes & AgentAvatarProps'

src/components/Agents/Settings/AgentDetailDialog.tsx:209:34 - error TS2322: Type 'string | null | undefined' is not assignable to type 'AgentScope'.
  Type 'undefined' is not assignable to type 'AgentScope'.

209                 <AgentScopeBadge scope={agent.scope} className="shrink-0" />
                                     ~~~~~

  src/components/Agents/Display/AgentBadge.tsx:18:3
    18   scope: AgentScope
         ~~~~~
    The expected type comes from property 'scope' which is declared here on type 'IntrinsicAttributes & ScopeBadgeProps'

src/components/Agents/Settings/AgentDetailDialog.tsx:222:17 - error TS2322: Type 'UserAgentConfigPublic' is not assignable to type 'Partial<UserAgentConfigCreate>'.
  Types of property 'name' are incompatible.
    Type 'string | null | undefined' is not assignable to type 'string | undefined'.
      Type 'null' is not assignable to type 'string | undefined'.

222                 initialData={agent}
                    ~~~~~~~~~~~

  src/components/Agents/Forms/AgentForm.tsx:130:3
    130   initialData?: Partial<UserAgentConfigCreate>
          ~~~~~~~~~~~
    The expected type comes from property 'initialData' which is declared here on type 'IntrinsicAttributes & AgentFormProps'

src/components/Agents/Settings/AgentModelSettings.tsx:31:10 - error TS2614: Module '"@/hooks/useAgentSettings"' has no exported member 'useAgentSettings'. Did you mean to use 'import useAgentSettings from "@/hooks/useAgentSettings"' instead?

31 import { useAgentSettings } from "@/hooks/useAgentSettings"
            ~~~~~~~~~~~~~~~~

src/components/Agents/Settings/AgentModelSettings.tsx:32:37 - error TS2306: File '/home/josep/dog/frontend/src/services/agentService.ts' is not a module.

32 import type { AgentViewModel } from "@/services/agentService"
                                       ~~~~~~~~~~~~~~~~~~~~~~~~~

src/routes/_layout/agent.$agentId.tsx:42:30 - error TS2306: File '/home/josep/dog/frontend/src/services/agentService.ts' is not a module.

42 import { AgentService } from "@/services/agentService"
                                ~~~~~~~~~~~~~~~~~~~~~~~~~

src/routes/_layout/agents.tsx:36:51 - error TS2306: File '/home/josep/dog/frontend/src/services/agentService.ts' is not a module.

36 import { AgentService, type AgentViewModel } from "@/services/agentService"
                                                     ~~~~~~~~~~~~~~~~~~~~~~~~~

src/routes/_layout/agents.tsx:195:34 - error TS7006: Parameter 'agent' implicitly has an 'any' type.

195             {personalAgents.map((agent) => (
                                     ~~~~~

src/routes/_layout/agents.tsx:209:32 - error TS7006: Parameter 'agent' implicitly has an 'any' type.

209             {systemAgents.map((agent) => (
                                   ~~~~~

src/routes/_layout/r.$roomId.tsx:33:51 - error TS2306: File '/home/josep/dog/frontend/src/services/agentService.ts' is not a module.

33 import { AgentService, type AgentViewModel } from "@/services/agentService"
                                                     ~~~~~~~~~~~~~~~~~~~~~~~~~

src/routes/_layout/r.$roomId.tsx:169:8 - error TS7006: Parameter 'a' implicitly has an 'any' type.

169       (a) => a.id === p.participant_id || a.name === p.participant_id,
           ~

src/routes/_layout/r.$roomId.tsx:184:8 - error TS7006: Parameter 'a' implicitly has an 'any' type.

184       (a) => a.id === p.participant_id || a.name === p.participant_id,
           ~

src/services/roomService.ts:40:30 - error TS2306: File '/home/josep/dog/frontend/src/services/agentService.ts' is not a module.

40 import { AgentService } from "./agentService"
                                ~~~~~~~~~~~~~~~~


Found 55 errors in 11 files.

Errors  Files
     2  src/components/Agents/Dialogs/EditAgentDialog.tsx:28
     1  src/components/Agents/Display/ModelBadge.tsx:21
     8  src/components/Agents/Selectors/InlineProviderSelector.tsx:22
    16  src/components/Agents/Selectors/ModelCombobox.tsx:57
     9  src/components/Agents/Selectors/ProviderModelSelector.tsx:28
     9  src/components/Agents/Settings/AgentDetailDialog.tsx:47
     2  src/components/Agents/Settings/AgentModelSettings.tsx:31
     1  src/routes/_layout/agent.$agentId.tsx:42
     3  src/routes/_layout/agents.tsx:36
     3  src/routes/_layout/r.$roomId.tsx:33
     1  src/services/roomService.ts:40