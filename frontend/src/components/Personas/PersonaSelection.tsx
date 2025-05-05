// src/components/Personas/PersonaSelection.tsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Box,
  SimpleGrid,
  Heading,
  Text,
  Button,
  Container,
  VStack,
  Flex,
  Spinner,
} from "@chakra-ui/react";
import { PersonasService } from "@/client";
import { PersonaCard } from "@/components/Common/PersonaCard";
import { PersonaPublic } from "@/client/types.gen";
import useCustomToast from "@/hooks/useCustomToast";

// This would be connected to an API in the future
interface SelectPersonaMutationParams {
  personaId: string;
}

const PERSONA_LIMIT = 3; // Show only 3 personas for selection

export const PersonaSelection = () => {
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(
    null,
  );
  const [selectionMade, setSelectionMade] = useState(false);
  const queryClient = useQueryClient();
  const { showSuccessToast, showErrorToast } = useCustomToast();


  // Fetch personas for selection
  const { data, isLoading, error } = useQuery({
    queryKey: ["personas", "selection"],
    queryFn: () => PersonasService.readPersonas({ limit: PERSONA_LIMIT }),
  });

  // Simulating a mutation to select a persona (will be replaced with actual API call)
  const selectPersonaMutation = useMutation({
    mutationFn: ({ personaId }: SelectPersonaMutationParams) => {
      // This is a placeholder for the real API call
      // Return a promise that resolves after a delay to simulate API call
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          resolve();
        }, 800);
      });
    },
    onSuccess: () => {
      showSuccessToast("Persona selected successfully!");
      setSelectionMade(true);

      // Invalidate relevant queries if needed
      queryClient.invalidateQueries({ queryKey: ["personas"] });
    },
    onError: (error) => {
      showErrorToast("Failed to select persona. Please try again.");
      console.error("Error selecting persona:", error);
    },
  });

  const handleSelectPersona = (personaId: string) => {
    setSelectedPersonaId(personaId);
  };

  const handleConfirmSelection = () => {
    if (selectedPersonaId) {
      selectPersonaMutation.mutate({ personaId: selectedPersonaId });
    }
  };

  if (isLoading) {
    return (
      <Flex justify="center" align="center" height="300px">
        <Spinner size="xl" />
      </Flex>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" p={8}>
        <Heading size="md" color="red.500">
          Error loading personas
        </Heading>
        <Text mt={4}>Please try again later</Text>
      </Box>
    );
  }

  const personas = data?.data || [];

  if (personas.length === 0) {
    return (
      <Box textAlign="center" p={8}>
        <Heading size="md">No personas available</Heading>
        <Text mt={4}>Please create some personas first</Text>
      </Box>
    );
  }

  // When selection is made, show only the selected persona
  if (selectionMade && selectedPersonaId) {
    const selectedPersona = personas.find((p) => p.id === selectedPersonaId);

    if (!selectedPersona) return null;

    return (
      <Container maxW="xl" py={8}>
        <VStack>
          <Heading size="lg">Your Selected Persona</Heading>
          <Box width="100%" maxW="400px">
            <PersonaCard
              persona={selectedPersona}
              isSelected={true}
              buttonText="Your Active Persona"
            />
          </Box>
        </VStack>
      </Container>
    );
  }

  return (
    <Container maxW="6xl" py={8}>
      <VStack>
        <Heading size="lg">Choose Your Persona</Heading>
        <Text>
          Select a persona that best represents you in this application
        </Text>

        <SimpleGrid columns={{ base: 1, md: 3 }} width="100%">
          {personas.map((persona) => (
            <PersonaCard
              key={persona.id}
              persona={persona}
              isSelectable
              isSelected={selectedPersonaId === persona.id}
              onSelect={() => handleSelectPersona(persona.id)}
            />
          ))}
        </SimpleGrid>

        <Button
          colorScheme="blue"
          size="lg"
          disabled={!selectedPersonaId}
          onClick={handleConfirmSelection}
          loading={selectPersonaMutation.isPending}
        >
          Confirm Selection
        </Button>
      </VStack>
    </Container>
  );
};

export default PersonaSelection;
