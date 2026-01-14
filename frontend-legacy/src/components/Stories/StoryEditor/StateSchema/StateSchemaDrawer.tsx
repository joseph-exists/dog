import { Box, HStack, Separator, Text, VStack } from "@chakra-ui/react"
import { FaCheck, FaExclamationTriangle } from "react-icons/fa"

import {
  DrawerBackdrop,
  DrawerBody,
  DrawerCloseTrigger,
  DrawerContent,
  DrawerHeader,
  DrawerRoot,
  DrawerTitle,
} from "@/components/ui/drawer"
import { useValidateStateSchema } from "@/hooks/stories/useStateSchema"
import StateSchemaEditor from "./StateSchemaEditor"

interface StateSchemaDrawerProps {
  storyId: string
  version: number
  isOpen: boolean
  onClose: () => void
  isReadOnly?: boolean
}

const StateSchemaDrawer = ({
  storyId,
  version,
  isOpen,
  onClose,
  isReadOnly = false,
}: StateSchemaDrawerProps) => {
  const { data: validationData } = useValidateStateSchema(storyId, version)

  return (
    <DrawerRoot
      size="md"
      placement="end"
      open={isOpen}
      onOpenChange={({ open }) => {
        if (!open) onClose()
      }}
    >
      <DrawerBackdrop />
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>State Variables</DrawerTitle>
        </DrawerHeader>
        <DrawerCloseTrigger />
        <DrawerBody>
          <VStack align="stretch" gap={4}>
            <Text fontSize="sm" color="fg.muted">
              Define variables that can be used in choice conditions. Variables
              control when choices appear and track player progress.
            </Text>

            {isReadOnly && (
              <Box
                p={3}
                bg="orange.subtle"
                borderRadius="md"
                borderWidth="1px"
                borderColor="orange.muted"
              >
                <Text fontSize="sm" color="orange.fg">
                  This is a published version. Create a new version to edit
                  variables.
                </Text>
              </Box>
            )}

            <StateSchemaEditor
              storyId={storyId}
              version={version}
              isReadOnly={isReadOnly}
            />

            {/* Validation Summary */}
            {validationData && (
              <>
                <Separator />
                <Box>
                  <Text fontSize="sm" fontWeight="bold" mb={2}>
                    Validation Summary
                  </Text>
                  {validationData.is_valid ? (
                    <HStack color="green.600" fontSize="sm">
                      <FaCheck />
                      <Text>All referenced variables are defined</Text>
                    </HStack>
                  ) : (
                    <VStack align="stretch" gap={2}>
                      <HStack color="orange.600" fontSize="sm">
                        <FaExclamationTriangle />
                        <Text>
                          {validationData.undefined_variables.length} undefined
                          variable
                          {validationData.undefined_variables.length !== 1
                            ? "s"
                            : ""}{" "}
                          used in choices
                        </Text>
                      </HStack>
                      <Box
                        pl={5}
                        fontSize="xs"
                        fontFamily="mono"
                        color="fg.muted"
                      >
                        {validationData.undefined_variables.map((key) => (
                          <Text key={key}>{key}</Text>
                        ))}
                      </Box>
                      <Text fontSize="xs" color="fg.muted">
                        Add these variables to the schema or remove them from
                        choices.
                      </Text>
                    </VStack>
                  )}
                </Box>
              </>
            )}

            {/* Usage stats */}
            {validationData && (
              <Box fontSize="xs" color="fg.muted">
                <Text>
                  Defined: {validationData.defined_variables.length} | Used:{" "}
                  {validationData.used_variables.length}
                </Text>
              </Box>
            )}
          </VStack>
        </DrawerBody>
      </DrawerContent>
    </DrawerRoot>
  )
}

export default StateSchemaDrawer
