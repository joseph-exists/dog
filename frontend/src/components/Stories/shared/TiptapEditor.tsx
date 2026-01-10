import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import { Box } from '@chakra-ui/react'

interface TiptapEditorProps {
  content: string
  onChange: (html: string) => void
  editable?: boolean
}

const TiptapEditor = ({ content, onChange, editable = true }: TiptapEditorProps) => {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: {
          HTMLAttributes: {
            class: 'code-block-monospace',
          },
        },
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          target: '_blank',
          rel: 'noopener noreferrer',
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
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
  })

  if (!editor) {
    return null
  }

  return (
    <Box
      className="tiptap-editor-content"
      borderWidth="1px"
      borderColor="border"
      borderRadius="md"
      bg="bg"
      minH="300px"
    >
      <EditorContent editor={editor} />
    </Box>
  )
}

export default TiptapEditor