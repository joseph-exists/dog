import type { UserRepoPublic } from "@/client"
import { OpenAPI } from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"

interface MessageResponse {
  message: string
}

export const UserRepoAppService = {
  async cancelUserRepoImport(repoId: string): Promise<UserRepoPublic> {
    const options: ApiRequestOptions<UserRepoPublic> = {
      method: "POST",
      url: `/api/v1/user-repos/${repoId}/cancel`,
    }
    return __request<UserRepoPublic>(OpenAPI, options)
  },

  async deleteUserRepo(repoId: string): Promise<MessageResponse> {
    const options: ApiRequestOptions<MessageResponse> = {
      method: "DELETE",
      url: `/api/v1/user-repos/${repoId}`,
    }
    return __request<MessageResponse>(OpenAPI, options)
  },
}
