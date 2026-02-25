
this generated json is being rendered, but we're not having much luck understanding what we can plug in and where.  the current Templates aren't aligned very well with our aesthetic needs - and it's tricky to find out what's a bug with the template, or with the demo-builder, or with our thinking.  Please help!  We need to understand what a "good" version of the below looks like, and what the different things we can put in as presentation_json are!

there are significant details in src/components/Demo/demo-docs/demo-testing-references 

and in frontend/src/components/Agents/docs/CARD-THEME-REFERENCE and THEME-CASCADE-REFERENCE.

Once we start building out 'attractive/aesthetically pleasing' bundles/sets, we can save them as new Templates. Right now, we don't really have that.



{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "manual",
  "persona_policy": "fixed_user_persona",
  "chat_mode": "participant",
  "fixed_user_persona_id": "69802a2e-95f1-4018-ab8e-2cbac8b9acbd",
  "page_theme_id": null,
  "cards_theme_id": null,
  "presentation_json": {
    "motion": {
      "panel_enter_ms": 260,
      "block_stagger_ms": 55
    },
    "callouts": {
      "chat_notice": {
        "icon": "spark",
        "style": "frosted"
      }
    },
    "typography": {
      "body_font": "IBM Plex Sans",
      "heading_font": "Space Grotesk"
    },
    "backgrounds": {
      "svg_overlay": "grid-wave-v1",
      "page_gradient": "radial-gradient(1200px 500px at 20% 0%, rgba(0, 200, 255, 0.18), rgba(14, 18, 36, 0.9))"
    }
  },
  "metadata_json": {
    "story_id": "5dbb852f-49b8-4ba9-b148-b1eca55371a7",
    "description": "Stylized ops baseline with seeded participants and themed chat.",
    "template_id": "composition_d_stylized_agent_ops",
    "template_setup": {
      "dismissed": false,
      "template_id": "composition_d_stylized_agent_ops",
      "confirmations": {
        "persona_policy": true,
        "runtime_policy": true
      }
    },
    "theme_title_hints": {
      "page_theme_title": "qa-aurora-page",
      "cards_theme_title": "qa-glass-cards",
      "panel_theme_title": "qa-chat-neon"
    },
    "preloaded_participants": {
      "user_agent_config_ids": [
        "orchestrator",
        "coder",
        "analyst"
      ],
      "activate_on_session_start": [
        "orchestrator",
        "coder"
      ]
    }
  },
  "panels": [
    {
      "id": "story-runtime-primary",
      "kind": "storyRuntime",
      "prominence": "primary",
      "order": 1,
      "title": "Live Story Runtime",
      "theme_id": null,
      "presentation_json": {
        "overlays": {
          "panel_header": {
            "css": "linear-gradient(120deg, rgba(32, 196, 255, 0.16), rgba(12, 22, 42, 0.85))"
          }
        }
      },
      "default_size": null,
      "min_size": 20,
      "max_size": null,
      "viewport_mode": "panel",
      "options": {
        "send_runtime_events_to_chat": true,
        "viewer_mode": false
      }
    },
    {
      "id": "chat-stylized-aux",
      "kind": "chat",
      "prominence": "primary",
      "order": 2,
      "title": "Stylized Chat",
      "theme_id": null,
      "presentation_json": {
        "tokens": {
          "feed_density": "compact"
        },
        "effects": {
          "message_row_highlight": {
            "css": "inset 0 0 0 1px rgba(56,189,248,0.35), 0 8px 24px rgba(2,8,23,0.45)",
            "enable": true
          }
        },
        "typography": {
          "size": "sm"
        }
      },
      "default_size": null,
      "min_size": 20,
      "max_size": null,
      "viewport_mode": "panel",
      "options": {
        "mode": "participant",
        "include_internal_messages": true
      }
    },
    {
      "id": "participants-ops-aux",
      "kind": "participantPanel",
      "prominence": "primary",
      "order": 3,
      "title": "Ops Participants",
      "theme_id": null,
      "presentation_json": {},
      "default_size": null,
      "min_size": 25,
      "max_size": null,
      "viewport_mode": "panel",
      "options": {
        "showUsers": true,
        "showAgents": true,
        "compact": false,
        "allowQuickAdd": true
      }
    }
  ],
  "blocks": [
    {
      "id": "mission-brief-top",
      "type": "content",
      "region": "top",
      "order": 1,
      "title": "bartertown",
      "visibility": "visible",
      "theme_id": null,
      "presentation_json": {},
      "config_json": {},
      "content_json": {
        "metadata": {
          "variant": "callout",
          "label": null,
          "constraints": null,
          "options": null
        },
        "id": null,
        "format": "markdown",
        "value": "### Launch Checklist\n- Verify runtime attach\n- Verify seeded agents\n- Verify stylized chat rendering"
      }
    },
    {
      "id": "roster-primary",
      "type": "agentRoster",
      "region": "primary",
      "order": 1,
      "title": "Agent Roster",
      "visibility": "visible",
      "theme_id": null,
      "presentation_json": {},
      "config_json": {
        "show_participant_status": true
      }
    }
  ],
  "id": "a20626ef-0df2-4fac-b98c-52162708a71d",
  "demo_config_id": "d67e6412-2d1b-413c-88b2-ddcf6392b048",
  "owner_id": "228d7ff2-960d-48b3-91a0-979034859cfe",
  "created_at": "2026-02-24T20:43:38.423624",
  "updated_at": "2026-02-24T20:53:59.378757"
}