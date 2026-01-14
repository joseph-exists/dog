/**
 * RichTextEditor - TipTap-based rich text editor with toolbar
 *
 * Features:
 * - Full formatting toolbar
 * - Link and image support
 * - Editable toggle for read-only mode
 * - Optional debounced onChange for performance
 * - Outputs HTML
 */

import { useRef, useEffect, useCallback } from "react"
import { EditorContent, useEditor } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Link from "@tiptap/extension-link"
import Image from "@tiptap/extension-image"
import TiptapToolbar from "./TiptapToolbar"

interface RichTextEditorProps {
  content: string
  onChange: (html: string) => void
  editable?: boolean
  debounceMs?: number
}

const RichTextEditor = ({
  content,
  onChange,
  editable = true,
  debounceMs = 0,
}: RichTextEditorProps) => {
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
    [onChange, debounceMs]
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
    immediatelyRender: false,
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
    <div className="flex flex-col gap-0">
      <TiptapToolbar editor={editor} />
      <div className="tiptap-editor-content border border-border border-t-0 rounded-b-md bg-background min-h-[300px] p-4">
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}

export default RichTextEditor
