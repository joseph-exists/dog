Key observations:

  1. content field is a plain str with no max_length constraint - can store arbitrarily long content
  2. content_format enum for TEXT, HTML, JSON, MARKDOWN

  Rich Text Storage Options

  Option 1: HTML

  Storage: Store HTML string in content field
  Pros:
  - ✅ Works with current schema (no migration needed)
  - ✅ Easy to render for players (just need HTML sanitization)
  - ✅ Human-readable in database for debugging
  - ✅ Tiptap can output HTML natively
  - ✅ Backward compatible (plain text is valid HTML)
  - ✅ Maximum formatting flexibility

  Cons:
  - ⚠️ Requires XSS sanitization (use DOMPurify)
  - ⚠️ Slightly larger file size than plain text
  - ⚠️ Mixing plain text and HTML in same field (unless we add indicator)

  Implementation:
  // Save from Tiptap
  const htmlContent = editor.getHTML()
  updateNode({ content: htmlContent })

  // Display in preview/player
  import DOMPurify from 'dompurify'
  <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }} />

  Option 2: Markdown

  Storage: Store Markdown string in content field
  Pros:
  - ✅ Clean, human-readable
  - ✅ Smaller file size
  - ✅ Easy to edit manually in database

  Cons:
  - ❌ Limited formatting (no colors, complex layouts)
  - ❌ Requires markdown parser for display
  - ❌ Less rich than HTML
  - ⚠️ Tiptap doesn't natively output Markdown (needs plugin)

  Option 3: Tiptap JSON (ProseMirror)

  Storage: Store JSON string in content field
  Pros:
  - ✅ Structured, type-safe
  - ✅ Easy to manipulate programmatically
  - ✅ No XSS risk

  Cons:
  - ❌ Not human-readable in database
  - ❌ Requires Tiptap to render (tight coupling)
  - ❌ Harder to migrate away from
  - ⚠️ Would need to JSON.stringify() before saving


  Approach:
  1. Use existing content field to store HTML
  2. Update NodeEditorForm to use Tiptap rich text editor
  3. Editor outputs HTML via editor.getHTML()
 

  This enables us to:
  - Store plain text, HTML, and json content
  - Know how to render each node appropriately

  Implementation Path



  1. content_format field has been added to backend models
  2. Set new nodes with content_format when using rich text editor
  4. Render based on format indicator

Changes made to StoryNode and Story models:


class ContentFormat(str, Enum):  # More accurate name
      TEXT = "text"
      HTML = "html"
      MARKDOWN = "markdown"
      JSON = "json"


content_format: ContentFormat = Field(default=ContentFormat.TEXT)  #
 


  1. Backend Changes

  a) Enum Definition added (backend/app/models.py):


  class ContentType(str, Enum):
      TEXT = "text"
      HTML = "html"
      MARKDOWN = "markdown"
      JSON = "json"


  2. Migration (complete)

  3. Frontend Changes

  a) [x] Regenerated Client SDK

# TODO : VALIDATE FOLLOWING AS STILL CONTEXTUALLY APPROPRIATE

  b) Update NodeEditorForm to include format selector:
  <Field label="Content Format">
    <Select
      value={contentFormat}
      onChange={(e) => setValue("content_type", e.target.value as ContentType)}
    >
      <option value="text">Plain Text</option>
      <option value="html">Rich Text (HTML)</option>
      <option value="markdown">Markdown</option>
    </Select>
  </Field>

  c) Conditional Editor Rendering:
  {node.node_type === "html" ? (
    <TiptapEditor content={content} onChange={...} />
  ) : (
    <Textarea content={content} onChange={...} />
  )}

  d) Preview Rendering:
  // In StoryPreview.tsx
  const renderContent = (node: StoryNodePublic) => {
    switch (node.content_type) {
      case "html":
        return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(node.content) }} />
      case "markdown":
        return <ReactMarkdown>{node.content}</ReactMarkdown>
      case "text":
      default:
        return <Text whiteSpace="pre-wrap">{node.content}</Text>
    }
  }

  4. Validation

  Consider adding content validation based on type:

  from pydantic import field_validator

  class StoryNodeCreate(StoryNodeBase):
      @field_validator('content')
      def validate_content_format(cls, v, info):
          content_type = info.data.get('content_type')

          if content_type == ContentType.HTML:
              # Could validate HTML syntax
              pass
          elif content_type == ContentType.MARKDOWN:
              # Could validate Markdown
              pass
          elif content_type == ContentType.JSON:
              # Validate JSON parseable
              try:
                  json.loads(v)
              except:
                  raise ValueError("Invalid JSON content")

          return v

  5. Tests

  a) Update test fixtures:
  # backend/app/tests/fixtures.py
  def test_story_node():
      return {
          "title": "Test Node",
          "content": "Test content",
          "content_type": ContentType.TEXT,  # Use enum
          # ...
      }

  b) Test enum validation:
  def test_invalid_node_type():
      with pytest.raises(ValidationError):
          StoryNodeCreate(
              title="Test",
              content="Test",
              node_type="invalid",  # Should fail
              story_id=uuid4(),
              story_version=1
          )

  6. Default Handling in Create Modal

  // CreateNodeModal.tsx
  const defaultValues = {
    title: "",
    content: "",
    node_type: "text",  // Default to plain text
    is_start_node: false,
    is_end_node: false,
  }








  A. Add frontend format selector
  B. Implement conditional rendering


  The content field and content_format field are separate concerns:

  - content: Stores the actual data (string)
  - content_format: Metadata describing how to interpret that string


  Frontend Types:

  export enum ContentFormat {
      TEXT = "text",
      HTML = "html",
      MARKDOWN = "markdown",
      JSON = "json",
  }

  export type StoryNodePublic = {
      title: string;
      content?: string; 
      content_format?: ContentFormat;  
      node_type?: string; 
      is_start_node?: boolean;
      is_end_node?: boolean;
      id: string;
      story_id: string;
      story_version: number;
      created_at: string;
      updated_at: string;
  };

  What Stays the Same

  ✅ content field structure (string)
  ✅ content field constraints (no max_length)
  ✅ How content is stored in the database
  ✅ Existing content validation

  Why No Content Field Changes Needed

  The content field is format-agnostic:

  # All of these work with the same content field:
  node1 = StoryNode(
      content="Plain text content",
      content_format=ContentFormat.TEXT
  )

  node2 = StoryNode(
      content="<p>HTML <strong>content</strong></p>",
      content_format=ContentFormat.HTML
  )

  node3 = StoryNode(
      content="# Markdown\n\n**bold** text",
      content_format=ContentFormat.MARKDOWN
  )

  node4 = StoryNode(
      content='{"type": "doc", "content": [...]}',
      content_format=ContentFormat.JSON
  )


