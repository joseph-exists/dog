import { Avatar, Box, Button, Card, Container, Text } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <>
      <Container maxW="full">
        <Box pt={12} m={4}>
          <Text fontSize="2xl">
            Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
          </Text>
          <Text>Welcome back, how nice to see you again!</Text>
        </Box>
        <Box>
          <Card.Root width="320px">
            <Card.Body gap="2">
              <Avatar.Root size="lg" shape="rounded">
                <Avatar.Image src="https://picsum.photos/200/300" />
                <Avatar.Fallback name="Beeboop The Flatterer" />
              </Avatar.Root>
              <Card.Title mt="2">Boop Boop For Real Boop</Card.Title>
              <Card.Description>
                This is IN THE INDEX card body. Lorem ipsum dolor sit amet,
                consectetur adipiscing elit. Curabitur nec odio vel dui euismod
                fermentum. Curabitur nec odio vel dui euismod fermentum. This is
                the card body. Lorem ipsum dolor sit amet, consectetur
                adipiscing elit. Curabitur nec odio vel dui euismod fermentum.
                Curabitur nec odio vel dui euismod fermentum. This is the card
                body. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                Curabitur nec odio vel dui euismod fermentum. Curabitur nec odio
                vel dui euismod fermentum.
              </Card.Description>
            </Card.Body>
            <Card.Footer justifyContent="flex-end">
              <Button variant="outline">View</Button>
              <Button>Join</Button>
            </Card.Footer>
          </Card.Root>
        </Box>
      </Container>
    </>
  )
}
