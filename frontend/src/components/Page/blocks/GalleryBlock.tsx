// src/components/Page/blocks/GalleryBlock.tsx
import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { BlockContainer } from "../primitives"

export interface GalleryImage {
  id: string
  url: string
  alt?: string
  caption?: string
}

export interface GalleryBlockConfig {
  columns: number
  lightbox: boolean
}

export interface GalleryBlockProps {
  config: GalleryBlockConfig
  images: GalleryImage[]
}

const gridColumnClasses: Record<number, string> = {
  1: "grid-cols-1",
  2: "grid-cols-2",
  3: "grid-cols-3",
  4: "grid-cols-4",
}

/**
 * GalleryBlock - Displays a grid of images with optional lightbox
 *
 * Renders images in a configurable grid layout (1-4 columns).
 * When lightbox is enabled, clicking an image opens it in a dialog.
 * Returns null if no images are provided.
 */
export function GalleryBlock({ config, images }: GalleryBlockProps) {
  const [selectedImage, setSelectedImage] = useState<GalleryImage | null>(null)

  if (images.length === 0) {
    return null
  }

  const columnClass = gridColumnClasses[config.columns] || "grid-cols-2"

  const renderImage = (image: GalleryImage) => (
    <img
      src={image.url}
      alt={image.alt || ""}
      className="aspect-square object-cover rounded-md w-full h-full"
    />
  )

  return (
    <>
      <BlockContainer title="Gallery">
        <div className={cn("grid gap-2 p-4", columnClass)}>
          {images.map((image) =>
            config.lightbox ? (
              <button
                key={image.id}
                type="button"
                onClick={() => setSelectedImage(image)}
                className="cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-md"
              >
                {renderImage(image)}
              </button>
            ) : (
              <div key={image.id}>{renderImage(image)}</div>
            ),
          )}
        </div>
      </BlockContainer>

      <Dialog
        open={selectedImage !== null}
        onOpenChange={(open) => !open && setSelectedImage(null)}
      >
        <DialogContent className="max-w-3xl">
          <DialogTitle className="sr-only">
            {selectedImage?.alt || "Gallery image"}
          </DialogTitle>
          {selectedImage && (
            <div className="flex flex-col gap-4">
              <img
                src={selectedImage.url}
                alt={selectedImage.alt || ""}
                className="w-full rounded-md"
              />
              {selectedImage.caption && (
                <DialogDescription className="text-center">
                  {selectedImage.caption}
                </DialogDescription>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
