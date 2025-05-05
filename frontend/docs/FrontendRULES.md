# Tinyfoot Frontend Development Rules

Based on my analysis of the Tinyfoot frontend codebase, here's a comprehensive set of rules to follow when developing new components:

## 1. Component Organization

- Organize components by feature in the `src/components` directory
- Place reusable UI components in `src/components/ui`
- Follow a modular approach with single-responsibility components
- Use descriptive, PascalCase names for component files (e.g., `AddUser.tsx`)
- Export components as default exports for easier imports

## 2. State Management

- Use React Query for server state management
  - Create query keys following the pattern: `[entity]` or `[entity, id]`
  - Invalidate queries after mutations using `queryClient.invalidateQueries`
- Use local React state (`useState`) for UI state
- Extract complex state logic into custom hooks in the `src/hooks` directory
- Use controlled components with React Hook Form for form handling

## 3. API Integration

- Use the auto-generated API clients from `src/client` for all backend communication
- Follow the pattern:
  ```typescript
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
  ```
- Handle authentication consistently using the `useAuth` hook
- Always handle API errors using the `handleError` utility

## 4. UI & Styling

- Use Chakra UI components for consistent styling
- Follow the component hierarchy in dialogs, forms, and layouts as seen in existing components
- Use the design system tokens for colors, spacing, and typography
- Implement responsive designs using Chakra's responsive syntax (e.g., `display={{ base: "flex", md: "none" }}`)
- Use Flex and Box components for layout
- Use semantic HTML elements where appropriate

## 5. Routing & Navigation

- Use TanStack Router for all routing needs
- Place route definitions in the `src/routes` directory following TanStack Router's file-based routing conventions
- Add authentication guards with `beforeLoad` for protected routes
- Use `useNavigate` for programmatic navigation

## 6. Form Handling

- Use React Hook Form for all form implementations
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
  ```

## 7. Error Handling

- Use the `useCustomToast` hook for displaying notifications
- Handle API errors with the `handleError` utility function
- Show appropriate error messages in form fields
- Implement error boundaries for component-level error handling

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
