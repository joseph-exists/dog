import { Card as ChakraCard } from "@chakra-ui/react"
import * as React from "react"
import { CloseButton } from "./close-button"


export const CardContent = React.forwardRef<
  HTMLDivElement
>(function CardContent(props, ref) {
  const {  ...rest } = props
  return ()
})

export const CardCloseTrigger = React.forwardRef<
  HTMLButtonElement,
  ChakraCard.CloseTriggerProps
>(function CardCloseTrigger(props, ref) {
  return (
    <CloseButton
      position="absolute"
      top="2"
      insetEnd="2"
      {...props}
      asChild
    >
      <CloseButton size="sm" ref={ref} />
    </.CloseTrigger>
  )
})

export const CardBody = ChakraCard.Body
export const CardRoot = ChakraCard.Root
export const CardFooter = ChakraCard.Footer
export const CardHeader = ChakraCard.Header
export const CardDescription = ChakraCard.Description
export const CardTitle = ChakraCard.Title
