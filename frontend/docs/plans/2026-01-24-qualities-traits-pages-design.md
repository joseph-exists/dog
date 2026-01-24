# Qualities & Traits Pages Design

## Overview

Create top-level listing pages and block-based detail pages for Qualities and Traits entities, including reverse-lookup "used by" relationships.

## Architecture

### Listing Pages (`/qualities`, `/traits`)

Same card-grid pattern as `/archetypes`:
- Card grid with search, create dialog, delete confirmation
- Cards show name + description + created date
- Cards link to detail pages

### Detail Pages (`/quality/$qualityId`, `/trait/$traitId`)

PageShell with entity-type-aware blocks, auto-create + hydrate pattern.

**Quality template blocks**: Identity, Bio, TraitsBlock (linked traits via QualityTraitLink), UsedByBlock (archetypes/personas)

**Trait template blocks**: Identity, Bio, QualitiesBlock (linked qualities via QualityTraitLink), UsedByBlock (archetypes/personas)

## Backend — Reverse Lookup Routes

Four new read-only endpoints for "who uses this trait/quality":

**`trait_users.py`** (tag: `trait-users`):
- `GET /traits/{trait_id}/archetypes` → list[ArchetypePublic] (via archetypetraitlink)
- `GET /traits/{trait_id}/personas` → list[PersonaPublic] (via personatraitlink)

**`quality_users.py`** (tag: `quality-users`):
- `GET /qualities/{quality_id}/archetypes` → list[ArchetypePublic] (via archetypequalitylink)
- `GET /qualities/{quality_id}/personas` → list[PersonaPublic] (via personaqualitylink)

No mutations — adding/removing happens from the archetype/persona side.

## Frontend — Service Extensions

**EntityTraitsService** — add `quality` fetcher/adder/remover:
- Fetcher: `QualityTraitLinksService.readQualityTraits(qualityId)`
- Adder/Remover: `QualityTraitLinksService.createQualityTraitLink` / `deleteQualityTraitLink`

**EntityQualitiesService** — add `trait` fetcher/adder/remover:
- Fetcher: `QualityTraitLinksService.readTraitQualities(traitId)`
- Adder/Remover: same service

## Frontend — New Components

**Entity Types**: Add `quality` (Gem icon, purple) and `trait` (Sparkles icon, pink) to registry.

**Page Templates**: Quality and Trait templates with appropriate blocks.

**New Block: `UsedByBlock`**: Read-only block showing archetypes and personas that reference this entity. Uses TraitUsersService/QualityUsersService.

**Listing pages**: CreateQualityDialog, CreateTraitDialog (name + description).

**Detail pages**: Auto-create + hydrate, PageShell with entityType.

**Sidebar**: Add Qualities and Traits links.

## Implementation Order

1. Backend: trait_users.py and quality_users.py routes
2. Backend: Register routes in api/main.py
3. Frontend: Entity types + page templates in registry
4. Frontend: UsedByBlock component
5. Frontend: Extend EntityTraitsService (quality fetcher) and EntityQualitiesService (trait fetcher)
6. Frontend: CreateQualityDialog + CreateTraitDialog
7. Frontend: Listing pages (/qualities, /traits)
8. Frontend: Detail pages with auto-create + hydrate
9. Frontend: Sidebar links
10. Regenerate client, verify build
