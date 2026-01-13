import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
// src/components/Personas/SelectPersona.tsx
import { useState } from "react"
import { PersonasService } from "../../client"
import { PersonaCard } from "../../components/Common/PersonaCard"
import { usePersona } from "../../contexts/PersonaContext"
import useCustomToast from "../../hooks/useCustomToast"

const PERSONA_LIMIT = 3 // Show only 3 personas for selection

export const PersonaSelection = () => {
  const [localSelectedId, setLocalSelectedId] = useState<string | null>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Use the context for global state
  const { selectedPersonaId, selectionComplete, selectPersona } = usePersona()

  // Fetch personas for selection
  const { data, isLoading, error } = useQuery({
    queryKey: ["personas", "selection"],
    queryFn: () => PersonasService.readPersonas({ limit: PERSONA_LIMIT }),
  })

  // When selection complete, fetch selected persona details
  const { data: selectedPersonaData } = useQuery({
    queryKey: ["personas", selectedPersonaId],
    queryFn: () =>
      selectedPersonaId
        ? PersonasService.readPersona({ id: selectedPersonaId })
        : null,
    enabled: !!selectedPersonaId && selectionComplete,
  })

  const handleSelectPersona = (personaId: string) => {
    setLocalSelectedId(personaId)
  }

  const handleConfirmSelection = () => {
    if (localSelectedId) {
      try {
        selectPersona(localSelectedId)
        showSuccessToast("Persona selected successfully!")
      } catch (err) {
        showErrorToast("Failed to select persona")
        console.error(err)
      }
    }
  }

  if (isLoading) {
    return (
      <Flex justify="center" align="center" height="300px">
        <Spinner size="xl" />
      </Flex>
    )
  }

  if (error) {
    return (
      <Box textAlign="center" p={8}>
        <Heading size="md" color="red.500">
          Error loading personas
        </Heading>
        <Text mt={4}>Please try again later</Text>
      </Box>
    )
  }

  const personas = data?.data || []

  if (personas.length === 0) {
    return (
      <Box textAlign="center" p={8}>
        <Heading size="md">No personas available</Heading>
        <Text mt={4}>Please create some personas first</Text>
      </Box>
    )
  }

  // When selection is complete, show only the selected persona
  if (selectionComplete && selectedPersonaId && selectedPersonaData) {
    return (
      <Container maxW="xl" py={8}>
        <VStack>
          <Heading size="lg">Your Selected Persona</Heading>
          <Box width="100%" maxW="400px">
            <PersonaCard
              persona={selectedPersonaData}
              isSelected={true}
              buttonText="Your Active Persona"
            />
          </Box>
        </VStack>
      </Container>
    )
  }

  return (
    <Container maxW="6xl" py={8}>
      <VStack>
        <Heading size="lg">Choose Your Persona</Heading>
        <Text>
          Select the persona that best represents you in this application.
        </Text>

        <SimpleGrid columns={{ base: 1, md: 3 }} width="100%">
          {personas.map((persona) => (
            <PersonaCard
              key={persona.id}
              persona={persona}
              isSelectable
              isSelected={localSelectedId === persona.id}
              onSelect={() => handleSelectPersona(persona.id)}
            />
          ))}
        </SimpleGrid>

        <Button
          colorScheme="blue"
          size="lg"
          disabled={!localSelectedId}
          onClick={handleConfirmSelection}
        >
          Confirm Selection
        </Button>
      </VStack>
    </Container>
  )
}

export default PersonaSelection
