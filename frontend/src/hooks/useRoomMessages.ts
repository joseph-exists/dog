/**
 * useRoomMessages Hook - Focused Message Operations
 *
 * Purpose: Provide message-specific operations with pagination and polling.
 * This is a focused hook that handles only messages, separate from room
 * metadata and participants.
 *
 * Features:
 * - TanStack Query for caching and state management
 * - Cursor-based pagination for loading older messages
 * - Polling for new messages (Phase 3, replaced by WebSocket in Phase 4)
 * - Optimistic updates for message sending
 * - Automatic cache invalidation
 *
 * @see Phase3-TechnicalSpec.md §3.2
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import { RoomService } from '@/services/roomService';
import type { MessageViewModel } from '@/services/roomService';
import type { ApiError } from '@/client';
import useAuth from './useAuth';
import { handleError } from '@/utils';

export interface UseRoomMessagesOptions {
  enablePolling?: boolean;
  pollingInterval?: number;
  pageSize?: number;
}

export interface UseRoomMessagesResult {
  messages: MessageViewModel[];
  isLoading: boolean;
  error: Error | null;

  // Pagination
  hasMore: boolean;
  loadMore: () => Promise<void>;
  isLoadingMore: boolean;

  // Actions
  sendMessage: (content: string) => Promise<void>;
  isSending: boolean;

  // Polling Status
  isPolling: boolean;
  lastUpdated: Date | null;
}

/**
 * Hook for managing room messages with pagination and real-time updates
 *
 * @param roomId - Room UUID
 * @param options - Configuration options
 * @returns Message state and operations
 *
 * @example
 * ```tsx
 * const {
 *   messages,
 *   sendMessage,
 *   loadMore,
 *   hasMore,
 *   isLoading
 * } = useRoomMessages(roomId, { enablePolling: true });
 *
 * // Send a message
 * await sendMessage("Hello, world!");
 *
 * // Load older messages
 * if (hasMore) {
 *   await loadMore();
 * }
 * ```
 */
export function useRoomMessages(
  roomId: string,
  options?: UseRoomMessagesOptions
): UseRoomMessagesResult {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Options with defaults
  const enablePolling = options?.enablePolling ?? true;
  const pollingInterval = options?.pollingInterval ?? 3000; // 3 seconds
  const pageSize = options?.pageSize ?? 50;

  // State for pagination
  const [hasMore, setHasMore] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Query key for messages
  const messagesQueryKey = ['rooms', roomId, 'messages'];

  // Fetch messages query with polling
  const {
    data: messagesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: messagesQueryKey,
    queryFn: async () => {
      const result = await RoomService.getMessages(
        roomId,
        { limit: pageSize },
        user?.id
      );
      setHasMore(result.has_more);
      setLastUpdated(new Date());
      return result;
    },
    refetchInterval: enablePolling ? pollingInterval : false,
    // Disable polling when tab is not visible
    refetchIntervalInBackground: false,
    // Keep previous data while refetching
    placeholderData: (previousData) => previousData,
  });

  // Messages array from query data
  const messages = messagesData?.messages ?? [];

  // Send message mutation with optimistic update
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      return await RoomService.sendMessage(roomId, content, user?.id);
    },
    onMutate: async (content: string) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: messagesQueryKey });

      // Snapshot previous value
      const previousMessages = queryClient.getQueryData(messagesQueryKey);

      // Optimistically add message
      queryClient.setQueryData(messagesQueryKey, (old: any) => {
        if (!old) return old;

        const optimisticMessage: MessageViewModel = {
          message_id: `temp-${Date.now()}`,
          room_id: roomId,
          sender_type: 'user',
          sender_name: user?.full_name || user?.email || 'You',
          sender_id: user?.id || null,
          agent_name: null,
          content,
          button_options: null,
          created_at: new Date(),
          is_own_message: true,
        };

        return {
          ...old,
          messages: [...old.messages, optimisticMessage],
        };
      });

      return { previousMessages };
    },
    onError: (err: ApiError, _content, context) => {
      // Rollback optimistic update on error
      if (context?.previousMessages) {
        queryClient.setQueryData(messagesQueryKey, context.previousMessages);
      }
      handleError(err);
    },
    onSuccess: () => {
      // Refetch to get the real message + any agent responses
      queryClient.invalidateQueries({ queryKey: messagesQueryKey });
    },
  });

  // Load more messages (pagination)
  const loadMore = useCallback(async () => {
    if (!hasMore || isLoadingMore) return;

    setIsLoadingMore(true);
    try {
      // Use the oldest message's timestamp as cursor
      const oldestMessage = messages[0];
      const beforeCursor = oldestMessage?.created_at.toISOString();

      const result = await RoomService.getMessages(
        roomId,
        { limit: pageSize, before: beforeCursor },
        user?.id
      );

      // Update query data with prepended older messages
      queryClient.setQueryData(messagesQueryKey, (old: any) => {
        if (!old) return result;

        return {
          ...old,
          messages: [...result.messages, ...old.messages],
          has_more: result.has_more,
        };
      });

      setHasMore(result.has_more);
    } catch (err) {
      handleError(err as ApiError);
    } finally {
      setIsLoadingMore(false);
    }
  }, [hasMore, isLoadingMore, messages, roomId, pageSize, user?.id, queryClient, messagesQueryKey]);

  // Send message wrapper
  const sendMessage = useCallback(
    async (content: string) => {
      await sendMessageMutation.mutateAsync(content);
    },
    [sendMessageMutation]
  );

  // Determine if polling is active
  const isPolling = enablePolling && !isLoading;

  return {
    messages,
    isLoading,
    error: error as Error | null,

    // Pagination
    hasMore,
    loadMore,
    isLoadingMore,

    // Actions
    sendMessage,
    isSending: sendMessageMutation.isPending,

    // Polling Status
    isPolling,
    lastUpdated,
  };
}
