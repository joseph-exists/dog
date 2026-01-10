import { HStack, IconButton, Separator } from '@chakra-ui/react'
import {
  FaBold, FaItalic, FaStrikethrough, FaCode,
  FaListUl, FaListOl, FaQuoteRight,
  FaFileCode, FaLink, FaImage
} from 'react-icons/fa'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/tiptap-ui-primitive/tooltip/tooltip'
import type { Editor } from '@tiptap/react'

interface TiptapToolbarProps {
  editor: Editor | null
}

const TiptapToolbar = ({ editor }: TiptapToolbarProps) => {
  if (!editor) return null

  return (
    <HStack
      wrap="wrap"
      gap={1}
      p={2}
      borderBottomWidth="1px"
      borderColor="border"
      bg="bg.subtle"
    >
      {/* Bold */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('bold') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleBold().run()}
            aria-label="Bold"
          >
            <FaBold />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Bold (Ctrl+B)</TooltipContent>
      </Tooltip>

      {/* Italic */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('italic') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleItalic().run()}
            aria-label="Italic"
          >
            <FaItalic />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Italic (Ctrl+I)</TooltipContent>
      </Tooltip>

      {/* Strike */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('strike') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleStrike().run()}
            aria-label="Strikethrough"
          >
            <FaStrikethrough />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Strikethrough</TooltipContent>
      </Tooltip>

      {/* Inline Code */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('code') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleCode().run()}
            aria-label="Code"
          >
            <FaCode />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Inline Code</TooltipContent>
      </Tooltip>

      <Separator orientation="vertical" h="24px" />

      {/* Headings */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('heading', { level: 1 }) ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
            aria-label="Heading 1"
          >
            H1
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Heading 1</TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('heading', { level: 2 }) ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            aria-label="Heading 2"
          >
            H2
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Heading 2</TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('heading', { level: 3 }) ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            aria-label="Heading 3"
          >
            H3
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Heading 3</TooltipContent>
      </Tooltip>

      <Separator orientation="vertical" h="24px" />

      {/* Lists */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('bulletList') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            aria-label="Bullet List"
          >
            <FaListUl />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Bullet List</TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('orderedList') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            aria-label="Numbered List"
          >
            <FaListOl />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Numbered List</TooltipContent>
      </Tooltip>

      <Separator orientation="vertical" h="24px" />

      {/* Blockquote */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('blockquote') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            aria-label="Quote"
          >
            <FaQuoteRight />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Quote</TooltipContent>
      </Tooltip>

      {/* Code Block */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('codeBlock') ? 'solid' : 'ghost'}
            onClick={() => editor.chain().focus().toggleCodeBlock().run()}
            aria-label="Code Block"
          >
            <FaFileCode />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Code Block</TooltipContent>
      </Tooltip>

      <Separator orientation="vertical" h="24px" />

      {/* Link */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            variant={editor.isActive('link') ? 'solid' : 'ghost'}
            onClick={() => {
              const url = window.prompt('Enter URL:')
              if (url) {
                editor.chain().focus().setLink({ href: url }).run()
              }
            }}
            aria-label="Link"
          >
            <FaLink />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Add Link</TooltipContent>
      </Tooltip>

      {/* Image */}
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            size="sm"
            onClick={() => {
              const url = window.prompt('Enter image URL:')
              if (url) {
                editor.chain().focus().setImage({ src: url }).run()
              }
            }}
            aria-label="Image"
          >
            <FaImage />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent>Add Image</TooltipContent>
      </Tooltip>
    </HStack>
  )
}

export default TiptapToolbar
