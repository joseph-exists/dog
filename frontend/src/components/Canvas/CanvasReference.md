
```typescript
import { useSync } from `@tldraw/sync`
import { multiplayerAssetStore } from `./multiplayerAssetStore`
import { getBookmarkPreview } from './getBookmarkPreview'
import { Tldraw } from 'tldraw'
import useAuth from '../../hooks/useAuth'

interface CanvasProps {
    roomId?: string
    roomToken?: string
  }

function Canvas({ room_id, roomToken }: CanvasProps) {
    const { user } = useAuth()

    // redirect to login if not authenticated

    if (!user) { return /login}

  // Show loading state while waiting for room token
  if (!roomId && !roomToken) {
    return (canvas with notes or whatnot)
  }

  // Build the connection URI
  const connectionUri = roomToken 
    ? `${TLDRAW_WORKER_URL}/connect/${roomId}?token=${roomToken}`
    : `${TLDRAW_WORKER_URL}/connect/${roomId}`

  const store = useSync({
    uri: connectionUri,
    assets: multiplayerAssetStore,
  })

  return (
  <Container
  >
            <Tldraw 
          store={store}
          onMount={(editor)=> {
            // when the editor is ready, we may need to register our bookmark unfurling service
            editor.registerExternalAssetHandler('url', getBookmarkPreview)
          }}
        />
  </Container>

}

export default Canvas
```


```typescript
// this is the multiplayerAssetStore.tsx

import { TLAssetStore, uniqueId } from 'tldraw'

const WORKER_URL = process.env.TLDRAW_WORKER_URL

// How does our server handle assets like images and videos?
export const multiplayerAssetStore: TLAssetStore = {
	// to upload an asset, we...
	async upload(_asset, file) {
		// ...create a unique name & URL...
		const id = uniqueId()
		const objectName = `${id}-${file.name}`.replace(/[^a-zA-Z0-9.]/g, '-')
		const url = `${WORKER_URL}/uploads/${objectName}`

		// ...POST it to out worker to upload it...
		const response = await fetch(url, {
			method: 'POST',
			body: file,
		})

		if (!response.ok) {
			throw new Error(`Failed to upload asset: ${response.statusText}`)
		}

		// ...and return the URL to be stored with the asset record.
		return { src: url }
	},

	// to retrieve an asset, we can just use the same URL. you could customize this to add extra
	// auth, or to serve optimized versions / sizes of the asset.
	resolve(asset) {
		return asset.props.src
	},
}
```

## use sync Reference


```typescript
import { Editor } from 'tldraw';
import { Signal } from 'tldraw';
import { TLAssetStore } from 'tldraw';
import { TLPresenceStateInfo } from 'tldraw';
import { TLPresenceUserInfo } from 'tldraw';
import { TLStore } from 'tldraw';
import { TLStoreSchemaOptions } from 'tldraw';
import { TLStoreWithStatus } from 'tldraw';

/** @public */
export declare type RemoteTLStoreWithStatus = Exclude<TLStoreWithStatus, {
    status: 'not-synced';
} | {
    status: 'synced-local';
}>;

/**
 * useSync creates a store that is synced with a multiplayer server.
 *
 * The store can be passed directly into the `<Tldraw />` component to enable multiplayer features.
 * It will handle loading states, and enable multiplayer UX like user cursors and following.
 *
 * To enable external blob storage, you should also pass in an `assets` object that implements the {@link tldraw#TLAssetStore} interface.
 * If you don't do this, adding large images and videos to rooms will cause performance issues at serialization boundaries.
 *
 * @example
 * ```tsx
 * function MyApp() {
 *     const store = useSync({
 *         uri: 'wss://myapp.com/sync/my-test-room',
 *         assets: myAssetStore
 *     })
 *     return <Tldraw store={store} />
 * }
 *
 * ```
 * @param opts - Options for the multiplayer sync store. See {@link UseSyncOptions} and {@link tldraw#TLStoreSchemaOptions}.
 *
 * @public
 */
export declare function useSync(opts: UseSyncOptions & TLStoreSchemaOptions): RemoteTLStoreWithStatus;

/**
 * Creates a tldraw store synced with a multiplayer room hosted on tldraw's demo server `https://demo.tldraw.xyz`.
 *
 * The store can be passed directly into the `<Tldraw />` component to enable multiplayer features.
 * It will handle loading states, and enable multiplayer UX like user cursors and following.
 *
 * All data on the demo server is
 *
 * - Deleted after a day or so.
 * - Publicly accessible to anyone who knows the room ID. Use your company name as a prefix to help avoid collisions, or generate UUIDs for maximum privacy.
 *
 * @example
 * ```tsx
 * function MyApp() {
 *     const store = useSyncDemo({roomId: 'my-app-test-room'})
 *     return <Tldraw store={store} />
 * }
 * ```
 *
 * @param options - Options for the multiplayer demo sync store. See {@link UseSyncDemoOptions} and {@link tldraw#TLStoreSchemaOptions}.
 *
 * @public
 */
export declare function useSyncDemo(options: UseSyncDemoOptions & TLStoreSchemaOptions): RemoteTLStoreWithStatus;

/** @public */
export declare interface UseSyncDemoOptions {
    /**
     * The room ID to sync with. Make sure the room ID is unique. The namespace is shared by
     * everyone using the demo server. Consider prefixing it with your company or project name.
     */
    roomId: string;
    /**
     * A signal that contains the user information needed for multiplayer features.
     * This should be synchronized with the `userPreferences` configuration for the main `<Tldraw />` component.
     * If not provided, a default implementation based on localStorage will be used.
     */
    userInfo?: Signal<TLPresenceUserInfo> | TLPresenceUserInfo;
    /* Excluded from this release type: host */
    /**
     * {@inheritdoc UseSyncOptions.getUserPresence}
     * @public
     */
    getUserPresence?(store: TLStore, user: TLPresenceUserInfo): null | TLPresenceStateInfo;
}

/**
 * Options for the {@link useSync} hook.
 * @public
 */
export declare interface UseSyncOptions {
    /**
     * The URI of the multiplayer server. This must include the protocol,
     *
     *   e.g. `wss://server.example.com/my-room` or `ws://localhost:5858/my-room`.
     *
     * Note that the protocol can also be `https` or `http` and it will upgrade to a websocket
     * connection.
     *
     * Optionally, you can pass a function which will be called each time a connection is
     * established to get the URI. This is useful if you need to include e.g. a short-lived session
     * token for authentication.
     */
    uri: (() => Promise<string> | string) | string;
    /**
     * A signal that contains the user information needed for multiplayer features.
     * This should be synchronized with the `userPreferences` configuration for the main `<Tldraw />` component.
     * If not provided, a default implementation based on localStorage will be used.
     */
    userInfo?: Signal<TLPresenceUserInfo> | TLPresenceUserInfo;
    /**
     * The asset store for blob storage. See {@link tldraw#TLAssetStore}.
     *
     * If you don't have time to implement blob storage and just want to get started, you can use the inline base64 asset store. {@link tldraw#inlineBase64AssetStore}
     * Note that storing base64 blobs inline in JSON is very inefficient and will cause performance issues quickly with large images and videos.
     */
    assets: TLAssetStore;
    /* Excluded from this release type: onMount */
    /* Excluded from this release type: roomId */
    /* Excluded from this release type: trackAnalyticsEvent */
    /**
     * A reactive function that returns a {@link @tldraw/tlschema#TLInstancePresence} object. The
     * result of this function will be synchronized across all clients to display presence
     * indicators such as cursors. See {@link @tldraw/tlschema#getDefaultUserPresence} for
     * the default implementation of this function.
     */
    getUserPresence?(store: TLStore, user: TLPresenceUserInfo): null | TLPresenceStateInfo;
}


export * from "@tldraw/sync-core";

export { }
```
```typescript
import { AssetRecordType, TLAsset, TLBookmarkAsset, getHashForString } from 'tldraw'

// How does our server handle bookmark unfurling?
export async function getBookmarkPreview({ url }: { url: string }): Promise<TLAsset> {
	// we start with an empty asset record
	const asset: TLBookmarkAsset = {
		id: AssetRecordType.createId(getHashForString(url)),
		typeName: 'asset',
		type: 'bookmark',
		meta: {},
		props: {
			src: url,
			description: '',
			image: '',
			favicon: '',
			title: '',
		},
	}

	try {
		// try to fetch the preview data from the server
		const response = await fetch(
			`${process.env.TLDRAW_WORKER_URL}/unfurl?url=${encodeURIComponent(url)}`
		)
		const data = await response.json()

		// fill in our asset with whatever info we found
		asset.props.description = data?.description ?? ''
		asset.props.image = data?.image ?? ''
		asset.props.favicon = data?.favicon ?? ''
		asset.props.title = data?.title ?? ''
	} catch (e) {
		console.error(e)
	}

	return asset
}
```

