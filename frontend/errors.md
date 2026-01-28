src/components/Agents/AgentForm.tsx:16:15 - error TS2305: Module '"@/client"' has no exported member 'LLMProviderType'.

16 import type { LLMProviderType } from "@/client"
                 ~~~~~~~~~~~~~~~

src/components/UserSettings/LLMProviders.tsx:161:7 - error TS2561: Object literal may only specify known properties, but 'provider_type' does not exist in type 'UserLLMProviderCreate'. Did you mean to write 'provider_type_id'?

161       provider_type: data.provider_type,
          ~~~~~~~~~~~~~

src/services/agentService.ts:25:8 - error TS2305: Module '"@/client"' has no exported member 'LLMProviderType'.

25   type LLMProviderType,
          ~~~~~~~~~~~~~~~

src/services/llmCatalogService.ts:19:8 - error TS2305: Module '"@/client"' has no exported member 'LLMProviderType'.

19   type LLMProviderType,
          ~~~~~~~~~~~~~~~

src/services/llmCatalogService.ts:30:15 - error TS2305: Module '"@/client"' has no exported member 'LLMProviderType'.

30 export type { LLMProviderType } from "@/client"
                 ~~~~~~~~~~~~~~~

src/services/llmProviderService.ts:18:8 - error TS2305: Module '"@/client"' has no exported member 'LLMProviderType'.

18   type LLMProviderType,
          ~~~~~~~~~~~~~~~

src/services/llmProviderService.ts:37:15 - error TS2305: Module '"@/client"' has no exported member 'LLMProviderType'.

37 export type { LLMProviderType } from "@/client"
                 ~~~~~~~~~~~~~~~