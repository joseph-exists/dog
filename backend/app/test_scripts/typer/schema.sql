--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Ubuntu 17.5-1.pgdg22.04+1)
-- Dumped by pg_dump version 17.5 (Ubuntu 17.5-1.pgdg22.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Community Edition)';


--
-- Name: ai; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA ai;


ALTER SCHEMA ai OWNER TO postgres;

--
-- Name: timescaledb_toolkit; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb_toolkit WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb_toolkit; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION timescaledb_toolkit IS 'Library of analytical hyperfunctions, time-series pipelining, and other SQL utilities';


--
-- Name: plpython3u; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpython3u WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpython3u; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpython3u IS 'PL/Python3U untrusted procedural language';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: ai; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS ai WITH SCHEMA ai;


--
-- Name: EXTENSION ai; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION ai IS 'helper functions for ai workflows';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: bindingtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.bindingtype AS ENUM (
    'user_pref',
    'authored'
);


ALTER TYPE public.bindingtype OWNER TO postgres;

--
-- Name: contentformat; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.contentformat AS ENUM (
    'TEXT',
    'HTML',
    'MARKDOWN',
    'JSON',
    'YAML',
    'MDX',
    'CODE',
    'SVG',
    'IMAGE',
    'AUDIO',
    'VIDEO',
    'EMPTY',
    'UNKNOWN',
    'TEST'
);


ALTER TYPE public.contentformat OWNER TO postgres;

--
-- Name: llmprovidertype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.llmprovidertype AS ENUM (
    'OPENAI',
    'ANTHROPIC',
    'GOOGLE',
    'OPENAI_COMPATIBLE',
    'EMPTY'
);


ALTER TYPE public.llmprovidertype OWNER TO postgres;

--
-- Name: qualitysourcetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.qualitysourcetype AS ENUM (
    'TRAIT_DEPENDENT',
    'DEFAULT',
    'MANUALLY_ADDED'
);


ALTER TYPE public.qualitysourcetype OWNER TO postgres;

--
-- Name: qualitystate; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.qualitystate AS ENUM (
    'ENABLED',
    'DISABLED',
    'REMOVED'
);


ALTER TYPE public.qualitystate OWNER TO postgres;

--
-- Name: statevaluetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.statevaluetype AS ENUM (
    'BOOLEAN',
    'NUMBER',
    'STRING',
    'ENUM'
);


ALTER TYPE public.statevaluetype OWNER TO postgres;

--
-- Name: themecategory; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.themecategory AS ENUM (
    'page',
    'card',
    'syntax',
    'motion'
);


ALTER TYPE public.themecategory OWNER TO postgres;

--
-- Name: themescope; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.themescope AS ENUM (
    'system',
    'org',
    'personal',
    'shared'
);


ALTER TYPE public.themescope OWNER TO postgres;

--
-- Name: themeslot; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.themeslot AS ENUM (
    'page',
    'cards',
    'syntax',
    'motion'
);


ALTER TYPE public.themeslot OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_personas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.agent_personas (
    nickname character varying(255),
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    agent_id uuid NOT NULL,
    persona_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.agent_personas OWNER TO postgres;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: api_areas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.api_areas (
    id bigint NOT NULL,
    tag_name text NOT NULL,
    tag_description text,
    chunk_text text NOT NULL,
    embedding public.vector(1536),
    service text,
    version text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.api_areas OWNER TO postgres;

--
-- Name: api_areas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.api_areas_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.api_areas_id_seq OWNER TO postgres;

--
-- Name: api_areas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.api_areas_id_seq OWNED BY public.api_areas.id;


--
-- Name: api_code_chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.api_code_chunks (
    id bigint NOT NULL,
    corpus text NOT NULL,
    chunk_key text NOT NULL,
    source_file text NOT NULL,
    symbol text NOT NULL,
    kind text NOT NULL,
    start_line integer NOT NULL,
    end_line integer NOT NULL,
    raw_text text NOT NULL,
    embed_text text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    embedding public.vector(1536) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.api_code_chunks OWNER TO postgres;

--
-- Name: api_code_chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.api_code_chunks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.api_code_chunks_id_seq OWNER TO postgres;

--
-- Name: api_code_chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.api_code_chunks_id_seq OWNED BY public.api_code_chunks.id;


--
-- Name: archetype; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archetype (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    description character varying(255),
    name character varying(255) NOT NULL
);


ALTER TABLE public.archetype OWNER TO postgres;

--
-- Name: archetypepersonalink; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archetypepersonalink (
    archetype_id uuid NOT NULL,
    persona_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.archetypepersonalink OWNER TO postgres;

--
-- Name: archetypequalitylink; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archetypequalitylink (
    archetype_id uuid NOT NULL,
    quality_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.archetypequalitylink OWNER TO postgres;

--
-- Name: archetypetraitlink; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archetypetraitlink (
    archetype_id uuid NOT NULL,
    trait_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    id uuid NOT NULL
);


ALTER TABLE public.archetypetraitlink OWNER TO postgres;

--
-- Name: event; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event (
    name character varying(255) NOT NULL,
    description character varying(100),
    event_type character varying(100) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.event OWNER TO postgres;

--
-- Name: frontier_access_provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.frontier_access_provider (
    base_url character varying(100),
    testing_api_key character varying,
    name character varying(100) NOT NULL,
    is_enabled boolean NOT NULL,
    is_visible boolean NOT NULL,
    is_deprecated boolean NOT NULL,
    description character varying(500),
    id uuid NOT NULL,
    provider_type_id uuid NOT NULL
);


ALTER TABLE public.frontier_access_provider OWNER TO postgres;

--
-- Name: item; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.item (
    description character varying(255),
    id uuid NOT NULL,
    owner_id uuid NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE public.item OWNER TO postgres;

--
-- Name: llmmodel; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llmmodel (
    model_id character varying(100) NOT NULL,
    display_name character varying(100) NOT NULL,
    description character varying(500),
    context_window integer,
    is_default boolean NOT NULL,
    is_enabled boolean NOT NULL,
    is_deprecated boolean NOT NULL,
    sort_order integer NOT NULL,
    has_vision boolean,
    has_function_calling boolean,
    has_streaming boolean,
    has_json_mode boolean,
    id uuid NOT NULL,
    secondary_capabilities jsonb,
    is_system boolean NOT NULL,
    multiple_provider_type_support boolean NOT NULL,
    primary_provider_type_id uuid NOT NULL,
    owner_id uuid NOT NULL
);


ALTER TABLE public.llmmodel OWNER TO postgres;

--
-- Name: nodechoice; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nodechoice (
    text character varying(500) NOT NULL,
    "order" integer NOT NULL,
    id uuid NOT NULL,
    requires_state json,
    sets_state json,
    from_node_id uuid NOT NULL,
    to_node_id uuid NOT NULL
);


ALTER TABLE public.nodechoice OWNER TO postgres;

--
-- Name: pages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pages (
    entity_type character varying(50) NOT NULL,
    entity_id character varying(255) NOT NULL,
    layout_version integer NOT NULL,
    layout_json jsonb,
    id uuid NOT NULL,
    owner_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.pages OWNER TO postgres;

--
-- Name: panel_presets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.panel_presets (
    id uuid NOT NULL,
    owner_id uuid,
    name character varying NOT NULL,
    description character varying,
    panels json,
    is_system boolean NOT NULL,
    shared_to_room_id uuid,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.panel_presets OWNER TO postgres;

--
-- Name: persona; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.persona (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    description character varying(255),
    name character varying(255) NOT NULL,
    long_description character varying,
    general_domain character varying(255),
    specific_domain character varying(255),
    general_domain_high character varying(255),
    specific_domain_high character varying(255)
);


ALTER TABLE public.persona OWNER TO postgres;

--
-- Name: personaqualitylink; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.personaqualitylink (
    persona_id uuid NOT NULL,
    quality_id uuid NOT NULL,
    source_type public.qualitysourcetype NOT NULL,
    state public.qualitystate NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    source_trait_id uuid,
    source_archetype_id uuid
);


ALTER TABLE public.personaqualitylink OWNER TO postgres;

--
-- Name: personatraitlink; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.personatraitlink (
    persona_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    trait_id uuid NOT NULL,
    is_inherited boolean NOT NULL,
    source_archetype_id uuid
);


ALTER TABLE public.personatraitlink OWNER TO postgres;

--
-- Name: playstate; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.playstate (
    visited_at timestamp without time zone NOT NULL,
    id uuid NOT NULL,
    play_id uuid NOT NULL,
    node_id uuid NOT NULL
);


ALTER TABLE public.playstate OWNER TO postgres;

--
-- Name: progresssnapshot; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.progresssnapshot (
    story_state json,
    current_node_id uuid NOT NULL,
    id uuid NOT NULL,
    progress_id uuid NOT NULL,
    choice_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.progresssnapshot OWNER TO postgres;

--
-- Name: provider_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.provider_type (
    name character varying(30) NOT NULL,
    details character varying(500),
    validated boolean NOT NULL,
    is_system boolean NOT NULL,
    id uuid NOT NULL
);


ALTER TABLE public.provider_type OWNER TO postgres;

--
-- Name: quality; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quality (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    description character varying(255),
    name character varying(255) NOT NULL
);


ALTER TABLE public.quality OWNER TO postgres;

--
-- Name: qualityeventtrigger; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.qualityeventtrigger (
    quality_id uuid NOT NULL,
    event_id uuid NOT NULL,
    new_state public.qualitystate NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    condition_json character varying
);


ALTER TABLE public.qualityeventtrigger OWNER TO postgres;

--
-- Name: qualitytraitlink; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.qualitytraitlink (
    quality_id uuid NOT NULL,
    trait_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    auto_enable boolean NOT NULL,
    is_required boolean NOT NULL
);


ALTER TABLE public.qualitytraitlink OWNER TO postgres;

--
-- Name: room_agent_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_agent_settings (
    id uuid NOT NULL,
    room_id uuid NOT NULL,
    agent_slug character varying(50),
    prompt_config json,
    tool_policy json,
    rule_config json,
    revision integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.room_agent_settings OWNER TO postgres;

--
-- Name: room_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_events (
    event_type character varying(50) NOT NULL,
    payload json NOT NULL,
    event_id uuid NOT NULL,
    room_id uuid NOT NULL,
    room_sequence integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    enrichment_metadata json
);


ALTER TABLE public.room_events OWNER TO postgres;

--
-- Name: room_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_messages (
    content character varying NOT NULL,
    sender_type character varying(20) NOT NULL,
    message_id uuid NOT NULL,
    room_id uuid NOT NULL,
    sender_id uuid,
    agent_name character varying(255),
    created_at timestamp without time zone NOT NULL,
    button_options json,
    edited_at timestamp without time zone,
    edited_by uuid,
    is_pinned boolean NOT NULL,
    pinned_at timestamp without time zone,
    pinned_by uuid,
    active_for_context boolean NOT NULL,
    ui_components jsonb
);


ALTER TABLE public.room_messages OWNER TO postgres;

--
-- Name: room_panel_defaults; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_panel_defaults (
    panels json,
    id uuid NOT NULL,
    room_id uuid NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.room_panel_defaults OWNER TO postgres;

--
-- Name: room_participant_bindings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_participant_bindings (
    participant_type character varying(10) NOT NULL,
    participant_id character varying(255) NOT NULL,
    persona_id uuid,
    model_name character varying(100),
    id uuid NOT NULL,
    room_id uuid NOT NULL,
    user_id uuid,
    agent_id uuid,
    effective_at timestamp without time zone NOT NULL,
    ended_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    user_access_provider_id uuid,
    CONSTRAINT ck_room_participant_bindings_participant_type CHECK (((participant_type)::text = ANY ((ARRAY['user'::character varying, 'agent'::character varying])::text[]))),
    CONSTRAINT ck_room_participant_bindings_resolved_ids CHECK (((((participant_type)::text = 'user'::text) AND (user_id IS NOT NULL) AND (agent_id IS NULL)) OR (((participant_type)::text = 'agent'::text) AND (agent_id IS NOT NULL) AND (user_id IS NULL))))
);


ALTER TABLE public.room_participant_bindings OWNER TO postgres;

--
-- Name: room_participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_participants (
    participant_id character varying(255) NOT NULL,
    participant_type character varying(10) NOT NULL,
    role character varying(20) NOT NULL,
    id uuid NOT NULL,
    room_id uuid NOT NULL,
    joined_at timestamp without time zone NOT NULL,
    left_at timestamp without time zone,
    active boolean NOT NULL
);


ALTER TABLE public.room_participants OWNER TO postgres;

--
-- Name: room_story_progresses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_story_progresses (
    id uuid NOT NULL,
    room_id uuid NOT NULL,
    story_id uuid NOT NULL,
    story_version integer NOT NULL,
    active_progress_id uuid NOT NULL,
    revision integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.room_story_progresses OWNER TO postgres;

--
-- Name: rooms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rooms (
    title character varying(255),
    story_id uuid,
    room_id uuid NOT NULL,
    creator_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    last_activity timestamp without time zone NOT NULL,
    deleted_at timestamp without time zone
);


ALTER TABLE public.rooms OWNER TO postgres;

--
-- Name: shadow_outbox_attempts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadow_outbox_attempts (
    outbox_job_id uuid NOT NULL,
    attempt_number integer NOT NULL,
    started_at timestamp without time zone DEFAULT now() NOT NULL,
    finished_at timestamp without time zone,
    result character varying(30) NOT NULL,
    error_type character varying(100),
    error_message character varying,
    forgejo_repo character varying(255),
    forgejo_commit_sha character varying(40),
    id uuid NOT NULL
);


ALTER TABLE public.shadow_outbox_attempts OWNER TO postgres;

--
-- Name: shadow_outbox_jobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadow_outbox_jobs (
    shadow_repo_id uuid NOT NULL,
    shadow_version_id uuid NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    status character varying(30) DEFAULT 'queued'::character varying NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    run_after timestamp without time zone DEFAULT now() NOT NULL,
    locked_at timestamp without time zone,
    locked_by character varying(255),
    last_error character varying,
    last_error_at timestamp without time zone,
    priority integer DEFAULT 100 NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.shadow_outbox_jobs OWNER TO postgres;

--
-- Name: shadow_outbox_repo_leases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadow_outbox_repo_leases (
    shadow_repo_id uuid NOT NULL,
    locked_at timestamp without time zone,
    locked_by character varying(255)
);


ALTER TABLE public.shadow_outbox_repo_leases OWNER TO postgres;

--
-- Name: shadow_repo_version_counters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadow_repo_version_counters (
    shadow_repo_id uuid NOT NULL,
    next_version_number integer DEFAULT 1 NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.shadow_repo_version_counters OWNER TO postgres;

--
-- Name: shadowrepo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadowrepo (
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    forgejo_repo_name character varying(255) NOT NULL,
    forgejo_repo_id integer,
    id uuid NOT NULL,
    forked_from_id uuid,
    created_at timestamp without time zone NOT NULL,
    owner_id uuid NOT NULL
);


ALTER TABLE public.shadowrepo OWNER TO postgres;

--
-- Name: shadowuser; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadowuser (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    forgejo_repo_name character varying(255) NOT NULL,
    forgejo_repo_id integer
);


ALTER TABLE public.shadowuser OWNER TO postgres;

--
-- Name: shadowversion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shadowversion (
    commit_sha character varying(40) NOT NULL,
    version_number integer NOT NULL,
    message character varying(500) NOT NULL,
    id uuid NOT NULL,
    shadow_repo_id uuid NOT NULL,
    snapshot_json json,
    created_by_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    status character varying(20) DEFAULT 'committed'::character varying NOT NULL,
    committed_at timestamp without time zone,
    last_error character varying,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.shadowversion OWNER TO postgres;

--
-- Name: story; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.story (
    title character varying(255) NOT NULL,
    description character varying(1000),
    is_published boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    owner_id uuid NOT NULL,
    current_version integer NOT NULL,
    published_version integer,
    content_format public.contentformat,
    deleted_at timestamp without time zone,
    story_type character varying,
    presentation json
);


ALTER TABLE public.story OWNER TO postgres;

--
-- Name: storynode; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.storynode (
    title character varying(255) NOT NULL,
    content character varying NOT NULL,
    node_type character varying(50),
    is_start_node boolean NOT NULL,
    is_end_node boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    story_id uuid NOT NULL,
    story_version integer NOT NULL,
    content_format public.contentformat
);


ALTER TABLE public.storynode OWNER TO postgres;

--
-- Name: storyplay; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.storyplay (
    player_name character varying(255),
    is_completed boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    story_id uuid NOT NULL,
    user_id uuid
);


ALTER TABLE public.storyplay OWNER TO postgres;

--
-- Name: storyrequirement; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.storyrequirement (
    requirement_type character varying(50) NOT NULL,
    target_id uuid NOT NULL,
    description character varying(255),
    id uuid NOT NULL,
    story_id uuid NOT NULL
);


ALTER TABLE public.storyrequirement OWNER TO postgres;

--
-- Name: storystatevariable; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.storystatevariable (
    key character varying(100) NOT NULL,
    value_type public.statevaluetype NOT NULL,
    default_value json,
    enum_values json,
    description character varying(500),
    category character varying(100),
    id uuid NOT NULL,
    story_id uuid NOT NULL,
    story_version integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.storystatevariable OWNER TO postgres;

--
-- Name: storytotag; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.storytotag (
    story_id uuid NOT NULL,
    tag_id uuid NOT NULL
);


ALTER TABLE public.storytotag OWNER TO postgres;

--
-- Name: tag; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tag (
    name character varying(50) NOT NULL,
    color character varying(20),
    id uuid NOT NULL
);


ALTER TABLE public.tag OWNER TO postgres;

--
-- Name: theme; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.theme (
    name character varying(100) NOT NULL,
    description character varying(500),
    category public.themecategory NOT NULL,
    scope public.themescope NOT NULL,
    tokens jsonb,
    id uuid NOT NULL,
    owner_id uuid,
    is_system boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.theme OWNER TO postgres;

--
-- Name: theme_binding; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.theme_binding (
    binding_type public.bindingtype NOT NULL,
    context_key character varying(500) NOT NULL,
    slot public.themeslot NOT NULL,
    id uuid NOT NULL,
    owner_id uuid NOT NULL,
    theme_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.theme_binding OWNER TO postgres;

--
-- Name: trait; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trait (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    description character varying(255),
    name character varying(255) NOT NULL
);


ALTER TABLE public.trait OWNER TO postgres;

--
-- Name: traitconflictgroup; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.traitconflictgroup (
    name character varying(255) NOT NULL,
    description character varying(1000),
    conflict_type character varying(50) NOT NULL,
    reason character varying(2000),
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.traitconflictgroup OWNER TO postgres;

--
-- Name: traitconflictgroupmember; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.traitconflictgroupmember (
    id uuid NOT NULL,
    group_id uuid NOT NULL,
    trait_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.traitconflictgroupmember OWNER TO postgres;

--
-- Name: user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."user" (
    email character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    is_superuser boolean NOT NULL,
    full_name character varying(255),
    hashed_password character varying NOT NULL,
    id uuid NOT NULL
);


ALTER TABLE public."user" OWNER TO postgres;

--
-- Name: user_access_provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_access_provider (
    base_url character varying(100),
    name character varying(100) NOT NULL,
    is_enabled boolean NOT NULL,
    is_default boolean NOT NULL,
    is_validated boolean NOT NULL,
    description character varying(500),
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    provider_type_multiple boolean NOT NULL,
    alpha_provider_type_id uuid NOT NULL,
    owner_id uuid NOT NULL,
    api_key character varying
);


ALTER TABLE public.user_access_provider OWNER TO postgres;

--
-- Name: user_agent_configs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_agent_configs (
    name character varying(100),
    slug character varying(50),
    description character varying(500),
    user_access_provider uuid,
    provider_type uuid,
    model_id uuid,
    model_name character varying,
    system_prompt character varying,
    custom_system_prompt character varying,
    instructions character varying,
    tool_config json,
    deps_config json,
    agent_metadata json,
    is_enabled boolean,
    is_clonable boolean,
    is_visible boolean,
    scope character varying,
    participation_mode character varying,
    is_coordinator boolean,
    max_tool_iterations integer,
    capabilities json,
    id uuid NOT NULL,
    owner_id uuid,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    version integer NOT NULL,
    model character varying(100),
    agent_type character varying,
    presentation json
);


ALTER TABLE public.user_agent_configs OWNER TO postgres;

--
-- Name: user_panel_defaults; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_panel_defaults (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    preset_id character varying,
    panels json,
    reduce_motion boolean NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.user_panel_defaults OWNER TO postgres;

--
-- Name: user_room_panel_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_room_panel_config (
    panels json,
    use_room_defaults boolean NOT NULL,
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    room_id uuid NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.user_room_panel_config OWNER TO postgres;

--
-- Name: usernodechoice; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usernodechoice (
    choice_text character varying(1000) NOT NULL,
    from_node_id uuid NOT NULL,
    to_node_id uuid NOT NULL,
    state_changes json,
    id uuid NOT NULL,
    progress_id uuid NOT NULL,
    choice_time timestamp without time zone NOT NULL,
    parent_choice_id uuid,
    rng_data json
);


ALTER TABLE public.usernodechoice OWNER TO postgres;

--
-- Name: userpersona; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.userpersona (
    nickname character varying(255),
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    persona_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.userpersona OWNER TO postgres;

--
-- Name: userstoryprogress; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.userstoryprogress (
    current_node_id uuid,
    is_completed boolean NOT NULL,
    story_state json,
    id uuid NOT NULL,
    user_persona_id uuid NOT NULL,
    story_id uuid NOT NULL,
    story_version integer NOT NULL,
    started_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    head_choice_id uuid,
    head_version integer NOT NULL
);


ALTER TABLE public.userstoryprogress OWNER TO postgres;

--
-- Name: api_areas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_areas ALTER COLUMN id SET DEFAULT nextval('public.api_areas_id_seq'::regclass);


--
-- Name: api_code_chunks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_code_chunks ALTER COLUMN id SET DEFAULT nextval('public.api_code_chunks_id_seq'::regclass);


--
-- Name: agent_personas agent_personas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_personas
    ADD CONSTRAINT agent_personas_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_areas api_areas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_areas
    ADD CONSTRAINT api_areas_pkey PRIMARY KEY (id);


--
-- Name: api_areas api_areas_service_version_tag_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_areas
    ADD CONSTRAINT api_areas_service_version_tag_key UNIQUE (service, version, tag_name);


--
-- Name: api_code_chunks api_code_chunks_corpus_chunk_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_code_chunks
    ADD CONSTRAINT api_code_chunks_corpus_chunk_key_key UNIQUE (corpus, chunk_key);


--
-- Name: api_code_chunks api_code_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_code_chunks
    ADD CONSTRAINT api_code_chunks_pkey PRIMARY KEY (id);


--
-- Name: archetype archetype_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetype
    ADD CONSTRAINT archetype_pkey PRIMARY KEY (id);


--
-- Name: archetypepersonalink archetypepersonalink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypepersonalink
    ADD CONSTRAINT archetypepersonalink_pkey PRIMARY KEY (id);


--
-- Name: archetypequalitylink archetypequalitylink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypequalitylink
    ADD CONSTRAINT archetypequalitylink_pkey PRIMARY KEY (id);


--
-- Name: archetypetraitlink archetypetraitlink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypetraitlink
    ADD CONSTRAINT archetypetraitlink_pkey PRIMARY KEY (archetype_id, trait_id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (id);


--
-- Name: frontier_access_provider frontier_access_provider_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frontier_access_provider
    ADD CONSTRAINT frontier_access_provider_pkey PRIMARY KEY (id);


--
-- Name: item item_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item
    ADD CONSTRAINT item_pkey PRIMARY KEY (id);


--
-- Name: llmmodel llmmodel_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llmmodel
    ADD CONSTRAINT llmmodel_pkey PRIMARY KEY (id);


--
-- Name: nodechoice nodechoice_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nodechoice
    ADD CONSTRAINT nodechoice_pkey PRIMARY KEY (id);


--
-- Name: pages pages_entity_type_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pages
    ADD CONSTRAINT pages_entity_type_entity_id_key UNIQUE (entity_type, entity_id);


--
-- Name: pages pages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pages
    ADD CONSTRAINT pages_pkey PRIMARY KEY (id);


--
-- Name: panel_presets panel_presets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.panel_presets
    ADD CONSTRAINT panel_presets_pkey PRIMARY KEY (id);


--
-- Name: persona persona_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.persona
    ADD CONSTRAINT persona_pkey PRIMARY KEY (id);


--
-- Name: personaqualitylink personaqualitylink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personaqualitylink
    ADD CONSTRAINT personaqualitylink_pkey PRIMARY KEY (id);


--
-- Name: personatraitlink personatraitlink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personatraitlink
    ADD CONSTRAINT personatraitlink_pkey PRIMARY KEY (id);


--
-- Name: playstate playstate_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.playstate
    ADD CONSTRAINT playstate_pkey PRIMARY KEY (id);


--
-- Name: progresssnapshot progresssnapshot_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.progresssnapshot
    ADD CONSTRAINT progresssnapshot_pkey PRIMARY KEY (id);


--
-- Name: provider_type provider_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.provider_type
    ADD CONSTRAINT provider_type_pkey PRIMARY KEY (id);


--
-- Name: quality quality_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quality
    ADD CONSTRAINT quality_pkey PRIMARY KEY (id);


--
-- Name: qualityeventtrigger qualityeventtrigger_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualityeventtrigger
    ADD CONSTRAINT qualityeventtrigger_pkey PRIMARY KEY (id);


--
-- Name: qualitytraitlink qualitytraitlink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualitytraitlink
    ADD CONSTRAINT qualitytraitlink_pkey PRIMARY KEY (id);


--
-- Name: room_agent_settings room_agent_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_agent_settings
    ADD CONSTRAINT room_agent_settings_pkey PRIMARY KEY (id);


--
-- Name: room_agent_settings room_agent_settings_room_id_agent_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_agent_settings
    ADD CONSTRAINT room_agent_settings_room_id_agent_slug_key UNIQUE (room_id, agent_slug);


--
-- Name: room_events room_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_events
    ADD CONSTRAINT room_events_pkey PRIMARY KEY (event_id);


--
-- Name: room_messages room_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_messages
    ADD CONSTRAINT room_messages_pkey PRIMARY KEY (message_id);


--
-- Name: room_panel_defaults room_panel_defaults_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_panel_defaults
    ADD CONSTRAINT room_panel_defaults_pkey PRIMARY KEY (id);


--
-- Name: room_participant_bindings room_participant_bindings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participant_bindings
    ADD CONSTRAINT room_participant_bindings_pkey PRIMARY KEY (id);


--
-- Name: room_participants room_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participants
    ADD CONSTRAINT room_participants_pkey PRIMARY KEY (id);


--
-- Name: room_story_progresses room_story_progresses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_story_progresses
    ADD CONSTRAINT room_story_progresses_pkey PRIMARY KEY (id);


--
-- Name: room_story_progresses room_story_progresses_room_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_story_progresses
    ADD CONSTRAINT room_story_progresses_room_id_key UNIQUE (room_id);


--
-- Name: rooms rooms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rooms
    ADD CONSTRAINT rooms_pkey PRIMARY KEY (room_id);


--
-- Name: shadow_outbox_attempts shadow_outbox_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_outbox_attempts
    ADD CONSTRAINT shadow_outbox_attempts_pkey PRIMARY KEY (id);


--
-- Name: shadow_outbox_jobs shadow_outbox_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_outbox_jobs
    ADD CONSTRAINT shadow_outbox_jobs_pkey PRIMARY KEY (id);


--
-- Name: shadow_outbox_repo_leases shadow_outbox_repo_leases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_outbox_repo_leases
    ADD CONSTRAINT shadow_outbox_repo_leases_pkey PRIMARY KEY (shadow_repo_id);


--
-- Name: shadow_repo_version_counters shadow_repo_version_counters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_repo_version_counters
    ADD CONSTRAINT shadow_repo_version_counters_pkey PRIMARY KEY (shadow_repo_id);


--
-- Name: shadowrepo shadowrepo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowrepo
    ADD CONSTRAINT shadowrepo_pkey PRIMARY KEY (id);


--
-- Name: shadowuser shadowuser_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowuser
    ADD CONSTRAINT shadowuser_pkey PRIMARY KEY (id);


--
-- Name: shadowuser shadowuser_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowuser
    ADD CONSTRAINT shadowuser_user_id_key UNIQUE (user_id);


--
-- Name: shadowversion shadowversion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowversion
    ADD CONSTRAINT shadowversion_pkey PRIMARY KEY (id);


--
-- Name: story story_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.story
    ADD CONSTRAINT story_pkey PRIMARY KEY (id);


--
-- Name: storynode storynode_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storynode
    ADD CONSTRAINT storynode_pkey PRIMARY KEY (id);


--
-- Name: storyplay storyplay_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storyplay
    ADD CONSTRAINT storyplay_pkey PRIMARY KEY (id);


--
-- Name: storyrequirement storyrequirement_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storyrequirement
    ADD CONSTRAINT storyrequirement_pkey PRIMARY KEY (id);


--
-- Name: storystatevariable storystatevariable_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storystatevariable
    ADD CONSTRAINT storystatevariable_pkey PRIMARY KEY (id);


--
-- Name: storytotag storytotag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storytotag
    ADD CONSTRAINT storytotag_pkey PRIMARY KEY (story_id, tag_id);


--
-- Name: tag tag_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_name_key UNIQUE (name);


--
-- Name: tag tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tag
    ADD CONSTRAINT tag_pkey PRIMARY KEY (id);


--
-- Name: theme_binding theme_binding_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.theme_binding
    ADD CONSTRAINT theme_binding_pkey PRIMARY KEY (id);


--
-- Name: theme theme_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.theme
    ADD CONSTRAINT theme_pkey PRIMARY KEY (id);


--
-- Name: trait trait_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trait
    ADD CONSTRAINT trait_pkey PRIMARY KEY (id);


--
-- Name: traitconflictgroup traitconflictgroup_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.traitconflictgroup
    ADD CONSTRAINT traitconflictgroup_pkey PRIMARY KEY (id);


--
-- Name: traitconflictgroupmember traitconflictgroupmember_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.traitconflictgroupmember
    ADD CONSTRAINT traitconflictgroupmember_pkey PRIMARY KEY (id);


--
-- Name: agent_personas uq_agent_personas_agent_persona; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_personas
    ADD CONSTRAINT uq_agent_personas_agent_persona UNIQUE (agent_id, persona_id);


--
-- Name: llmmodel uq_llmmodel_provider_model; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llmmodel
    ADD CONSTRAINT uq_llmmodel_provider_model UNIQUE (primary_provider_type_id, model_id);


--
-- Name: shadowversion uq_shadowversion_shadow_repo_id_version_number; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowversion
    ADD CONSTRAINT uq_shadowversion_shadow_repo_id_version_number UNIQUE (shadow_repo_id, version_number);


--
-- Name: theme_binding uq_theme_binding_context; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.theme_binding
    ADD CONSTRAINT uq_theme_binding_context UNIQUE (binding_type, owner_id, context_key, slot);


--
-- Name: user_access_provider user_access_provider_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_access_provider
    ADD CONSTRAINT user_access_provider_pkey PRIMARY KEY (id);


--
-- Name: user_agent_configs user_agent_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_agent_configs
    ADD CONSTRAINT user_agent_configs_pkey PRIMARY KEY (id);


--
-- Name: user_panel_defaults user_panel_defaults_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_panel_defaults
    ADD CONSTRAINT user_panel_defaults_pkey PRIMARY KEY (id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user_room_panel_config user_room_panel_config_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_room_panel_config
    ADD CONSTRAINT user_room_panel_config_pkey PRIMARY KEY (id);


--
-- Name: user_room_panel_config user_room_panel_config_user_id_room_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_room_panel_config
    ADD CONSTRAINT user_room_panel_config_user_id_room_id_key UNIQUE (user_id, room_id);


--
-- Name: usernodechoice usernodechoice_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usernodechoice
    ADD CONSTRAINT usernodechoice_pkey PRIMARY KEY (id);


--
-- Name: userpersona userpersona_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userpersona
    ADD CONSTRAINT userpersona_pkey PRIMARY KEY (id);


--
-- Name: userstoryprogress userstoryprogress_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userstoryprogress
    ADD CONSTRAINT userstoryprogress_pkey PRIMARY KEY (id);


--
-- Name: idx_api_areas_ivf; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_api_areas_ivf ON public.api_areas USING ivfflat (embedding) WITH (lists='100');


--
-- Name: ix_frontier_access_provider_provider_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_frontier_access_provider_provider_type_id ON public.frontier_access_provider USING btree (provider_type_id);


--
-- Name: ix_llmmodel_is_system; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_llmmodel_is_system ON public.llmmodel USING btree (is_system);


--
-- Name: ix_llmmodel_primary_provider_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_llmmodel_primary_provider_type_id ON public.llmmodel USING btree (primary_provider_type_id);


--
-- Name: ix_pages_entity_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_pages_entity_id ON public.pages USING btree (entity_id);


--
-- Name: ix_pages_entity_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_pages_entity_type ON public.pages USING btree (entity_type);


--
-- Name: ix_pages_owner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_pages_owner_id ON public.pages USING btree (owner_id);


--
-- Name: ix_panel_presets_owner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_panel_presets_owner_id ON public.panel_presets USING btree (owner_id);


--
-- Name: ix_panel_presets_shared_to_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_panel_presets_shared_to_room_id ON public.panel_presets USING btree (shared_to_room_id);


--
-- Name: ix_room_agent_settings_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_agent_settings_room_id ON public.room_agent_settings USING btree (room_id);


--
-- Name: ix_room_events_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_events_created_at ON public.room_events USING btree (created_at);


--
-- Name: ix_room_events_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_events_room_id ON public.room_events USING btree (room_id);


--
-- Name: ix_room_messages_active_for_context; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_messages_active_for_context ON public.room_messages USING btree (active_for_context);


--
-- Name: ix_room_messages_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_messages_created_at ON public.room_messages USING btree (created_at);


--
-- Name: ix_room_messages_is_pinned; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_messages_is_pinned ON public.room_messages USING btree (is_pinned);


--
-- Name: ix_room_messages_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_messages_room_id ON public.room_messages USING btree (room_id);


--
-- Name: ix_room_panel_defaults_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_room_panel_defaults_room_id ON public.room_panel_defaults USING btree (room_id);


--
-- Name: ix_room_participant_bindings_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_participant_bindings_room_id ON public.room_participant_bindings USING btree (room_id);


--
-- Name: ix_room_participants_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_participants_room_id ON public.room_participants USING btree (room_id);


--
-- Name: ix_room_story_progresses_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_room_story_progresses_room_id ON public.room_story_progresses USING btree (room_id);


--
-- Name: ix_shadow_outbox_attempts_outbox_job_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_shadow_outbox_attempts_outbox_job_id ON public.shadow_outbox_attempts USING btree (outbox_job_id);


--
-- Name: ix_shadow_outbox_jobs_entity_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_shadow_outbox_jobs_entity_id ON public.shadow_outbox_jobs USING btree (entity_id);


--
-- Name: ix_shadow_outbox_jobs_entity_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_shadow_outbox_jobs_entity_type ON public.shadow_outbox_jobs USING btree (entity_type);


--
-- Name: ix_shadow_outbox_jobs_run_after; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_shadow_outbox_jobs_run_after ON public.shadow_outbox_jobs USING btree (run_after);


--
-- Name: ix_shadow_outbox_jobs_shadow_repo_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_shadow_outbox_jobs_shadow_repo_id ON public.shadow_outbox_jobs USING btree (shadow_repo_id);


--
-- Name: ix_shadow_outbox_jobs_shadow_version_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_shadow_outbox_jobs_shadow_version_id ON public.shadow_outbox_jobs USING btree (shadow_version_id);


--
-- Name: ix_shadow_outbox_jobs_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_shadow_outbox_jobs_status ON public.shadow_outbox_jobs USING btree (status);


--
-- Name: ix_traitconflictgroupmember_group_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_traitconflictgroupmember_group_id ON public.traitconflictgroupmember USING btree (group_id);


--
-- Name: ix_traitconflictgroupmember_trait_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_traitconflictgroupmember_trait_id ON public.traitconflictgroupmember USING btree (trait_id);


--
-- Name: ix_user_access_provider_alpha_provider_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_access_provider_alpha_provider_type_id ON public.user_access_provider USING btree (alpha_provider_type_id);


--
-- Name: ix_user_access_provider_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_access_provider_user_id ON public.user_access_provider USING btree (user_id);


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_user_email ON public."user" USING btree (email);


--
-- Name: ix_user_panel_defaults_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_user_panel_defaults_user_id ON public.user_panel_defaults USING btree (user_id);


--
-- Name: ix_user_room_panel_config_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_room_panel_config_room_id ON public.user_room_panel_config USING btree (room_id);


--
-- Name: ix_user_room_panel_config_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_room_panel_config_user_id ON public.user_room_panel_config USING btree (user_id);


--
-- Name: agent_personas agent_personas_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_personas
    ADD CONSTRAINT agent_personas_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.user_agent_configs(id) ON DELETE CASCADE;


--
-- Name: agent_personas agent_personas_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_personas
    ADD CONSTRAINT agent_personas_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.persona(id) ON DELETE CASCADE;


--
-- Name: archetypepersonalink archetypepersonalink_archetype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypepersonalink
    ADD CONSTRAINT archetypepersonalink_archetype_id_fkey FOREIGN KEY (archetype_id) REFERENCES public.archetype(id);


--
-- Name: archetypepersonalink archetypepersonalink_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypepersonalink
    ADD CONSTRAINT archetypepersonalink_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.persona(id);


--
-- Name: archetypequalitylink archetypequalitylink_archetype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypequalitylink
    ADD CONSTRAINT archetypequalitylink_archetype_id_fkey FOREIGN KEY (archetype_id) REFERENCES public.archetype(id);


--
-- Name: archetypequalitylink archetypequalitylink_quality_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypequalitylink
    ADD CONSTRAINT archetypequalitylink_quality_id_fkey FOREIGN KEY (quality_id) REFERENCES public.quality(id);


--
-- Name: archetypetraitlink archetypetraitlink_archetype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypetraitlink
    ADD CONSTRAINT archetypetraitlink_archetype_id_fkey FOREIGN KEY (archetype_id) REFERENCES public.archetype(id);


--
-- Name: archetypetraitlink archetypetraitlink_trait_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archetypetraitlink
    ADD CONSTRAINT archetypetraitlink_trait_id_fkey FOREIGN KEY (trait_id) REFERENCES public.trait(id);


--
-- Name: frontier_access_provider frontier_access_provider_provider_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frontier_access_provider
    ADD CONSTRAINT frontier_access_provider_provider_type_id_fkey FOREIGN KEY (provider_type_id) REFERENCES public.provider_type(id);


--
-- Name: item item_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item
    ADD CONSTRAINT item_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: llmmodel llmmodel_primary_provider_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llmmodel
    ADD CONSTRAINT llmmodel_primary_provider_type_id_fkey FOREIGN KEY (primary_provider_type_id) REFERENCES public.provider_type(id);


--
-- Name: nodechoice nodechoice_from_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nodechoice
    ADD CONSTRAINT nodechoice_from_node_id_fkey FOREIGN KEY (from_node_id) REFERENCES public.storynode(id) ON DELETE CASCADE;


--
-- Name: nodechoice nodechoice_to_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nodechoice
    ADD CONSTRAINT nodechoice_to_node_id_fkey FOREIGN KEY (to_node_id) REFERENCES public.storynode(id) ON DELETE CASCADE;


--
-- Name: pages pages_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pages
    ADD CONSTRAINT pages_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public."user"(id);


--
-- Name: panel_presets panel_presets_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.panel_presets
    ADD CONSTRAINT panel_presets_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public."user"(id);


--
-- Name: panel_presets panel_presets_shared_to_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.panel_presets
    ADD CONSTRAINT panel_presets_shared_to_room_id_fkey FOREIGN KEY (shared_to_room_id) REFERENCES public.rooms(room_id);


--
-- Name: personaqualitylink personaqualitylink_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personaqualitylink
    ADD CONSTRAINT personaqualitylink_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.persona(id);


--
-- Name: personaqualitylink personaqualitylink_quality_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personaqualitylink
    ADD CONSTRAINT personaqualitylink_quality_id_fkey FOREIGN KEY (quality_id) REFERENCES public.quality(id);


--
-- Name: personaqualitylink personaqualitylink_source_archetype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personaqualitylink
    ADD CONSTRAINT personaqualitylink_source_archetype_id_fkey FOREIGN KEY (source_archetype_id) REFERENCES public.archetype(id);


--
-- Name: personaqualitylink personaqualitylink_source_trait_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personaqualitylink
    ADD CONSTRAINT personaqualitylink_source_trait_id_fkey FOREIGN KEY (source_trait_id) REFERENCES public.trait(id);


--
-- Name: personatraitlink personatraitlink_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personatraitlink
    ADD CONSTRAINT personatraitlink_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.persona(id);


--
-- Name: personatraitlink personatraitlink_source_archetype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personatraitlink
    ADD CONSTRAINT personatraitlink_source_archetype_id_fkey FOREIGN KEY (source_archetype_id) REFERENCES public.archetype(id);


--
-- Name: personatraitlink personatraitlink_trait_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.personatraitlink
    ADD CONSTRAINT personatraitlink_trait_id_fkey FOREIGN KEY (trait_id) REFERENCES public.trait(id);


--
-- Name: playstate playstate_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.playstate
    ADD CONSTRAINT playstate_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.storynode(id) ON DELETE CASCADE;


--
-- Name: playstate playstate_play_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.playstate
    ADD CONSTRAINT playstate_play_id_fkey FOREIGN KEY (play_id) REFERENCES public.storyplay(id) ON DELETE CASCADE;


--
-- Name: progresssnapshot progresssnapshot_choice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.progresssnapshot
    ADD CONSTRAINT progresssnapshot_choice_id_fkey FOREIGN KEY (choice_id) REFERENCES public.usernodechoice(id);


--
-- Name: progresssnapshot progresssnapshot_progress_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.progresssnapshot
    ADD CONSTRAINT progresssnapshot_progress_id_fkey FOREIGN KEY (progress_id) REFERENCES public.userstoryprogress(id) ON DELETE CASCADE;


--
-- Name: qualityeventtrigger qualityeventtrigger_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualityeventtrigger
    ADD CONSTRAINT qualityeventtrigger_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.event(id);


--
-- Name: qualityeventtrigger qualityeventtrigger_quality_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualityeventtrigger
    ADD CONSTRAINT qualityeventtrigger_quality_id_fkey FOREIGN KEY (quality_id) REFERENCES public.quality(id);


--
-- Name: qualitytraitlink qualitytraitlink_quality_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualitytraitlink
    ADD CONSTRAINT qualitytraitlink_quality_id_fkey FOREIGN KEY (quality_id) REFERENCES public.quality(id);


--
-- Name: qualitytraitlink qualitytraitlink_trait_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qualitytraitlink
    ADD CONSTRAINT qualitytraitlink_trait_id_fkey FOREIGN KEY (trait_id) REFERENCES public.trait(id);


--
-- Name: room_agent_settings room_agent_settings_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_agent_settings
    ADD CONSTRAINT room_agent_settings_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id) ON DELETE CASCADE;


--
-- Name: room_events room_events_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_events
    ADD CONSTRAINT room_events_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id);


--
-- Name: room_messages room_messages_edited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_messages
    ADD CONSTRAINT room_messages_edited_by_fkey FOREIGN KEY (edited_by) REFERENCES public."user"(id);


--
-- Name: room_messages room_messages_pinned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_messages
    ADD CONSTRAINT room_messages_pinned_by_fkey FOREIGN KEY (pinned_by) REFERENCES public."user"(id);


--
-- Name: room_messages room_messages_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_messages
    ADD CONSTRAINT room_messages_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id);


--
-- Name: room_messages room_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_messages
    ADD CONSTRAINT room_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public."user"(id);


--
-- Name: room_panel_defaults room_panel_defaults_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_panel_defaults
    ADD CONSTRAINT room_panel_defaults_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id);


--
-- Name: room_participant_bindings room_participant_bindings_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participant_bindings
    ADD CONSTRAINT room_participant_bindings_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.user_agent_configs(id);


--
-- Name: room_participant_bindings room_participant_bindings_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participant_bindings
    ADD CONSTRAINT room_participant_bindings_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.persona(id);


--
-- Name: room_participant_bindings room_participant_bindings_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participant_bindings
    ADD CONSTRAINT room_participant_bindings_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id) ON DELETE CASCADE;


--
-- Name: room_participant_bindings room_participant_bindings_user_access_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participant_bindings
    ADD CONSTRAINT room_participant_bindings_user_access_provider_id_fkey FOREIGN KEY (user_access_provider_id) REFERENCES public.user_access_provider(id);


--
-- Name: room_participant_bindings room_participant_bindings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participant_bindings
    ADD CONSTRAINT room_participant_bindings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: room_participants room_participants_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_participants
    ADD CONSTRAINT room_participants_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id);


--
-- Name: room_story_progresses room_story_progresses_active_progress_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_story_progresses
    ADD CONSTRAINT room_story_progresses_active_progress_id_fkey FOREIGN KEY (active_progress_id) REFERENCES public.userstoryprogress(id);


--
-- Name: room_story_progresses room_story_progresses_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_story_progresses
    ADD CONSTRAINT room_story_progresses_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id) ON DELETE CASCADE;


--
-- Name: room_story_progresses room_story_progresses_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_story_progresses
    ADD CONSTRAINT room_story_progresses_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id);


--
-- Name: rooms rooms_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rooms
    ADD CONSTRAINT rooms_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public."user"(id);


--
-- Name: rooms rooms_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rooms
    ADD CONSTRAINT rooms_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id);


--
-- Name: shadow_outbox_attempts shadow_outbox_attempts_outbox_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_outbox_attempts
    ADD CONSTRAINT shadow_outbox_attempts_outbox_job_id_fkey FOREIGN KEY (outbox_job_id) REFERENCES public.shadow_outbox_jobs(id);


--
-- Name: shadow_outbox_jobs shadow_outbox_jobs_shadow_repo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_outbox_jobs
    ADD CONSTRAINT shadow_outbox_jobs_shadow_repo_id_fkey FOREIGN KEY (shadow_repo_id) REFERENCES public.shadowrepo(id);


--
-- Name: shadow_outbox_jobs shadow_outbox_jobs_shadow_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_outbox_jobs
    ADD CONSTRAINT shadow_outbox_jobs_shadow_version_id_fkey FOREIGN KEY (shadow_version_id) REFERENCES public.shadowversion(id);


--
-- Name: shadow_outbox_repo_leases shadow_outbox_repo_leases_shadow_repo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_outbox_repo_leases
    ADD CONSTRAINT shadow_outbox_repo_leases_shadow_repo_id_fkey FOREIGN KEY (shadow_repo_id) REFERENCES public.shadowrepo(id);


--
-- Name: shadow_repo_version_counters shadow_repo_version_counters_shadow_repo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadow_repo_version_counters
    ADD CONSTRAINT shadow_repo_version_counters_shadow_repo_id_fkey FOREIGN KEY (shadow_repo_id) REFERENCES public.shadowrepo(id);


--
-- Name: shadowrepo shadowrepo_forked_from_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowrepo
    ADD CONSTRAINT shadowrepo_forked_from_id_fkey FOREIGN KEY (forked_from_id) REFERENCES public.shadowrepo(id);


--
-- Name: shadowrepo shadowrepo_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowrepo
    ADD CONSTRAINT shadowrepo_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: shadowuser shadowuser_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowuser
    ADD CONSTRAINT shadowuser_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: shadowversion shadowversion_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowversion
    ADD CONSTRAINT shadowversion_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);


--
-- Name: shadowversion shadowversion_shadow_repo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shadowversion
    ADD CONSTRAINT shadowversion_shadow_repo_id_fkey FOREIGN KEY (shadow_repo_id) REFERENCES public.shadowrepo(id) ON DELETE CASCADE;


--
-- Name: story story_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.story
    ADD CONSTRAINT story_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: storynode storynode_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storynode
    ADD CONSTRAINT storynode_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id) ON DELETE CASCADE;


--
-- Name: storyplay storyplay_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storyplay
    ADD CONSTRAINT storyplay_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id) ON DELETE CASCADE;


--
-- Name: storyplay storyplay_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storyplay
    ADD CONSTRAINT storyplay_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE SET NULL;


--
-- Name: storyrequirement storyrequirement_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storyrequirement
    ADD CONSTRAINT storyrequirement_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id) ON DELETE CASCADE;


--
-- Name: storystatevariable storystatevariable_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storystatevariable
    ADD CONSTRAINT storystatevariable_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id) ON DELETE CASCADE;


--
-- Name: storytotag storytotag_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storytotag
    ADD CONSTRAINT storytotag_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id) ON DELETE CASCADE;


--
-- Name: storytotag storytotag_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.storytotag
    ADD CONSTRAINT storytotag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tag(id) ON DELETE CASCADE;


--
-- Name: theme_binding theme_binding_theme_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.theme_binding
    ADD CONSTRAINT theme_binding_theme_id_fkey FOREIGN KEY (theme_id) REFERENCES public.theme(id);


--
-- Name: theme theme_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.theme
    ADD CONSTRAINT theme_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public."user"(id);


--
-- Name: traitconflictgroupmember traitconflictgroupmember_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.traitconflictgroupmember
    ADD CONSTRAINT traitconflictgroupmember_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.traitconflictgroup(id);


--
-- Name: traitconflictgroupmember traitconflictgroupmember_trait_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.traitconflictgroupmember
    ADD CONSTRAINT traitconflictgroupmember_trait_id_fkey FOREIGN KEY (trait_id) REFERENCES public.trait(id);


--
-- Name: user_access_provider user_access_provider_alpha_provider_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_access_provider
    ADD CONSTRAINT user_access_provider_alpha_provider_type_id_fkey FOREIGN KEY (alpha_provider_type_id) REFERENCES public.provider_type(id);


--
-- Name: user_access_provider user_access_provider_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_access_provider
    ADD CONSTRAINT user_access_provider_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: user_agent_configs user_agent_configs_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_agent_configs
    ADD CONSTRAINT user_agent_configs_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public."user"(id);


--
-- Name: user_panel_defaults user_panel_defaults_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_panel_defaults
    ADD CONSTRAINT user_panel_defaults_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user_room_panel_config user_room_panel_config_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_room_panel_config
    ADD CONSTRAINT user_room_panel_config_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.rooms(room_id);


--
-- Name: user_room_panel_config user_room_panel_config_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_room_panel_config
    ADD CONSTRAINT user_room_panel_config_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: usernodechoice usernodechoice_parent_choice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usernodechoice
    ADD CONSTRAINT usernodechoice_parent_choice_id_fkey FOREIGN KEY (parent_choice_id) REFERENCES public.usernodechoice(id);


--
-- Name: usernodechoice usernodechoice_progress_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usernodechoice
    ADD CONSTRAINT usernodechoice_progress_id_fkey FOREIGN KEY (progress_id) REFERENCES public.userstoryprogress(id) ON DELETE CASCADE;


--
-- Name: userpersona userpersona_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userpersona
    ADD CONSTRAINT userpersona_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.persona(id);


--
-- Name: userpersona userpersona_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userpersona
    ADD CONSTRAINT userpersona_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: userstoryprogress userstoryprogress_head_choice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userstoryprogress
    ADD CONSTRAINT userstoryprogress_head_choice_id_fkey FOREIGN KEY (head_choice_id) REFERENCES public.usernodechoice(id);


--
-- Name: userstoryprogress userstoryprogress_story_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userstoryprogress
    ADD CONSTRAINT userstoryprogress_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.story(id) ON DELETE CASCADE;


--
-- Name: userstoryprogress userstoryprogress_user_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userstoryprogress
    ADD CONSTRAINT userstoryprogress_user_persona_id_fkey FOREIGN KEY (user_persona_id) REFERENCES public.userpersona(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

