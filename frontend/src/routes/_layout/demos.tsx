import { createFileRoute } from "@tanstack/react-router"
import { DemoLibraryPage } from "@/components/Demo/DemoLibraryPage"
 
export const Route = createFileRoute("/_layout/demos")({
   component: DemosPage,
   head: () => ({
     meta: [{ title: "Demo Library" }],
   }),
 })
 
 function DemosPage() {
   return <DemoLibraryPage />
 }