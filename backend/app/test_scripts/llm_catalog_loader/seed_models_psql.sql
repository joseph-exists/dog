-- Seed llmmodel from models-original.csv
-- Run: psql $DATABASE_URL -f seed_models_psql.sql
-- Or from project root: docker compose exec db psql -U postgres -d app -f /path/to/seed_models_psql.sql

-- provider_name -> primary_provider_type_id mapping (from debugging-llm-catalogs.md)
-- OpenAI: 673f1787-8474-4e1c-986c-8e19f14c989c
-- Anthropic: 008dc763-4309-43cd-ba5f-1eb1323a0964
-- OpenAI Compatible: e09ade10-8563-4748-8deb-1a6c87c97134
-- Custom: 186672e2-f50a-4457-a7dd-a50084077ff7
-- Empty: 37520103-0644-4d29-99b6-583eb0996370
-- Google: ae07eb0b-929e-4844-8b75-4fe6abca09df

-- Use first user as owner for system models (or replace with your superuser id)
-- If owner_id has no FK, any UUID works. If it has FK to user, we need a real user.
INSERT INTO llmmodel (
  id, model_id, display_name, description, context_window,
  is_default, is_enabled, is_deprecated, sort_order,
  has_vision, has_function_calling, has_streaming, has_json_mode,
  secondary_capabilities, is_system, multiple_provider_type_support,
  primary_provider_type_id, owner_id
)
SELECT
  gen_random_uuid(),
  v.model_id, v.display_name, v.description, v.context_window,
  v.is_default, v.is_enabled, false,
  v.sort_order, v.has_vision, v.has_function_calling, v.has_streaming, v.has_json_mode,
  NULL, true, false,
  v.primary_provider_type_id,
  COALESCE((SELECT id FROM "user" LIMIT 1), '00000000-0000-0000-0000-000000000001'::uuid)
FROM (VALUES
  ('gpt-4o', 'GPT-4o', 'Latest multimodal flagship', 128000, false, true, 0, true, true, true, true, '673f1787-8474-4e1c-986c-8e19f14c989c'::uuid),
  ('gpt-4o-mini', 'GPT-4o Mini', 'Fast and affordable', 128000, true, true, 1, true, true, true, true, '673f1787-8474-4e1c-986c-8e19f14c989c'::uuid),
  ('gpt-4-turbo', 'GPT-4 Turbo', 'Previous generation flagship', 128000, false, true, 2, true, true, true, true, '673f1787-8474-4e1c-986c-8e19f14c989c'::uuid),
  ('gpt-3.5-turbo', 'GPT-3.5 Turbo', 'Fast and economical', 16385, false, true, 3, false, true, true, true, '673f1787-8474-4e1c-986c-8e19f14c989c'::uuid),
  ('o1', 'o1', 'Advanced reasoning', 200000, false, true, 4, true, false, true, false, '673f1787-8474-4e1c-986c-8e19f14c989c'::uuid),
  ('o1-mini', 'o1 Mini', 'Faster reasoning', 128000, false, true, 5, false, false, true, false, '673f1787-8474-4e1c-986c-8e19f14c989c'::uuid),
  ('claude-sonnet-4-20250514', 'Claude Sonnet 4', 'Latest balanced model', 200000, false, true, 0, true, true, true, true, '008dc763-4309-43cd-ba5f-1eb1323a0964'::uuid),
  ('claude-3-5-sonnet-latest', 'Claude 3.5 Sonnet', 'Previous Sonnet', 200000, false, true, 1, true, true, true, true, '008dc763-4309-43cd-ba5f-1eb1323a0964'::uuid),
  ('claude-3-5-haiku-latest', 'Claude 3.5 Haiku', 'Fast and affordable', 200000, true, true, 2, true, true, true, true, '008dc763-4309-43cd-ba5f-1eb1323a0964'::uuid),
  ('claude-3-opus-latest', 'Claude 3 Opus', 'Most capable', 200000, false, true, 3, true, true, true, true, '008dc763-4309-43cd-ba5f-1eb1323a0964'::uuid),
  ('gemini-2.0-flash', 'Gemini 2.0 Flash', 'Latest fast model', 1048576, false, true, 0, true, true, true, true, 'ae07eb0b-929e-4844-8b75-4fe6abca09df'::uuid),
  ('gemini-1.5-pro', 'Gemini 1.5 Pro', 'Long context flagship', 2097152, false, true, 1, true, true, true, true, 'ae07eb0b-929e-4844-8b75-4fe6abca09df'::uuid),
  ('gemini-1.5-flash', 'Gemini 1.5 Flash', 'Fast and capable', 1048576, true, true, 2, true, true, true, true, 'ae07eb0b-929e-4844-8b75-4fe6abca09df'::uuid)
) AS v(model_id, display_name, description, context_window, is_default, is_enabled, sort_order, has_vision, has_function_calling, has_streaming, has_json_mode, primary_provider_type_id)
ON CONFLICT (primary_provider_type_id, model_id) DO NOTHING;
