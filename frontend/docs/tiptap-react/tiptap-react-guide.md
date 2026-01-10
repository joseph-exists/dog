
Helpful Notes from https://tiptap.dev/docs/editor/getting-started/install/react

To actually start using Tiptap we need to create a new component. Let's call it Tiptap and add the following example code in src/Tiptap.tsx.

```typescript
// src/Tiptap.tsx
import { useEditor, EditorContent } from '@tiptap/react'
import { FloatingMenu, BubbleMenu } from '@tiptap/react/menus'
import StarterKit from '@tiptap/starter-kit'

const Tiptap = () => {
  const editor = useEditor({
    extensions: [StarterKit], // define your extension array
    content: '<p>Hello World!</p>', // initial content
  })

  return (
    <>
      <EditorContent editor={editor} />
      <FloatingMenu editor={editor}>This is the floating menu</FloatingMenu>
      <BubbleMenu editor={editor}>This is the bubble menu</BubbleMenu>
    </>
  )
}

export default Tiptap
```

Add it to your app
Finally, replace the content of src/App.tsx with our new Tiptap component.

```typescript
import Tiptap from './Tiptap'

const App = () => {
  return (
    <div className="card">
      <Tiptap />
    </div>
  )
}

export default App
```

Using the EditorContext

Tiptap provides a React context called EditorContext, that allows you to access the editor instance and its state from anywhere in your component tree. This is particularly useful for building custom toolbars, menus, or other components that need to interact with the editor.

```typescript
// src/Tiptap.tsx
import { useEditor, EditorContent, EditorContext } from '@tiptap/react'
import { FloatingMenu, BubbleMenu } from '@tiptap/react/menus'
import StarterKit from '@tiptap/starter-kit'

const Tiptap = () => {
  const editor = useEditor({
    extensions: [StarterKit], // define your extension array
    content: '<p>Hello World!</p>', // initial content
  })

  // Memoize the provider value to avoid unnecessary re-renders
  const providerValue = useMemo(() => ({ editor }), [editor])

  return (
    <EditorContext.Provider value={providerValue}>
      <EditorContent editor={editor} />
      <FloatingMenu editor={editor}>This is the floating menu</FloatingMenu>
      <BubbleMenu editor={editor}>This is the bubble menu</BubbleMenu>
    </EditorContext.Provider>
  )
}

export default Tiptap

Consume the Editor context in child components
If you use the EditorProvider to set up your Tiptap editor, you can now access your editor instance from any child component using the useCurrentEditor hook.

import { useCurrentEditor } from '@tiptap/react'

const EditorJSONPreview = () => {
  const { editor } = useCurrentEditor()

  return <pre>{JSON.stringify(editor.getJSON(), null, 2)}</pre>
}
```

Important: This won't work if you use the useEditor hook to setup your editor.

You should now see a pretty barebones example of Tiptap in your browser.

Reacting to Editor state changes
To react to editor state changes, you can use the useEditorState hook from @tiptap/react. This hook can be used to fetch information from the editor state without causing re-renders on the editor component or it's children.

```typescript
import { useEditorState } from '@tiptap/react'

function MyEditorComponent() {
  // ... your editor setup code

  const editorState = useEditorState({
    editor,

    // the selector function is used to select the state you want to react to
    selector: ({ editor }) => {
      if (!editor) return null;

      return {
        isEditable: editor.isEditable,
        currentSelection: editor.state.selection,
        currentContent: editor.getJSON(),
        // you can add more state properties here e.g.:
        // isBold: editor.isActive('bold'),
        // isItalic: editor.isActive('italic'),
      };
    },
  });
}
```

Use SSR with React and Tiptap
Tiptap can be used with server-side rendering (SSR) in React applications. However, to ensure that the editor is only initialized on the client side, you need to use the immediatelyRender option when creating the editor instance to prevent it from rendering on the server.

Here is an example of how to set up Tiptap with SSR in a React component:

```typescript
'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

export function MyEditor() {
  const editor = useEditor({
    extensions: [StarterKit],
    content: '<p>Hello World!</p>',
    // Disable immediate rendering to prevent SSR issues
    immediatelyRender: false,
  })

  if (!editor) {
    return null // Prevent rendering until the editor is initialized
  }

  return <EditorContent editor={editor} />
}
```