
src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:115:4 - error TS2304: Cannot find name 'SelectRoot'.

115   <SelectRoot
       ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:116:13 - error TS2304: Cannot find name 'contentFormat'.

116     value={[contentFormat]}
                ~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:117:21 - error TS7006: Parameter 'e' implicitly has an 'any' type.

117     onValueChange={(e) => setValue("content_format", e.value[0] as ContentFormat)}
                        ~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:117:27 - error TS2304: Cannot find name 'setValue'.

117     onValueChange={(e) => setValue("content_format", e.value[0] as ContentFormat)}
                              ~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:120:6 - error TS2304: Cannot find name 'SelectTrigger'.

120     <SelectTrigger>
         ~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:121:8 - error TS2304: Cannot find name 'SelectValueText'.

121       <SelectValueText placeholder="Select format" />
           ~~~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:122:7 - error TS2304: Cannot find name 'SelectTrigger'.

122     </SelectTrigger>
          ~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:123:6 - error TS2304: Cannot find name 'SelectContent'.

123     <SelectContent>
         ~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:124:8 - error TS2304: Cannot find name 'SelectItem'.

124       <SelectItem value="HTML">Rich Text (HTML)</SelectItem>
           ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:124:50 - error TS2304: Cannot find name 'SelectItem'.

124       <SelectItem value="HTML">Rich Text (HTML)</SelectItem>
                                                     ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:125:8 - error TS2304: Cannot find name 'SelectItem'.

125       <SelectItem value="TEXT">Plain Text</SelectItem>
           ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:125:44 - error TS2304: Cannot find name 'SelectItem'.

125       <SelectItem value="TEXT">Plain Text</SelectItem>
                                               ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:126:8 - error TS2304: Cannot find name 'SelectItem'.

126       <SelectItem value="JSON">JSON (Advanced)</SelectItem>
           ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:126:49 - error TS2304: Cannot find name 'SelectItem'.

126       <SelectItem value="JSON">JSON (Advanced)</SelectItem>
                                                    ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:127:7 - error TS2304: Cannot find name 'SelectContent'.

127     </SelectContent>
          ~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx:128:5 - error TS2304: Cannot find name 'SelectRoot'.

128   </SelectRoot>
        ~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/NodeEditorForm.tsx:20:8 - error TS2307: Cannot find module '@/components/ui/select' or its corresponding type declarations.

20 } from "@/components/ui/select"
          ~~~~~~~~~~~~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/NodeEditorForm.tsx:40:10 - error TS6133: 'formatChangeWarning' is declared but its value is never read.

40   const [formatChangeWarning, setFormatChangeWarning] = useState(false)
            ~~~~~~~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/NodeEditorForm.tsx:40:31 - error TS6133: 'setFormatChangeWarning' is declared but its value is never read.

40   const [formatChangeWarning, setFormatChangeWarning] = useState(false)
                                 ~~~~~~~~~~~~~~~~~~~~~~

src/components/Stories/StoryEditor/NodeEditor/NodeEditorForm.tsx:40:57 - error TS2304: Cannot find name 'useState'.

40   const [formatChangeWarning, setFormatChangeWarning] = useState(false)
                                                           ~~~~~~~~

src/components/Stories/StoryPlayer/StoryPreview.tsx:34:7 - error TS6133: 'renderContent' is declared but its value is never read.

34 const renderContent = (node: StoryNodePublic) => {
         ~~~~~~~~~~~~~

src/components/Stories/StoryPlayer/StoryPreview.tsx:39:10 - error TS2678: Type '"HTML"' is not comparable to type 'ContentFormat | "TEXT"'.

39     case "HTML":
            ~~~~~~

src/components/Stories/StoryPlayer/StoryPreview.tsx:46:11 - error TS2322: Type '{ className: string; dangerouslySetInnerHTML: { __html: string; }; fontSize: "lg"; lineHeight: "tall"; sx: { '& p': { margin: string; }; '& h1': { fontSize: string; fontWeight: string; margin: string; }; '& h2': { ...; }; ... 6 more ...; '& img': { ...; }; }; }' is not assignable to type 'IntrinsicAttributes & Omit<PatchHtmlProps<Omit<DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement>, "ref">>, "color" | ... 808 more ... | keyof PolymorphicProps> & Omit<...> & PolymorphicProps & { ...; }'.
  Property 'sx' does not exist on type 'IntrinsicAttributes & Omit<PatchHtmlProps<Omit<DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement>, "ref">>, "color" | ... 808 more ... | keyof PolymorphicProps> & Omit<...> & PolymorphicProps & { ...; }'.

46           sx={{
             ~~

src/components/Stories/StoryPlayer/StoryPreview.tsx:78:10 - error TS2678: Type '"JSON"' is not comparable to type 'ContentFormat | "TEXT"'.

78     case "JSON":
            ~~~~~~

