

# for the build errors with AgentForm.tsx (representative example, one of many):

```
 src/components/Agents/Forms/AgentForm.tsx:214:5 - error TS2322: Type 'Resolver<{ name: string; slug: string; provider_type: string; description?: string | undefined; user_access_provider?: string | null | undefined; model?: string | null | undefined; model_id?: string | ... 1 more ... | undefined; ... 14 more ...; agent_metadata_raw?: string | undefined; }, any, { ...; }>' is not assignable to type 'Resolver<{ name: string; slug: string; description: string; user_access_provider: string | null; provider_type: string; model: string | null; model_id: string | null; model_name: string; system_prompt: string; ... 12 more ...; agent_metadata_raw: string; }, any, { ...; }>'.

Types of parameters 'options' and 'options' are incompatible.
Type 'ResolverOptions<{ name: string; slug: string; description: string; user_access_provider: string | null; provider_type: string; model: string | null; model_id: string | null; model_name: string; system_prompt: string; ... 12 more ...; agent_metadata_raw: string; }>' is not assignable to type 'ResolverOptions<{ name: string; slug: string; provider_type: string; description?: string | undefined; user_access_provider?: string | null | undefined; model?: string | null | undefined; model_id?: string | ... 1 more ... | undefined; ... 14 more ...; agent_metadata_raw?: string | undefined; }>'.
Type 'string | undefined' is not assignable to type 'string'.
Type 'undefined' is not assignable to type 'string'.

214     resolver: zodResolver(agentFormSchema),
```

### Architect Guidance:

The error you’re seeing is a **type‑mismatch between what `zodResolver(schema)` expects and what you’re feeding into `useForm<FormValues>` and `AgentFormData`**, not a bug in your logic. The core issue is that:

- `zodResolver` derives its type from `z.infer<typeof agentFormSchema>` (your `FormValues`).
- Your `AgentFormData` type is **slightly different** (e.g., some fields are optional or can be `undefined`), and you’re attempting to align those two as if they were the same schema‑output.

TypeScript is complaining that:

```
- `Resolver<FormValues>` is not assignable to `Resolver<AgentFormData>` because their `options` parameters are incompatible.
```

- Concretely, `AgentFormData`’s fields are non‑optional `string` (e.g., `model_name: string`), but your `FormValues` (from `z.string().default("")`) are `string | undefined` in some contexts, hence `Type 'string | undefined' is not assignable to type 'string'`.

***

### Root cause

You have:

```ts
type FormValues = z.infer<typeof agentFormSchema>
```

and then:

```ts
const data: AgentFormData = {
  name: values.name,
  slug: values.slug,
  description: values.description,
  user_access_provider: values.user_access_provider || null,
  model: values.model || null,
  model_id: values.model_id || null,
  model_name: values.model_name || undefined, // ← this is `string | undefined`
  // ...
}
```

But `AgentFormData['model_name']` is defined as:

```ts
model_name?: string
```

So the `values.model_name` coming from Zod is effectively `string | null` (because `.nullable().default(null)`), while `model_name` on `AgentFormData` is optional—yet TypeScript is still seeing `AgentFormData` as stricter than the inferred `FormValues`.

At the same time, in your `useForm<FormValues>` you’re passing `FormValues` to `useForm`, but the error message suggests somewhere in the call‑stack TS is treating the resolver as expecting `AgentFormData` (or another shape that has **all fields as non‑optional**). This usually happens when:

- `useForm` is being invoked with a generic that **doesn’t match** the resolver’s inferred type.
- Or `useForm` is getting default values that are typed as `AgentFormData`, creating a mismatch between `FormValues` and `AgentFormData`.

***

### How to fix it correctly

You have two clean paths:

#### 1. **Make `useForm` generic match `FormValues` exactly**

Change this line to be explicit and consistent:

```ts
const form = useForm<FormValues>({
  resolver: zodResolver(agentFormSchema),
  mode: "onBlur",
  defaultValues: { /* ... */ },
})
```

If you’re using `defaultValues` derived from `defaultValues?: UserAgentConfigPublic`, make sure `UserAgentConfigPublic` is not **leaking into** the `useForm<T>` generic. Do not write:

```ts
const form = useForm<AgentFormData>(...)
```

because `AgentFormData` is your **output** type, not your **form input** type.

`FormValues` is the shape that Zod produces and the form controls bind to. `AgentFormData` is just a transformation:

```ts
const data: AgentFormData = {
  // transform from FormValues to AgentFormData
}
```

This keeps the resolver and schema in agreement.

#### 2. **Align `AgentFormData` with `FormValues`**

If you want to keep passing `AgentFormData` as the `useForm` generic, you must derive the schema from that shape:

```ts
const agentFormSchema = z.object({
  name: z.string().min(1),
  slug: z.string().min(1),
  description: z.string().default(""),


  user_access_provider: z.string().nullable().default(null),
  provider_type: z.string().min(1),
  model: z.string().nullable().default(null),
  model_id: z.string().nullable().default(null),
  model_name: z.string().nullable().default(null), // or .default("") if you really want non‑optional


  system_prompt: z.string().default(""),
  custom_system_prompt: z.string().nullable().default(null),
  instructions: z.string().nullable().default(null),
  // ... etc
})

type FormValues = z.output<typeof agentFormSchema> // or z.infer
```

Then:

```ts
export type AgentFormData = FormValues // or minimally aligned
```

In other words, **do not** define `FormValues` and `AgentFormData` independently. Let one derive from the other through Zod.

Alternatively, if you want them **independent**, you can:

```ts
const data: AgentFormData = {
  name: values.name,
  slug: values.slug,
  description: values.description ?? "",
  user_access_provider: values.user_access_provider ?? null,
  model: values.model ?? null,
  model_id: values.model_id ?? null,
  model_name: values.model_name ?? "", // ensure `string`, not `undefined`
  // ...
}
```

This forces all optional fields to a concrete value so they’re assignable to `AgentFormData`’s non‑optional or `string`‑only fields.

***

### Recommended minimal change

Given your current code, the **minimal fix** is:

1. Keep `FormValues` as `z.infer<typeof agentFormSchema>` (current behavior).
2. Change `AgentFormData` so all fields that can be `null` or `undefined` are marked as such:
```ts
export type AgentFormData = {
  name: string
  slug: string
  description: string
  user_access_provider?: string | null
  provider_type: string
  model?: string | null
  model_id?: string | null
  model_name?: string | null  // or just optional
  system_prompt: string
  custom_system_prompt?: string | null
  instructions?: string | null
  is_enabled: boolean
  is_clonable: boolean
  is_visible: boolean
  scope: string
  participation_mode: string
  is_coordinator: boolean
  max_tool_iterations: number
  capabilities: string[]
  tool_config?: Record<string, unknown> | null
  deps_config?: Record<string, unknown> | null
  agent_metadata?: Record<string, unknown> | null
}
```

Then, in `handleSubmit`, ensure you never pass `undefined` where `string` is expected:

```ts
model_name: values.model_name ?? ""
```

This way, `zodResolver` stays on `FormValues`, `useForm` is generic over `FormValues`, and `AgentFormData` is a superset of `FormValues` that accepts `null` or `undefined` where Zod might produce it.

***

### Summary

You’re not misusing `react‑hook‑form` or `zodResolver` in principle; the problem is **type‑level misalignment** between:

- what Zod thinks your form shape is (`FormValues`), and
- what your `AgentFormData` type expects (some fields are `string` only, not `string | null | undefined`).

Either:

- make `useForm` generic over `FormValues` (not `AgentFormData`), and treat `AgentFormData` as a type‑safe transform, or
- derive `FormValues` from `AgentFormData` via Zod, so the shapes are in sync.

The first approach is usually cleaner for your pattern.
