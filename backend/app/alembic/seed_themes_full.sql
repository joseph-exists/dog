-- Full seed system themes for the theme registry
-- Migrated from frontend TypeScript theme definitions
-- Run with: psql -d your_database -f seed_themes_full.sql

-- =============================================================================
-- Page Themes (category: page)
-- =============================================================================

INSERT INTO theme (id, name, description, category, scope, owner_id, is_system, tokens, created_at, updated_at)
VALUES
  -- Default
  (
    'a0000000-0000-0000-0000-000000000001',
    'Default',
    'Application theme',
    'page',
    'system',
    NULL,
    true,
    '{}',
    NOW(),
    NOW()
  ),
  -- Midnight
  (
    'a0000000-0000-0000-0000-000000000002',
    'Midnight',
    'Deep blue-violet dark surface',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.15 0.03 280)",
      "--card": "oklch(0.18 0.03 280)",
      "--card-foreground": "oklch(0.92 0.01 280)",
      "--foreground": "oklch(0.90 0.01 280)",
      "--border": "oklch(0.28 0.03 280)",
      "--muted": "oklch(0.22 0.03 280)",
      "--muted-foreground": "oklch(0.62 0.02 280)",
      "--secondary": "oklch(0.25 0.04 280)",
      "--secondary-foreground": "oklch(0.88 0.01 280)",
      "--accent": "oklch(0.30 0.04 280)",
      "--accent-foreground": "oklch(0.92 0.01 280)"
    }',
    NOW(),
    NOW()
  ),
  -- Warm Sand
  (
    'a0000000-0000-0000-0000-000000000003',
    'Warm Sand',
    'Warm neutral light surface',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.97 0.02 75)",
      "--card": "oklch(0.95 0.02 75)",
      "--card-foreground": "oklch(0.20 0.02 75)",
      "--foreground": "oklch(0.18 0.02 75)",
      "--border": "oklch(0.85 0.03 75)",
      "--muted": "oklch(0.90 0.02 75)",
      "--muted-foreground": "oklch(0.45 0.02 75)",
      "--secondary": "oklch(0.88 0.03 75)",
      "--secondary-foreground": "oklch(0.25 0.02 75)",
      "--accent": "oklch(0.90 0.04 75)",
      "--accent-foreground": "oklch(0.20 0.02 75)"
    }',
    NOW(),
    NOW()
  ),
  -- Forest
  (
    'a0000000-0000-0000-0000-000000000004',
    'Forest',
    'Dark green surface',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.13 0.04 155)",
      "--card": "oklch(0.16 0.04 155)",
      "--card-foreground": "oklch(0.92 0.02 155)",
      "--foreground": "oklch(0.90 0.02 155)",
      "--border": "oklch(0.26 0.04 155)",
      "--muted": "oklch(0.20 0.03 155)",
      "--muted-foreground": "oklch(0.62 0.03 155)",
      "--secondary": "oklch(0.23 0.04 155)",
      "--secondary-foreground": "oklch(0.88 0.02 155)",
      "--accent": "oklch(0.28 0.05 155)",
      "--accent-foreground": "oklch(0.92 0.02 155)"
    }',
    NOW(),
    NOW()
  ),
  -- Cool Ocean
  (
    'a0000000-0000-0000-0000-000000000005',
    'Cool Ocean',
    'Cool blue-tinted light surface',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.98 0.01 230)",
      "--card": "oklch(0.97 0.015 230)",
      "--card-foreground": "oklch(0.15 0.03 230)",
      "--foreground": "oklch(0.15 0.03 230)",
      "--border": "oklch(0.88 0.02 230)",
      "--muted": "oklch(0.94 0.01 230)",
      "--muted-foreground": "oklch(0.5 0.02 230)",
      "--secondary": "oklch(0.93 0.015 230)",
      "--secondary-foreground": "oklch(0.2 0.03 230)",
      "--accent": "oklch(0.93 0.015 230)",
      "--accent-foreground": "oklch(0.2 0.03 230)"
    }',
    NOW(),
    NOW()
  ),
  -- Slate
  (
    'a0000000-0000-0000-0000-000000000006',
    'Slate',
    'Cool neutral dark surface',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.17 0.01 250)",
      "--card": "oklch(0.20 0.01 250)",
      "--card-foreground": "oklch(0.90 0.01 250)",
      "--foreground": "oklch(0.88 0.01 250)",
      "--border": "oklch(0.30 0.01 250)",
      "--muted": "oklch(0.24 0.01 250)",
      "--muted-foreground": "oklch(0.60 0.01 250)",
      "--secondary": "oklch(0.27 0.01 250)",
      "--secondary-foreground": "oklch(0.86 0.01 250)",
      "--accent": "oklch(0.32 0.02 250)",
      "--accent-foreground": "oklch(0.90 0.01 250)"
    }',
    NOW(),
    NOW()
  ),
  -- Enchanted Rose
  (
    'a0000000-0000-0000-0000-000000000007',
    'Enchanted Rose',
    'Warm romantic pink tones',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.97 0.02 350)",
      "--card": "oklch(0.95 0.03 350)",
      "--card-foreground": "oklch(0.30 0.12 350)",
      "--foreground": "oklch(0.28 0.10 350)",
      "--border": "oklch(0.80 0.10 350)",
      "--muted": "oklch(0.92 0.04 350)",
      "--muted-foreground": "oklch(0.45 0.08 350)",
      "--secondary": "oklch(0.90 0.06 350)",
      "--secondary-foreground": "oklch(0.32 0.10 350)",
      "--accent": "oklch(0.70 0.15 350)",
      "--accent-foreground": "oklch(0.98 0.01 350)"
    }',
    NOW(),
    NOW()
  ),
  -- Dark Forest
  (
    'a0000000-0000-0000-0000-000000000008',
    'Dark Forest',
    'Moody emerald and amber',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.15 0.04 160)",
      "--card": "oklch(0.22 0.05 160)",
      "--card-foreground": "oklch(0.92 0.04 160)",
      "--foreground": "oklch(0.85 0.04 160)",
      "--border": "oklch(0.35 0.06 160)",
      "--muted": "oklch(0.25 0.04 160)",
      "--muted-foreground": "oklch(0.65 0.05 160)",
      "--secondary": "oklch(0.28 0.05 160)",
      "--secondary-foreground": "oklch(0.88 0.04 160)",
      "--accent": "oklch(0.55 0.12 160)",
      "--accent-foreground": "oklch(0.95 0.02 160)"
    }',
    NOW(),
    NOW()
  ),
  -- Ancient Tome
  (
    'a0000000-0000-0000-0000-000000000009',
    'Ancient Tome',
    'Parchment sepia tones',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.96 0.02 80)",
      "--card": "oklch(0.94 0.03 80)",
      "--card-foreground": "oklch(0.28 0.05 45)",
      "--foreground": "oklch(0.22 0.04 45)",
      "--border": "oklch(0.65 0.10 45)",
      "--muted": "oklch(0.90 0.04 80)",
      "--muted-foreground": "oklch(0.45 0.06 45)",
      "--secondary": "oklch(0.88 0.05 80)",
      "--secondary-foreground": "oklch(0.30 0.05 45)",
      "--accent": "oklch(0.60 0.12 45)",
      "--accent-foreground": "oklch(0.95 0.02 80)"
    }',
    NOW(),
    NOW()
  ),
  -- Gruvbox
  (
    'a0000000-0000-0000-0000-000000000010',
    'Gruvbox',
    'Classic warm retro palette',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.22 0.02 60)",
      "--card": "oklch(0.28 0.02 60)",
      "--card-foreground": "oklch(0.88 0.04 80)",
      "--foreground": "oklch(0.85 0.03 80)",
      "--border": "oklch(0.38 0.02 60)",
      "--muted": "oklch(0.32 0.02 60)",
      "--muted-foreground": "oklch(0.60 0.02 60)",
      "--secondary": "oklch(0.35 0.02 60)",
      "--secondary-foreground": "oklch(0.82 0.03 80)",
      "--accent": "oklch(0.65 0.15 45)",
      "--accent-foreground": "oklch(0.92 0.02 80)"
    }',
    NOW(),
    NOW()
  ),
  -- Dracula
  (
    'a0000000-0000-0000-0000-000000000011',
    'Dracula',
    'Rich purples and soft pinks',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.22 0.03 280)",
      "--card": "oklch(0.32 0.03 280)",
      "--card-foreground": "oklch(0.95 0.01 0)",
      "--foreground": "oklch(0.95 0.01 0)",
      "--border": "oklch(0.45 0.04 260)",
      "--muted": "oklch(0.35 0.03 280)",
      "--muted-foreground": "oklch(0.55 0.04 260)",
      "--secondary": "oklch(0.40 0.03 280)",
      "--secondary-foreground": "oklch(0.92 0.01 0)",
      "--accent": "oklch(0.70 0.18 300)",
      "--accent-foreground": "oklch(0.98 0.01 0)"
    }',
    NOW(),
    NOW()
  ),
  -- Bauhaus
  (
    'a0000000-0000-0000-0000-000000000012',
    'Bauhaus',
    'Bold primary colors, geometric',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.96 0 0)",
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.15 0 0)",
      "--foreground": "oklch(0.15 0 0)",
      "--border": "oklch(0.15 0 0)",
      "--muted": "oklch(0.95 0 0)",
      "--muted-foreground": "oklch(0.40 0 0)",
      "--secondary": "oklch(0.85 0.20 90)",
      "--secondary-foreground": "oklch(0.15 0 0)",
      "--accent": "oklch(0.55 0.22 30)",
      "--accent-foreground": "oklch(1 0 0)"
    }',
    NOW(),
    NOW()
  ),
  -- Dekonstruct
  (
    'a0000000-0000-0000-0000-000000000013',
    'Dekonstruct',
    'Fragmented brutalist aesthetic',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.94 0 0)",
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.12 0 0)",
      "--foreground": "oklch(0.25 0 0)",
      "--border": "oklch(0.12 0 0)",
      "--muted": "oklch(0.95 0 0)",
      "--muted-foreground": "oklch(0.45 0 0)",
      "--secondary": "oklch(0.90 0 0)",
      "--secondary-foreground": "oklch(0.15 0 0)",
      "--accent": "oklch(0.55 0.22 25)",
      "--accent-foreground": "oklch(1 0 0)"
    }',
    NOW(),
    NOW()
  ),
  -- Medieval
  (
    'a0000000-0000-0000-0000-000000000014',
    'Medieval',
    'Illuminated manuscript style',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.93 0.03 70)",
      "--card": "oklch(0.95 0.03 70)",
      "--card-foreground": "oklch(0.25 0.08 30)",
      "--foreground": "oklch(0.20 0.06 30)",
      "--border": "oklch(0.70 0.12 70)",
      "--muted": "oklch(0.92 0.03 70)",
      "--muted-foreground": "oklch(0.45 0.06 45)",
      "--secondary": "oklch(0.22 0.04 280)",
      "--secondary-foreground": "oklch(0.80 0.10 70)",
      "--accent": "oklch(0.45 0.15 30)",
      "--accent-foreground": "oklch(0.95 0.02 70)"
    }',
    NOW(),
    NOW()
  ),
  -- Math
  (
    'a0000000-0000-0000-0000-000000000015',
    'Math',
    'LaTeX-inspired academic',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.99 0 0)",
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.15 0 0)",
      "--foreground": "oklch(0.25 0 0)",
      "--border": "oklch(0.80 0 0)",
      "--muted": "oklch(0.97 0 0)",
      "--muted-foreground": "oklch(0.50 0 0)",
      "--secondary": "oklch(0.96 0.01 230)",
      "--secondary-foreground": "oklch(0.35 0.08 230)",
      "--accent": "oklch(0.55 0.15 250)",
      "--accent-foreground": "oklch(0.98 0 0)"
    }',
    NOW(),
    NOW()
  ),
  -- Technorave
  (
    'a0000000-0000-0000-0000-000000000016',
    'Technorave',
    'Cyberpunk neon on black',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.08 0 0)",
      "--card": "oklch(0.12 0 0)",
      "--card-foreground": "oklch(0.90 0 0)",
      "--foreground": "oklch(0.90 0 0)",
      "--border": "oklch(0.60 0.25 190)",
      "--muted": "oklch(0.15 0 0)",
      "--muted-foreground": "oklch(0.55 0 0)",
      "--secondary": "oklch(0.15 0 0)",
      "--secondary-foreground": "oklch(0.75 0.25 330)",
      "--accent": "oklch(0.70 0.25 330)",
      "--accent-foreground": "oklch(1 0 0)"
    }',
    NOW(),
    NOW()
  ),
  -- Spiritual Math
  (
    'a0000000-0000-0000-0000-000000000017',
    'Spiritual Math',
    'Sacred geometry meets mathematics',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.18 0.05 280)",
      "--card": "oklch(0.25 0.05 280)",
      "--card-foreground": "oklch(0.85 0.05 260)",
      "--foreground": "oklch(0.80 0.05 260)",
      "--border": "oklch(0.65 0.12 70)",
      "--muted": "oklch(0.28 0.04 280)",
      "--muted-foreground": "oklch(0.65 0.06 260)",
      "--secondary": "oklch(0.30 0.05 280)",
      "--secondary-foreground": "oklch(0.82 0.05 260)",
      "--accent": "oklch(0.72 0.12 70)",
      "--accent-foreground": "oklch(0.15 0.04 280)"
    }',
    NOW(),
    NOW()
  ),
  -- Terminal
  (
    'a0000000-0000-0000-0000-000000000018',
    'Terminal',
    'Green phosphor CRT aesthetic',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.08 0.01 145)",
      "--card": "oklch(0.12 0.02 145)",
      "--card-foreground": "oklch(0.75 0.20 145)",
      "--foreground": "oklch(0.70 0.18 145)",
      "--border": "oklch(0.35 0.10 145)",
      "--muted": "oklch(0.15 0.02 145)",
      "--muted-foreground": "oklch(0.50 0.12 145)",
      "--secondary": "oklch(0.18 0.03 145)",
      "--secondary-foreground": "oklch(0.72 0.18 145)",
      "--accent": "oklch(0.75 0.22 145)",
      "--accent-foreground": "oklch(0.12 0.02 145)"
    }',
    NOW(),
    NOW()
  ),
  -- Vaporwave
  (
    'a0000000-0000-0000-0000-000000000019',
    'Vaporwave',
    'Retro-futurist pastels',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "oklch(0.15 0.06 310)",
      "--card": "oklch(0.22 0.08 310)",
      "--card-foreground": "oklch(0.88 0.06 300)",
      "--foreground": "oklch(0.85 0.05 300)",
      "--border": "oklch(0.55 0.18 310)",
      "--muted": "oklch(0.25 0.06 310)",
      "--muted-foreground": "oklch(0.60 0.10 310)",
      "--secondary": "oklch(0.28 0.07 310)",
      "--secondary-foreground": "oklch(0.82 0.05 300)",
      "--accent": "oklch(0.70 0.22 350)",
      "--accent-foreground": "oklch(1 0 0)"
    }',
    NOW(),
    NOW()
  )
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  tokens = EXCLUDED.tokens,
  updated_at = NOW();


-- =============================================================================
-- Card Themes (category: card)
-- =============================================================================

INSERT INTO theme (id, name, description, category, scope, owner_id, is_system, tokens, created_at, updated_at)
VALUES
  -- Default (Upstream)
  (
    'b0000000-0000-0000-0000-000000000001',
    'Upstream',
    'Inherit from page theme',
    'card',
    'system',
    NULL,
    true,
    '{}',
    NOW(),
    NOW()
  ),
  -- Midnight
  (
    'b0000000-0000-0000-0000-000000000002',
    'Midnight',
    'Deep blue-violet dark surface',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.18 0.03 280)",
      "--card-foreground": "oklch(0.92 0.01 280)",
      "--foreground": "oklch(0.90 0.01 280)",
      "--border": "oklch(0.28 0.03 280)",
      "--muted": "oklch(0.22 0.03 280)",
      "--muted-foreground": "oklch(0.62 0.02 280)",
      "--secondary": "oklch(0.25 0.04 280)",
      "--secondary-foreground": "oklch(0.88 0.01 280)",
      "--accent": "oklch(0.30 0.04 280)",
      "--accent-foreground": "oklch(0.92 0.01 280)"
    }',
    NOW(),
    NOW()
  ),
  -- Warm Sand
  (
    'b0000000-0000-0000-0000-000000000003',
    'Warm Sand',
    'Warm neutral light surface',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.95 0.02 75)",
      "--card-foreground": "oklch(0.20 0.02 75)",
      "--foreground": "oklch(0.18 0.02 75)",
      "--border": "oklch(0.85 0.03 75)",
      "--muted": "oklch(0.90 0.02 75)",
      "--muted-foreground": "oklch(0.45 0.02 75)",
      "--secondary": "oklch(0.88 0.03 75)",
      "--secondary-foreground": "oklch(0.25 0.02 75)",
      "--accent": "oklch(0.90 0.04 75)",
      "--accent-foreground": "oklch(0.20 0.02 75)"
    }',
    NOW(),
    NOW()
  ),
  -- Forest
  (
    'b0000000-0000-0000-0000-000000000004',
    'Forest',
    'Dark green surface',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.16 0.04 155)",
      "--card-foreground": "oklch(0.92 0.02 155)",
      "--foreground": "oklch(0.90 0.02 155)",
      "--border": "oklch(0.26 0.04 155)",
      "--muted": "oklch(0.20 0.03 155)",
      "--muted-foreground": "oklch(0.62 0.03 155)",
      "--secondary": "oklch(0.23 0.04 155)",
      "--secondary-foreground": "oklch(0.88 0.02 155)",
      "--accent": "oklch(0.28 0.05 155)",
      "--accent-foreground": "oklch(0.92 0.02 155)"
    }',
    NOW(),
    NOW()
  ),
  -- Cool Ocean
  (
    'b0000000-0000-0000-0000-000000000005',
    'Cool Ocean',
    'Cool blue-tinted light surface',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.97 0.015 230)",
      "--card-foreground": "oklch(0.15 0.03 230)",
      "--foreground": "oklch(0.15 0.03 230)",
      "--border": "oklch(0.88 0.02 230)",
      "--muted": "oklch(0.94 0.01 230)",
      "--muted-foreground": "oklch(0.5 0.02 230)",
      "--secondary": "oklch(0.93 0.015 230)",
      "--secondary-foreground": "oklch(0.2 0.03 230)",
      "--accent": "oklch(0.93 0.015 230)",
      "--accent-foreground": "oklch(0.2 0.03 230)"
    }',
    NOW(),
    NOW()
  ),
  -- Slate
  (
    'b0000000-0000-0000-0000-000000000006',
    'Slate',
    'Cool neutral dark surface',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.20 0.01 250)",
      "--card-foreground": "oklch(0.90 0.01 250)",
      "--foreground": "oklch(0.88 0.01 250)",
      "--border": "oklch(0.30 0.01 250)",
      "--muted": "oklch(0.24 0.01 250)",
      "--muted-foreground": "oklch(0.60 0.01 250)",
      "--secondary": "oklch(0.27 0.01 250)",
      "--secondary-foreground": "oklch(0.86 0.01 250)",
      "--accent": "oklch(0.32 0.02 250)",
      "--accent-foreground": "oklch(0.90 0.01 250)"
    }',
    NOW(),
    NOW()
  ),
  -- Oracle
  (
    'b0000000-0000-0000-0000-000000000007',
    'Oracle',
    'Mystical green with organic feel',
    'card',
    'system',
    NULL,
    true,
    '{
      "--agent-accent": "oklch(0.6 0.15 150)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.97 0.015 145)",
      "--card-foreground": "oklch(0.18 0.03 150)",
      "--border": "oklch(0.85 0.03 145)",
      "--muted": "oklch(0.93 0.01 145)",
      "--muted-foreground": "oklch(0.5 0.02 150)",
      "--agent-card-shadow": "0 6px 24px oklch(0.5 0.1 150 / 0.07), 0 2px 6px oklch(0.5 0.08 150 / 0.04)",
      "--agent-card-radius": "20px",
      "--agent-accent-position": "top",
      "--agent-accent-width": "3px"
    }',
    NOW(),
    NOW()
  ),
  -- Whisper
  (
    'b0000000-0000-0000-0000-000000000008',
    'Whisper',
    'Soft ethereal lavender',
    'card',
    'system',
    NULL,
    true,
    '{
      "--agent-accent": "oklch(0.65 0.1 290)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.98 0.008 290)",
      "--card-foreground": "oklch(0.25 0.02 290)",
      "--border": "oklch(0.92 0.015 290)",
      "--muted": "oklch(0.96 0.006 290)",
      "--muted-foreground": "oklch(0.55 0.03 290)",
      "--agent-card-shadow": "0 8px 32px oklch(0.5 0.08 290 / 0.05)",
      "--agent-card-radius": "24px",
      "--agent-accent-position": "none",
      "--agent-accent-width": "0px"
    }',
    NOW(),
    NOW()
  ),
  -- Precise
  (
    'b0000000-0000-0000-0000-000000000009',
    'Precise',
    'Clean analytical blue',
    'card',
    'system',
    NULL,
    true,
    '{
      "--agent-accent": "oklch(0.5 0.08 240)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.97 0.01 80)",
      "--card-foreground": "oklch(0.18 0.02 240)",
      "--border": "oklch(0.84 0.02 240)",
      "--muted": "oklch(0.94 0.008 80)",
      "--muted-foreground": "oklch(0.5 0.02 240)",
      "--agent-card-shadow": "0 1px 2px oklch(0.4 0.04 240 / 0.06)",
      "--agent-card-radius": "2px",
      "--agent-accent-position": "bottom",
      "--agent-accent-width": "2px"
    }',
    NOW(),
    NOW()
  ),
  -- Neon
  (
    'b0000000-0000-0000-0000-000000000010',
    'Neon',
    'Electric cyberpunk glow',
    'card',
    'system',
    NULL,
    true,
    '{
      "--agent-accent": "oklch(0.7 0.25 340)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.18 0.04 300)",
      "--card-foreground": "oklch(0.92 0.02 320)",
      "--border": "oklch(0.32 0.08 340)",
      "--muted": "oklch(0.22 0.03 300)",
      "--muted-foreground": "oklch(0.6 0.04 320)",
      "--secondary": "oklch(0.25 0.05 310)",
      "--secondary-foreground": "oklch(0.85 0.06 330)",
      "--foreground": "oklch(0.92 0.02 320)",
      "--agent-card-shadow": "0 0 25px oklch(0.65 0.25 340 / 0.12), 0 0 5px oklch(0.7 0.2 340 / 0.08)",
      "--agent-card-radius": "4px",
      "--agent-accent-position": "left",
      "--agent-accent-width": "4px"
    }',
    NOW(),
    NOW()
  ),
  -- Armadillo
  (
    'b0000000-0000-0000-0000-000000000011',
    'Armadillo',
    'Warm amber protective shell',
    'card',
    'system',
    NULL,
    true,
    '{
      "--agent-accent": "oklch(0.65 0.14 55)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.96 0.015 60)",
      "--card-foreground": "oklch(0.2 0.02 50)",
      "--border": "oklch(0.85 0.04 55)",
      "--muted": "oklch(0.92 0.01 55)",
      "--muted-foreground": "oklch(0.5 0.02 50)",
      "--agent-card-shadow": "0 4px 20px oklch(0.5 0.1 55 / 0.1), 0 1px 3px oklch(0.5 0.08 55 / 0.06)",
      "--agent-card-radius": "14px",
      "--agent-accent-position": "top",
      "--agent-accent-width": "3px"
    }',
    NOW(),
    NOW()
  ),
  -- Axiom
  (
    'b0000000-0000-0000-0000-000000000012',
    'Axiom',
    'Brutalist black and yellow',
    'card',
    'system',
    NULL,
    true,
    '{
      "--agent-accent": "oklch(0.85 0.17 90)",
      "--agent-accent-foreground": "oklch(0.15 0 0)",
      "--card": "oklch(0.97 0 0)",
      "--card-foreground": "oklch(0.12 0 0)",
      "--border": "oklch(0.7 0 0)",
      "--muted": "oklch(0.93 0 0)",
      "--muted-foreground": "oklch(0.45 0 0)",
      "--agent-card-shadow": "6px 6px 0 oklch(0.55 0.25 29)",
      "--agent-card-radius": "0px",
      "--agent-accent-position": "left",
      "--agent-accent-width": "6px"
    }',
    NOW(),
    NOW()
  ),
  -- Enchanted Rose
  (
    'b0000000-0000-0000-0000-000000000013',
    'Enchanted Rose',
    'Warm romantic pink tones',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.95 0.03 350)",
      "--card-foreground": "oklch(0.30 0.12 350)",
      "--foreground": "oklch(0.28 0.10 350)",
      "--border": "oklch(0.80 0.10 350)",
      "--muted": "oklch(0.92 0.04 350)",
      "--muted-foreground": "oklch(0.45 0.08 350)",
      "--secondary": "oklch(0.90 0.06 350)",
      "--secondary-foreground": "oklch(0.32 0.10 350)",
      "--accent": "oklch(0.70 0.15 350)",
      "--accent-foreground": "oklch(0.98 0.01 350)",
      "--agent-card-shadow": "0 2px 8px oklch(0.65 0.15 350 / 0.12)",
      "--agent-card-radius": "12px"
    }',
    NOW(),
    NOW()
  ),
  -- Dark Forest
  (
    'b0000000-0000-0000-0000-000000000014',
    'Dark Forest',
    'Moody emerald and amber',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.22 0.05 160)",
      "--card-foreground": "oklch(0.92 0.04 160)",
      "--foreground": "oklch(0.85 0.04 160)",
      "--border": "oklch(0.35 0.06 160)",
      "--muted": "oklch(0.25 0.04 160)",
      "--muted-foreground": "oklch(0.65 0.05 160)",
      "--secondary": "oklch(0.28 0.05 160)",
      "--secondary-foreground": "oklch(0.88 0.04 160)",
      "--accent": "oklch(0.55 0.12 160)",
      "--accent-foreground": "oklch(0.95 0.02 160)",
      "--agent-card-shadow": "0 2px 8px oklch(0.35 0.08 160 / 0.2)",
      "--agent-card-radius": "8px"
    }',
    NOW(),
    NOW()
  ),
  -- Ancient Tome
  (
    'b0000000-0000-0000-0000-000000000015',
    'Ancient Tome',
    'Parchment sepia tones',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.94 0.03 80)",
      "--card-foreground": "oklch(0.28 0.05 45)",
      "--foreground": "oklch(0.22 0.04 45)",
      "--border": "oklch(0.65 0.10 45)",
      "--muted": "oklch(0.90 0.04 80)",
      "--muted-foreground": "oklch(0.45 0.06 45)",
      "--secondary": "oklch(0.88 0.05 80)",
      "--secondary-foreground": "oklch(0.30 0.05 45)",
      "--accent": "oklch(0.60 0.12 45)",
      "--accent-foreground": "oklch(0.95 0.02 80)",
      "--agent-card-radius": "4px"
    }',
    NOW(),
    NOW()
  ),
  -- Gruvbox
  (
    'b0000000-0000-0000-0000-000000000016',
    'Gruvbox',
    'Classic warm retro palette',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.28 0.02 60)",
      "--card-foreground": "oklch(0.88 0.04 80)",
      "--foreground": "oklch(0.85 0.03 80)",
      "--border": "oklch(0.38 0.02 60)",
      "--muted": "oklch(0.32 0.02 60)",
      "--muted-foreground": "oklch(0.60 0.02 60)",
      "--secondary": "oklch(0.35 0.02 60)",
      "--secondary-foreground": "oklch(0.82 0.03 80)",
      "--accent": "oklch(0.65 0.15 45)",
      "--accent-foreground": "oklch(0.92 0.02 80)",
      "--agent-card-shadow": "0 2px 6px oklch(0.1 0 0 / 0.3)",
      "--agent-card-radius": "8px"
    }',
    NOW(),
    NOW()
  ),
  -- Dracula
  (
    'b0000000-0000-0000-0000-000000000017',
    'Dracula',
    'Rich purples and soft pinks',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.32 0.03 280)",
      "--card-foreground": "oklch(0.95 0.01 0)",
      "--foreground": "oklch(0.95 0.01 0)",
      "--border": "oklch(0.45 0.04 260)",
      "--muted": "oklch(0.35 0.03 280)",
      "--muted-foreground": "oklch(0.55 0.04 260)",
      "--secondary": "oklch(0.40 0.03 280)",
      "--secondary-foreground": "oklch(0.92 0.01 0)",
      "--accent": "oklch(0.70 0.18 300)",
      "--accent-foreground": "oklch(0.98 0.01 0)",
      "--agent-card-shadow": "0 2px 8px oklch(0.1 0 0 / 0.4)",
      "--agent-card-radius": "8px"
    }',
    NOW(),
    NOW()
  ),
  -- Bauhaus
  (
    'b0000000-0000-0000-0000-000000000018',
    'Bauhaus',
    'Bold primary colors, geometric',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.15 0 0)",
      "--foreground": "oklch(0.15 0 0)",
      "--border": "oklch(0.15 0 0)",
      "--muted": "oklch(0.95 0 0)",
      "--muted-foreground": "oklch(0.40 0 0)",
      "--secondary": "oklch(0.85 0.20 90)",
      "--secondary-foreground": "oklch(0.15 0 0)",
      "--accent": "oklch(0.55 0.22 30)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow": "6px 6px 0 oklch(0.15 0 0)",
      "--agent-card-radius": "0px"
    }',
    NOW(),
    NOW()
  ),
  -- Dekonstruct
  (
    'b0000000-0000-0000-0000-000000000019',
    'Dekonstruct',
    'Fragmented brutalist aesthetic',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.12 0 0)",
      "--foreground": "oklch(0.25 0 0)",
      "--border": "oklch(0.12 0 0)",
      "--muted": "oklch(0.95 0 0)",
      "--muted-foreground": "oklch(0.45 0 0)",
      "--secondary": "oklch(0.90 0 0)",
      "--secondary-foreground": "oklch(0.15 0 0)",
      "--accent": "oklch(0.55 0.22 25)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow": "8px 8px 0 oklch(0.12 0 0), -2px -2px 0 oklch(0.55 0.22 25)",
      "--agent-card-radius": "0px"
    }',
    NOW(),
    NOW()
  ),
  -- Medieval
  (
    'b0000000-0000-0000-0000-000000000020',
    'Medieval',
    'Illuminated manuscript style',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.95 0.03 70)",
      "--card-foreground": "oklch(0.25 0.08 30)",
      "--foreground": "oklch(0.20 0.06 30)",
      "--border": "oklch(0.45 0.15 30)",
      "--muted": "oklch(0.92 0.03 70)",
      "--muted-foreground": "oklch(0.45 0.06 45)",
      "--secondary": "oklch(0.22 0.04 280)",
      "--secondary-foreground": "oklch(0.80 0.10 70)",
      "--accent": "oklch(0.70 0.12 70)",
      "--accent-foreground": "oklch(0.20 0.06 30)",
      "--agent-card-radius": "2px"
    }',
    NOW(),
    NOW()
  ),
  -- Math
  (
    'b0000000-0000-0000-0000-000000000021',
    'Math',
    'LaTeX-inspired academic',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.15 0 0)",
      "--foreground": "oklch(0.25 0 0)",
      "--border": "oklch(0.80 0 0)",
      "--muted": "oklch(0.97 0 0)",
      "--muted-foreground": "oklch(0.50 0 0)",
      "--secondary": "oklch(0.96 0.01 230)",
      "--secondary-foreground": "oklch(0.35 0.08 230)",
      "--accent": "oklch(0.55 0.15 250)",
      "--accent-foreground": "oklch(0.98 0 0)",
      "--agent-card-radius": "0px"
    }',
    NOW(),
    NOW()
  ),
  -- Technorave
  (
    'b0000000-0000-0000-0000-000000000022',
    'Technorave',
    'Cyberpunk neon on black',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.12 0 0)",
      "--card-foreground": "oklch(0.90 0 0)",
      "--foreground": "oklch(0.90 0 0)",
      "--border": "oklch(0.60 0.25 190)",
      "--muted": "oklch(0.15 0 0)",
      "--muted-foreground": "oklch(0.55 0 0)",
      "--secondary": "oklch(0.15 0 0)",
      "--secondary-foreground": "oklch(0.75 0.25 330)",
      "--accent": "oklch(0.70 0.25 330)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow": "0 0 10px oklch(0.60 0.25 190 / 0.3)",
      "--agent-card-radius": "0px"
    }',
    NOW(),
    NOW()
  ),
  -- Spiritual Math
  (
    'b0000000-0000-0000-0000-000000000023',
    'Spiritual Math',
    'Sacred geometry meets mathematics',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.25 0.05 280)",
      "--card-foreground": "oklch(0.85 0.05 260)",
      "--foreground": "oklch(0.80 0.05 260)",
      "--border": "oklch(0.65 0.12 70)",
      "--muted": "oklch(0.28 0.04 280)",
      "--muted-foreground": "oklch(0.65 0.06 260)",
      "--secondary": "oklch(0.30 0.05 280)",
      "--secondary-foreground": "oklch(0.82 0.05 260)",
      "--accent": "oklch(0.72 0.12 70)",
      "--accent-foreground": "oklch(0.15 0.04 280)",
      "--agent-card-shadow": "0 4px 15px oklch(0.65 0.10 70 / 0.1)",
      "--agent-card-radius": "50% / 10%"
    }',
    NOW(),
    NOW()
  ),
  -- Terminal
  (
    'b0000000-0000-0000-0000-000000000024',
    'Terminal',
    'Green phosphor CRT aesthetic',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.12 0.02 145)",
      "--card-foreground": "oklch(0.75 0.20 145)",
      "--foreground": "oklch(0.70 0.18 145)",
      "--border": "oklch(0.35 0.10 145)",
      "--muted": "oklch(0.15 0.02 145)",
      "--muted-foreground": "oklch(0.50 0.12 145)",
      "--secondary": "oklch(0.18 0.03 145)",
      "--secondary-foreground": "oklch(0.72 0.18 145)",
      "--accent": "oklch(0.75 0.22 145)",
      "--accent-foreground": "oklch(0.12 0.02 145)",
      "--agent-card-shadow": "0 0 8px oklch(0.65 0.18 145 / 0.1)",
      "--agent-card-radius": "0px"
    }',
    NOW(),
    NOW()
  ),
  -- Vaporwave
  (
    'b0000000-0000-0000-0000-000000000025',
    'Vaporwave',
    'Retro-futurist pastels',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "oklch(0.22 0.08 310)",
      "--card-foreground": "oklch(0.88 0.06 300)",
      "--foreground": "oklch(0.85 0.05 300)",
      "--border": "oklch(0.55 0.18 310)",
      "--muted": "oklch(0.25 0.06 310)",
      "--muted-foreground": "oklch(0.60 0.10 310)",
      "--secondary": "oklch(0.28 0.07 310)",
      "--secondary-foreground": "oklch(0.82 0.05 300)",
      "--accent": "oklch(0.70 0.22 350)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow": "0 4px 20px oklch(0.55 0.18 310 / 0.15)",
      "--agent-card-radius": "16px"
    }',
    NOW(),
    NOW()
  )
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  tokens = EXCLUDED.tokens,
  updated_at = NOW();


-- =============================================================================
-- Syntax Themes (category: syntax)
-- =============================================================================

INSERT INTO theme (id, name, description, category, scope, owner_id, is_system, tokens, created_at, updated_at)
VALUES
  (
    'c0000000-0000-0000-0000-000000000001',
    'GitHub Dark',
    'Shiki built-in GitHub dark theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "github-dark"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000002',
    'GitHub Light',
    'Shiki built-in GitHub light theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "github-light"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000003',
    'One Dark Pro',
    'Shiki built-in One Dark Pro theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "one-dark-pro"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000004',
    'Dracula',
    'Shiki built-in Dracula theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "dracula"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000005',
    'Nord',
    'Shiki built-in Nord theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "nord"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000006',
    'Monokai',
    'Shiki built-in Monokai theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "monokai"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000007',
    'Solarized Dark',
    'Shiki built-in Solarized Dark theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "solarized-dark"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000008',
    'Solarized Light',
    'Shiki built-in Solarized Light theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "solarized-light"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000009',
    'Vitesse Dark',
    'Shiki built-in Vitesse Dark theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "vitesse-dark"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000010',
    'Vitesse Light',
    'Shiki built-in Vitesse Light theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "vitesse-light"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000011',
    'Tokyo Night',
    'Shiki built-in Tokyo Night theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "tokyo-night"}',
    NOW(),
    NOW()
  ),
  (
    'c0000000-0000-0000-0000-000000000012',
    'Material Theme',
    'Shiki built-in Material Theme',
    'syntax',
    'system',
    NULL,
    true,
    '{"shikiTheme": "material-theme"}',
    NOW(),
    NOW()
  )
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  tokens = EXCLUDED.tokens,
  updated_at = NOW();


-- =============================================================================
-- Motion Themes (category: motion)
-- =============================================================================

INSERT INTO theme (id, name, description, category, scope, owner_id, is_system, tokens, created_at, updated_at)
VALUES
  (
    'd0000000-0000-0000-0000-000000000001',
    'Default',
    'Standard animations',
    'motion',
    'system',
    NULL,
    true,
    '{
      "reducedMotion": false,
      "transitionDuration": "0.2s",
      "easingFunction": "ease-out",
      "springStiffness": 100,
      "springDamping": 10,
      "springMass": 1
    }',
    NOW(),
    NOW()
  ),
  (
    'd0000000-0000-0000-0000-000000000002',
    'Snappy',
    'Fast, crisp transitions',
    'motion',
    'system',
    NULL,
    true,
    '{
      "reducedMotion": false,
      "transitionDuration": "0.1s",
      "easingFunction": "ease-out",
      "springStiffness": 300,
      "springDamping": 25,
      "springMass": 0.5
    }',
    NOW(),
    NOW()
  ),
  (
    'd0000000-0000-0000-0000-000000000003',
    'Smooth',
    'Slower, flowing transitions',
    'motion',
    'system',
    NULL,
    true,
    '{
      "reducedMotion": false,
      "transitionDuration": "0.4s",
      "easingFunction": "ease-in-out",
      "springStiffness": 50,
      "springDamping": 8,
      "springMass": 1.5
    }',
    NOW(),
    NOW()
  ),
  (
    'd0000000-0000-0000-0000-000000000004',
    'Reduced',
    'Minimal motion for accessibility',
    'motion',
    'system',
    NULL,
    true,
    '{
      "reducedMotion": true,
      "transitionDuration": "0.01s",
      "easingFunction": "linear",
      "springStiffness": 1000,
      "springDamping": 100,
      "springMass": 1
    }',
    NOW(),
    NOW()
  ),
  (
    'd0000000-0000-0000-0000-000000000005',
    'Bouncy',
    'Playful spring animations',
    'motion',
    'system',
    NULL,
    true,
    '{
      "reducedMotion": false,
      "transitionDuration": "0.5s",
      "easingFunction": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
      "springStiffness": 180,
      "springDamping": 12,
      "springMass": 1
    }',
    NOW(),
    NOW()
  ),
  (
    'd0000000-0000-0000-0000-000000000006',
    'Elegant',
    'Refined, subtle movements',
    'motion',
    'system',
    NULL,
    true,
    '{
      "reducedMotion": false,
      "transitionDuration": "0.35s",
      "easingFunction": "cubic-bezier(0.4, 0, 0.2, 1)",
      "springStiffness": 120,
      "springDamping": 20,
      "springMass": 1
    }',
    NOW(),
    NOW()
  )
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  tokens = EXCLUDED.tokens,
  updated_at = NOW();


-- Verification query
SELECT category, COUNT(*) as count FROM theme WHERE is_system = true GROUP BY category ORDER BY category;
SELECT category, name FROM theme WHERE is_system = true ORDER BY category, name;
