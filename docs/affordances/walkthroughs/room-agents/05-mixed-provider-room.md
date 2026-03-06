# Walkthrough 05: Validate Mixed-Provider Agents In One Room

Status: `partial`
Persona: `operator`

## Goal

Verify that agents backed by different providers/models can coexist and
participate in the same room conversation.

## Preconditions

- at least two agents exist with different provider/model configurations
- both agents are enabled and visible
- room owner can add both to the same room

## Setup

1. Open `/agents`.
2. Inspect at least two agents on `/agent/$agentId`.
3. Confirm they differ in provider or model configuration.
4. If necessary, create or clone agents so the pair clearly differs.

## Steps

1. Open `/r/$roomId`.
2. Add both differently configured agents to the room.
3. Confirm both appear in participants.
4. Send a prompt broad enough to invite multiple perspectives, for example:
   `Each of you propose an approach for building a release-readiness review workflow.`
5. Observe the responses from both agents.
6. If one is a coordinator or router, send a second prompt that encourages
   cross-agent collaboration.

## Expected Results

- both agents can coexist in the same room
- both can respond within the same shared conversation
- provider/model diversity does not block room participation

## Validation Checklist

- [ ] multiple differently configured agents are present in one room
- [ ] both can produce responses in the same session
- [ ] no room-level conflict appears because of provider diversity

## Current Limitation

The room UI does not strongly expose provider identity in participants, so this
walkthrough depends on validating provider diversity from the agent detail
surface and then observing runtime behavior in the room.

## Failure Modes

- one agent never responds:
  participation mode or agent configuration issue, not necessarily provider incompatibility
- provider difference cannot be confirmed from room alone:
  expected; use the agent detail page for provider verification

## Evidence

- `/home/josep/dog/frontend/src/routes/_layout/agent.$agentId.tsx`
- `/home/josep/dog/frontend/src/components/Agents/Dialogs/AgentDetailDialog.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
