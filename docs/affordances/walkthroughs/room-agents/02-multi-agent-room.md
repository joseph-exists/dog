# Walkthrough 02: Add Multiple Agents To One Room

Status: `ready-ish`
Persona: `room owner`

## Goal

Add several agents to a room in one action and verify that the room supports a
multi-agent participant set.

## Preconditions

- you own the room
- at least three visible agents exist
- the room includes the `Chat` panel

## Setup

1. Open `/agents`.
2. Confirm at least three agents are available.
3. Prefer agents with clearly different participation modes or roles so their
   behavior is easier to distinguish later.
4. Open `/r/$roomId` as room owner.

## Steps

1. In the `Chat` panel header, click the multi-agent add control.
2. Select two or more agents not already present in the room.
3. Confirm the selection.
4. Open or inspect the `Participants` panel.
5. Verify all selected agents are present.
6. Send a broad prompt such as `Everyone, summarize how you would help with a product launch.`.

## Expected Results

- multiple agents are added in one action
- all selected agents appear in participants
- one or more agents respond depending on their participation modes

## Validation Checklist

- [ ] multi-select add control is visible to room owner
- [ ] multiple agents appear after one confirm action
- [ ] existing agents are not duplicated
- [ ] room remains usable with a larger participant set

## Failure Modes

- control missing:
  you may not be room owner, or the active panel set may not include standard chat controls
- only some agents appear:
  participant adds may have partially failed
- no responses:
  added agents may be `on_mention` or `manual`

## Evidence

- `/home/josep/dog/frontend/src/components/Room/panels/ChatPanel.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
