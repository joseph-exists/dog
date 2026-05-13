Plan for the plan, fix the plan for the plan, make a good plan.
We are ready for our first handoff to the frontend team, so that they can iterate on story authoring UI and let us know if they need more features.

They will be using the exported client and sdk functions (in frontend/src/client/) as their interface with the story authoring functionality, and they will be implementing it within the existing frontend application.  our job is to create a guide which will enable the frontend team to create their own plan and choices for the UI implementation.  This guide should be wonderful, interesting, and follow the pyramid principle as well as being cross-referenced and incredibly accurate.

bad-dog-docs/STORY_MODEL_REVIEW.md and bad-dog-docs/TechSpecTinyfoot-Minimog.md are earlier iterations of our design -  and backend/docs/CYOA/STORY_SYSTEM_V2.md is a more recent, backend update to backend/docs/CYOA/STORY_SYSTEM.md

backend/app/tests/test_petri_timeline.py, test_story_branching, test_story_timeline, and test_user_story_tree can show different approaches to story creation - these are examples, the frontend team will not be using these files.

The frontend team will be required to create UI functionality for branching and longer stories with lots of nodes and lots of different types of state changes - directions, equipment, etc.  We need to help them as much as we can by providing a great, accurate, and cross-referenced guide to our system.

this is a minimal set of use cases, which will need to be expanded AFTER we've settled on the right approach to our handoff guide.

(existing) user logs in

selects storyteller on left hand nav
can select 
  - existing stories
  - existing nodes
  - create new story

selecting an existing story:
	shows status of the story (versions, published, author, history, etc)
	shows the nodes associated with that story

edit story:
	user can edit story
	user can edit storyrequirements
	user can edit nodes
	user can add nodes to a story
	publish story

view/edit nodes
view edit requirements