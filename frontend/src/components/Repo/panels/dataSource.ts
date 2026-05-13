import { RoomsService, UserReposService } from "@/client/sdk.gen"
import type {
  RoomArtifactFileContent,
  ShadowRepoViewResponse,
  ShadowRepoTreeEntry,
  UserRepoCommitResponse,
  UserRepoFileContent,
  UserRepoFileMutationInput,
  UserRepoPublic,
  UserRepoViewResponse,
} from "@/client/types.gen"

export type RepoPanelTarget =
  | {
      model: "user_repo"
      repoId: string
    }
  | {
      model: "room_shadow_repo"
      roomId: string
      repoId: "room"
    }

export interface RepoPanelFileContent
  extends Omit<UserRepoFileContent, "content"> {
  content: string | null
  write_hint?: {
    branch?: string | null
    expected_head_sha?: string | null
  }
  resolved_from_path?: string
}

export interface RepoPanelCommitResponse
  extends Omit<UserRepoCommitResponse, "repo_id" | "previous_head_sha"> {
  repo_id?: string
  room_id?: string
  previous_head_sha?: string | null
}

export interface RepoPanelDataSourceAdapter {
  target: RepoPanelTarget
  targetKey: string
  getTree(args: {
    path?: string
    ref?: string
    commitLimit?: number
  }): Promise<UserRepoViewResponse>
  getFile(args: { path: string; ref?: string }): Promise<RepoPanelFileContent>
  getReadme(args: { ref?: string }): Promise<RepoPanelFileContent>
  commit(args: {
    branch: string
    expectedHeadSha: string
    commitMessage: string
    mutations: Array<UserRepoFileMutationInput>
  }): Promise<RepoPanelCommitResponse>
  getHead(args: {
    ref?: string | null
  }): Promise<{ ref: string; expectedHeadSha: string | null }>
}

export function repoPanelTargetKey(target: RepoPanelTarget): string {
  return target.model === "user_repo"
    ? `user_repo:${target.repoId}`
    : `room_shadow_repo:${target.roomId}`
}

function normalizeRoomArtifactViewResponse(
  response: ShadowRepoViewResponse,
): UserRepoViewResponse {
  return {
    ...response,
    summary: {
      repo_id: response.summary.entity_id,
      slug: "room",
      display_name: "Room repo",
      repo_available: response.summary.repo_available,
      default_branch: response.summary.default_branch,
      latest_commit_sha: response.summary.latest_commit_sha,
      latest_commit_message: response.summary.latest_commit_message,
      latest_commit_authored_at: response.summary.latest_commit_authored_at,
    },
    tree: response.tree ?? [],
    commits: response.commits ?? [],
  }
}

function normalizeRoomArtifactFileContent(
  response: RoomArtifactFileContent,
): RepoPanelFileContent {
  return {
    ...response,
    content: response.content ?? null,
    encoding: response.encoding ?? undefined,
  }
}

function createUserRepoPanelAdapter(repoId: string): RepoPanelDataSourceAdapter {
  const target: RepoPanelTarget = { model: "user_repo", repoId }
  return {
    target,
    targetKey: repoPanelTargetKey(target),
    getTree: (args) =>
      UserReposService.getUserRepoTree({
        repoId,
        path: args.path,
        ref: args.ref,
        commitLimit: args.commitLimit,
      }),
    getFile: (args) =>
      UserReposService.getUserRepoFile({
        repoId,
        path: args.path,
        ref: args.ref,
      }),
    getReadme: (args) =>
      UserReposService.getUserRepoReadme({
        repoId,
        ref: args.ref,
      }),
    commit: (args) =>
      UserReposService.commitUserRepoChanges({
        repoId,
        requestBody: {
          branch: args.branch,
          expected_head_sha: args.expectedHeadSha,
          commit_message: args.commitMessage,
          mutations: args.mutations,
        },
      }),
    getHead: async (args) => {
      const view = await UserReposService.getUserRepoTree({
        repoId,
        ref: args.ref || undefined,
        commitLimit: 1,
      })
      return {
        ref: view.ref,
        expectedHeadSha: view.summary.latest_commit_sha || null,
      }
    },
  }
}

function createRoomArtifactPanelAdapter(
  roomId: string,
): RepoPanelDataSourceAdapter {
  const target: RepoPanelTarget = {
    model: "room_shadow_repo",
    roomId,
    repoId: "room",
  }
  return {
    target,
    targetKey: repoPanelTargetKey(target),
    getTree: (args) =>
      RoomsService.getRoomArtifactTree({
        roomId,
        path: args.path,
        commitLimit: args.commitLimit,
      }).then(normalizeRoomArtifactViewResponse),
    getFile: (args) =>
      RoomsService.getRoomArtifactFile({
        roomId,
        path: args.path,
        ref: args.ref,
      }).then(normalizeRoomArtifactFileContent),
    getReadme: async (args) => {
      const candidates = ["README.md", "README", "readme.md", "Readme.md"]
      let lastError: unknown = null
      for (const path of candidates) {
        try {
          const content = await RoomsService.getRoomArtifactFile({
            roomId,
            path,
            ref: args.ref,
          })
          return {
            ...normalizeRoomArtifactFileContent(content),
            resolved_from_path: path,
          }
        } catch (error) {
          lastError = error
        }
      }
      throw lastError
    },
    commit: (args) =>
      RoomsService.commitRoomArtifactChanges({
        roomId,
        requestBody: {
          branch: args.branch,
          expected_head_sha: args.expectedHeadSha,
          commit_message: args.commitMessage,
          mutations: args.mutations,
        },
      }),
    getHead: async () => {
      const view = await RoomsService.getRoomArtifactTree({
        roomId,
        commitLimit: 1,
      })
      return {
        ref: view.ref,
        expectedHeadSha: view.summary.latest_commit_sha || null,
      }
    },
  }
}

export function createRepoPanelAdapter(
  target: RepoPanelTarget,
): RepoPanelDataSourceAdapter {
  return target.model === "user_repo"
    ? createUserRepoPanelAdapter(target.repoId)
    : createRoomArtifactPanelAdapter(target.roomId)
}

export function createRoomArtifactRepoIdentity(params: {
  roomId: string
  roomTitle?: string | null
}): UserRepoPublic {
  const now = new Date().toISOString()
  return {
    id: "room",
    slug: "room",
    display_name: params.roomTitle
      ? `${params.roomTitle} repo`
      : "Room repo",
    description: "Room artifact repository",
    source_repo_url: null,
    source_branch: "main",
    import_status: "ready",
    import_error: null,
    imported_at: now,
    gogs_repo_name: `room-${params.roomId}`,
    gogs_repo_id: null,
    gogs_full_name: null,
    gogs_html_url: null,
    is_private: true,
    owner_user_id: params.roomId,
    created_at: now,
    updated_at: now,
    default_branch: "main",
    capabilities: {
      has_file_tree: true,
      has_blob_content: true,
      has_commit_history: true,
      has_search: false,
      has_branches: false,
      default_branch: "main",
    },
  }
}

export type RepoPanelTreeEntry = ShadowRepoTreeEntry
