# TinyFoot Backend Development Tasks

This document outlines the tasks needed to complete the TinyFoot backend implementation as specified in the capture-structure.md requirements. Each task includes specific exit criteria and validation steps.

## Existing Models and API Testing



## CRUD Operations

### TASK 7: REVIEW ALL TASKS BELOW TO ENSURE THEY STILL NEED TO HAPPEN

### Task 8: Implement Quality CRUD Operations
**Description**: Add CRUD operations for Quality model in crud.py.

**Implementation Details**:
- Create create_quality function
- Create get_quality and get_qualities functions
- Create update_quality function
- Create delete_quality function

**Exit Criteria**:
- All required CRUD operations are implemented
- Functions follow the established pattern
- All operations include proper error handling

**Validation**:
- Write unit tests for each CRUD operation
- Verify all tests pass

### Task 9: Implement Trait CRUD Operations
**Description**: Add CRUD operations for Trait model in crud.py.

**Implementation Details**:
- Create create_trait function
- Create get_trait and get_traits functions
- Create update_trait function
- Create delete_trait function

**Exit Criteria**:
- All required CRUD operations are implemented
- Functions follow the established pattern
- All operations include proper error handling

**Validation**:
- Write unit tests for each CRUD operation
- Verify all tests pass

### Task 10: Implement Relationship CRUD Operations
**Description**: Add CRUD operations for trait assignment to archetypes and personas.

Additional during discovery for CRUD and API routes:

Trait Inheritance: When a Persona is associated with an Archetype, it should inherit all of that Archetype's traits. We'll need to add code to handle this in the CRUD operation for creating a Persona.
Trait Modification Rules: Some traits are marked as modifiable, some are modifiable only during creation, and some are required. We'll need to enforce these rules in the API endpoints.
Maximum Active Personas: Some traits have a max_active_personas limit. We'll need to add validation logic to enforce this limit.
Mutually Exclusive Traits: The example mentions "Chaotic" and "Harmonious" as mutually exclusive traits. We might need to add a way to define trait groups where only one trait from the group can be active on a Persona.

**Implementation Details**:
- Create add_trait_to_archetype function with configuration parameters
- Create remove_trait_from_archetype function
- Create add_trait_to_persona function
- Create remove_trait_from_persona function
- Create update_trait_in_persona function if needed

**Exit Criteria**:
- All required relationship CRUD operations are implemented
- Functions follow the established pattern
- All operations include proper error handling

**Validation**:
- Write unit tests for each CRUD operation
- Verify all tests pass

### Task 11: Update Persona CRUD Operations
**Description**: Update persona CRUD operations to handle archetype relationships.

**Implementation Details**:
- Update create_persona to associate with an archetype
- Update create_persona to inherit traits from the archetype as needed
- Update functions to handle trait inheritance rules

**Exit Criteria**:
- Updated CRUD operations handle archetype and trait relationships
- Business rules for trait inheritance are properly implemented

**Validation**:
- Write unit tests for each updated CRUD operation
- Verify all tests pass

## API Routes

### Task 12: Implement Qualities API Routes
**Description**: Create qualities.py route file with CRUD endpoints.

**Implementation Details**:
- Create router with /qualities prefix
- Add GET endpoint for retrieving all qualities with pagination
- Add GET endpoint for retrieving a specific quality
- Add POST endpoint for creating a quality (superuser only)
- Add PUT endpoint for updating a quality (superuser only)
- Add DELETE endpoint for deleting a quality (superuser only)

**Exit Criteria**:
- All required endpoints are implemented
- Endpoints follow established pattern
- Appropriate permissions are enforced
- Response models are correctly defined

**Validation**:
- Write API tests for each endpoint
- Verify all tests pass

### Task 13: Implement Traits API Routes
**Description**: Create traits.py route file with CRUD endpoints.

**Implementation Details**:
- Create router with /traits prefix
- Add GET endpoint for retrieving all traits with pagination
- Add GET endpoint for retrieving a specific trait
- Add POST endpoint for creating a trait (superuser only)
- Add PUT endpoint for updating a trait (superuser only)
- Add DELETE endpoint for deleting a trait (superuser only)

**Exit Criteria**:
- All required endpoints are implemented
- Endpoints follow established pattern
- Appropriate permissions are enforced
- Response models are correctly defined

**Validation**:
- Write API tests for each endpoint
- Verify all tests pass

### Task 14: Update Archetypes API Routes
**Description**: Update archetypes.py to handle trait relationships.

**Implementation Details**:
- Add endpoint for adding a trait to an archetype
- Add endpoint for removing a trait from an archetype
- Add endpoint for listing traits associated with an archetype
- Add endpoint for updating trait configuration within an archetype

**Exit Criteria**:
- New endpoints are implemented
- Endpoints follow established pattern
- Appropriate permissions are enforced
- Response models are correctly defined

**Validation**:
- Write API tests for each new and updated endpoint
- Verify all tests pass

### Task 15: Update Personas API Routes
**Description**: Update personas.py to handle archetype and trait relationships.

**Implementation Details**:
- Update create persona endpoint to require archetype association
- Add endpoint for listing traits associated with a persona
- Add endpoint for updating trait values within a persona
- Add validation to ensure trait modifications follow archetype rules

**Exit Criteria**:
- Updated endpoints handle archetype and trait relationships
- Business rules for trait inheritance and modification are enforced
- Appropriate permissions are enforced
- Response models are correctly defined

**Validation**:
- Write API tests for each updated endpoint
- Verify all tests pass

### Task 16: Update API Router Registration
**Description**: Update app/api/main.py to include the new routers.

**Implementation Details**:
- Import new router modules
- Add include_router statements for new routers
- Ensure routes are included in the appropriate order

**Exit Criteria**:
- All new routers are registered correctly
- API documentation shows all expected endpoints

**Validation**:
- Start the API server and verify all routes are accessible
- Check the OpenAPI documentation for completeness

## Tests

### Task 17: Write Trait Model Tests
**Description**: Create tests for the Trait model and its relationships.

**Implementation Details**:
- Create test_trait.py in app/tests/api/routes/
- Add tests for creating, retrieving, updating, and deleting traits
- Test permission enforcement for trait operations

**Exit Criteria**:
- All trait endpoints have corresponding tests
- Tests verify both success and failure cases
- Tests verify permission enforcement

**Validation**:
- Run tests and verify they pass
- Verify test coverage with coverage tool

### Task 18: Write Quality Model Tests
**Description**: Create tests for the Quality model and its endpoints.

**Implementation Details**:
- Create test_quality.py in app/tests/api/routes/
- Add tests for creating, retrieving, updating, and deleting qualities
- Test permission enforcement for quality operations

**Exit Criteria**:
- All quality endpoints have corresponding tests
- Tests verify both success and failure cases
- Tests verify permission enforcement

**Validation**:
- Run tests and verify they pass
- Verify test coverage with coverage tool

### Task 19: Write Archetype-Trait Relationship Tests
**Description**: Create tests for the archetype-trait relationship operations.

**Implementation Details**:
- Update or create tests for adding traits to archetypes
- Test trait inheritance rules
- Test trait configuration within archetypes

**Exit Criteria**:
- All archetype-trait relationship operations have corresponding tests
- Tests verify both success and failure cases
- Tests verify business rules are enforced

**Validation**:
- Run tests and verify they pass
- Verify test coverage with coverage tool

### Task 20: Write Persona-Trait Relationship Tests
**Description**: Create tests for the persona-trait relationship operations.

**Implementation Details**:
- Update or create tests for persona creation with archetype
- Test trait inheritance from archetype to persona
- Test trait modification rules based on archetype configuration

**Exit Criteria**:
- All persona-trait relationship operations have corresponding tests
- Tests verify both success and failure cases
- Tests verify business rules are enforced

**Validation**:
- Run tests and verify they pass
- Verify test coverage with coverage tool

## Integration and Final Verification

### Task 21: End-to-End Testing
**Description**: Verify the complete flow works as expected.

**Implementation Details**:
- Create a test that simulates the user flow described in capture-structure.md
- Test creating an archetype with traits
- Test creating a persona with that archetype
- Test trait inheritance and modification

**Exit Criteria**:
- End-to-end test passes successfully
- All business requirements are met

**Validation**:
- Run the end-to-end test
- Manually test the flow with API requests

### Task 22: Documentation and Final Review
**Description**: Document the new features and perform a final review.

**Implementation Details**:
- Update docstrings for all new functions and endpoints
- Verify OpenAPI documentation is complete and accurate
- Perform a code review against RULES.md guidelines

**Exit Criteria**:
- All new code has appropriate documentation
- Code follows established patterns and guidelines
- No regression issues are found

**Validation**:
- Run all tests and verify they pass
- Review OpenAPI documentation for completeness
- Manual verification of key workflows
