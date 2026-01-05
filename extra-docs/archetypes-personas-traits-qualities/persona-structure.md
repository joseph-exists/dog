
We need to think through the User -> Persona -> Story model.

Users select a Persona to use.
A version of that Persona is created which is specific to that User.
Other Users can also select and use that Persona, and they will have their own Versions.

User & Persona References
- Users have Personas available to Use
- Users select a Persona from a list of available (to them) Personas
- this creates a user-persona
- Users have Personas they are currentl3y using (user-personas) 
- these instances of the Persona have their own data being tracked
- specific Persona instances will have data updates (query and mutation)

Persona and Story References:
- Users will have selected a Persona
- Users are able to select from Stories if they meet requirements
- Stories may have Requirements on top level Persona or on the version of the Persona the player is using.
- Some Stories will be open to all Users.

Figure out data model and then implement:
 - Player specific Story based on Story (progress over nodes)
 - Story model and application


Implement the actual API integration

We still need to implement mechanisms for:

Persona & Story Links for a User
  A Persona is selected and in that story there are things that should be saved only for that story and things that should be saved to that persona instance

Changing personas after initial selection
Reverting to selection if needed
Updating persona information

Verify this works:

Users can select a Persona (creating a UserPersona)
Users can select a Story (creating a UserStoryProgress)
The Story starts with a specific StoryNode
Users can see the current node content and available choices
When users choose an option, the system:

Records their choice (UserNodeChoice)
Updates the story state
Moves them to the next node
Checks for story completion
