note: all agents presentation work needs to be carefully reviewed against presentation-as-data design and cascading themes. see Agents/docs/agent-card-presentation-guide and card-themes-reference for more thinking here - note that these guides may not currently be completely accurate, but they point towards the intent of compositional inheritance, presentation-as-data, and enabling high degrees of user specificity in how they want various objects to appear.  these affordances are the POINT. do not cut away complexity because you can't understand that it's meaningful - do not limit creative expression because you are prioritizing a pattern that is not prioritized by this project.

a) agents presentation:

If I select the agent @pompous-debonair-chipmunk-of-leadership, then edit, then expand their advanced configuration, this is displayed in their presentation config:

    {
  "tokens": {
    "--agent-accent": "oklch(0.7 0.25 340)",
    "--agent-accent-foreground": "oklch(1 0 0)",
    "--card": "oklch(0.18 0.04 300)",
    "--card-foreground": "oklch(0.92 0.02 320)",
    "--border": "oklch(0.32 0.08 340)",
    "--muted": "oklch(0.22 0.03 300)",
    "--muted-foreground": "oklch(0.6 0.04 320)",
    "--secondary": "oklch(0.25 0.05 310)",
    "--secondary-foreground": "oklch(0.85 0.06 330)",
    "--foreground": "oklch(0.92 0.02 320)",
    "--agent-card-shadow": "0 0 25px oklch(0.65 0.25 340 / 0.12), 0 0 5px oklch(0.7 0.2 340 / 0.08)",
    "--agent-card-radius": "4px",
    "--agent-accent-position": "left",
    "--agent-accent-width": "4px"
  },
  "avatar": {
    "emoji": "⚡",
    "backgroundColor": "oklch(0.65 0.25 340)"
  },
  "decorationHint": "neon"
}

if I copy that presentation config, open another agent, and paste that exact text into the agent config, the agent does not have the same display properties as the first agent.  Also, if I reopen that agents settings, the box for presentation config is emptied.

b) agents card themes: selecting an agent, editing the agent, then selecting the card theme for that agent does not apply that visual style.  

X) the edit modal for agents needs UX review and radical UX redesign.

X) the direct agent's pages are awful (agent/agent-slug). they are incredibly limited in functionality, and they don't provide good data. we need to extend these with the features that the structure of our project enables.

X) agent search/sort/filtering.
needs design and review.



