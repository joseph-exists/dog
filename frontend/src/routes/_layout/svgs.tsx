import { createFileRoute } from "@tanstack/react-router"
import type { ReactNode } from "react"
import {
  BatchSeedSvgDialog,
  CreateSvgDialog,
  SvgOperationsPanel,
  SvgShell,
  SvgsGalleryPanel,
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
      id: "operations",
      kind: "svgOperations",
      prominence: "auxiliary",
      title: "Operations",
      render: panelComponents.operations,
      min_size: 20,
      default_size: 100,
    },
  ]

  return (
    <SvgShell
      title="SVG Library"
      description="Browse your SVG assets, validate quickly in-gallery, and run batch seeding controls for rapid content population."
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
