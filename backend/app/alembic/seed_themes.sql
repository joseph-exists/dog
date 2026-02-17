-- Seed system themes for the theme registry
-- Run with: psql -d your_database -f seed_themes.sql

-- =============================================================================
-- Page Themes (category: page)
-- =============================================================================

INSERT INTO theme (id, name, description, category, scope, owner_id, is_system, tokens, created_at, updated_at)
VALUES
  (
    'a0000000-0000-0000-0000-000000000001',
    'Default',
    'Application default theme (inherits from :root CSS variables)',
    'page',
    'system',
    NULL,
    true,
    '{}',
    NOW(),
    NOW()
  ),
  (
    'a0000000-0000-0000-0000-000000000002',
    'Midnight',
    'Deep blue dark theme',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "222 47% 11%",
      "--foreground": "210 40% 98%",
      "--card": "222 47% 14%",
      "--card-foreground": "210 40% 98%",
      "--border": "217 33% 25%",
      "--muted": "217 33% 20%",
      "--muted-foreground": "215 20% 65%",
      "--secondary": "217 33% 18%",
      "--secondary-foreground": "210 40% 98%",
      "--accent": "217 91% 60%",
      "--accent-foreground": "210 40% 98%"
    }',
    NOW(),
    NOW()
  ),
  (
    'a0000000-0000-0000-0000-000000000003',
    'Warm Sand',
    'Warm light theme with sandy tones',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "39 40% 96%",
      "--foreground": "20 14% 15%",
      "--card": "39 40% 100%",
      "--card-foreground": "20 14% 15%",
      "--border": "30 20% 85%",
      "--muted": "30 20% 92%",
      "--muted-foreground": "20 10% 45%",
      "--secondary": "30 25% 88%",
      "--secondary-foreground": "20 14% 15%",
      "--accent": "25 95% 53%",
      "--accent-foreground": "39 40% 98%"
    }',
    NOW(),
    NOW()
  ),
  (
    'a0000000-0000-0000-0000-000000000004',
    'Forest',
    'Green-tinted dark theme',
    'page',
    'system',
    NULL,
    true,
    '{
      "--background": "150 20% 10%",
      "--foreground": "140 20% 95%",
      "--card": "150 20% 13%",
      "--card-foreground": "140 20% 95%",
      "--border": "150 15% 22%",
      "--muted": "150 15% 18%",
      "--muted-foreground": "140 10% 60%",
      "--secondary": "150 15% 16%",
      "--secondary-foreground": "140 20% 95%",
      "--accent": "142 71% 45%",
      "--accent-foreground": "150 20% 10%"
    }',
    NOW(),
    NOW()
  )
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- Card Themes (category: card)
-- =============================================================================

INSERT INTO theme (id, name, description, category, scope, owner_id, is_system, tokens, created_at, updated_at)
VALUES
  (
    'b0000000-0000-0000-0000-000000000001',
    'Default',
    'Inherit from page theme (no overrides)',
    'card',
    'system',
    NULL,
    true,
    '{}',
    NOW(),
    NOW()
  ),
  (
    'b0000000-0000-0000-0000-000000000002',
    'Oracle',
    'Purple-tinted card surfaces',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "270 50% 15%",
      "--card-foreground": "270 20% 95%",
      "--border": "270 30% 25%",
      "--muted": "270 30% 20%",
      "--muted-foreground": "270 15% 65%",
      "--secondary": "270 30% 18%",
      "--secondary-foreground": "270 20% 95%",
      "--accent": "270 91% 65%",
      "--accent-foreground": "270 20% 98%"
    }',
    NOW(),
    NOW()
  ),
  (
    'b0000000-0000-0000-0000-000000000003',
    'Ember',
    'Warm amber card surfaces',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "25 50% 14%",
      "--card-foreground": "30 20% 95%",
      "--border": "25 35% 25%",
      "--muted": "25 35% 20%",
      "--muted-foreground": "25 15% 60%",
      "--secondary": "25 35% 18%",
      "--secondary-foreground": "30 20% 95%",
      "--accent": "25 95% 55%",
      "--accent-foreground": "25 50% 10%"
    }',
    NOW(),
    NOW()
  ),
  (
    'b0000000-0000-0000-0000-000000000004',
    'Arctic',
    'Cool blue-gray card surfaces',
    'card',
    'system',
    NULL,
    true,
    '{
      "--card": "210 30% 15%",
      "--card-foreground": "210 20% 95%",
      "--border": "210 20% 25%",
      "--muted": "210 20% 20%",
      "--muted-foreground": "210 10% 60%",
      "--secondary": "210 20% 18%",
      "--secondary-foreground": "210 20% 95%",
      "--accent": "200 80% 55%",
      "--accent-foreground": "210 30% 10%"
    }',
    NOW(),
    NOW()
  )
ON CONFLICT (id) DO NOTHING;


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
  )
ON CONFLICT (id) DO NOTHING;


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
  )
ON CONFLICT (id) DO NOTHING;


-- Verification query
SELECT category, name, is_system FROM theme WHERE is_system = true ORDER BY category, name;
