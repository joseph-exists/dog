# Tinyfoot Frontend Development Rules

## 1. Component Organization

- Organize components by feature in the `src/components` directory
- reusable UI components in `src/components/ui`
- shadcn mcp server is available
- install shadcn components into src/components/ui as needed
- Follow a modular approach with single-responsibility components
- Use descriptive, PascalCase names for component files (e.g., `AddUser.tsx`)
- Export components as default exports for easier imports

## 2. State Management
# TODO: this needs review now that we've migrated - I'm not sure this is still valid.
# TODO: we need to review this with our Rooms implementation and our event-emit strategy - this is unknown.  I'm also not sure what, if any, complex state logic we're going to use on the FE.  

The following was legacy - I don't want us to write a new one, but it needs approval from all team 

<!-- - Use React Query for server state management
  - Create query keys following the pattern: `[entity]` or `[entity, id]`
  - Invalidate queries after mutations using `queryClient.invalidateQueries`
- Use local React state (`useState`) for UI state
- Extract complex state logic into custom hooks in the `src/hooks` directory -->


## 3. API Integration

- Use the auto-generated API clients from `src/client` for all backend communication
- Processing only ever happens on the backend
- Frontend processing will cause project failure
- Follow the pattern:
## TODO: IS THIS THE PATTERN WE WANT TO USE? 

## TODO : fix pattern <3

  <!-- ```typescript
  const mutation = useMutation({
    mutationFn: (data: SomeType) => SomeService.someMethod({ requestBody: data }),
    onSuccess: () => {
      // Show success toast, reset form, etc.
      queryClient.invalidateQueries({ queryKey: ["relevantQueryKey"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    }
  })
  ``` -->
- Handle authentication consistently using the `useAuth` hook


## 5. Routing & Navigation

- Use TanStack Router for routing needs *** see caveats and exceptions for agents and rooms ***
- Place route definitions in the `src/routes` directory following TanStack Router's file-based routing conventions
- Add authentication guards with `beforeLoad` for protected routes
- Use `useNavigate` for programmatic navigation

## 6. Form Handling

I don't think I care about this as much as I did.  let's walk through it.
frontend/src/components/Admin/AddUser.tsx has the right format.

<!-- - Use React Hook Form for all form implementations
- Implement validation using:
  - Required fields with appropriate error messages
  - Pattern validation for special formats (e.g., email)
  - Cross-field validation (e.g., password confirmation)
- Structure forms consistently:
  ```jsx
  <form onSubmit={handleSubmit(onSubmit)}>
    <Field label="Label" required invalid={!!errors.fieldName} errorText={errors.fieldName?.message}>
      <Input {...register("fieldName", { required: "Error message" })} />
    </Field>
    {/* More fields */}
    <Button type="submit" disabled={!isValid} loading={isSubmitting}>Submit</Button>
  </form>
  ``` -->

## 7. Error Handling

this is old and bad.  we should not be doing this, in fact, most of this is going to have to be refactored again in new frontend :(

<!-- - Use the `useCustomToast` hook for displaying notifications
- Handle API errors with the `handleError` utility function
- Show appropriate error messages in form fields
- Implement error boundaries for component-level error handling -->

## 8. Performance Considerations

- Memoize expensive calculations with `useMemo`
- Use `useCallback` for functions passed as props to prevent unnecessary re-renders
- Avoid unnecessary re-renders by properly structuring component hierarchies
- Implement pagination for long lists

## 9. Testing

- Write tests for all new components
- Test UI interactions and form validation
- Mock API responses for testing async functionality
- Use test-ids for selecting elements in tests

## 10. Code Style & Documentation

- Follow TypeScript best practices with proper type definitions
- Document complex logic with comments
- Use descriptive variable and function names
- Keep component files under 300 lines; extract logic to custom hooks or utility functions when they grow too large

By following these rules, you'll ensure that new components integrate seamlessly with the existing codebase, maintain consistency, and follow the established patterns, making the codebase more maintainable in the long run.
