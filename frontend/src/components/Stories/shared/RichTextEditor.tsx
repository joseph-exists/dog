import { Box, VStack } from '@chakra-ui/react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import TiptapToolbar from './TiptapToolbar'

interface RichTextEditorProps {
  content: string
  onChange: (html: string) => void
  editable?: boolean
}

const RichTextEditor = ({ content, onChange, editable = true }: RichTextEditorProps) => {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: {
          HTMLAttributes: {
            class: 'tiptap-code-block',
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
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
  })

  if (!editor) {
    return null
  }

  return (
    <VStack align="stretch" gap={0}>
      <TiptapToolbar editor={editor} />
      <Box
        className="tiptap-editor-content"
        borderWidth="1px"
        borderColor="border"
        borderRadius="md"
        borderTopRadius={0}
        bg="bg"
        minH="300px"
        p={4}
      >
        <EditorContent editor={editor} />
      </Box>
    </VStack>
  )
}

export default RichTextEditor