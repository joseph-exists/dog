OLD	PATTERN
```
mutationFn: (data: UserAgentConfigUpdate) => AgentsService.updateAgent({ requestBody: data })	
const payload: UserAgentConfigUpdate = { ... }
updateMutation.mutateAsync(payload)	await 
```

NEW IMPLEMENTATION
```
mutationFn: () => AgentsService.updateAgent({ requestBody: { provider_type: agent.provider_type!, ...formData } as AgentsUpdateAgentData['requestBody'] })
updateMutation.mutateAsync() (no payload)
```

How this works:

agent.provider_type (from UserAgentConfigPublic) → routes to correct Type1Update/Type3Update - allows extensibility of more TypeNUpdate.

AgentsUpdateAgentData['requestBody'] → OpenAPI union type (auto‑generated).

Form state unchanged → spreads into discriminated payload.

TypeScript safe → autocomplete warns about missing type‑specific fields.


finding old code:
```
mutationFn: (data: UserAgentConfigUpdate) =>
  AgentsService.updateAgent\({
    agentId: [^,]*,?
    requestBody: data,
```

fixing with new code:
```
mutationFn: () =>
  AgentsService.updateAgent({
    agentId: $1,
    requestBody: {
      provider_type: agent.provider_type!,
```


Then handleSave: mutateAsync(payload) → mutateAsync()

the buildDiscriminatedPayload might be applicable in many cases.


Generic helper pattern and usage:
```
export const sparseAgentUpdate = (
  agent: { provider_type: string },
  changes: Record<string, any> = {}
): AgentsUpdateAgentData['requestBody'] => ({
  provider_type: agent.provider_type!,
  ...changes,
} as AgentsUpdateAgentData['requestBody'];
```

potential use:

```
const requestBody = sparseAgentUpdate(agent, {
  ...(providerId && { user_access_provider: providerId }),
  ...(modelName && { model_name: modelName }),
});
```

Current tasks based on failures:

(all files in frontend/src/components/Agents/Dialogs/)

AgentCloneButton.tsx - 
migrate from UserAgentConfigCreate 

CreateAgentDialog.tsx:
migrate from UserAgentConfigCreate

EditAgentDialog:
migrate from UserAgentConfigCreate

Here’s the concrete plan to migrate the remaining dialogs to the new discriminated‑union pattern:

- **Review Current Code**: Inspect `AgentCloneButton.tsx`, `CreateAgentDialog.tsx`, and `EditAgentDialog.tsx` to map where they still use the old `mutationFn: (data) => …updateAgent({ requestBody: data })` and `mutate(payload)` calls, plus any manual payload building with `UserAgentConfigUpdate/UserAgentConfigCreate`.
- **Choose/Build Helper**: Decide whether to reuse the existing `sparseAgentUpdate`/`buildDiscriminatedPayload` helper or add a small shared util (e.g., `sparseAgentUpdate(agent, changes)`) so each dialog can assemble `AgentsUpdateAgentData['requestBody']` with `provider_type` included and minimal changed fields.
- **Refactor Each Dialog**: For Clone, Create, and Edit:
  - Switch `mutationFn` to the new pattern: no parameter; call `AgentsService.updateAgent/createAgent` with inline `requestBody` constructed via the helper, including `agentId` where needed.
  - Adjust submit handlers to call `mutate()`/`mutateAsync()` without args, relying on captured form state.
  - Ensure provider_type is correctly set for all TypeN variants; keep form validation/“no changes” guard consistent.
- **Type/Lint Pass**: Run type-check/lint on these files to confirm the union is satisfied and no implicit `any` leaks; manually sanity-check clone/create/edit flows for required fields and unchanged payload behavior.

- Overall fit: The plan keeps the forms’ external contract stable: `AgentForm` still emits `AgentFormData`, and dialogs still call `AgentsService.updateAgent`/`createAgent`—only the payload construction shifts to the discriminated union, so upstream callers (triggers, routing) and downstream API remain unaffected.  

- Payload correctness: Including `provider_type` in the helper guarantees the backend can discriminate to the right TypeN schema; using a sparse “changed fields” map preserves current minimal PATCH‑like behavior and avoids regressions in audit/validation downstream.  

- Extensibility: Centralizing payload shaping (helper) means adding future Type4…Type7 only needs generator type updates; dialogs shouldn’t need per-type branches, keeping the surface open for more provider types.  

- Engineering hygiene: Removing `mutate(payload)` arguments reduces drifting signatures, and capturing form state in closure avoids mismatched types; adding validation/no-change guards preserves UX contracts. Keep the helper near Agents components or a shared `utils/agentPayload.ts` to avoid duplication.  

- Caution points: Ensure the helper enforces required fields per union member (e.g., some TypeN may require system_prompt); consider narrowing via `agent.provider_type` to set those required keys to avoid runtime 422s. Add unit-ish tests or at least type tests for the helper with representative Type1/Type3 payloads to lock behavior.  


Current Failure below, potentially related to earlier problem addressed in AgentForm.

In AgentForm, we resolved this type error by only passing provider_type into AgentForm when it matches the Type3 literal; otherwise it’s left undefined. Added a TYPE3_PROVIDER constant for clarity. This keeps initialData compatible with Type3Create while avoiding the literal mismatch.

Previously, we attempted to rework the provider_type handling to avoid a brittle single-UUID check, by passing provider_type back to AgentForm as provider_type as ProviderType | undefined, so any current or future literal provider types remain valid without extra conditionals.  However, we were unable to get this to pass Typescript checks.


src/components/Agents/Dialogs/EditAgentDialog.tsx:184:11 - error TS2322: Type '{ name: string; slug: string; description: string; model_id: string; model_name: string; system_prompt: string; participation_mode: string; provider_type: string; user_access_provider: string | undefined; }' is not assignable to type 'Partial<Type3Create>'.
  Types of property 'provider_type' are incompatible.
    Type 'string' is not assignable to type '"e09ade10-8563-4748-8deb-1a6c87c97134"'.

184           initialData={sanitizedAgent}
              ~~~~~~~~~~~

  src/components/Agents/Forms/AgentForm.tsx:135:3
    135   initialData?: Partial<Type3Create>
          ~~~~~~~~~~~
    The expected type comes from property 'initialData' which is declared here on type 'IntrinsicAttributes & AgentFormProps'

