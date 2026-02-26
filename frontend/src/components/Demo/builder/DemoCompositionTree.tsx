import type { EditableComposition } from "@/components/Demo/builder/demoBuilderSchema"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface CompositionTreeNode {
  nodeKind: "panel" | "block"
  id: string
  title: string
  descriptor: string
  path: string
  children: CompositionTreeNode[]
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function toNodeTitle(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : fallback
}

function toNodeId(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : fallback
}

function getNestedNodes(
  value: unknown,
  path: string,
  maxDepth: number,
  depth: number,
): CompositionTreeNode[] {
  if (depth >= maxDepth) return []
  if (Array.isArray(value)) {
    return value.flatMap((item, index) =>
      getNestedNodes(item, `${path}[${index}]`, maxDepth, depth + 1),
    )
  }
  if (!isObjectRecord(value)) return []

  const asPanel: CompositionTreeNode | null =
    typeof value.kind === "string"
      ? {
          nodeKind: "panel" as const,
          id: toNodeId(value.id, `panel-${depth}`),
          title: toNodeTitle(value.title, "Untitled Panel"),
          descriptor: value.kind,
          path,
          children: [],
        }
      : null

  const asBlock: CompositionTreeNode | null =
    typeof value.type === "string"
      ? {
          nodeKind: "block" as const,
          id: toNodeId(value.id, `block-${depth}`),
          title: toNodeTitle(value.title, "Untitled Block"),
          descriptor: value.type,
          path,
          children: [],
        }
      : null

  if (asPanel || asBlock) {
    const node = asPanel ?? asBlock!
    const children = Object.entries(value).flatMap(([key, childValue]) =>
      getNestedNodes(childValue, `${path}.${key}`, maxDepth, depth + 1),
    )
    node.children = children
    return [node]
  }

  return Object.entries(value).flatMap(([key, childValue]) =>
    getNestedNodes(childValue, `${path}.${key}`, maxDepth, depth + 1),
  )
}

function buildCompositionTree(composition: EditableComposition): CompositionTreeNode[] {
  const maxDepth = 8
  const panelRoots = (composition.panels ?? []).map((panel, index) => {
    const rootPath = `panels[${index}]`
    const children = Object.entries(panel as Record<string, unknown>).flatMap(
      ([key, value]) => getNestedNodes(value, `${rootPath}.${key}`, maxDepth, 0),
    )
    return {
      nodeKind: "panel" as const,
      id: toNodeId(panel.id, `panel-${index + 1}`),
      title: toNodeTitle(panel.title, `Panel ${index + 1}`),
      descriptor:
        typeof panel.kind === "string" ? panel.kind : "unknown-panel-kind",
      path: rootPath,
      children,
    }
  })

  const blockRoots = (composition.blocks ?? []).map((block, index) => {
    const rootPath = `blocks[${index}]`
    const children = Object.entries(block as Record<string, unknown>).flatMap(
      ([key, value]) => getNestedNodes(value, `${rootPath}.${key}`, maxDepth, 0),
    )
    return {
      nodeKind: "block" as const,
      id: toNodeId(block.id, `block-${index + 1}`),
      title: toNodeTitle(block.title, `Block ${index + 1}`),
      descriptor:
        typeof block.type === "string" ? block.type : "unknown-block-type",
      path: rootPath,
      children,
    }
  })

  return [...panelRoots, ...blockRoots]
}

function countNodes(nodes: CompositionTreeNode[]): number {
  return nodes.reduce(
    (total, node) => total + 1 + countNodes(node.children),
    0,
  )
}

function TreeNodeRow({
  node,
  depth,
  onAddChild,
  onFocusNode,
}: {
  node: CompositionTreeNode
  depth: number
  onAddChild?: (params: {
    parentPath: string
    childKind: "panel" | "block"
  }) => void
  onFocusNode?: (params: { nodePath: string }) => void
}) {
  return (
    <div className="space-y-1">
      <div
        className="rounded border px-2 py-1.5"
        style={{ marginLeft: `${depth * 14}px` }}
      >
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={node.nodeKind === "panel" ? "default" : "secondary"}>
            {node.nodeKind}
          </Badge>
          <span className="text-sm font-medium">{node.title}</span>
          <span className="text-xs text-muted-foreground">{node.descriptor}</span>
          <span className="text-xs text-muted-foreground font-mono">{node.id}</span>
        </div>
        <div className="text-[11px] text-muted-foreground font-mono mt-1">
          {node.path}
        </div>
        {onAddChild && (
          <div className="mt-2 flex flex-wrap gap-2">
            {onFocusNode && (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => onFocusNode({ nodePath: node.path })}
              >
                Focus In Editor
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                onAddChild({
                  parentPath: node.path,
                  childKind: "block",
                })
              }
            >
              Add Block Child
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                onAddChild({
                  parentPath: node.path,
                  childKind: "panel",
                })
              }
            >
              Add Panel Child
            </Button>
          </div>
        )}
      </div>

      {node.children.map((child) => (
        <TreeNodeRow
          key={`${child.path}:${child.id}`}
          node={child}
          depth={depth + 1}
          onAddChild={onAddChild}
          onFocusNode={onFocusNode}
        />
      ))}
    </div>
  )
}

export function DemoCompositionTree({
  composition,
  onAddChild,
  onFocusNode,
}: {
  composition: EditableComposition
  onAddChild?: (params: {
    parentPath: string
    childKind: "panel" | "block"
  }) => void
  onFocusNode?: (params: { nodePath: string }) => void
}) {
  const roots = buildCompositionTree(composition)
  const nestedCount = countNodes(roots) - roots.length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Composition Tree</CardTitle>
        <p className="text-xs text-muted-foreground">
          Surfaces and nested panel/block nodes detected in composition JSON.
          Root nodes: {roots.length}. Nested nodes: {Math.max(0, nestedCount)}.
        </p>
      </CardHeader>
      <CardContent className="space-y-2 max-h-[440px] overflow-auto">
        {roots.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No panel/block roots configured yet.
          </div>
        ) : (
          roots.map((root) => (
            <TreeNodeRow
              key={`${root.path}:${root.id}`}
              node={root}
              depth={0}
              onAddChild={onAddChild}
              onFocusNode={onFocusNode}
            />
          ))
        )}
      </CardContent>
    </Card>
  )
}
