/**
 * TiptapEditor - Standalone Tiptap editor without toolbar
 *
 * Features:
 * - Bare editor content (no toolbar)
 * - Editable toggle for read-only mode
 * - Debounced onChange callback for performance
 * - Configurable debounce delay
 *
 * Use RichTextEditor if you need the formatting toolbar.
 */

import Image from "@tiptap/extension-image"
import Link from "@tiptap/extension-link"
import { EditorContent, useEditor } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import { useCallback, useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

interface TiptapEditorProps {
  content: string
  onChange: (html: string) => void
  editable?: boolean
  debounceMs?: number
  className?: string
  minHeight?: string
}

const TiptapEditor = ({
  content,
  onChange,
  editable = true,
  debounceMs = 300,
  className,
  minHeight = "300px",
}: TiptapEditorProps) => {
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)

  // Debounced onChange handler
  const debouncedOnChange = useCallback(
    (html: string) => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }

      if (debounceMs > 0) {
        debounceTimer.current = setTimeout(() => {
          onChange(html)
        }, debounceMs)
      } else {
        onChange(html)
      }
    },
    [onChange, debounceMs],
  )

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
    }
  }, [])

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: {
          HTMLAttributes: {
            class: "tiptap-code-block",
          },
        },
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          target: "_blank",
          rel: "noopener noreferrer",
        },
      }),
      Image.configure({
        inline: true,
        allowBase64: true,
      }),
    ],
    content,
    editable,
    immediatelyRender: false, // SSR compatibility
    onUpdate: ({ editor: ed }) => {
      debouncedOnChange(ed.getHTML())
    },
  })

  // Update editable state when prop changes
  useEffect(() => {
    if (editor) {
      editor.setEditable(editable)
    }
  }, [editor, editable])

  if (!editor) {
    return null
  }

  return (
    <div
      className={cn(
        "tiptap-editor-content border border-border rounded-md bg-background p-4",
        className,
      )}
      style={{ minHeight }}
    >
      <EditorContent editor={editor} />
    </div>
  )
}

export default TiptapEditor
