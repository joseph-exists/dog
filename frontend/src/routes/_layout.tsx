import { Flex } from "@chakra-ui/react"
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import Navbar from "@/components/Common/Navbar"
import Sidebar from "@/components/Common/Sidebar"
//import { usePersona } from "@/contexts/PersonaContext"
import { isLoggedIn } from "@/hooks/useAuth"
// import { Navigate } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  // const { selectionComplete } = usePersona()

  // if (!selectionComplete && location.pathname !== '/select-persona') {
  //  return <Navigate to="/select-persona" />
  //  }

  return (
    <Flex direction="column" h="100vh">
      <Navbar />
      <Flex flex="1" overflow="hidden">
        <Sidebar />
        <Flex flex="1" direction="column" p={4} overflowY="auto">
          <Outlet />
        </Flex>
      </Flex>
    </Flex>
  )
}
export default Layout
