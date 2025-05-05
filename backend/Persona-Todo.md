User & Persona References
- Users have Personas available
- Users have Personas they are currently using
- these instances of the Persona have their own data being tracked
- specific Persona instances will have data updates (query and mutation)

Figure out data model and then implement:
 - Player specific Story based on Story (progress over nodes)
 - Story model and application

Fix /components/ui/card.tsx
Fix /components/Common/PersonaCard.tsx
Fix /components/Personas/PersonaSelection.tsx

add PersonaSelection component to a route where users will select Personas

Implement the actual API integration once the backend team provides the API endpoints

Figure out the test (in tests/persona-tests.ts)

---

We need to implement state management to store the selected persona across the application. This could be done using:

React Context
React Query's cache
Local Storage
Redux or similar state management library


The selection process should be persisted, so when a user refreshes or returns to the application, their selected persona is still active.

We still need to implement mechanisms for:

Persona & Story Links for a User
  A Persona is selected and in that story there are things that should be saved only for that story and things that should be saved to that persona instance

Changing personas after initial selection
Reverting to selection if needed
Updating persona information
