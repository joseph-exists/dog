Tinyfoot Frontend Structure Analysis
Tech Stack
The frontend is built with a modern React stack including:

Vite as the build tool
React with TypeScript
TanStack Query for data fetching and cache management
TanStack Router for routing
Chakra UI for component styling and theming

API Communication

The application uses OpenAPI-generated client code to interact with the backend
API clients are auto-generated from an OpenAPI spec file (openapi.json)
The client uses Axios for HTTP requests
Authentication is handled via JWT tokens stored in localStorage

Application Architecture

Component Structure: Well-organized by feature (Admin, Archetypes, Items, Personas)
Routing: File-based routing with TanStack Router
State Management:

TanStack Query for server state
React's built-in state for UI state
Custom hooks for shared functionality (useAuth, useCustomToast)


UI Components: Mix of Chakra UI components and custom components

Authentication and Authorization

JWT-based authentication
Token stored in localStorage
Automatic redirects to login page for unauthenticated users
Role-based UI elements (superuser vs regular user)

Data Flow

API clients make requests to the backend
TanStack Query handles caching, loading states, and error states
Components use React Hook Form for form handling
Mutations update server state and invalidate relevant queries

Project Structure Highlights

Clean separation of concerns between components, hooks, and routing
Consistent component patterns across features
Reusable UI components in the ui directory
Proper error handling with custom toast notifications

This architecture provides a solid foundation for adding new interactive components that query and update the backend. The code follows modern React patterns and best practices for maintainability and scalability.
