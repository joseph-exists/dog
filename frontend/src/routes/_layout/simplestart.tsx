import { Avatar, Box, Button, Card, Container } from "@chakra-ui/react"

import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/simplestart")({})
;<Container>
  <Box>
    <Card.Root width="320px">
      <Card.Body gap="2">
        <Avatar.Root size="lg" shape="rounded">
          <Avatar.Image src="https://picsum.photos/200/300" />
          <Avatar.Fallback name="Beeboop The Flatterer" />
        </Avatar.Root>
        <Card.Title mt="2">Bee Boop For Real Boop</Card.Title>
        <Card.Description>
          This is the card body. Lorem ipsum dolor sit amet, consectetur
          adipiscing elit. Curabitur nec odio vel dui euismod fermentum.
          Curabitur nec odio vel dui euismod fermentum. This is the card body.
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur nec
          odio vel dui euismod fermentum. Curabitur nec odio vel dui euismod
          fermentum. This is the card body. Lorem ipsum dolor sit amet,
          consectetur adipiscing elit. Curabitur nec odio vel dui euismod
          fermentum. Curabitur nec odio vel dui euismod fermentum.
        </Card.Description>
      </Card.Body>
      <Card.Footer justifyContent="flex-end">
        <Button variant="outline">View</Button>
        <Button>Join</Button>
      </Card.Footer>
    </Card.Root>
  </Box>
</Container>
