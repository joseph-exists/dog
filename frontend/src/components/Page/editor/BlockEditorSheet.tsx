// src/components/Page/editor/BlockEditorSheet.tsx

import type {
  ProfileImageContent,
  ProfileImageBlockConfig,
  IdentityContent,
  IdentityBlockConfig,
  BioContent,
  BioBlockConfig,
  ContactContent,
  ContactBlockConfig,
  LinksContent,
  LinksBlockConfig,
  GalleryContent,
  GalleryBlockConfig,
} from "@/components/Page/blocks"
import { getBlockType, type TemplateBlock } from "@/components/Page/registry"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  ProfileImageForm,
  IdentityForm,
  BioForm,
  ContactForm,
  LinksForm,
  GalleryForm,
} from "./forms"

interface BlockEditorSheetProps {
  block: TemplateBlock | null
  onSave: (blockId: string, content: Record<string, unknown>) => void
  onClose: () => void
}

/**
 * BlockEditorSheet - Slide-out panel for editing block content
 *
 * Renders the appropriate form based on block type.
 * Uses shadcn Sheet component with right-side slide.
 */
export function BlockEditorSheet({
  block,
  onSave,
  onClose,
}: BlockEditorSheetProps) {
  const isOpen = block !== null
  const blockTypeDef = block ? getBlockType(block.type) : null

  // Helper to wrap form save handlers with proper typing
  const createSaveHandler = <T,>(blockId: string | undefined) => {
    return (formContent: T) => {
      if (blockId) {
        // Cast to unknown first, then to Record for type safety
        onSave(blockId, formContent as unknown as Record<string, unknown>)
      }
      onClose()
    }
  }

  const renderForm = () => {
    if (!block || !blockTypeDef) return null

    // Cast content and config through unknown for type safety
    const content = (block.content ?? {}) as unknown
    const config = block.config as unknown

    switch (block.type) {
      case "profileImage":
        return (
          <ProfileImageForm
            content={content as ProfileImageContent}
            config={config as ProfileImageBlockConfig}
            onSave={createSaveHandler<ProfileImageContent>(block.id)}
            onCancel={onClose}
          />
        )
      case "identity":
        return (
          <IdentityForm
            content={content as IdentityContent}
            config={config as IdentityBlockConfig}
            onSave={createSaveHandler<IdentityContent>(block.id)}
            onCancel={onClose}
          />
        )
      case "bio":
        return (
          <BioForm
            content={content as BioContent}
            config={config as BioBlockConfig}
            onSave={createSaveHandler<BioContent>(block.id)}
            onCancel={onClose}
          />
        )
      case "contact":
        return (
          <ContactForm
            content={content as ContactContent}
            config={config as ContactBlockConfig}
            onSave={createSaveHandler<ContactContent>(block.id)}
            onCancel={onClose}
          />
        )
      case "links":
        return (
          <LinksForm
            content={content as LinksContent}
            config={config as LinksBlockConfig}
            onSave={createSaveHandler<LinksContent>(block.id)}
            onCancel={onClose}
          />
        )
      case "gallery":
        return (
          <GalleryForm
            content={content as GalleryContent}
            config={config as GalleryBlockConfig}
            onSave={createSaveHandler<GalleryContent>(block.id)}
            onCancel={onClose}
          />
        )
      // Note: relationships, activityFeed, dataTable, chart don't have forms yet
      default:
        return (
          <div className="p-4 text-center text-muted-foreground">
            <p>No editor available for {blockTypeDef.label} blocks.</p>
          </div>
        )
    }
  }

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="w-[400px] sm:w-[450px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            {blockTypeDef && (
              <>
                <blockTypeDef.icon className="h-5 w-5" />
                <span>Edit {blockTypeDef.label}</span>
              </>
            )}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-4">
          {renderForm()}
        </div>
      </SheetContent>
    </Sheet>
  )
}
