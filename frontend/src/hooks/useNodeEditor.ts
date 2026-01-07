// import { useState } from 'react';
// import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
// import { client } from '../client';

// export function useNodeEditor(storyId: string, storyVersion: number) {
//   const queryClient = useQueryClient();
//   const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

//   // Fetch all nodes for story version
//   const { data: allNodes, isLoading } = useQuery({
//     queryKey: ['nodes', storyId],
//     queryFn: async () => {
//       const response = await client.GET('/api/v1/storynodes', {
//         params: { query: { skip: 0, limit: 1000 } }
//       });
//       if (response.error) throw response.error;

//       // Filter to current story version
//       return response.data?.data.filter(
//         node => node.story_id === storyId && node.story_version === storyVersion
//       ) || [];
//     }
//   });

//   // Create node mutation
//   const createNodeMutation = useMutation({
//     mutationFn: async (data: {
//       title: string;
//       content: string;
//       node_type?: string;
//       is_start_node?: boolean;
//       is_end_node?: boolean;
//     }) => {
//       const response = await client.POST('/api/v1/storynodes', {
//         body: {
//           story_id: storyId,
//           story_version: storyVersion,
//           ...data
//         }
//       });
//       if (response.error) throw response.error;
//       return response.data;
//     },
//     onSuccess: () => {
//       queryClient.invalidateQueries({ queryKey: ['nodes', storyId] });
//     }
//   });

//   // Update node mutation
//   const updateNodeMutation = useMutation({
//     mutationFn: async ({
//       nodeId,
//       data
//     }: {
//       nodeId: string;
//       data: Partial<{ title: string; content: string }>;
//     }) => {
//       const response = await client.PUT('/api/v1/storynodes/{node_id}', {
//         params: { path: { node_id: nodeId } },
//         body: data
//       });
//       if (response.error) throw response.error;
//       return response.data;
//     },
//     onSuccess: () => {
//       queryClient.invalidateQueries({ queryKey: ['nodes', storyId] });
//     }
//   });

//   const selectedNode = allNodes?.find(node => node.id === selectedNodeId);

//   return {
//     nodes: allNodes || [],
//     isLoading,
//     selectedNode,
//     selectedNodeId,
//     setSelectedNodeId,
//     createNode: createNodeMutation.mutate,
//     updateNode: updateNodeMutation.mutate,
//     isCreating: createNodeMutation.isPending,
//     isUpdating: updateNodeMutation.isPending
//   };
// }