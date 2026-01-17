 Scope & Purpose
  - What specific tasks should the skill handle? (component creation, styling, state management,
  routing, testing?)

here are the basic frontend tasks i would assign a frontend team - let's figure out how these skills should be compartmentalized and how these skills should be used. I am unsure if there is a need for multiple skills to be used in orchestration, or one giant skill.  


co-designing UI/UX

reviewing backend reference card against design - ie, is the design contract satisfiable with the primitives/interfaces the backend team has exposed?

adding new UI/UX features as a whole (using backend references)
IE: new observability page

assessing existing ui/components for feature needs 
proposing new components to be added to ui/components

adding sub-features to an existing page or feature

ensuring that : - we are following our best practices for design and implementation (and the rules of engagement with the codebase)

  - What should it explicitly NOT do?

it should not cross the boundary to the backend
it should not look up models files
it should not modify any services
it should not create new utilities or hooks without explicit human authorization
it should not create throwaway code
it should always create accurate inline documentation

  - When should it be invoked vs. other skills?

  Tech Stack Specifics
  - Which parts of your stack need special guidance? (React, TypeScript, Shadcn, TanStack
  Query/Router, Vite)

    yes 

  - Are there patterns unique to this codebase vs. generic React?

    yes

  - How should it handle the auto-generated API client workflow?

    with care and wonder

  Conventions & Patterns
  - File/folder organization rules?
  - Naming conventions for components, hooks, routes?
  - State management patterns to follow?
  - How should components interact with TanStack Query?

  Quality & Verification
  - Biome linting rules to enforce?
  - TypeScript strictness expectations?
  - When/how should Playwright tests be written or run?

  Integration
  - How does frontend work coordinate with backend changes?
  - When to regenerate the API client?
  - Any specific build/dev workflow steps?

  Anti-patterns
  - What mistakes should the skill actively prevent?
  - What legacy patterns should it avoid introducing?
