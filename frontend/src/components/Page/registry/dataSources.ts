/**
 * Data Sources Registry
 *
 * Provides fetcher functions for user-defined data blocks (DataTable, Chart).
 * Data sources are used to populate dynamic content in pages.
 */

export interface DataSourceDefinition {
  id: string
  label: string
  description: string
  fetcher: () => Promise<unknown[]>
}

/**
 * Placeholder fetcher that returns an empty array.
 * Used as default until real data fetchers are implemented.
 */
const placeholderFetcher = async (): Promise<unknown[]> => []

/**
 * Available data sources for page blocks.
 */
export const dataSources: DataSourceDefinition[] = [
  {
    id: "favorites",
    label: "My Favorites",
    description: "Items you have favorited",
    fetcher: placeholderFetcher,
  },
  {
    id: "myAgents",
    label: "My Agents",
    description: "Agents you have created",
    fetcher: placeholderFetcher,
  },
  {
    id: "myRooms",
    label: "My Rooms",
    description: "Rooms you participate in",
    fetcher: placeholderFetcher,
  },
  {
    id: "activity",
    label: "Activity",
    description: "Recent activity data for charts",
    fetcher: placeholderFetcher,
  },
]

/**
 * Get a data source definition by ID.
 */
export function getDataSource(id: string): DataSourceDefinition | undefined {
  return dataSources.find((source) => source.id === id)
}

/**
 * Fetch data from a data source by ID.
 * Returns an empty array and logs a warning if the source is not found.
 */
export async function fetchDataSource(id: string): Promise<unknown[]> {
  const source = getDataSource(id)
  if (!source) {
    console.warn(`Data source not found: ${id}`)
    return []
  }
  return source.fetcher()
}
