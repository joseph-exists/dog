import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { UITableData } from "../types"

export function UITableBlock({ data }: { data: UITableData }) {
  return (
    <div>
      {data.title && <h4 className="text-sm font-medium mb-2">{data.title}</h4>}
      <div className="rounded-md border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              {data.columns.map((col) => (
                <TableHead
                  key={col.key}
                  className={cn(
                    col.align === "center" && "text-center",
                    col.align === "right" && "text-right",
                  )}
                >
                  {col.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.rows.map((row, idx) => (
              <TableRow
                key={idx}
                className={cn(data.striped && idx % 2 === 1 && "bg-muted/50")}
              >
                {data.columns.map((col) => (
                  <TableCell
                    key={col.key}
                    className={cn(
                      col.align === "center" && "text-center",
                      col.align === "right" && "text-right",
                      data.compact && "py-1 text-xs",
                    )}
                  >
                    {String(row[col.key] ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
