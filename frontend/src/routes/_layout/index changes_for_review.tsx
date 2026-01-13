import {
  Box,
  CardBody,
  CardFooter,
  CardHeader,
  Card as ChakraCard,
  Container,
  Heading,
  Icon,
  SimpleGrid,
  Text,
} from "@chakra-ui/react"

// import { FeatureCard } from "@/components/Common/FeatureCard";

import { createFileRoute } from "@tanstack/react-router"
import {
  FiActivity,
  FiPackage,
  // FiArrowRight,
  FiUser,
  FiUsers,
} from "react-icons/fi"

import { LinkButton } from "@/components/ui/link-button"
import { Link } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/index changes_for_review")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <Container maxW="container.x1" py={8}>
      <Box>
        <Heading mb={6}>
          Welcome, {currentUser?.full_name || currentUser?.email}{" "}
        </Heading>
      </Box>
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} rowGap={6}>
        {/* User Profile Card */}
        <ChakraCard.Root>
          <CardHeader>
            <Heading size="md">User Profile</Heading>
          </CardHeader>
          <CardBody>
            <Icon as={FiUser} boxSize={8} mb={4} color="teal.500" />
            <Text>Manage your personal information and account settings</Text>
          </CardBody>
          <CardFooter>
            <LinkButton
              // rightIcon={<FiArrowRight />}
              colorScheme="teal"
              variant="outline"
              as={Link}
              href="/settings"
            >
              Go to Profile
            </LinkButton>
          </CardFooter>
        </ChakraCard.Root>

        {/* Items Management Card */}
        <ChakraCard.Root>
          <CardHeader>
            <Heading size="md">Items</Heading>
          </CardHeader>
          <CardBody>
            <Icon as={FiPackage} boxSize={8} mb={4} color="blue.500" />
            <Text>View and manage your items collection</Text>
          </CardBody>
          <CardFooter>
            <LinkButton
              // rightIcon={<FiArrowRight />}
              colorScheme="blue"
              variant="outline"
              as="a"
              href="/items"
            >
              Manage Items
            </LinkButton>
          </CardFooter>
        </ChakraCard.Root>

        {/* Personas Card */}
        <ChakraCard.Root>
          <CardHeader>
            <Heading size="md">Personas</Heading>
          </CardHeader>
          <CardBody>
            <Icon as={FiUsers} boxSize={8} mb={4} color="purple.500" />
            <Text>Create and manage character personas</Text>
          </CardBody>
          <CardFooter>
            <LinkButton
              // rightIcon={<FiArrowRight />}
              colorScheme="purple"
              variant="outline"
              as="a"
              href="/personas"
            >
              View Personas
            </LinkButton>
          </CardFooter>
        </ChakraCard.Root>

        {/* Archetypes Card */}
        <ChakraCard.Root>
          <CardHeader>
            <Heading size="md">Archetypes</Heading>
          </CardHeader>
          <CardBody>
            <Icon as={FiActivity} boxSize={8} mb={4} color="orange.500" />
            <Text>Browse and create character archetypes</Text>
          </CardBody>
          <CardFooter>
            <LinkButton
              // rightIcon={<FiArrowRight />}
              colorScheme="orange"
              variant="outline"
              as="a"
              href="/archetypes"
            >
              Explore Archetypes
            </LinkButton>
          </CardFooter>
        </ChakraCard.Root>
      </SimpleGrid>
    </Container>
  )
}
