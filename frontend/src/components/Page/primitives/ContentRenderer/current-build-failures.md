src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx:8:37 - error TS6196: 'Content' is declared but never used.

8 import type { ContentRendererProps, Content, PluginValidationResult } from "./types"
                                      ~~~~~~~

src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx:11:1 - error TS6133: 'getRenderer' is declared but its value is never read.

11 import { getRenderer } from "./registry"
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx:19:13 - error TS2322: Type '({ content }: FallbackRendererProps) => Element' is not assignable to type 'FC<Content<ContentFormat>>'.
  Types of parameters '__0' and 'props' are incompatible.
    Property 'content' is missing in type 'Content<ContentFormat>' but required in type 'FallbackRendererProps'.

19   fallback: FallbackComponent =
               ~~~~~~~~~~~~~~~~~

  src/components/Page/primitives/ContentRenderer/components/FallbackRenderer.tsx:9:3
    9   content: Content
        ~~~~~~~
    'content' is declared here.

src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx:29:8 - error TS6133: 'codeTheme' is declared but its value is never read.

29  const { codeTheme } = useThemeResolution({ content, theme, decorationHint })
          ~~~~~~~~~~~~~

src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx:29:54 - error TS2353: Object literal may only specify known properties, and 'theme' does not exist in type 'ThemeResolutionInput'.

29  const { codeTheme } = useThemeResolution({ content, theme, decorationHint })
                                                        ~~~~~

src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx:50:31 - error TS2322: Type '{ content: Content<ContentFormat>; }' is not assignable to type 'IntrinsicAttributes & Content<ContentFormat>'.
  Property 'content' does not exist on type 'IntrinsicAttributes & Content<ContentFormat>'.

50     return <FallbackComponent content={transformedContent} />
                                 ~~~~~~~

src/components/Page/primitives/ContentRenderer/pluginRegistry.ts:173:38 - error TS2322: Type 'PluginRenderer<"json"> | PluginRenderer<"text"> | PluginRenderer<"unknown"> | PluginRenderer<"html"> | ... 9 more ... | PluginRenderer<...>' is not assignable to type 'PluginRenderer<ContentFormat>'.
  Type 'PluginRenderer<"json">' is not assignable to type 'PluginRenderer<ContentFormat>'.
    Types of property 'Component' are incompatible.
      Type 'FC<ContentProps<"json">>' is not assignable to type 'FC<ContentProps<ContentFormat>>'.
        Type 'ContentProps<ContentFormat>' is not assignable to type 'ContentProps<"json">'.
          Type 'ContentFormat' is not assignable to type '"json"'.
            Type '"text"' is not assignable to type '"json"'.

173       pluginRenderers.push({ plugin, renderer })
                                         ~~~~~~~~

  src/components/Page/primitives/ContentRenderer/pluginRegistry.ts:166:5
    166     renderer: PluginRenderer
            ~~~~~~~~
    The expected type comes from property 'renderer' which is declared here on type '{ plugin: RegisteredPlugin<ContentFormat>; renderer: PluginRenderer<ContentFormat>; }'


Found 7 errors in 2 files.

Errors  Files
     6  src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx:8
     1  src/components/Page/primitives/ContentRenderer/pluginRegistry.ts:173