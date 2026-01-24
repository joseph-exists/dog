// src/components/Page/blocks/LinksBlock.tsx
import {
  ExternalLink,
  Github,
  Globe,
  Linkedin,
  type LucideIcon,
  Twitter,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { BlockContainer } from "../primitives"

export interface Link {
  id: string
  type: "website" | "github" | "twitter" | "linkedin" | "other"
  url: string
  label?: string
}

export interface LinksBlockConfig {
  layout: "list" | "grid"
}

export interface LinksContent {
  items: Link[]
}

export interface LinksBlockProps {
  config: LinksBlockConfig
  content?: LinksContent
  className?: string
}

const linkIcons: Record<Link["type"], LucideIcon> = {
  website: Globe,
  github: Github,
  twitter: Twitter,
  linkedin: Linkedin,
  other: ExternalLink,
}

/**
 * Extract hostname from URL for display when no label is provided
 */
function getHostname(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}

/**
 * LinksBlock - Displays a collection of external links
 *
 * Renders links in either grid or list layout based on config.
 * Each link shows an icon based on type and opens in a new tab.
 * Returns null if no links are provided.
 * View-only block - no edit functionality.
 */
export function LinksBlock({ config, content, className }: LinksBlockProps) {
  const links = content?.items || []

  if (links.length === 0) {
    return (
      <BlockContainer title="Links" className={className}>
        <div className="p-4">
          <p className="text-sm text-muted-foreground italic">No links yet.</p>
        </div>
      </BlockContainer>
    )
  }

  return (
    <BlockContainer title="Links" className={className}>
      <div
        className={cn(
          "p-4 gap-3",
          config.layout === "grid" ? "grid grid-cols-2" : "flex flex-col",
        )}
      >
        {links.map((link) => {
          const Icon = linkIcons[link.type]
          const displayLabel = link.label || getHostname(link.url)

          return (
            <a
              key={link.id}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{displayLabel}</span>
            </a>
          )
        })}
      </div>
    </BlockContainer>
  )
}
