# Walkthrough 04: Validate Mention-Based And Coordinator Orchestration

Status: `partial`
Persona: `operator`

## Goal

Verify visible multi-agent orchestration in one room using coordinator behavior
and mention-based A2A.

## Preconditions

- a room owner can add multiple agents
- at least one coordinator-style agent exists, or can be configured
- at least two specialist agents exist
- runtime path supports the required orchestration behavior

## Recommended Agent Set

Use the demo patterns already documented in:
- `/home/josep/dog/backend/app/services/service-docs/agent-demo-quickstart.md`

Recommended minimum set:
- one coordinator or analyzer agent with `participation_mode=always`
- two specialists with `participation_mode=on_mention`

## Steps

1. Open `/r/$roomId` as room owner.
2. Add the coordinator/analyzer and the specialist agents.
3. Confirm participants show the coordinator badge for the coordinating agent.
4. Send a prompt that should cause routing, for example:
   `I need help designing an API and writing the user-facing error messages.`
5. Observe the first agent response.
6. Check whether it mentions one or more specialists.
7. Observe follow-on specialist responses.
8. If your room/debug flow allows it, enable internal-message visibility and
   inspect internal orchestration traces.

## Expected Results

- coordinator/analyzer responds first or early in the sequence
- one or more specialists respond after being mentioned
- specialist behavior aligns with domain handoff implied by the routing agent

## Validation Checklist

- [ ] coordinator badge is visible in participants
- [ ] mentioned specialists respond without manual add/remove operations
- [ ] on-mention specialists remain quieter until routed to
- [ ] no infinite loops occur during mention chaining

## Failure Modes

- coordinator responds but no specialists do:
  mentions may not match room agents, or specialist mode may be `manual`
- specialists respond out of sequence:
  runtime orchestration ordering may differ from expectation
- no visible orchestration traces:
  internal-message visibility may be disabled

## Caveat

This walkthrough validates observable orchestration, not the full backend
orchestration graph. Mention-based A2A is user-visible; the underlying trigger
logic lives in runtime services outside the room UI.

## Evidence

- `/home/josep/dog/frontend/src/components/Room/panels/ParticipantPanel.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
- `/home/josep/dog/backend/app/services/a2a_orchestrator.py`
- `/home/josep/dog/backend/app/services/service-docs/agent-demo-quickstart.md`
