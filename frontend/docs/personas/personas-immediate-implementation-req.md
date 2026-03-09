A: Lock the MVP publication model.
Use page snapshot publication for MVP, with backend entities authoritative for owner authoring and page layout plus published snapshot as the visitor contract.

B: Lock the MVP audience model.
Requirement: define the contract required to ensure public/private/group scopes immediately. The frontend and backend have been arguing about responsibility instead of being explicitly declarative about what needs implementation.  The non-public resolution model is a top-level requirement of this MVP: all work has been funded based on the supposition that engineering understood this requirement.  The rest is scaffolding towards this end.  Engineering needs to deliver a plan, immediately, with the exact steps and contracts required.

C: Update composer UI/UX.  These minor changes should have been completed already.
Persona and audience-view edits are immediate product-entity edits now; layout and other page-shell constructs are still draft-until-save. UX needs to reflect that.

D: Finish the visitor-safe snapshot contract.  
Saving/publishing should intentionally serialize only the published persona/presentation state visitors are allowed to see.  With respect to A, B, & D above: Product Management, Project Management, and Engineering Leadership have been in repeated meetings with Engineering where A,B, and D were discussed and moved forward.  The current state is sloppy and reflects poorly.  This is a highly competitive environment focused on deep team collaboration: the current state of inter-team conflict and finger-pointing is unacceptable.  Get the work done.