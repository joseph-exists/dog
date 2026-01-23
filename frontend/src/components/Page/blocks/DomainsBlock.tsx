// src/components/Page/blocks/DomainsBlock.tsx
import { Globe } from "lucide-react"

import { BlockContainer } from "../primitives"

export interface DomainsBlockConfig {
  showHierarchy?: boolean
}

export interface DomainsContent {
  generalDomain?: string
  specificDomain?: string
  generalDomainHigh?: string
  specificDomainHigh?: string
}

export interface DomainsBlockProps {
  config: DomainsBlockConfig
  content?: DomainsContent
  className?: string
}

/**
 * DomainsBlock - Displays domain expertise areas for a persona
 *
 * Shows general and specific domain labels in a hierarchical layout.
 * Returns null if no domain content exists.
 */
export function DomainsBlock({
  config,
  content,
  className,
}: DomainsBlockProps) {
  if (!content) return null

  const {
    generalDomain,
    specificDomain,
    generalDomainHigh,
    specificDomainHigh,
  } = content

  // Nothing to show
  if (
    !generalDomain &&
    !specificDomain &&
    !generalDomainHigh &&
    !specificDomainHigh
  ) {
    return null
  }

  const showHierarchy = config.showHierarchy ?? true

  return (
    <BlockContainer title="Domains" className={className}>
      <div className="p-4 space-y-3">
        {/* High-level domains */}
        {(generalDomainHigh || specificDomainHigh) && showHierarchy && (
          <div className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              High-Level
            </span>
            <div className="flex flex-wrap gap-2">
              {generalDomainHigh && (
                <DomainBadge label={generalDomainHigh} variant="high" />
              )}
              {specificDomainHigh && (
                <DomainBadge label={specificDomainHigh} variant="high" />
              )}
            </div>
          </div>
        )}

        {/* Standard domains */}
        {(generalDomain || specificDomain) && (
          <div className="space-y-1">
            {showHierarchy && (generalDomainHigh || specificDomainHigh) && (
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Specific
              </span>
            )}
            <div className="flex flex-wrap gap-2">
              {generalDomain && (
                <DomainBadge label={generalDomain} variant="general" />
              )}
              {specificDomain && (
                <DomainBadge label={specificDomain} variant="specific" />
              )}
            </div>
          </div>
        )}
      </div>
    </BlockContainer>
  )
}

function DomainBadge({
  label,
  variant,
}: {
  label: string
  variant: "high" | "general" | "specific"
}) {
  const variantClasses = {
    high: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
    general: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
    specific:
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium ${variantClasses[variant]}`}
    >
      <Globe className="size-3" />
      {label}
    </span>
  )
}
