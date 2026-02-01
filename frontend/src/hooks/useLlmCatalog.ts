/**
 * useLlmCatalog Hook
 *
 * Provides access to the system-wide LLM provider and model catalog.
 * Uses TanStack Query with infinite cache (catalog rarely changes).
 *
 * This hook returns model options in the format expected by existing
 * components
 *
 * // NOPE.  JUST DELETED 500 lines of code that wasted about a week,
 * // everything here is available from the backend in client/core - read the FRONTEND rules again.
 *
 */

// TODO: Reimplement using client SDK directly
export default function useLlmCatalog() {
  return {
    modelsByProvider: {},
    allModels: [],
    isLoading: false,
    findModel: () => null,
    formatModelName: (name: string) => name,
    getProviderTypeLabel: () => "",
    createCustomModel: async () => {},
    isCreatingCustomModel: false,
  }
}
