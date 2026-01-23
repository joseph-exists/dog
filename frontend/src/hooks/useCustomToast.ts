import { toast } from "sonner"

// Module-level functions — referentially stable across renders.
// These have no React state dependencies; wrapping them in a hook
// caused unstable references that triggered infinite re-render loops
// in any useEffect/useCallback that included them as dependencies.

export const showSuccessToast = (description: string) => {
  toast.success("Success!", { description })
}

export const showErrorToast = (description: string) => {
  toast.error("Something went wrong!", { description })
}

export const showWarningToast = (description: string) => {
  toast("Warning", { description })
}

/** @deprecated Use named exports directly: `import { showErrorToast } from "@/hooks/useCustomToast"` */
const useCustomToast = () => {
  return { showSuccessToast, showErrorToast, showWarningToast }
}

export default useCustomToast
