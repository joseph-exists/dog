# Reference: provider_type serialization

## Symptom
- Pydantic validation error for provider_type (expects string but receives relationship object).
  - Example log: backend/app/api/failure-mode.md

## Cause
- Response schema expects denormalized provider_type: string.
  - UserLLMProviderPublic.provider_type: backend/app/models.py:1343-1354
- ORM returns relationship object unless serialized explicitly.
  - UserLLMProvider.provider_type relationship: backend/app/models.py:3929-3936

## Fix pattern
- For short-term stability, join the provider_type table and map the name into the public schema.
  - list/create/get/update routes join LLMProviderType and serialize provider_type name:
    - backend/app/api/routes/llm_providers.py:33-156
  - Helper utilities:
    - backend/app/api/routes/llm_providers.py:232-253

## Checklist for new endpoints
- If a response model has denormalized fields, do not return ORM objects directly.
- Use a serializer that maps relationship fields to scalar strings.
- Ensure relationships used in serialization are loaded (selectinload or explicit join).
