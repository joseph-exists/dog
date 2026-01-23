import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { UITabsData } from "../types"

export function UITabsBlock({ data }: { data: UITabsData }) {
  const defaultTab = `tab-${data.default_tab ?? 0}`

  return (
    <Tabs defaultValue={defaultTab}>
      <TabsList>
        {data.tabs.map((tab, idx) => (
          <TabsTrigger key={idx} value={`tab-${idx}`}>
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {data.tabs.map((tab, idx) => (
        <TabsContent key={idx} value={`tab-${idx}`} className="text-sm">
          <p className="whitespace-pre-wrap">{tab.content}</p>
        </TabsContent>
      ))}
    </Tabs>
  )
}
