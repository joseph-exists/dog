import {
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"

import { ArchetypesService } from "../../client"
import AddArchetype from "../../components/Archetypes/AddArchetype"
import { ArchetypeActionsMenu } from "../../components/Common/ArchetypeActionsMenu"
import PendingArchetypes from "../../components/Pending/PendingArchetypes"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination.tsx"

const archetypesSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 5

function getArchetypesQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      ArchetypesService.readArchetypes({
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
      }),
    queryKey: ["archetypes", { page }],
  }
}

export const Route = createFileRoute("/_layout/archetypes")({
  component: Archetypes,
  validateSearch: (search) => archetypesSearchSchema.parse(search),
})

function ArchetypesTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getArchetypesQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: { [key: string]: string }) => ({ ...prev, page }),
    })

  const archetypes = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingArchetypes />
  }

  if (archetypes.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>
              You don't have any archetypes yet
            </EmptyState.Title>
            <EmptyState.Description>
              Add a new archetype to get started
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  return (
    <>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="30%">ID</Table.ColumnHeader>
            <Table.ColumnHeader w="30%">Name</Table.ColumnHeader>
            <Table.ColumnHeader w="30%">Description</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {archetypes?.map((archetype) => (
            <Table.Row key={archetype.id} opacity={isPlaceholderData ? 0.5 : 1}>
              <Table.Cell truncate maxW="30%">
                {archetype.id}
              </Table.Cell>
              <Table.Cell truncate maxW="30%">
                {archetype.name}
              </Table.Cell>
              <Table.Cell
                color={!archetype.description ? "gray" : "inherit"}
                truncate
                maxW="30%"
              >
                {archetype.description || "N/A"}
              </Table.Cell>
              <Table.Cell width="10%">
                <ArchetypeActionsMenu archetype={archetype} />
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
      <Flex justifyContent="flex-end" mt={4}>
        <PaginationRoot
          count={count}
          pageSize={PER_PAGE}
          onPageChange={({ page }) => setPage(page)}
        >
          <Flex>
            <PaginationPrevTrigger />
            <PaginationItems />
            <PaginationNextTrigger />
          </Flex>
        </PaginationRoot>
      </Flex>
    </>
  )
}

function Archetypes() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Archetypes Management
      </Heading>
      <AddArchetype />
      <ArchetypesTable />
    </Container>
  )
}
