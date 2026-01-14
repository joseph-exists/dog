import { Box, Card as ChakraCard } from "@chakra-ui/react"

import * as React from "react"
import { CloseButton, type CloseButtonProps } from "./close-button"

export const CardContent = React.forwardRef<HTMLDivElement>(
  function CardContent(props, ref) {
    const { ...rest } = props
    return <Box p={4} {...rest} ref={ref} />
  },
)

export const CardCloseTrigger = React.forwardRef<
  HTMLButtonElement,
  CloseButtonProps
>(function CardCloseTrigger(props, ref) {
  return (
    <CloseButton position="absolute" top="2" insetEnd="2" {...props} asChild>
      <CloseButton size="sm" ref={ref} />
    </CloseButton>
  )
})

// Add new enhanced components or props
export interface CardRootProps extends ChakraCard.RootProps {
  isSelectable?: boolean
  isSelected?: boolean
  onSelect?: () => void
}

export const CardRoot = React.forwardRef<HTMLDivElement, CardRootProps>(
  function CardRoot(
    { isSelectable, isSelected, onSelect, children, ...props },
    ref,
  ) {
    // const selectedBg =  //need to set this effect
    // const selectedBorder = // need to set this effect
    //  const hoverBg = // need to set this effect

    return (
      <ChakraCard.Root
        ref={ref}
        cursor={isSelectable ? "pointer" : "default"}
        onClick={isSelectable ? onSelect : undefined}
        // bg={isSelected ? selectedBg : undefined}
        // borderColor={isSelected ? selectedBorder : undefined}
        // borderWidth={isSelected ? "2px" : "1px"}
        transition="all 0.2s"
        _hover={
          isSelectable
            ? {
                //  bg: isSelected ? selectedBg : hoverBg,
                transform: "translateY(-2px)",
                boxShadow: "md",
              }
            : undefined
        }
        {...props}
      >
        {children}
      </ChakraCard.Root>
    )
  },
)

// Existing exports
export const CardBody = ChakraCard.Body
export const CardFooter = ChakraCard.Footer
export const CardHeader = ChakraCard.Header
export const CardDescription = ChakraCard.Description
export const CardTitle = ChakraCard.Title
