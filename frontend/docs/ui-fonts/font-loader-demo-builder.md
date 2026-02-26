  I've implemented the complete font loading system for the demo presentation system. Here's what was done:

  Files Modified
  ┌────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                    File                    │                                              Changes                                               │
  ├────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ demoBuilderCapabilityRegistry.ts:1074-1189 │ Added typography.fonts.v1 capability pack with font presets and field specs                        │
  ├────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ demoPresentationResolver.ts                │ Added resolveFontStyle() function + updated resolveDemoPresentationFrame() to include fontFamilies │
  ├────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ DemoPresentationFrame.tsx                  │ Added useFontLoader() hook for dynamic Google Fonts loading                                        │
  ├────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ demo-themes.css:1524-1628                  │ Added CSS rules for --font-heading and --font-body consumption                                     │
  ├────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ presentation-customization-roadmap.md      │ Updated to reflect completed implementation                                                        │
  └────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────┘
  Architecture

  The implementation follows the existing patterns as you requested:

  1. Capability Pack - Defines available font presets via BuilderCapabilityRegistryPack, making them discoverable in the builder UI
  2. Presentation Resolver - Resolves font values to CSS custom properties (--font-heading, --font-body)
  3. Presentation Frame - Dynamically loads Google Fonts via useFontLoader() hook
  4. CSS Consumption - Rules in demo-themes.css apply the variables to appropriate elements

  Available Font Presets

  - system (uses default --font-sans stack)
  - Inter
  - Space Grotesk
  - IBM Plex Sans
  - JetBrains Mono
  - Playfair Display
  - Source Sans Pro
  - Lora
  - Fira Code
  - Work Sans

  Extensibility

  To add new fonts:
  1. Add the font name to TYPOGRAPHY_FONT_PRESETS in demoBuilderCapabilityRegistry.ts
  2. The font loader automatically fetches it from Google Fonts when used

  To enable the typography pack:
  VITE_DEMO_BUILDER_PACKS=typography.fonts.v1