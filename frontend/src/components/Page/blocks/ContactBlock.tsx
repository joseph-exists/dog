// src/components/Page/blocks/ContactBlock.tsx

import { Check, Copy, Mail, Phone } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { BlockContainer } from "../primitives"

export interface ContactBlockConfig {
  showEmail?: boolean
  showPhone?: boolean
}

export interface ContactBlockProps {
  config: ContactBlockConfig
  contact: { email?: string; phone?: string }
}

/**
 * ContactBlock - Displays contact information with copy buttons
 *
 * Shows email and/or phone based on config settings.
 * Each item has a copy button that shows a check mark for 2 seconds after copying.
 * Returns null if no content would be visible based on config and data.
 */
export function ContactBlock({ config, contact }: ContactBlockProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const showEmail = config.showEmail && contact.email
  const showPhone = config.showPhone && contact.phone

  // If nothing to show, render nothing
  if (!showEmail && !showPhone) {
    return null
  }

  const handleCopy = async (field: string, value: string) => {
    await navigator.clipboard.writeText(value)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  return (
    <BlockContainer title="Contact">
      <div className="p-4 space-y-3">
        {showEmail && (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-sm truncate">{contact.email}</span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => handleCopy("email", contact.email!)}
              aria-label="Copy email"
            >
              {copiedField === "email" ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        )}
        {showPhone && (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <Phone className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-sm truncate">{contact.phone}</span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => handleCopy("phone", contact.phone!)}
              aria-label="Copy phone"
            >
              {copiedField === "phone" ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        )}
      </div>
    </BlockContainer>
  )
}
