

The vast majority of functions and types we need exist in:
- `@/client/sdk.gen` - Service classes 
- `@/client/types.gen` - TypeScript types 
- `@/client/schemas.gen` - data structures



here are a few - we need to review the story-presentation-design.md through the lens of what we already have. 


```typescript
/**
 * Output from batch theme resolution.
 */
export type BatchResolvedThemesResponse = {
    /**
     * Resolution results keyed by slot
     */
    results: {
        [key: string]: ResolvedThemeResponse;
    };
};

/**
 * Input for batch theme resolution.
 * Resolves multiple slots in a single request for efficiency.
 */
export type BatchResolveThemeRequest = {
    /**
     * Ordered path segments
     */
    context_path: Array<(string)>;
    /**
     * Which theme categories to resolve
     */
    slots: Array<ThemeSlot>;
    entity_context?: (EntityContext | null);
};

/**
 * Classification of theme binding ownership.
 *
 * - user_pref: owner_id = user_id (viewer's personal preferences)
 * - authored: owner_id = entity_id (creator's content theming)
 */
export type BindingType = 'user_pref' | 'authored';



/**
 * Collection response for Story templates
 */
export type StoriesPublic = {
    data: Array<StoryPublic>;
    count: number;
};

/**
 * Input model for creating a new Story template
 */
export type StoryCreate = {
    title: string;
    content_format?: (ContentFormat | null);
    description?: (string | null);
    is_published?: boolean;
    /**
     * text for type that can be overloaded in presentation
     */
    story_type?: (string | null);
    presentation?: ({
    [key: string]: unknown;
} | null);
};

/**
 * Input model for creating a StoryNode
 */
export type StoryNodeCreate = {
    title: string;
    content?: string;
    content_format?: ContentFormat;
    node_type?: (string | null);
    is_start_node?: boolean;
    is_end_node?: boolean;
    story_id: string;
    story_version: number;
};

/**
 * Public API response model for StoryNode
 */
export type StoryNodePublic = {
    title: string;
    content?: string;
    content_format?: (ContentFormat | null);
    node_type?: (string | null);
    is_start_node?: boolean;
    is_end_node?: boolean;
    id: string;
    story_id: string;
    story_version: number;
    created_at: string;
    updated_at: string;
};

/**
 * Collection response for StoryNodes
 */
export type StoryNodesPublic = {
    data: Array<StoryNodePublic>;
    count: number;
};

/**
 * Pre-computed tree structure for a story version.
 */
export type StoryNodeTree = {
    root?: (StoryNodeTreeNode | null);
    orphaned_nodes?: Array<StoryNodeTreeNode>;
    total_nodes: number;
    reachable_nodes: number;
};

/**
 * A node in the pre-computed story tree structure.
 */
export type StoryNodeTreeNode = {
    id: string;
    title: string;
    is_start_node: boolean;
    is_end_node: boolean;
    level: number;
    children?: Array<StoryNodeTreeNode>;
};

/**
 * Input model for updating StoryNode (all fields optional)
 */
export type StoryNodeUpdate = {
    title?: (string | null);
    content?: (string | null);
    content_format?: (ContentFormat | null);
    node_type?: (string | null);
    is_start_node?: (boolean | null);
    is_end_node?: (boolean | null);
};

/**
 * Public API response model for Story template
 */
export type StoryPublic = {
    title: string;
    content_format?: (ContentFormat | null);
    description?: (string | null);
    is_published: boolean;
    /**
     * text for type that can be overloaded in presentation
     */
    story_type?: (string | null);
    presentation?: ({
    [key: string]: unknown;
} | null);
    id: string;
    owner_id: string;
    current_version: number;
    published_version: (number | null);
    created_at: string;
    updated_at: string;
};

/**
 * Base model for Story access requirements
 */
export type StoryRequirementBase = {
    requirement_type: string;
    target_id: string;
    description?: (string | null);
};

/**
 * Public API response model for StoryRequirement
 */
export type StoryRequirementPublic = {
    requirement_type: string;
    target_id: string;
    description?: (string | null);
    id: string;
    story_id: string;
};

/**
 * Collection response for StoryRequirements
 */
export type StoryRequirementsPublic = {
    data: Array<StoryRequirementPublic>;
    count: number;
};

export type StoryStateVariableBase = {
    key: string;
    value_type?: StateValueType;
    default_value?: (unknown | null);
    enum_values?: (Array<(string)> | null);
    description?: (string | null);
    category?: (string | null);
};

export type StoryStateVariablePublic = {
    key: string;
    value_type?: StateValueType;
    default_value?: (unknown | null);
    enum_values?: (Array<(string)> | null);
    description?: (string | null);
    category?: (string | null);
    id: string;
    story_id: string;
    story_version: number;
};

export type StoryStateVariablesPublic = {
    data: Array<StoryStateVariablePublic>;
    count: number;
};

export type StoryStateVariableUpdate = {
    key?: (string | null);
    value_type?: (StateValueType | null);
    default_value?: (unknown | null);
    enum_values?: (Array<(string)> | null);
    description?: (string | null);
    category?: (string | null);
};

/**
 * Input model for updating Story template (all fields optional)
 */
export type StoryUpdate = {
    title?: (string | null);
    description?: (string | null);
    content_format?: (ContentFormat | null);
};

/**
 * Result of validating a story's graph structure for publishing.
 */
export type StoryValidationResult = {
    is_valid: boolean;
    errors: Array<(string)>;
    warnings: Array<(string)>;
    node_count: number;
    choice_count: number;
    start_node_count: number;
    end_node_count: number;
    orphaned_node_count: number;
    state_schema_validation?: (StateSchemaValidationResult | null);
};

/**
 * API input for creating a theme binding.
 *
 * For user_pref bindings: owner_id is set by system to authenticated user
 * For authored bindings: owner_id is validated against entity ownership
 */
export type ThemeBindingCreate = {
    /**
     * Classification of binding ownership
     */
    binding_type: BindingType;
    /**
     * Composite context path (e.g., 'page:story/panel:debug')
     */
    context_key: string;
    /**
     * Which theme category slot this binding fills
     */
    slot: ThemeSlot;
    /**
     * Reference to theme being bound
     */
    theme_id: string;
};

/**
 * API response model for ThemeBinding entity.
 */
export type ThemeBindingPublic = {
    /**
     * Classification of binding ownership
     */
    binding_type: BindingType;
    /**
     * Composite context path (e.g., 'page:story/panel:debug')
     */
    context_key: string;
    /**
     * Which theme category slot this binding fills
     */
    slot: ThemeSlot;
    id: string;
    owner_id: string;
    theme_id: string;
    created_at: string;
    updated_at: string;
};

/**
 * Paginated collection response for ThemeBinding list endpoints.
 */
export type ThemeBindingsPublic = {
    data: Array<ThemeBindingPublic>;
    count: number;
};

/**
 * Classification of theme purpose. Each category has distinct token schemas.
 *
 * - page: Page surface theming (includes --background)
 * - card: Card/panel content areas (excludes --background)
 * - syntax: Code syntax highlighting (Shiki theme or token colors)
 * - motion: Animation characteristics (duration, easing, spring physics)
 */
export type ThemeCategory = 'page' | 'card' | 'syntax' | 'motion';

/**
 * API input for creating a new theme.
 * owner_id is set by the system based on authenticated user.
 * is_system is always False for user-created themes.
 */
export type ThemeCreate = {
    /**
     * Human-readable theme name
     */
    name: string;
    /**
     * Optional theme description
     */
    description?: (string | null);
    /**
     * Classification of theme purpose
     */
    category: ThemeCategory;
    /**
     * Visibility and ownership rules
     */
    scope?: ThemeScope;
    /**
     * Category-specific token payload (CSS variables, Shiki config, motion params)
     */
    tokens?: {
        [key: string]: unknown;
    };
};

/**
 * API response model for Theme entity.
 * Includes all fields visible to API consumers.
 */
export type ThemePublic = {
    /**
     * Human-readable theme name
     */
    name: string;
    /**
     * Optional theme description
     */
    description?: (string | null);
    /**
     * Classification of theme purpose
     */
    category: ThemeCategory;
    /**
     * Visibility and ownership rules
     */
    scope?: ThemeScope;
    /**
     * Category-specific token payload (CSS variables, Shiki config, motion params)
     */
    tokens?: {
        [key: string]: unknown;
    };
    id: string;
    owner_id: (string | null);
    is_system: boolean;
    created_at: string;
    updated_at: string;
};

/**
 * Visibility and ownership rules for themes.
 *
 * - system: Immutable system-seeded themes, visible to all users
 * - org: Admin-created themes, visible to all org users
 * - personal: User-created themes, visible only to owner
 * - shared: User-created themes, visible to all org users
 */
export type ThemeScope = 'system' | 'org' | 'personal' | 'shared';

/**
 * Which theme category slot is being filled by a binding.
 * Matches ThemeCategory values.
 */
export type ThemeSlot = 'page' | 'cards' | 'syntax' | 'motion';

/**
 * Paginated collection response for Theme list endpoints.
 */
export type ThemesPublic = {
    data: Array<ThemePublic>;
    count: number;
};

/**
 * API input for updating an existing theme.
 * All fields optional - only provided fields are updated.
 *
 * Constraints:
 * - Cannot update is_system themes
 * - Cannot change scope to/from 'system'
 * - Cannot change category (would invalidate tokens)
 */
export type ThemeUpdate = {
    name?: (string | null);
    description?: (string | null);
    scope?: (ThemeScope | null);
    tokens?: ({
    [key: string]: unknown;
} | null);
};
