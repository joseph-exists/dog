SVG Library: Gallery View: Need Multi-select delete.

SVG Library: Gallery View: need tagging
SVG Library: Gallery View: need filtering and sort controls.

SVG Library: Gallery View: Preview: CSS/style is flawed. a) SVG is rendered, but is shown off-center in the top section (shifted to the right).  b) linewrap not applied to svg code/text.  c) svg code text has no quick copy button d) svg code text is plain text.  e) svg code text should be in a collapsible.  f) svg preview should have a 'show exact size' for SVG in a page-sized panel without the constraints of current panel.

SVG Library: Gallery View: should enable rename.

SVG Library: Gallery View: Gallery Preview: should enable 'edit mode' directly for users: modify svg code, push button, see changes in the preview.  Does not need validation until save, the feedback loop of the visual is sufficient for this purpose. Save creates new SVG, not overwrite.

SVG Library: Tesser Studio: need to add guided controls, knobs, and extended script guidance for allowed scripts. review the backend/app/test_scripts/render_things/ docs and scripts as well as test_scripts/typer/commands/svgs.py - and we need to be very clear in our inline documentation as we do. We'll be extending our tesser interactivity dramatically - and we can be very kind to our future selves if we do the work with that in mind.

SVG Library: Tesser Studio: Gentle Mode.  We are going to add a third button option to Guided and JSON - Gentle Mode. There are a few functional affordances we'll need to add for this to work effectively. This will be built iteratively and so we'll keep in mind that the goal here is not to be exhaustive or correct: the goal is to learn through doing and experimentation what works for our users, and how we can enable them to find value in what we've built. We may need to add modal tooltips or other expressive callouts - we'll need to think through how we can be kind without making assumptions or putting too many conceptual roadblocks in their way.

Operations: Need to dramatically extend the functionality here with the affordances that tesser provides.  We can start by adding the currently exposed svgs functionality for the new svg.compose functions.  We should inline document this work as well. We'll need to extend/reuse our thinking as we move forward with better batch seed integration.

SVG dialogs:  Batch seed needs extended - not usable in current form.  see backend/app/test_scripts/render_things for examples

SVG dialogs: text in svgs is not represented here