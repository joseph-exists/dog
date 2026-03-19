# Tesser GIF/MP4 Extension Analysis

**Date**: 2026-03-19
**Status**: Review Artifact
**Related**:

- `frontend/docs/plans/2026-03-19-tesser-svg-integration-mvp-plan.md`
- `frontend/docs/plans/2026-03-19-tesser-svg-integration-implementation-sequence.md`

## Short Answer

Supporting GIF and MP4 is feasible, but it is not the same class of work as the SVG MVP.

SVG works unusually well in the current stack because it is:

- returned inline in the Tesser payload as markup
- previewable inline in the browser with no file delivery layer
- persistable in an existing first-class SVG library model

GIF and MP4 break that convenience triangle.

The frontend difficulty is not mostly "render a different media tag." The main differentiation is:

1. how non-SVG artifacts become browser-accessible
2. how host surfaces stop assuming `svg` specifically
3. whether these outputs belong in the SVG library or in a more general media/render asset model

## What Already Exists

## Tesser already has multi-format artifact support

In Tesser, render results are artifact-oriented:

- `RenderRequest.formats` supports multiple formats
- `RenderResult` includes `artifacts`
- `RenderArtifact` includes:
  - `path`
  - `media_type`
  - `size_bytes`
  - `sha256`

That means Tesser itself is not the hard part.

The key nuance is that the Redis/Tesser response currently promotes SVG specially:

- if an SVG artifact exists, `render_payload["format"] = "svg"`
- and `render_payload["svg"] = <inline markup>`
- otherwise the payload remains artifact-oriented with `format: "external"` and `artifacts: [...]`

So the backend/Tesser contract already has the information needed for GIF/MP4, but the frontend path is currently optimized around the SVG special case.

## The current shared Tesser frontend service is mostly ready conceptually

`frontend/src/services/tesserService.ts` already models:

- `render.format`
- `render.artifacts`
- `render.manifest_path`
- `render.runtime_profile`
- `render.resolved_capabilities`

That is a good foundation.

However, the helper surface is still SVG-first:

- `getSvgMarkupFromRender(...)`

For GIF/MP4, we would want generalized artifact selectors and URL resolution, not just inline SVG extraction.

## Where the current frontend is SVG-specific

## 1. SVG Library model is explicitly SVG-only

The current persistence layer is not a generic render/media library.

The backend `SvgAsset` contract requires:

- `svg_markup`
- valid non-empty `<svg>...</svg>`

That means neither GIF nor MP4 can be saved into the current `/svgs` library without a new model or a separate generalized asset system.

This is the largest structural difference between "support GIF/MP4 preview" and "support GIF/MP4 as first-class saved outputs."

## 2. Demo canvas job contracts are SVG-only

The demo canvas path is strongly hardcoded around SVG:

- `DemoCanvasRenderResponse` exposes `svg: str`
- `DemoCanvasRenderJobResponse` exposes `svg?: string | null`
- demo job state stores `svg`
- canvas context types are suffixed with `.svg`
- finalization logic persists SVG into the demo composition/context flow

So even though generic Tesser routes can describe external artifacts, the demo-canvas route family is currently normalized to SVG only.

## 3. CanvasPanel is explicitly named and rendered as SVG

`CanvasPanel.tsx` takes:

- `svgContent`
- `onRenderSvg`

and renders with:

- `dangerouslySetInnerHTML` for inline SVG

This host is not hard to evolve, but it is currently an SVG panel, not a generic render panel.

## 4. Tesser Studio in the SVG workspace is intentionally SVG-shaped

The new Tesser Studio panel now:

- previews inline SVG
- saves successful outputs into the SVG library
- names the loop around SVG assets

That is correct for the MVP, but it means GIF/MP4 support in this exact surface would require either:

- a broadened mission for the page
- or a different host page/panel for non-SVG media outputs

## 5. ContentRenderer only partially helps

The generic content stack already supports:

- `svg`
- `image`

It does **not** currently support:

- `video`

This leads to an asymmetric result:

- GIF is closer, because it can behave like an image if we can provide a browser-usable URL
- MP4 is harder, because we also need a `video` renderer and content wiring

## Difficulty Breakdown

## A. Support GIF preview only

**Difficulty**: Moderate

If the goal is:

- run Tesser
- detect a GIF artifact
- preview it in a frontend surface

then the frontend work is not that large.

Needed changes:

1. expose a browser-usable URL for the GIF artifact
2. add generalized artifact helpers in `tesserService.ts`
3. update the host surface to render either:
   - inline SVG
   - image URL for GIF

The main blocker is not React rendering. It is artifact delivery.

Today the Tesser artifact payload exposes filesystem paths, not public URLs. A browser cannot use `/data/artifacts/...` or container-local paths directly.

So GIF preview becomes easy only after adding one of:

- backend download/proxy endpoint
- signed URL generation
- temporary media-serving route
- data URL/base64 transport for small outputs

## B. Support MP4 preview only

**Difficulty**: Moderate to High

Compared to GIF, MP4 adds two requirements:

1. browser-accessible artifact delivery
2. a real video rendering path in the frontend

The content system has no `VideoRenderer` today, and the registry explicitly treats video as future work.

So MP4 preview needs:

- `ContentRenderer` support for `video`
- `VideoRenderer`
- content options for autoplay/controls/muted/poster if desired
- host-surface updates where preview assumptions are currently SVG-specific

Still, this is not fundamentally hard. It is just broader than GIF because both transport and renderer support are missing.

## C. Support GIF/MP4 inside current SVG Library

**Difficulty**: High

This is where the work becomes architectural.

The current SVG library is not a generic media asset library. It assumes:

- SVG validation
- SVG markup persistence
- SVG preview semantics
- SVG naming and operations language

If we tried to force GIF/MP4 into the same model, we would end up fighting the data model everywhere.

A cleaner route would be one of:

1. keep `/svgs` SVG-only and introduce a separate render/media asset model
2. generalize the asset model into something like `RenderAsset` or `MediaAsset`
3. keep the SVG page SVG-focused and expose GIF/MP4 through demos/projects/rooms first

For product coherence, option 3 is probably the least disruptive if the immediate goal is just to use Tesser’s broader media outputs.

## D. Support GIF/MP4 in demos/rooms/projects

**Difficulty**: Moderate, if artifact delivery is solved first

These surfaces are actually better candidates than the SVG library for non-SVG outputs.

Reason:

- they already think in terms of runtime render outputs
- they do not need to pretend everything is an SVG asset
- they can evolve toward a generic "render result" abstraction more naturally

The demo canvas path is still SVG-specific today, but conceptually it is closer to a generalized render surface than the SVG library is.

## The Real Frontend Differentiation By Filetype

## SVG

- transport: inline markup already available
- preview: already solved
- persistence: already solved in `/svgs`
- renderer: already solved

## GIF

- transport: not solved
- preview: effectively solved once URL delivery exists, because `image` rendering already exists
- persistence: not solved in `/svgs`
- renderer: can reuse `ImageRenderer`

## MP4

- transport: not solved
- preview: not solved
- persistence: not solved in `/svgs`
- renderer: requires new `VideoRenderer` and content registration

## Most Important Missing Capability: Artifact Delivery

This is the actual hinge point.

Tesser artifact payloads currently expose:

- `path`
- `media_type`
- `size_bytes`
- `sha256`

That is useful for backend bookkeeping, but not sufficient for frontend rendering.

The browser needs a retrievable source:

- `url`
- `download_url`
- `data_url` for small assets
- or an API route that serves the artifact bytes

Until that exists, GIF and MP4 support will feel artificially blocked even though Tesser itself produced the media successfully.

## Clean Extension Strategy

## Stage 1: Generalize render result handling, not the SVG library

Add generalized frontend helpers in `tesserService.ts` such as:

- `getPrimaryArtifact(render)`
- `getArtifactByMediaType(render, mediaTypePrefix)`
- `getRenderableMediaKind(render)` returning `svg | image | video | external`

This is easy and low-risk.

## Stage 2: Add artifact delivery contract

Introduce a backend/browser delivery mechanism so artifact entries can include a usable URL.

This is the most important enabling step for GIF/MP4.

## Stage 3: Generalize host surfaces

Update host components so they stop assuming SVG specifically:

- `CanvasPanel`
- demo canvas route state
- Tesser Studio preview card

At that point:

- SVG can still render inline
- GIF can render through image content
- MP4 can render through video content

## Stage 4: Decide on persistence strategy

Do **not** stretch `/svgs` to hold GIF/MP4.

Instead choose one:

- keep non-SVG outputs transient/runtime-only at first
- add a separate media/render asset library
- later unify assets under a generalized model

This is where most of the product/design complexity lives.

## Recommendation

If the goal is to support Tesser’s broader output formats with the least disruption, I would do this:

1. Keep the current SVG Library and Tesser Studio explicitly SVG-focused.
2. Add generalized Tesser artifact handling in the frontend service layer.
3. Introduce backend artifact delivery URLs.
4. Add GIF support first in a runtime surface such as demo canvas or a generalized Tesser preview panel.
5. Add MP4 support after that by introducing a `VideoRenderer`.
6. Only after real usage appears, decide whether a generalized media/render asset library is warranted.

## Bottom Line

The frontend differentiation is:

- **GIF** is mostly a transport-and-host-surface problem.
- **MP4** is a transport problem plus a missing renderer problem.
- **Saving either into the current SVG library** is a data-model problem and therefore much more expensive.

So if you are asking "how hard is it to support GIF/MP4 from Tesser?", the honest answer is:

- preview support: very plausible, especially for GIF
- full first-class library support inside the current SVG stack: materially harder and likely the wrong first move
