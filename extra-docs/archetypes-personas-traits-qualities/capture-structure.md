
We are going to finish the backend work, apply the schema changes, write tests, and ensure that the tests pass before we do any work on the frontend.

We need to create a comprehensive set of tasks which cover the following functional implementation.  These tasks should be specific and detailed, with clear exit criteria.  Each task should have a corresponding test or validation step to ensure it's been completed correctly.

Backend Files we know need to be created or changed:

Routes:
./backend/app/api/routes/personas.py
./backend/app/api/routes/archetypes.py
./backend/app/api/routes/traits.py
./backend/app/api/routes/qualities.py
./backend/app/api/routes/main.py 

CRUD:
./backend/app/crud.py

Models:
./backend/app/models.py

If functionality below is not marked PENDING, then it exists within the application.

Create an Archetype with a Name, a Description, and N number of additional Qualities with Names and Descriptions.
    Add Traits to that Archetype from existing Traits.
    Create new Traits for that Archetype.
    PENDING: Modify values of Traits when those values are modifiable.
    PENDING: Set which values of Traits are modifiable for Personas created from that Archetype
        PENDING: Set which Traits are modifiable only during Persona creation.
        PENDING: Set which Traits are modifiable as an update to the Persona.


Create a Persona and associate it with one and only one Archetype.
    That Persona inherits a set of Traits from that Archetype.


 Traits:
    Properties:
    PENDING: Some Traits can only be added to Archetypes.
    PENDING: Some Traits can only be active on N number of Active Personas at any given time.
    PENDING: Traits can be extended with properties.

Example of potential user flow:

User logs in and selects Create Archetype.
User gives Archetype the name "Magician" and adds the description "Represents a visionary and transformative individual or entity."
PENDING: User selects pre-existing Traits "Dynamic" and "Visionary" for the Magician Archetype.

User creates Traits "Chaotic" and "Harmonious".
User adds "Chaotic" and "Harmonious" as mutually exclusive traits for Personas which are associated with this Archetype.

User saves "Magician" Archetype.

User creates Persona.
User gives Persona the name "Merlin" and adds the description "Legendary magician with mysterious history and great powers."
User associates Merlin with the "Magician" Archetype.
User is required to select one of "Chaotic" or "Harmonious" for Merlin.
User selects "Harmonious" for Merlin, and saves the Merlin Persona.
