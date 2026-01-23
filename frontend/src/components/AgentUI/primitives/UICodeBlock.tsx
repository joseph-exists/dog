import type { UICodeData } from "../types"

export function UICodeBlock({ data }: { data: UICodeData }) {
  return (
    <div>
      {data.title && (
        <div className="text-xs text-muted-foreground mb-1 font-mono">
          {data.title}
        </div>
      )}
      <pre className="bg-muted rounded-md p-3 overflow-x-auto text-sm">
        <code className={data.language ? `language-${data.language}` : ""}>
          {data.code}
        </code>
      </pre>
    </div>
  )
}
