this is the return of the following API call for users:

{
  "data": [
    {
      "entity_type": "user",
      "entity_id": "228d7ff2-960d-48b3-91a0-979034859cfe",
      "layout_version": 1,
      "layout_json": [
        {
          "id": "09817586-aee9-409a-95cf-54b904097810",
          "type": "identity",
          "order": 1,
          "column": "primary",
          "config": {
            "showTagline": true
          },
          "content": {
            "name": "josep",
            "tagline": "operator"
          },
          "visibility": "visible"
        },
        {
          "id": "0fcbc430-f015-4db0-9cc0-e4fd7607c05a",
          "type": "gallery",
          "order": 4,
          "column": "primary",
          "config": {
            "columns": 3
          },
          "content": {
            "images": []
          },
          "visibility": "hidden"
        },
        {
          "id": "470691bb-932c-4386-ab39-3cb29ba6103d",
          "type": "bio",
          "order": 1,
          "column": "auxiliary",
          "config": {},
          "content": {
            "text": "woo\n"
          },
          "visibility": "visible"
        },
        {
          "id": "b6e0fa8c-4e05-4152-a941-b8eaeb9ba16c",
          "type": "bio",
          "order": 5,
          "column": "primary",
          "config": {
            "maxLength": 500,
            "allowRichText": false
          },
          "content": {
            "text": ""
          },
          "visibility": "hidden"
        },
        {
          "id": "4b2282fd-93a9-472d-9db2-a52df5c3815c",
          "type": "identity",
          "order": 6,
          "column": "primary",
          "config": {
            "showTagline": true
          },
          "content": {
            "name": "Turtle",
            "tagline": "Turtle Does Turtle Stuff."
          },
          "visibility": "visible"
        },
        {
          "id": "fa397039-72cf-4e5e-8949-70c8257efc07",
          "type": "personas",
          "order": 2,
          "column": "primary",
          "config": {
            "layout": "grid",
            "maxVisible": 6,
            "showAddButton": true
          },
          "content": {},
          "visibility": "visible"
        },
        {
          "id": "414c9c6d-2f97-42f8-b991-41f7242ca9be",
          "type": "activityFeed",
          "order": 3,
          "column": "primary",
          "config": {
            "maxItems": 5
          },
          "content": {},
          "visibility": "visible"
        }
      ],
      "id": "00b6bc6b-2d99-4173-a3a1-5451fe4801fb",
      "owner_id": "228d7ff2-960d-48b3-91a0-979034859cfe",
      "created_at": "2026-01-22T18:13:58.450973",
      "updated_at": "2026-02-15T14:53:08.901192"
    }
  ],
  "count": 1
}

the pagepublic object schema: (with copy paste mangling)

Public response model for pages.

entity_typestring≤ 50 characters
entity_idstring≤ 255 characters
layout_versionCollapse allinteger
Default1
layout_jsonCollapse allarray<object>
ItemsCollapse allobject
Additional propertiesallowed
idstringuuid
owner_idstringuuid
created_atstringdate-time
updated_atstringdate-time

