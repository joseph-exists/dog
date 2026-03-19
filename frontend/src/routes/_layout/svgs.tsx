import { createFileRoute } from "@tanstack/react-router"
import type { ReactNode } from "react"
import {
  BatchSeedSvgDialog,
  CreateSvgDialog,
  SvgOperationsPanel,
  SvgShell,
  SvgsGalleryPanel,
  TesserStudioPanel,
  type SvgPanelConfig,
} from "@/components/Svg"

export const Route = createFileRoute("/_layout/svgs")({
  component: SvgsPage,
  head: () => ({
    meta: [{ title: "SVG Library" }],
  }),
})

function SvgsPage() {
  const panelComponents: Record<string, () => ReactNode> = {
    gallery: () => <SvgsGalleryPanel />,
    tesserStudio: () => <TesserStudioPanel />,
    operations: () => <SvgOperationsPanel />,
  }

  const panels: SvgPanelConfig[] = [
    {
      id: "gallery",
      kind: "svgGallery",
      prominence: "primary",
      title: "Gallery",
      render: panelComponents.gallery,
      min_size: 55,
    },
    {
      id: "tesser-studio",
      kind: "tesserStudio",
      prominence: "auxiliary",
      title: "Tesser Studio",
      render: panelComponents.tesserStudio,
      min_size: 22,
      default_size: 58,
    },
    {
      id: "operations",
      kind: "svgOperations",
      prominence: "auxiliary",
      title: "Operations",
      render: panelComponents.operations,
      min_size: 20,
      default_size: 42,
    },
  ]

  return (
    <SvgShell
      title="SVG Library"
      description="Browse the gallery, sculpt quick combinatoric studies, and open a direct line into Tesser Studio for script-driven SVG generation with room to explore both precision and surprise."
      panels={panels}
      actions={
        <div className="flex items-center gap-2">
          <BatchSeedSvgDialog />
          <CreateSvgDialog />
        </div>
      }
    />
  )
}
