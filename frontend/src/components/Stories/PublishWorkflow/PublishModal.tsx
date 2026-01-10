import { useState } from "react"
import {
  Box,
  Button,
  DialogActionTrigger,
  Heading,
  Separator,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { usePublishWorkflow } from "@/hooks/stories/usePublishWorkflow"
import ValidationSummary from "./ValidationSummary"

interface PublishModalProps {
  storyId: string
  isOpen: boolean
  onClose: () => void
}

const PublishModal = ({ storyId, isOpen, onClose }: PublishModalProps) => {
  const [confirmChecked, setConfirmChecked] = useState(false)
  const {
    story,
    validation,
    isReady,
    isLoading,
    publish,
    isPublishing,
  } = usePublishWorkflow({ storyId })

  const handlePublish = () => {
    publish()
    onClose()
    setConfirmChecked(false)
  }

  const handleClose = () => {
    onClose()
    setConfirmChecked(false)
  }

  return (
    <DialogRoot
      size={{ base: "sm", md: "lg" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => {
        if (!open) handleClose()
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Publish Story{story ? ` v${story.current_version}` : ""}?
          </DialogTitle>
        </DialogHeader>

        <DialogBody>
          <VStack align="stretch" gap={4}>
            <Text fontSize="sm" color="fg.muted">
              Publishing will make your story available in the catalog for all users to
              discover and play.
            </Text>

            {isLoading ? (
              <Box textAlign="center" py={8}>
                <Spinner size="lg" colorPalette="blue" />
                <Text mt={2} fontSize="sm" color="fg.muted">
                  Validating story...
                </Text>
              </Box>
            ) : (
              <>
                <Separator />

                <Box>
                  <Heading size="sm" mb={3}>
                    Validation Results
                  </Heading>
                  <ValidationSummary validation={validation} />
                </Box>

                {validation.warnings.length > 0 && (
                  <Box p={3} bg="orange.50" borderRadius="md">
                    <Text fontSize="sm" color="orange.800">
                      <strong>Note:</strong> You can publish despite warnings, but we
                      recommend addressing them for the best player experience.
                    </Text>
                  </Box>
                )}

                <Separator />

                <Checkbox
                  checked={confirmChecked}
                  onCheckedChange={(e) => setConfirmChecked(!!e.checked)}
                  disabled={!isReady}
                >
                  <Text fontSize="sm">
                    I understand this will make the story available in the catalog
                  </Text>
                </Checkbox>
              </>
            )}
          </VStack>
        </DialogBody>

        <DialogFooter gap={2}>
          <DialogActionTrigger asChild>
            <Button
              variant="subtle"
              colorPalette="gray"
              disabled={isPublishing}
              onClick={handleClose}
            >
              Cancel
            </Button>
          </DialogActionTrigger>
          <Button
            variant="solid"
            colorPalette="blue"
            onClick={handlePublish}
            disabled={!isReady || !confirmChecked || isLoading}
            loading={isPublishing}
          >
            Publish v{story?.current_version || "?"}
          </Button>
        </DialogFooter>

        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default PublishModal
