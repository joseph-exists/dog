import { TrendingDown, TrendingUp } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export interface MetricCardData {
  title: string
  value: string
  change: number
  changeLabel: string
  subtitle: string
}

export interface SectionCardsProps {
  metrics?: MetricCardData[]
}

const defaultMetrics: MetricCardData[] = [
  {
    title: "Total Revenue",
    value: "$1,250.00",
    change: 12.5,
    changeLabel: "Trending up this month",
    subtitle: "Visitors for the last 6 months",
  },
  {
    title: "New Customers",
    value: "1,234",
    change: -20,
    changeLabel: "Down 20% this period",
    subtitle: "Acquisition needs attention",
  },
  {
    title: "Active Accounts",
    value: "45,678",
    change: 12.5,
    changeLabel: "Strong user retention",
    subtitle: "Engagement exceed targets",
  },
  {
    title: "Growth Rate",
    value: "4.5%",
    change: 4.5,
    changeLabel: "Steady performance increase",
    subtitle: "Meets growth projections",
  },
]

export function SectionCards({ metrics = defaultMetrics }: SectionCardsProps) {
  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      {metrics.map((metric, index) => (
        <Card key={index} className="@container/card">
          <CardHeader>
            <CardDescription>{metric.title}</CardDescription>
            <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {metric.value}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                {metric.change >= 0 ? <TrendingUp /> : <TrendingDown />}
                {metric.change >= 0 ? "+" : ""}
                {metric.change}%
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter className="flex-col items-start gap-1.5 text-sm">
            <div className="line-clamp-1 flex gap-2 font-medium">
              {metric.changeLabel}
              {metric.change >= 0 ? (
                <TrendingUp className="size-4" />
              ) : (
                <TrendingDown className="size-4" />
              )}
            </div>
            <div className="text-muted-foreground">{metric.subtitle}</div>
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}
