import type {
  SvgAssetCreatePrivate,
  SvgAssetCreatePublicFromPrivate,
  SvgAssetPublic,
  SvgAssetUpdate,
  SvgAssetVisibility,
} from "@/client"
import { SvgsService } from "@/client"

export interface ListSvgsInput {
  skip?: number
  limit?: number
  visibility?: SvgAssetVisibility
}

export const SvgAppService = {
  async listSvgs(input: ListSvgsInput = {}): Promise<{
    data: SvgAssetPublic[]
    count: number
  }> {
    const response = await SvgsService.listSvgs({
      skip: input.skip,
      limit: input.limit,
      visibility: input.visibility,
    })
    return {
      data: response.data ?? [],
      count: response.count ?? 0,
    }
  },

  async getSvg(svgId: string): Promise<SvgAssetPublic> {
    return SvgsService.getSvg({ svgId })
  },

  async createPrivateSvg(
    input: SvgAssetCreatePrivate,
  ): Promise<SvgAssetPublic> {
    return SvgsService.createSvg({ requestBody: input })
  },

  async createPublicCopy(
    input: SvgAssetCreatePublicFromPrivate,
  ): Promise<SvgAssetPublic> {
    return SvgsService.createSvg({ requestBody: input })
  },

  async patchSvg(
    svgId: string,
    input: SvgAssetUpdate,
  ): Promise<SvgAssetPublic> {
    return SvgsService.patchSvg({ svgId, requestBody: input })
  },

  async deleteSvg(svgId: string): Promise<void> {
    await SvgsService.deleteSvg({ svgId })
  },
}
