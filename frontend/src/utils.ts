import { AxiosError } from "axios"
import type { ApiError } from "./client"

function extractErrorMessage(err: ApiError): string {
  if (err instanceof AxiosError) {
    return err.message
  }

  const errDetail = (err.body as any)?.detail

  // Handle array of validation errors (Pydantic format)
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    return errDetail[0].msg
  }

  // Handle object with message field (custom API errors)
  if (errDetail && typeof errDetail === "object" && "message" in errDetail) {
    return errDetail.message
  }

  // Handle string or fallback
  if (typeof errDetail === "string") {
    return errDetail
  }

  return "Something went wrong."
}

export const handleError = function (
  this: (msg: string) => void,
  err: ApiError,
) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
