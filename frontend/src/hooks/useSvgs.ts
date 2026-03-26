import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type {
  ApiError,
  SvgAssetCreatePrivate,
  SvgAssetCreatePublicFromPrivate,
  SvgAssetUpdate,
  SvgAssetVisibility,
} from "@/client"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { SvgAppService } from "@/services/svgService"
import { handleError } from "@/utils"

export const svgsQueryKeys = {
  all: ["svgs"] as const,
  list: (input?: {
    skip?: number
    limit?: number
    visibility?: SvgAssetVisibility
  }) =>
    [
      ...svgsQueryKeys.all,
      "list",
      input?.skip ?? 0,
      input?.limit ?? 100,
      input?.visibility ?? "all",
    ] as const,
  detail: (svgId: string) => [...svgsQueryKeys.all, "detail", svgId] as const,
}

export function useSvgsList(input: {
  skip?: number
  limit?: number
  visibility?: SvgAssetVisibility
}) {
  return useQuery({
    queryKey: svgsQueryKeys.list(input),
    queryFn: () => SvgAppService.listSvgs(input),
  })
}

export function useSvg(svgId: string) {
  return useQuery({
    queryKey: svgsQueryKeys.detail(svgId),
    queryFn: () => SvgAppService.getSvg(svgId),
    enabled: Boolean(svgId),
  })
}

export function useCreatePrivateSvg() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: SvgAssetCreatePrivate) =>
      SvgAppService.createPrivateSvg(input),
    onSuccess: () => {
      showSuccessToast("SVG asset created")
      queryClient.invalidateQueries({ queryKey: svgsQueryKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useCreatePublicSvgCopy() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: SvgAssetCreatePublicFromPrivate) =>
      SvgAppService.createPublicCopy(input),
    onSuccess: () => {
      showSuccessToast("Public SVG copy created")
      queryClient.invalidateQueries({ queryKey: svgsQueryKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function usePatchSvg() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { svgId: string; patch: SvgAssetUpdate }) =>
      SvgAppService.patchSvg(input.svgId, input.patch),
    onSuccess: (row) => {
      showSuccessToast("SVG updated")
      queryClient.invalidateQueries({ queryKey: svgsQueryKeys.all })
      queryClient.invalidateQueries({ queryKey: svgsQueryKeys.detail(row.id) })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useDeleteSvg() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (svgId: string) => SvgAppService.deleteSvg(svgId),
    onSuccess: () => {
      showSuccessToast("SVG deleted")
      queryClient.invalidateQueries({ queryKey: svgsQueryKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}
