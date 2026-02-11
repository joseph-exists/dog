// /**
//  * ParticipantList Component
//  *
//  * Displays active participants:
//  * - Users section with count
//  * - Agents section with count
//  * - Visual distinction (agent icon)
//  * - Loading state handling
//  * - Display mode toggle (names, IDs, avatars, all)
//  */

// import { Loader2 } from "lucide-react"
// import { useState } from "react"

// import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
// import {
//   Select,
//   SelectContent,
//   SelectItem,
//   SelectTrigger,
//   SelectValue,
// } from "@/components/ui/select"
// import {
//   Tooltip,
//   TooltipContent,
//   TooltipProvider,
//   TooltipTrigger,
// } from "@/components/ui/tooltip"
// import { cn } from "@/lib/utils"
// import type { ParticipantViewModel } from "@/services/roomService"
// import AgentToggle from "./AgentToggle"
// import RemoveParticipantButton from "./RemoveParticipantButton"

// /** Display modes for participants */
// type DisplayMode = "names" | "ids" | "avatars" | "all"

// interface ParticipantListProps {
//   activeUsers: ParticipantViewModel[]
//   activeAgents: ParticipantViewModel[]
//   isLoading?: boolean
//   currentUserRole: "owner" | "member" | null
//   onRemoveParticipant?: (participantId: string) => Promise<void>
//   onToggleAgent?: (agentId: string, activate: boolean) => Promise<void>
// }

// /**
//  * Get initials from a display name
//  */
// function getInitials(name: string): string {
//   return name
//     .split(" ")
//     .map((n) => n[0])
//     .join("")
//     .toUpperCase()
//     .slice(0, 2)
// }

// /**
//  * Format UUID for compact display (first 8 characters)
//  */
// function formatUuidShort(uuid: string): string {
//   return uuid.slice(0, 8)
// }

// /**
//  * ParticipantDisplay - Renders a participant based on display mode
//  */
// function ParticipantDisplay({
//   participant,
//   displayMode,
//   isAgent = false,
// }: {
//   participant: ParticipantViewModel
//   displayMode: DisplayMode
//   isAgent?: boolean
// }) {
//   const avatar = (
//     <Avatar className="h-6 w-6">
//       <AvatarImage
//         src={participant.avatar_url}
//         alt={participant.display_name}
//       />
//       <AvatarFallback className="text-xs">
//         {isAgent ? "🤖" : getInitials(participant.display_name)}
//       </AvatarFallback>
//     </Avatar>
//   )

//   switch (displayMode) {
//     case "avatars":
//       return (
//         <TooltipProvider delayDuration={200}>
//           <Tooltip>
//             <TooltipTrigger asChild>{avatar}</TooltipTrigger>
//             <TooltipContent side="top">
//               <p>{participant.display_name}</p>
//             </TooltipContent>
//           </Tooltip>
//         </TooltipProvider>
//       )

//     case "ids":
//       return (
//         <TooltipProvider delayDuration={200}>
//           <Tooltip>
//             <TooltipTrigger asChild>
//               <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono break-all">
//                 {participant.participant_id}
//               </code>
//             </TooltipTrigger>
//             <TooltipContent side="top">
//               <p>{participant.display_name}</p>
//             </TooltipContent>
//           </Tooltip>
//         </TooltipProvider>
//       )

//     case "all":
//       return (
//         <div className="flex items-center gap-2">
//           {avatar}
//           <div className="flex flex-col">
//             <span className="text-sm">
//               {isAgent && "🤖 "}
//               {participant.display_name}
//             </span>
//             <code className="text-[10px] text-muted-foreground font-mono">
//               {formatUuidShort(participant.participant_id)}
//             </code>
//           </div>
//         </div>
//       )
//     default:
//       return (
//         <span className="text-sm">
//           {isAgent && "🤖 "}
//           {participant.display_name}
//         </span>
//       )
//   }
// }

// export default function ParticipantList({
//   activeUsers,
//   activeAgents,
//   isLoading = false,
//   currentUserRole,
//   onRemoveParticipant,
//   onToggleAgent,
// }: ParticipantListProps) {
//   const [displayMode, setDisplayMode] = useState<DisplayMode>("names")

//   if (isLoading) {
//     return (
//       <div className="p-4 border-t border-border">
//         <Loader2 className="h-4 w-4 animate-spin" />
//       </div>
//     )
//   }

//   const isAvatarMode = displayMode === "avatars"

//   return (
//     <div className="p-4 border-t border-border bg-background">
//       {/* Header with display mode toggle */}
//       <div className="flex items-center justify-between mb-3">
//         <span className="text-sm font-bold">Participants</span>
//         <Select
//           value={displayMode}
//           onValueChange={(v) => setDisplayMode(v as DisplayMode)}
//         >
//           <SelectTrigger className="h-7 w-24 text-xs">
//             <SelectValue />
//           </SelectTrigger>
//           <SelectContent>
//             <SelectItem value="names">Names</SelectItem>
//             <SelectItem value="ids">IDs</SelectItem>
//             <SelectItem value="avatars">Avatars</SelectItem>
//             <SelectItem value="all">All</SelectItem>
//           </SelectContent>
//         </Select>
//       </div>

//       <div
//         className={cn(
//           "flex flex-col gap-2 text-sm",
//           isAvatarMode && "flex-row flex-wrap items-center",
//         )}
//       >
//         {/* Users section */}
//         {activeUsers.length > 0 && (
//           <>
//             {!isAvatarMode && (
//               <span className="text-xs text-muted-foreground">
//                 Users ({activeUsers.length})
//               </span>
//             )}
//             {activeUsers.map((p) => (
//               <div
//                 key={p.participant_id}
//                 className={cn(
//                   "flex items-center gap-2",
//                   !isAvatarMode && "justify-between w-full",
//                 )}
//               >
//                 <ParticipantDisplay
//                   participant={p}
//                   displayMode={displayMode}
//                   isAgent={false}
//                 />
//                 {!isAvatarMode &&
//                   currentUserRole === "owner" &&
//                   onRemoveParticipant && (
//                     <RemoveParticipantButton
//                       participantId={p.participant_id}
//                       participantName={p.display_name}
//                       participantType="user"
//                       onRemove={onRemoveParticipant}
//                     />
//                   )}
//               </div>
//             ))}
//           </>
//         )}

//         {/* Agents section */}
//         {activeAgents.length > 0 && (
//           <>
//             {!isAvatarMode && (
//               <span className="text-xs text-muted-foreground mt-2">
//                 Agents ({activeAgents.length})
//               </span>
//             )}
//             {activeAgents.map((p) =>
//               !isAvatarMode && currentUserRole === "owner" && onToggleAgent ? (
//                 <AgentToggle
//                   key={p.participant_id}
//                   agentId={p.participant_id}
//                   agentName={p.display_name}
//                   isActive={p.is_active}
//                   onToggle={onToggleAgent}
//                   displayMode={displayMode}
//                 />
//               ) : (
//                 <ParticipantDisplay
//                   key={p.participant_id}
//                   participant={p}
//                   displayMode={displayMode}
//                   isAgent={true}
//                 />
//               ),
//             )}
//           </>
//         )}

//         {/* Empty state */}
//         {activeUsers.length === 0 && activeAgents.length === 0 && (
//           <span className="text-xs text-muted-foreground">
//             No active participants
//           </span>
//         )}
//       </div>
//     </div>
//   )
// }
