import { PersonaSelection } from "@/components/Personas/SelectPersona"
import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"

const personaSelectSearchSchema = z.object({
  page: z.number().catch(1),
})

export const Route = createFileRoute("/_layout/persona-select")({
  component: PersonaSelection,
  validateSearch: (search) => personaSelectSearchSchema.parse(search),
})
