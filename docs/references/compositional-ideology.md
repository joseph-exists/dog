  Use Cases by Engagement Level

  Level 0: No Engagement (System Defaults)

  - UC-0a: User creates a room. It renders with the application's base theme. They never think about theming. Everything works.
  - UC-0b: User visits someone else's room that has custom theming. They experience it as-is. Their own spaces remain default.
  - UC-0c: An operator publishes a new base theme update. All Level 0 users get the update automatically because they have zero overrides.

  Level 1: Selection (Choosing Existing Variants)

  - UC-1a: User browses published card variants in-app, previews one, applies it to their user page. One click. The delta JSON is now associated with their page context.
  - UC-1b: User is in a room and sees a card style they like. They inspect it (right-click? a UI affordance?) and clone it into their own variant library.
  - UC-1c: User applies different published variants to different contexts - one card style on their profile page, a different one in their room. The system resolves per-context.
  - UC-1d: User removes a variant they applied. The component falls back to the base theme instantly.



● Level 2: Modification (Editing Variants)

  - UC-2a: User clones a variant (their own, a default, or someone else's published one). They now own a copy. The original is unaffected.
  - UC-2b: User opens their cloned variant and changes the border-radius and background color. The system stores only the delta from the base - two properties, not the entire card
  definition.
  - UC-2c: User previews their modification live, in-context - they see the card change on their actual page, not in an abstract sandbox.
  - UC-2d: User makes a change that would break accessibility contrast ratios. The system shows a warning but doesn't prevent the save. Information, not gates.
  - UC-2e: User's variant is based on a community variant. The upstream author publishes an update. The user sees the upstream changes in properties they haven't overridden, and
  their overrides are preserved.
  - UC-2f: User modifies a variant and decides it's worse. They revert to the parent variant's values (or any point in their edit history).

  Level 3: Composition (Combining and Layering)

  - UC-3a: User creates a "context rule" - this variant applies to cards in my rooms, that variant applies to cards on my profile. Rules are declarative and ordered.
  - UC-3b: User layers two variant deltas - one that changes colors, another that changes spacing. The system merges them with predictable precedence (last wins per-property).
  - UC-3c: User creates a "theme bundle" - a named collection of variants across multiple components (card, button, badge). Applying the bundle sets all of them at once.
  - UC-3d: User shares a theme bundle. Another user clones it and swaps out just the card variant, keeping the rest.
  - UC-3e: User sets a variant on a specific page. A room operator also sets a variant for that room. The system has clear, predictable resolution: user overrides > room operator >
  application defaults.

  Level 4: Authoring (Design System Primitives)

  - UC-4a: User creates a variant from scratch - not by cloning, but by starting from the base component and adding properties. The delta starts empty.
  - UC-4b: User defines their own design tokens (color aliases, spacing scales) and references them across multiple variants. Changing a token updates all variants that use it.
  - UC-4c: User publishes a variant or bundle to the community. Other users can browse, preview, and clone it. The author gets attribution.
  - UC-4d: User exports their entire theme configuration as a portable JSON document. They can import it into another instance of the application or share it out-of-band.
  - UC-4e: User writes raw CSS overrides that target data-slot attributes directly - the escape hatch for anything the configurator doesn't expose. The system injects their CSS
  scoped to their contexts.
  - UC-4f: User creates a variant that targets not just a single component, but a compositional pattern - "cards inside story panels should look like this." Selector composition via
   data attributes on ancestors.

  Cross-Cutting Concerns

  - UC-X1: Resolution order is inspectable. Any user can see why a component looks the way it does - which variant is active, where it came from, what the cascade is. Like browser
  DevTools for the theming system.
  - UC-X2: No destructive operations. Deleting a variant you shared doesn't break other users' clones. Clones are independent copies of the delta.
  - UC-X3: Hot-switching. Changing a variant or context rule takes effect immediately, no page reload. Attribute selectors on ancestor elements toggle which CSS rules apply.
  - UC-X4: Offline-capable deltas. Variant JSON is small and self-contained. It can be cached, applied optimistically, and synced later.
  - UC-X5: Backward compatibility. When the base component evolves (new shadcn update, new data-slot added), existing deltas continue to work - they only override what they specify.
   New properties fall through to the updated base.
