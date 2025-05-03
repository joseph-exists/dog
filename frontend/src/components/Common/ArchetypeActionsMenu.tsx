import { IconButton } from "@chakra-ui/react";
import { BsThreeDotsVertical } from "react-icons/bs";
import { MenuContent, MenuRoot, MenuTrigger } from "../ui/menu";

import type { ArchetypePublic } from "../../client";
import DeleteArchetype from "../Archetypes/DeleteArchetype";
import EditArchetype from "../Archetypes/EditArchetype";

interface ArchetypeActionsMenuProps {
  archetype: ArchetypePublic;
}

export const ArchetypeActionsMenu = ({
  archetype,
}: ArchetypeActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton variant="ghost" color="inherit">
          <BsThreeDotsVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditArchetype archetype={archetype} />
        <DeleteArchetype id={archetype.id} />
      </MenuContent>
    </MenuRoot>
  );
};
