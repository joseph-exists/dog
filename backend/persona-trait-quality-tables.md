tinyfoot=# \d+ persona;
                                                          Table "public.persona"
        Column        |            Type             | Collation | Nullable | Default | Storage  | Compression | Stats target | Description
----------------------+-----------------------------+-----------+----------+---------+----------+-------------+--------------+-------------
 id                   | uuid                        |           | not null |         | plain    |             |              |
 created_at           | timestamp without time zone |           | not null |         | plain    |             |              |
 description          | character varying(255)      |           |          |         | extended |             |              |
 name                 | character varying(255)      |           | not null |         | extended |             |              |
 long_description     | character varying           |           |          |         | extended |             |              |
 general_domain       | character varying(255)      |           |          |         | extended |             |              |
 specific_domain      | character varying(255)      |           |          |         | extended |             |              |
 general_domain_high  | character varying(255)      |           |          |         | extended |             |              |
 specific_domain_high | character varying(255)      |           |          |         | extended |             |              |
Indexes:
    "persona_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "agent_personas" CONSTRAINT "agent_personas_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id) ON DELETE CASCADE
    TABLE "archetypepersonalink" CONSTRAINT "archetypepersonalink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "personaqualitylink" CONSTRAINT "personaqualitylink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "personatraitlink" CONSTRAINT "personatraitlink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "room_participant_bindings" CONSTRAINT "room_participant_bindings_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "userpersona" CONSTRAINT "userpersona_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
Access method: heap

tinyfoot=# \d+ personatraitlink;
                                                     Table "public.personatraitlink"
       Column        |            Type             | Collation | Nullable | Default | Storage | Compression | Stats target | Description
---------------------+-----------------------------+-----------+----------+---------+---------+-------------+--------------+-------------
 persona_id          | uuid                        |           | not null |         | plain   |             |              |
 id                  | uuid                        |           | not null |         | plain   |             |              |
 created_at          | timestamp without time zone |           | not null |         | plain   |             |              |
 trait_id            | uuid                        |           | not null |         | plain   |             |              |
 is_inherited        | boolean                     |           | not null |         | plain   |             |              |
 source_archetype_id | uuid                        |           |          |         | plain   |             |              |
Indexes:
    "personatraitlink_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "personatraitlink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    "personatraitlink_source_archetype_id_fkey" FOREIGN KEY (source_archetype_id) REFERENCES archetype(id)
    "personatraitlink_trait_id_fkey" FOREIGN KEY (trait_id) REFERENCES trait(id)
Access method: heap

tinyfoot=# \d+ personaqualitylink;
                                                    Table "public.personaqualitylink"
       Column        |            Type             | Collation | Nullable | Default | Storage | Compression | Stats target | Description
---------------------+-----------------------------+-----------+----------+---------+---------+-------------+--------------+-------------
 persona_id          | uuid                        |           | not null |         | plain   |             |              |
 quality_id          | uuid                        |           | not null |         | plain   |             |              |
 source_type         | qualitysourcetype           |           | not null |         | plain   |             |              |
 state               | qualitystate                |           | not null |         | plain   |             |              |
 id                  | uuid                        |           | not null |         | plain   |             |              |
 created_at          | timestamp without time zone |           | not null |         | plain   |             |              |
 source_trait_id     | uuid                        |           |          |         | plain   |             |              |
 source_archetype_id | uuid                        |           |          |         | plain   |             |              |
Indexes:
    "personaqualitylink_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "personaqualitylink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    "personaqualitylink_quality_id_fkey" FOREIGN KEY (quality_id) REFERENCES quality(id)
    "personaqualitylink_source_archetype_id_fkey" FOREIGN KEY (source_archetype_id) REFERENCES archetype(id)
    "personaqualitylink_source_trait_id_fkey" FOREIGN KEY (source_trait_id) REFERENCES trait(id)
Access method: heap