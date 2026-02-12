Here's what to play with and what it's proving:
Six agents, six genuinely different visual identities — same component:

Armadillo Advisor — warm sandy tones, soft 14px radius, top accent, earthy shadow
Neon Muse — dark purple-black card, hot pink left accent with glow bleed, 4px sharp corners, cyberpunk
Cartograph — parchment white, ultra-precise 2px radius, bottom accent (unusual), tight shadow, cartographic
Verdant — botanical green, pillowy 20px radius, diffuse layered shadow, organic
AXIOM — zero radius, monospace font, hard offset shadow (4px 4px 0), thick yellow left accent, brutalist
Whisper — near-transparent lavender, maximum 24px radius, no accent strip at all, serif italic, ethereal

The key interactions to try:
Toggle "Object Styles" off. All six cards collapse to the same ambient appearance — proving the visual diversity comes entirely from the data, not from component variants or CSS classes. Toggle it back on and they reassert their identities.
Switch between page themes — especially Midnight and Deep Forest. Watch how agents with strong self-presentation (Neon Muse, AXIOM) resist the ambient, while Story Weaver (type defaults only) absorbs it.
Click different mini chips on the right to see the "Same agent, all variants" panel. This is the scaling proof — the same presentation data renders at full, compact, and mini density. The full card gets the accent strip, custom background, typography hint. The compact card distills it to a colored left border and avatar. The mini chip keeps just the avatar color. Same data, three intensities.
The vocabulary that's doing the work:
13 tokens control the entire range of visual expression: surface (bg, fg, border, muted, surface, shadow, radius), accent (color, position, width), badges (bg, fg). Plus the decorations.style hint that lets a card signal a typographic personality (brutalist → monospace uppercase, ethereal → serif italic) without the presentation data containing any font-family strings directly — the component interprets the hint.
That last point is worth discussing: should the decorations hint be an open vocabulary (the object says "I'm brutalist" and the component decides what that means) or should typography tokens be explicit (the object says --font-family: monospace)? The hint approach is safer and more portable — the component can adapt the interpretation — but it's less expressive. The explicit approach gives the creator full control but could produce unreadable results. That's the same dial question from our earlier conversation, and this POC lets you feel the tradeoff directly.