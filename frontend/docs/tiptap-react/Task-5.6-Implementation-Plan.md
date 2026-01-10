# Task 5.6: Rich Text Editor Implementation Plan

**Version:** 1.0
**Date:** 2026-01-08
**Status:** Ready for Implementation
**Parent Task:** Act V: Task 5.6 from Story-Authoring-Implementation-Plan.md

---

## Overview

Implement a rich text editor for StoryNode content using Tiptap, supporting multiple content formats (HTML, JSON, TEXT) with a seamless authoring experience.

**Key Requirements:**
- Format selector: HTML (default), JSON, TEXT
- Fixed toolbar with standard formatting options
- Image upload/embed support
- Code blocks with monospace formatting (no syntax highlighting)
- Backward compatible with existing TEXT nodes
- XSS protection for HTML rendering
- Dark theme compatible

---

## Prerequisites Completed ✅

- [X] Backend: `ContentFormat` enum added to StoryNode model
- [X] Backend: Migration applied for `content_format` field
- [X] Frontend: SDK regenerated with ContentFormat type
- [X] Tiptap packages already installed in project

---

## Implementation Tasks

### Task 5.6.1: Install Required Dependencies

**File:** `frontend/package.json`

**Acceptance Criteria:**
- [X] Install `dompurify` for XSS sanitization
- [X] Install `@types/dompurify` for TypeScript support
- [X] Verify Tiptap packages are installed:
  - `@tiptap/react`
  - `@tiptap/starter-kit`
  - `@tiptap/extension-link`
  - `@tiptap/extension-image`
- [X] Run `npm install` successfully

---

### Task 5.6.2: Review and Modify TiptapEditor Component

**File:** `src/components/Stories/shared/TiptapEditor.tsx`

**Acceptance Criteria:**
- [ ] Component accepts `content: string`, `onChange: (html: string) => void` props
- [ ] Uses `useEditor` hook with proper extensions
- [ ] Includes StarterKit (bold, italic, heading, lists, code block)
- [ ] Includes Link extension
- [ ] Includes Image extension
- [ ] Renders EditorContent with proper styling
- [ ] Styled to match Chakra UI theme (dark mode compatible)
- [ ] Returns HTML via `editor.getHTML()` on change
- [ ] Handles SSR with `immediatelyRender: false`
- [ ] Properly typed with TypeScript



**Extension Configuration:**
- **StarterKit:** Includes bold, italic, strike, code, heading, bulletList, orderedList, blockquote, codeBlock, hardBreak, horizontalRule
- **Link:** Opens in new tab, includes security attributes
- **Image:** Supports inline images and base64 (for paste/drag-drop)

**Styling Notes:**
- Use Chakra semantic tokens for theming
- Add custom CSS for editor content in `src/index.css`

---

### Task 5.6.3: Review and Modify TiptapToolbar Component

**File:** `src/components/Stories/shared/TiptapToolbar.tsx`

**Acceptance Criteria:**
- [ ] Fixed toolbar (not floating/bubble)
- [ ] Positioned above editor content
- [ ] Rewrite Buttons for: Bold, Italic, Strike, Code, Heading (H1-H3), BulletList, OrderedList, Blockquote, CodeBlock, Link, Image to use Tiptap buttons
- [ ] Active state styling for current format
- [ ] Disabled state when editor not editable
- [ ] Responsive layout (wraps on mobile)
- [ ] Tooltips for each button (tiptap tooltip, tooltiptrigger)
- [ ] Dark theme compatible


**Potential Enhancements:**
- Replace `window.prompt` with proper modals
- Add image upload functionality
- Add link editing (modify/remove existing links)

---

### Task 5.6.4: Review and Update RichTextEditor Container

**File:** `src/components/Stories/shared/RichTextEditor.tsx`

**Acceptance Criteria:**
- [ ] Combines TiptapToolbar and TiptapEditor
- [ ] Single component with clean API
- [ ] Exports editor instance for parent access
- [ ] Handles all editor state internally
- [ ] Props: `content`, `onChange`, `editable`
- [ ] Styled as single cohesive unit



---

### Task 5.6.5: Review and Update Tiptap Styles

**File:** `src/index.css`

**Acceptance Criteria:**
- [ ] Styles for editor content area
- [ ] Code block monospace styling
- [ ] Heading sizes
- [ ] List indentation
- [ ] Link styling
- [ ] Image styling
- [ ] Dark theme compatible using CSS variables
- [ ] Proper spacing and typography


---

### Task 5.6.6: Update NodeEditorForm with Format Selector

**File:** Review `src/components/Stories/StoryEditor/NodeEditor/NodeEditorForm.tsx` and update as necessary to ensure:

**Acceptance Criteria:**
- [ ] Add `content_format` field to form
- [ ] Default to `"HTML"` for new nodes
- [ ] Format selector dropdown: HTML (default), JSON, TEXT
- [ ] Conditional rendering based on selected format:
  - HTML → RichTextEditor
  - TEXT → Plain Textarea
  - JSON → Textarea with monospace font
- [ ] Integrate with React Hook Form using `Controller`
- [ ] Show format change warning if content exists
- [ ] Update mutation to send `content_format`
- [ ] Reset form properly when node changes


---

### Task 5.6.7: Update CreateNodeModal

**File:** `src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx`

**Acceptance Criteria:**
- [ ] Set default `content_format` to `"html"`
- [ ] Include format selector in create form
- [ ] Use plain Textarea for content (keep it simple)
- [ ] Pass `content_format` in mutation payload
- [ ] Form validation unchanged

**Review Default Values**

**Review Format Field**


---

### Task 5.6.8: Update StoryPreview with Format-Aware Rendering

**File:** `src/components/Stories/StoryPlayer/StoryPreview.tsx`

**Acceptance Criteria:**
- [ ] Install and import `dompurify`
- [ ] Create `renderContent` helper function
- [ ] Switch rendering based on `node.content_format`
- [ ] HTML → Sanitize with DOMPurify, render with `dangerouslySetInnerHTML`
- [ ] TEXT → Render with `whiteSpace="pre-wrap"`
- [ ] JSON → Attempt to parse and render (or show error)
- [ ] Apply consistent styling for all formats
- [ ] Test XSS protection with malicious HTML

**Implementation:**


// needs added to component
<Card.Body>
  <VStack align="stretch" gap={6}>
    {/* Node Content */}
    {renderContent(currentNode)}
    {/* ... rest of component ... */}
  </VStack>
</Card.Body>
```

**Security Testing:**
```typescript
// Test with malicious HTML
const maliciousHTML = '<img src=x onerror="alert(\'XSS\')"> <script>alert("XSS")</script>'
// Should be sanitized to: <img src="x">
```

---

### Task 5.6.9: Update Backend Models (Verify)

**File:** `backend/app/models.py`

**Acceptance Criteria:**
- [X] `ContentFormat` enum exists
- [X] `StoryNodeBase.content_format` field exists with default
- [X] `StoryNodeUpdate.content_format` field is optional
- [X] `StoryNodeCreate` includes content_format
- [X] Verify migration applied: `alembic current`


---

### Task 5.6.10: Test Suite (PENDING COMPLETION OF ABOVE, DO NOT WRITE TESTS UNTIL AFTER CURRENT MANUAL AND AUTOMATED SUITES PASS)

**Files to Create:**
- `frontend/src/components/Stories/shared/__tests__/RichTextEditor.test.tsx`
- `frontend/src/components/Stories/shared/__tests__/TiptapToolbar.test.tsx`

**Acceptance Criteria:**
- [ ] Test RichTextEditor renders correctly
- [ ] Test toolbar buttons toggle formatting
- [ ] Test onChange callback fires with HTML
- [ ] Test format switching in NodeEditorForm
- [ ] Test XSS sanitization in preview
- [ ] Test backward compatibility with TEXT nodes
- [ ] Test JSON validation and error handling

**Example Test:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import RichTextEditor from '../RichTextEditor'

describe('RichTextEditor', () => {
  it('renders editor with initial content', () => {
    const onChange = jest.fn()
    render(<RichTextEditor content="<p>Hello World</p>" onChange={onChange} />)
    expect(screen.getByText('Hello World')).toBeInTheDocument()
  })

  it('calls onChange when content updates', async () => {
    const onChange = jest.fn()
    render(<RichTextEditor content="" onChange={onChange} />)
    // Simulate typing
    // fireEvent...
    expect(onChange).toHaveBeenCalled()
  })

  it('sanitizes malicious HTML in preview', () => {
    const malicious = '<script>alert("XSS")</script><p>Safe</p>'
    const { container } = render(<StoryPreview node={{ content: malicious, content_format: 'HTML' }} />)
    expect(container.innerHTML).not.toContain('<script>')
    expect(screen.getByText('Safe')).toBeInTheDocument()
  })
})
```

---

## Implementation Checklist

### Phase 1: Core Setup
- [ ] **Task 5.6.1:** Install dependencies (dompurify, types)
- [ ] **Task 5.6.2:** Create TiptapEditor base component
- [ ] **Task 5.6.3:** Create TiptapToolbar component
- [ ] **Task 5.6.4:** Create RichTextEditor container
- [ ] **Task 5.6.5:** Add CSS styles to index.css

### Phase 2: Form Integration
- [ ] **Task 5.6.6:** Update NodeEditorForm with format selector and conditional rendering
- [ ] **Task 5.6.7:** Update CreateNodeModal with format field

### Phase 3: Preview & Rendering
- [ ] **Task 5.6.8:** Update StoryPreview with format-aware rendering and XSS protection

### Phase 4: Verification
- [ ] **Task 5.6.9:** Verify backend models and migration
- [ ] **Task 5.6.10:** Write and run test suite

---

## Testing Checklist

### Manual Testing
1. **Create new node with HTML format**
   - [ ] Format selector defaults to HTML
   - [ ] Rich text editor appears
   - [ ] Toolbar buttons work (bold, italic, heading, etc.)
   - [ ] Image URL prompt works
   - [ ] Link URL prompt works
   - [ ] Save preserves formatting
   - [ ] Preview shows formatted HTML

2. **Create new node with TEXT format**
   - [ ] Plain textarea appears
   - [ ] No toolbar shown
   - [ ] Content saved as plain text
   - [ ] Preview shows unformatted text with line breaks

3. **Create new node with JSON format**
   - [ ] Monospace textarea appears
   - [ ] JSON validation on save (future enhancement)
   - [ ] Preview shows JSON structure or error

4. **Edit existing TEXT node**
   - [ ] Opens with TEXT format selected
   - [ ] Shows plain textarea
   - [ ] Can switch to HTML (with warning if content exists)
   - [ ] Content preserved on save

5. **Format switching**
   - [ ] Warning shown when switching with existing content
   - [ ] Format change updates editor type
   - [ ] Content preserved (user responsibility)

6. **XSS Protection**
   - [ ] Test malicious HTML: `<script>alert('XSS')</script><p>Safe content</p>`
   - [ ] Script tags removed in preview
   - [ ] Safe content displayed
   - [ ] Image onerror handlers removed

7. **Dark Theme**
   - [ ] Toggle dark mode in app settings
   - [ ] Editor has proper background color
   - [ ] Toolbar buttons visible
   - [ ] Content text readable
   - [ ] Code blocks have proper background

8. **Responsive Design**
   - [ ] Toolbar wraps on mobile
   - [ ] Editor usable on small screens
   - [ ] Buttons accessible with touch

---

## Common Issues & Solutions

### Issue 1: Tiptap not rendering on first load
**Solution:** Ensure `immediatelyRender: false` is set in `useEditor` config

### Issue 2: Form dirty state not updating
**Solution:** Use `setValue` with `{ shouldDirty: true }` option

### Issue 3: Format change loses content
**Solution:** Warn user before format change, preserve string content as-is

### Issue 4: Images not showing in preview
**Solution:** Check CORS, ensure URL is valid, test with base64

### Issue 5: Dark mode styling broken
**Solution:** Use CSS variables (`var(--chakra-colors-*)`) instead of hardcoded colors

### Issue 6: Code blocks not monospace
**Solution:** Verify CSS is applied: `.tiptap-code-block` class, `font-family: monospace`

---

## Future Enhancements (Post-MVP)

1. **Image Upload**
   - Replace URL prompt with file upload
   - Store images in backend/S3
   - Show upload progress

2. **Link Editor**
   - Modal for editing links (text, URL, target)
   - Remove link button
   - Validate URLs

3. **JSON Schema Validation**
   - Define Tiptap JSON schema
   - Validate on save
   - Provide helpful error messages

4. **Autosave**
   - Debounce editor changes
   - Auto-save to backend
   - Show "Saving..." / "Saved" indicator

5. **Collaborative Editing**
   - Y.js integration for real-time collaboration
   - Show other editors' cursors
   - Conflict resolution

6. **Content Templates**
   - Predefined story templates
   - Insert common structures (character intro, choice prompt, etc.)

7. **Word Count**
   - Live word/character count
   - Reading time estimate

---

## Success Criteria

✅ **Task 5.6 Complete When:**
- All subtasks checked off
- Rich text editor functional with toolbar
- Format selector working (HTML/TEXT/JSON)
- Existing TEXT nodes still editable
- Preview renders HTML safely with DOMPurify
- Dark theme works correctly
- All manual tests pass
- Code committed and merged

---

**Ready to implement!** Follow tasks in order, test incrementally, and refer to FrontendRULES.md for patterns.
