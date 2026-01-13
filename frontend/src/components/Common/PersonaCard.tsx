import type { Persona, PersonaPublic } from "@/client/types.gen"
// src/components/Common/PersonaCard.tsx
import { type BoxProps, Button, Flex, Text } from "@chakra-ui/react"
import { FiUser } from "react-icons/fi"
import type { IconType } from "react-icons/lib"
import {
  CardBody,
  CardFooter,
  CardHeader,
  CardRoot,
  CardTitle,
  // CardDescription,
} from "../ui/card"

interface PersonaCardProps extends BoxProps {
  // TODO: I should probably figure out which of these is correct and update the api
  persona: PersonaPublic | Persona
  isSelectable?: boolean
  isSelected?: boolean
  onSelect?: () => void
  icon?: IconType
  buttonText?: string
  colorScheme?: string
}

export const PersonaCard = ({
  persona,
  isSelectable = false,
  isSelected = false,
  onSelect,
  icon = FiUser,
  buttonText = "Select Persona",
  colorScheme = "blue",
  ...boxProps
}: PersonaCardProps) => {
  const Icon = icon

  return (
    <CardRoot
      isSelectable={isSelectable}
      isSelected={isSelected}
      onSelect={onSelect}
      borderRadius="lg"
      boxShadow="md"
      height="100%"
      display="flex"
      flexDirection="column"
      {...boxProps}
    >
      <CardHeader>
        <CardTitle fontSize="xl">{persona.name}</CardTitle>
      </CardHeader>
      <CardBody flex="1">
        <Flex direction="column" h="100%">
          <Flex align="center" mb={4}>
            <Icon size={24} />
            <Text ml={2} fontWeight="medium" color={"black"}>
              {persona.general_domain || "General Persona"}
            </Text>
          </Flex>

          {persona.description && <Text mb={3}>{persona.description}</Text>}

          {persona.specific_domain && (
            <Text fontSize="sm" color="gray.500" mb={2}>
              Specific Domain: {persona.specific_domain}
            </Text>
          )}
        </Flex>
      </CardBody>
      <CardFooter>
        {isSelectable && (
          <Button
            width="full"
            colorScheme={colorScheme}
            variant={isSelected ? "solid" : "outline"}
            onClick={onSelect}
          >
            {isSelected ? "Selected" : buttonText}
          </Button>
        )}
      </CardFooter>
    </CardRoot>
  )
}
