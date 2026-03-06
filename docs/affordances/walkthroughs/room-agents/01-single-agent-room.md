# Walkthrough 01: Add One Agent To A Room

Status: `ready-ish`
Persona: `room owner`

## Goal

Create or open a room, add a single agent, and verify that the room chat and
participants surfaces reflect the new runtime participant.

## Preconditions

- you can open `/rooms`
- you have at least one visible agent in `/agents`
- you are the owner of the room you will use

## Setup

1. Open `/agents`.
2. Confirm that at least one agent exists.
3. If needed, create a personal agent with:
   - a recognizable name
   - `participation_mode=always`
   - `is_enabled=true`
4. Open `/rooms`.
5. Create a room or open an existing room you own.

## Steps

1. In `/r/$roomId`, locate the `Participants` panel.
2. Use the quick-add control in the panel header.
3. Select one agent that is not already in the room.
4. Confirm the agent appears in the `Agents` section of participants.
5. Send a simple chat message such as `Introduce yourself in one paragraph.`.
6. Wait for the room stream to update.

## Expected Results

- the chosen agent appears in the room participant list
- the participant row shows the agent name
- if metadata resolves, participation-mode and coordinator badges appear
- the agent responds in chat according to its configured participation mode

## Validation Checklist

- [ ] quick-add is visible for room owner
- [ ] added agent appears in participants without page reload
- [ ] agent message appears in room chat
- [ ] non-owner controls are not required for basic viewing after add

## Failure Modes

- quick-add missing:
  room likely not owned by current user, or panel set does not include participants
- add fails with toast error:
  participant mutation or permission issue
- agent never responds:
  participation mode may not be `always`, or runtime conditions may not trigger it

## Evidence

- `/home/josep/dog/frontend/src/components/Room/panels/ParticipantPanel.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoom.ts`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
