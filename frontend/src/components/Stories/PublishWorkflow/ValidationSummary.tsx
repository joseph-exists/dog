import { HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { FaCheckCircle, FaTimesCircle, FaExclamationTriangle } from "react-icons/fa"
import type { ValidationResult } from "../shared/storyValidation"

interface ValidationSummaryProps {
  validation: ValidationResult
}

const ValidationSummary = ({ validation }: ValidationSummaryProps) => {
  const passedChecks = [
    validation.errors.length === 0 && "Story structure is valid",
    validation.warnings.length === 0 && "No warnings detected",
  ].filter(Boolean) as string[]

  return (
    <VStack align="stretch" gap={3}>
      {/* Passed Checks */}
      {passedChecks.map((check) => (
        <HStack key={check} color="green.600">
          <Icon fontSize="lg">
            <FaCheckCircle />
          </Icon>
          <Text fontSize="sm">{check}</Text>
        </HStack>
      ))}

      {/* Errors */}
      {validation.errors.map((error) => (
        <HStack key={error} color="red.600">
          <Icon fontSize="lg">
            <FaTimesCircle />
          </Icon>
          <Text fontSize="sm">{error}</Text>
        </HStack>
      ))}

      {/* Warnings */}
      {validation.warnings.map((warning) => (
        <HStack key={warning} color="orange.600">
          <Icon fontSize="lg">
            <FaExclamationTriangle />
          </Icon>
          <Text fontSize="sm">{warning}</Text>
        </HStack>
      ))}

      {/* Overall Status */}
      {validation.isValid ? (
        <HStack color="green.700" mt={2} p={3} bg="green.50" borderRadius="md">
          <Icon fontSize="xl">
            <FaCheckCircle />
          </Icon>
          <Text fontWeight="bold">Story is ready to publish!</Text>
        </HStack>
      ) : (
        <HStack color="red.700" mt={2} p={3} bg="red.50" borderRadius="md">
          <Icon fontSize="xl">
            <FaTimesCircle />
          </Icon>
          <Text fontWeight="bold">
            Please fix {validation.errors.length} error(s) before publishing
          </Text>
        </HStack>
      )}
    </VStack>
  )
}

export default ValidationSummary
