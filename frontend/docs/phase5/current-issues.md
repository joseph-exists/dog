
> frontend@0.0.0 build
> tsc -p tsconfig.build.json && vite build

src/components/Common/EditDrawer.tsx:125:7 - error TS2322: Type '"right"' is not assignable to type 'ConditionalValue<"bottom" | "top" | "end" | "start" | undefined>'.

125       placement="right"
          ~~~~~~~~~

  node_modules/@chakra-ui/react/dist/types/styled-system/generated/recipes.gen.d.ts:560:3
    560   placement?: "start" | "end" | "top" | "bottom"
          ~~~~~~~~~
    The expected type comes from property 'placement' which is declared here on type 'IntrinsicAttributes & DrawerRootProps'

src/components/Rooms/MessageFilters.tsx:76:8 - error TS2604: JSX element type 'Select' does not have any construct or call signatures.

76       <Select
          ~~~~~~

src/components/Rooms/MessageFilters.tsx:76:8 - error TS2786: 'Select' cannot be used as a JSX component.
  Its type 'typeof import("/home/josep/dog/frontend/node_modules/@chakra-ui/react/dist/types/components/select/namespace")' is not a valid JSX element type.

76       <Select
          ~~~~~~

src/components/Rooms/MessageFilters.tsx:84:20 - error TS7006: Parameter 'e' implicitly has an 'any' type.

84         onChange={(e) => {
                      ~

src/components/Rooms/MessageFilters.tsx:98:8 - error TS2604: JSX element type 'Select' does not have any construct or call signatures.

98       <Select
          ~~~~~~

src/components/Rooms/MessageFilters.tsx:98:8 - error TS2786: 'Select' cannot be used as a JSX component.
  Its type 'typeof import("/home/josep/dog/frontend/node_modules/@chakra-ui/react/dist/types/components/select/namespace")' is not a valid JSX element type.

98       <Select
          ~~~~~~

src/components/Rooms/MessageFilters.tsx:104:20 - error TS7006: Parameter 'e' implicitly has an 'any' type.

104         onChange={(e) => {
                       ~

src/components/Rooms/MessageFilters.tsx:115:8 - error TS2604: JSX element type 'Select' does not have any construct or call signatures.

115       <Select
           ~~~~~~

src/components/Rooms/MessageFilters.tsx:115:8 - error TS2786: 'Select' cannot be used as a JSX component.
  Its type 'typeof import("/home/josep/dog/frontend/node_modules/@chakra-ui/react/dist/types/components/select/namespace")' is not a valid JSX element type.

115       <Select
           ~~~~~~

src/components/Rooms/MessageFilters.tsx:119:20 - error TS7006: Parameter 'e' implicitly has an 'any' type.

119         onChange={(e) =>
                       ~

src/components/Rooms/MessageList.tsx:215:11 - error TS2739: Type '{ message_id: string; room_id: string; sender_type: "agent"; sender_name: string; sender_id: null; agent_name: string; content: string; button_options: null; created_at: Date; is_own_message: false; }' is missing the following properties from type 'MessageViewModel': is_pinned, active_for_context

215           message={{
              ~~~~~~~

  src/components/Rooms/Message.tsx:23:3
    23   message: MessageViewModel;
         ~~~~~~~
    The expected type comes from property 'message' which is declared here on type 'IntrinsicAttributes & MessageProps'

src/components/Rooms/PinnedMessagesSection.tsx:51:3 - error TS6133: 'roomId' is declared but its value is never read.

51   roomId,
     ~~~~~~

src/components/ui/message-badge.tsx:15:25 - error TS2307: Cannot find module '@/components/ui/tooltip' or its corresponding type declarations.

15 import { Tooltip } from "@/components/ui/tooltip"
                           ~~~~~~~~~~~~~~~~~~~~~~~~~

src/hooks/useRoomMessages.ts:152:15 - error TS2739: Type '{ message_id: string; room_id: string; sender_type: "user"; sender_name: string; sender_id: string | null; agent_name: null; content: string; button_options: null; created_at: Date; is_own_message: true; }' is missing the following properties from type 'MessageViewModel': is_pinned, active_for_context

152         const optimisticMessage: MessageViewModel = {
                  ~~~~~~~~~~~~~~~~~

src/routes/_layout/room.$roomId.tsx:73:5 - error TS6133: 'isPinning' is declared but its value is never read.

73     isPinning,
       ~~~~~~~~~

src/routes/_layout/room.$roomId.tsx:75:5 - error TS6133: 'isUnpinning' is declared but its value is never read.

75     isUnpinning,
       ~~~~~~~~~~~

src/routes/_layout/room.$roomId.tsx:77:5 - error TS6133: 'isTogglingContext' is declared but its value is never read.

77     isTogglingContext,
       ~~~~~~~~~~~~~~~~~

src/routes/_layout/room.$roomId.tsx:79:5 - error TS6133: 'isDeleting' is declared but its value is never read.

79     isDeleting,
       ~~~~~~~~~~


Found 18 errors in 7 files.

Errors  Files
     1  src/components/Common/EditDrawer.tsx:125
     9  src/components/Rooms/MessageFilters.tsx:76
     1  src/components/Rooms/MessageList.tsx:215
     1  src/components/Rooms/PinnedMessagesSection.tsx:51
     1  src/components/ui/message-badge.tsx:15
     1  src/hooks/useRoomMessages.ts:152
     4  src/routes/_layout/room.$roomId.tsx:73