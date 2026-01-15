/**
 * AgentCarousel Component
 *
 * A horizontal scrollable carousel of agent cards for quick browsing.
 * Features:
 * - Smooth horizontal scrolling with mouse/touch
 * - Navigation arrows on hover
 * - Click to select an agent
 * - Keyboard navigation support
 */

import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { AgentScope, ParticipationMode } from "./AgentBadge"
import AgentCard from "./AgentCard"

export interface AgentData {
  id: string
  name: string
  description?: string | null
  scope?: AgentScope
  participationMode?: ParticipationMode
  isEnabled?: boolean
  modelName?: string
}

interface AgentCarouselProps {
  /** List of agents to display */
  agents: AgentData[]
  /** Currently selected agent ID */
  selectedId?: string
  /** Called when an agent is clicked */
  onSelect?: (agent: AgentData) => void
  /** Card variant to use */
  cardVariant?: "compact" | "mini"
  /** Show navigation arrows */
  showArrows?: boolean
  /** Additional classes */
  className?: string
  /** Empty state message */
  emptyMessage?: string
}

export default function AgentCarousel({
  agents,
  selectedId,
  onSelect,
  cardVariant = "compact",
  showArrows = true,
  className,
  emptyMessage = "No agents available",
}: AgentCarouselProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  // Check scroll position to show/hide arrows
  const updateScrollButtons = () => {
    if (!scrollRef.current) return
    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current
    setCanScrollLeft(scrollLeft > 0)
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10)
  }

  useEffect(() => {
    updateScrollButtons()
    const ref = scrollRef.current
    if (ref) {
      ref.addEventListener("scroll", updateScrollButtons)
      // Also update on resize
      window.addEventListener("resize", updateScrollButtons)
    }
    return () => {
      if (ref) {
        ref.removeEventListener("scroll", updateScrollButtons)
      }
      window.removeEventListener("resize", updateScrollButtons)
    }
  }, [updateScrollButtons])

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return
    const scrollAmount = scrollRef.current.clientWidth * 0.8
    scrollRef.current.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    })
  }

  if (agents.length === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center p-8 text-muted-foreground",
          className,
        )}
      >
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className={cn("relative group", className)}>
      {/* Left Arrow */}
      {showArrows && canScrollLeft && (
        <Button
          variant="outline"
          size="icon"
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 opacity-0 group-hover:opacity-100 transition-opacity shadow-md bg-background/95"
          onClick={() => scroll("left")}
        >
          <ChevronLeftIcon className="size-4" />
        </Button>
      )}

      {/* Scrollable Container */}
      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto scrollbar-hide scroll-smooth px-1 py-1"
        style={{
          scrollbarWidth: "none",
          msOverflowStyle: "none",
        }}
      >
        {agents.map((agent) => (
          <div key={agent.id} className="flex-shrink-0">
            <AgentCard
              id={agent.id}
              name={agent.name}
              description={agent.description}
              scope={agent.scope}
              participationMode={agent.participationMode}
              isEnabled={agent.isEnabled}
              variant={cardVariant}
              isSelected={selectedId === agent.id}
              onClick={() => onSelect?.(agent)}
              className={cn(
                cardVariant === "compact" && "w-72",
                cardVariant === "mini" && "w-40",
              )}
            />
          </div>
        ))}
      </div>

      {/* Right Arrow */}
      {showArrows && canScrollRight && (
        <Button
          variant="outline"
          size="icon"
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 opacity-0 group-hover:opacity-100 transition-opacity shadow-md bg-background/95"
          onClick={() => scroll("right")}
        >
          <ChevronRightIcon className="size-4" />
        </Button>
      )}

      {/* Fade edges for visual hint */}
      {canScrollLeft && (
        <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-background to-transparent pointer-events-none" />
      )}
      {canScrollRight && (
        <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-background to-transparent pointer-events-none" />
      )}
    </div>
  )
}
