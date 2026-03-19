import { useMutation, useQuery } from "@tanstack/react-query"
import type { ApiError } from "@/client"
import { showErrorToast } from "@/hooks/useCustomToast"
import {
  TesserService,
  type TesserScriptEnqueueRequest,
  type TesserScriptRunRequest,
} from "@/services/tesserService"
import { handleError } from "@/utils"

export const tesserQueryKeys = {
  all: ["tesser"] as const,
  scripts: (input?: { format?: string }) =>
    [...tesserQueryKeys.all, "scripts", input?.format ?? "all"] as const,
  scriptHelp: (scriptName: string) =>
    [...tesserQueryKeys.all, "scripts", scriptName, "help"] as const,
  examplesIndex: () => [...tesserQueryKeys.all, "examples", "index"] as const,
  jobs: () => [...tesserQueryKeys.all, "jobs"] as const,
  job: (jobId: string) => [...tesserQueryKeys.jobs(), jobId] as const,
}

export function useTesserScripts(input?: { format?: string }) {
  return useQuery({
    queryKey: tesserQueryKeys.scripts(input),
    queryFn: () => TesserService.listScripts(input),
  })
}

export function useTesserScriptHelp(
  scriptName: string,
  options?: { enabled?: boolean },
) {
  return useQuery({
    queryKey: tesserQueryKeys.scriptHelp(scriptName),
    queryFn: () => TesserService.getScriptHelp(scriptName),
    enabled: (options?.enabled ?? true) && Boolean(scriptName),
  })
}

export function useTesserExamplesIndex(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: tesserQueryKeys.examplesIndex(),
    queryFn: () => TesserService.getExamplesIndex(),
    enabled: options?.enabled ?? true,
  })
}

export function useRunTesserScript() {
  return useMutation({
    mutationFn: (input: {
      scriptName: string
      payload: TesserScriptRunRequest
    }) => TesserService.runScript(input.scriptName, input.payload),
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}

export function useEnqueueTesserScript() {
  return useMutation({
    mutationFn: (input: {
      scriptName: string
      payload: TesserScriptEnqueueRequest
    }) => TesserService.enqueueScript(input.scriptName, input.payload),
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}
