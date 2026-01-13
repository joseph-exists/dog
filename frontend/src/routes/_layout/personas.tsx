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

import { PersonasService } from "../../client"
import { PersonaActionsMenu } from "../../components/Common/PersonaActionsMenu"
import PendingPersonas from "../../components/Pending/PendingPersonas"
import AddPersona from "../../components/Personas/AddPersona"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "../../components/ui/pagination"

const personasSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 5

function getPersonasQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      PersonasService.readPersonas({
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
      }),
    queryKey: ["personas", { page }],
  }
}

export const Route = createFileRoute("/_layout/personas")({
  component: Personas,
  validateSearch: (search) => personasSearchSchema.parse(search),
})

function PersonasTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getPersonasQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) =>
    navigate({
      search: (prev: { [key: string]: string }) => ({ ...prev, page }),
    })

  const personas = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingPersonas />
  }

  if (personas.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any personas yet</EmptyState.Title>
            <EmptyState.Description>
              Add a new persona to get started
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
            <Table.ColumnHeader w="5%">ID</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">Name</Table.ColumnHeader>
            <Table.ColumnHeader w="30%">Description</Table.ColumnHeader>
            <Table.ColumnHeader w="30%">Long Description</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">General Domain</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">Specific Domain</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">General Domain High</Table.ColumnHeader>
            <Table.ColumnHeader w="10%">
              Specific Domain High
            </Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {personas?.map((persona) => (
            <Table.Row key={persona.id} opacity={isPlaceholderData ? 0.5 : 1}>
              <Table.Cell truncate maxW="5%">
                {persona.id}
              </Table.Cell>
              <Table.Cell truncate maxW="10%">
                {persona.name}
              </Table.Cell>
              <Table.Cell
                color={!persona.description ? "gray" : "inherit"}
                truncate
                maxW="5%"
              >
                {persona.description || "N/A"}
              </Table.Cell>
              <Table.Cell
                color={!persona.long_description ? "gray" : "inherit"}
                truncate
                maxW="50%"
              >
                {persona.long_description || "N/A"}
              </Table.Cell>
              <Table.Cell
                color={!persona.general_domain ? "gray" : "inherit"}
                truncate
                maxW="10%"
              >
                {persona.general_domain || "N/A"}
              </Table.Cell>
              <Table.Cell
                color={!persona.specific_domain ? "gray" : "inherit"}
                truncate
                maxW="10%"
              >
                {persona.specific_domain || "N/A"}
              </Table.Cell>
              <Table.Cell
                color={!persona.general_domain_high ? "gray" : "inherit"}
                truncate
                maxW="10%"
              >
                {persona.general_domain_high || "N/A"}
              </Table.Cell>
              <Table.Cell
                color={!persona.specific_domain_high ? "gray" : "inherit"}
                truncate
                maxW="10%"
              >
                {persona.specific_domain_high || "N/A"}
              </Table.Cell>
              <Table.Cell width="10%">
                <PersonaActionsMenu persona={persona} />
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

function Personas() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Personas Management
      </Heading>
      <AddPersona />
      <PersonasTable />
    </Container>
  )
}
