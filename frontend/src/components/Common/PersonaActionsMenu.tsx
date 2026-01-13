import { IconButton } from "@chakra-ui/react"
import { BsThreeDotsVertical } from "react-icons/bs"
import { MenuContent, MenuRoot, MenuTrigger } from "../ui/menu"

import type { PersonaPublic } from "../../client"
import DeletePersona from "../Personas/DeletePersona"
import EditPersona from "../Personas/EditPersona"

interface PersonaActionsMenuProps {
  persona: PersonaPublic
}

export const PersonaActionsMenu = ({ persona }: PersonaActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton variant="ghost" color="inherit">
          <BsThreeDotsVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditPersona persona={persona} />
        <DeletePersona id={persona.id} />
      </MenuContent>
    </MenuRoot>
  )
}
