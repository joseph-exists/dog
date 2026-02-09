
# FOR REFERENCE ONLY
# DOES NOT COMPILE
// /**
//  * Presentation-as-Data Demo Page
//  *
//  * Proves out the concept of objects carrying their own visual identity
//  * using the real project components (shadcn Card, Badge, Avatar).
//  *
//  * Route: /_layout/demo/presentation-poc (add to demos config)
//  */

// // import { useState } from "react"
// // import { Button } from "@/components/ui/button"
// // // import { cn } from "@/lib/utils"
// // // import presentationToStyle from resolve.ts
// // import AgentCard from "../Display/AgentCard"
// // import AgentAvatar from "../Display/AgentAvatar"
// // import { resolveAgentPresentation } from "../resolve"
// // import type { UserAgentConfigData as AgentWithPresentation } from "../types"

// // ── Sample Agent Data ─────────────────────────────────────────────────────

// const AGENTS: AgentWithPresentation[] = [
//   {
//     id: "a1",
//     name: "Armadillo Advisor",
//     slug: "armadillo-advisor",
//     description:
//       "Nine-banded guidance for armored decisions. Deliberate, thorough, protective.",
//     scope: "personal",
//     participationMode: "always",
//     isEnabled: true,
//     modelName: "anthropic:claude-sonnet-4-5-20250929",
//     agentType: "advisor",
//     owner_id: "Joseph",
//     presentation: {
//       tokens: {
//         "--agent-accent": "oklch(0.65 0.14 55)",
//         "--agent-accent-foreground": "oklch(1 0 0)",
//         "--card": "oklch(0.96 0.015 60)",
//         "--card-foreground": "oklch(0.2 0.02 50)",
//         "--border": "oklch(0.85 0.04 55)",
//         "--muted": "oklch(0.92 0.01 55)",
//         "--muted-foreground": "oklch(0.5 0.02 50)",
//         "--agent-card-shadow":
//           "0 4px 20px oklch(0.5 0.1 55 / 0.1), 0 1px 3px oklch(0.5 0.08 55 / 0.06)",
//         "--agent-card-radius": "14px",
//         "--agent-accent-position": "top",
//         "--agent-accent-width": "3px",
//       },
//       avatar: { emoji: "🦔", backgroundColor: "oklch(0.65 0.14 55)" },
//       decorationHint: "warm",
//     },
//   },
//   {
//     id: "a2",
//     name: "Neon Muse",
//     slug: "neon-muse",
//     description:
//       "Electric creativity. Generates unexpected connections between distant ideas.",
//     scope: "personal",
//     participationMode: "on_mention",
//     isEnabled: true,
//     modelName: "openai:gpt-4o",
//     agentType: "creative",
//     owner_id: "Mika",
//     presentation: {
//       tokens: {
//         "--agent-accent": "oklch(0.7 0.25 340)",
//         "--agent-accent-foreground": "oklch(1 0 0)",
//         "--card": "oklch(0.18 0.04 300)",
//         "--card-foreground": "oklch(0.92 0.02 320)",
//         "--border": "oklch(0.32 0.08 340)",
//         "--muted": "oklch(0.22 0.03 300)",
//         "--muted-foreground": "oklch(0.6 0.04 320)",
//         "--secondary": "oklch(0.25 0.05 310)",
//         "--secondary-foreground": "oklch(0.85 0.06 330)",
//         "--foreground": "oklch(0.92 0.02 320)",
//         "--agent-card-shadow":
//           "0 0 25px oklch(0.65 0.25 340 / 0.12), 0 0 5px oklch(0.7 0.2 340 / 0.08)",
//         "--agent-card-radius": "4px",
//         "--agent-accent-position": "left",
//         "--agent-accent-width": "4px",
//       },
//       avatar: { emoji: "⚡", backgroundColor: "oklch(0.65 0.25 340)" },
//       decorationHint: "neon",
//     },
//   },
//   {
//     id: "a3",
//     name: "Cartograph",
//     slug: "cartograph",
//     description:
//       "Maps the territory of your data. Finds structure in unstructured spaces.",
//     scope: "system",
//     participationMode: "manual",
//     isEnabled: true,
//     modelName: "anthropic:claude-sonnet-4-5-20250929",
//     agentType: "analyst",
//     owner_id: "System",
//     presentation: {
//       tokens: {
//         "--agent-accent": "oklch(0.5 0.08 240)",
//         "--agent-accent-foreground": "oklch(1 0 0)",
//         "--card": "oklch(0.97 0.01 80)",
//         "--card-foreground": "oklch(0.18 0.02 240)",
//         "--border": "oklch(0.84 0.02 240)",
//         "--muted": "oklch(0.94 0.008 80)",
//         "--muted-foreground": "oklch(0.5 0.02 240)",
//         "--agent-card-shadow": "0 1px 2px oklch(0.4 0.04 240 / 0.06)",
//         "--agent-card-radius": "2px",
//         "--agent-accent-position": "bottom",
//         "--agent-accent-width": "2px",
//       },
//       avatar: { emoji: "🗺️", backgroundColor: "oklch(0.5 0.08 240)" },
//       decorationHint: "precise",
//     },
//   },
//   {
//     id: "a4",
//     name: "Verdant",
//     slug: "verdant",
//     description:
//       "Grows ideas organically. Patient, nurturing, surprisingly deep roots.",
//     scope: "personal",
//     participationMode: "always",
//     isEnabled: true,
//     modelName: "google:gemini-pro",
//     agentType: "oracle",
//     owner_id: "Lena",
//     presentation: {
//       tokens: {
//         "--agent-accent": "oklch(0.6 0.15 150)",
//         "--agent-accent-foreground": "oklch(1 0 0)",
//         "--card": "oklch(0.97 0.015 145)",
//         "--card-foreground": "oklch(0.18 0.03 150)",
//         "--border": "oklch(0.85 0.03 145)",
//         "--muted": "oklch(0.93 0.01 145)",
//         "--muted-foreground": "oklch(0.5 0.02 150)",
//         "--agent-card-shadow":
//           "0 6px 24px oklch(0.5 0.1 150 / 0.07), 0 2px 6px oklch(0.5 0.08 150 / 0.04)",
//         "--agent-card-radius": "20px",
//         "--agent-accent-position": "top",
//         "--agent-accent-width": "3px",
//       },
//       avatar: { emoji: "🌿", backgroundColor: "oklch(0.55 0.15 150)" },
//       decorationHint: "organic",
//     },
//   },
//   {
//     id: "a5",
//     name: "AXIOM",
//     slug: "axiom",
//     description:
//       "Formal logic engine. Reduces ambiguity. Constructs proofs from premises.",
//     scope: "system",
//     participationMode: "manual",
//     isEnabled: true,
//     modelName: "anthropic:claude-sonnet-4-5-20250929",
//     agentType: "engineer",
//     owner_id: "System",
//     presentation: {
//       tokens: {
//         "--agent-accent": "oklch(0.85 0.17 90)",
//         "--agent-accent-foreground": "oklch(0.15 0 0)",
//         "--card": "oklch(0.97 0 0)",
//         "--card-foreground": "oklch(0.12 0 0)",
//         "--border": "oklch(0.7 0 0)",
//         "--muted": "oklch(0.93 0 0)",
//         "--muted-foreground": "oklch(0.45 0 0)",
//         "--agent-card-shadow": "6px 6px 0 oklch(0.55 0.25 29)",
//         "--agent-card-radius": "0px",
//         "--agent-accent-position": "left",
//         "--agent-accent-width": "6px",
//       },
//       avatar: { emoji: "◆", backgroundColor: "oklch(0.8 0.15 90)" },
//       decorationHint: "brutalist",
//     },
//   },
//   {
//     id: "a6",
//     name: "Whisper",
//     slug: "whisper",
//     description:
//       "Subtle influence. Reads between the lines and speaks in implications.",
//     scope: "personal",
//     participationMode: "on_mention",
//     isEnabled: true,
//     modelName: "openai:gpt-4o",
//     agentType: "oracle",
//     owner_id: "Ren",
//     presentation: {
//       tokens: {
//         "--agent-accent": "oklch(0.65 0.1 290)",
//         "--agent-accent-foreground": "oklch(1 0 0)",
//         "--card": "oklch(0.98 0.008 290)",
//         "--card-foreground": "oklch(0.25 0.02 290)",
//         "--border": "oklch(0.92 0.015 290)",
//         "--muted": "oklch(0.96 0.006 290)",
//         "--muted-foreground": "oklch(0.55 0.03 290)",
//         "--agent-card-shadow": "0 8px 32px oklch(0.5 0.08 290 / 0.05)",
//         "--agent-card-radius": "24px",
//         "--agent-accent-position": "none",
//         "--agent-accent-width": "0px",
//       },
//       avatar: { emoji: "◯", backgroundColor: "oklch(0.65 0.1 290)" },
//       decorationHint: "ethereal",
//     },
//   },
// ]

// // An agent with NO presentation — falls through to type defaults
// const PLAIN_AGENT: AgentWithPresentation = {
//   id: "a7",
//   name: "Story Weaver",
//   slug: "story-weaver",
//   description: "Crafts narrative threads from scattered ideas. No custom styling.",
//   scope: "personal",
//   participationMode: "on_mention",
//   isEnabled: true,
//   modelName: "openai:gpt-4o",
//   agentType: "creative",
//   owner_id: "Default User",
//   presentation: null,
// }

// // ── Ambient Theme Presets ─────────────────────────────────────────────────

// const AMBIENT_THEMES: Record<string, { name: string; style: React.CSSProperties }> = {
//   none: { name: "Default", style: {} },
//   ocean: {
//     name: "Cool Ocean",
//     style: {
//       "--card": "oklch(0.97 0.015 230)",
//       "--card-foreground": "oklch(0.15 0.03 230)",
//       "--foreground": "oklch(0.15 0.03 230)",
//       "--border": "oklch(0.88 0.02 230)",
//       "--muted": "oklch(0.94 0.01 230)",
//       "--muted-foreground": "oklch(0.5 0.02 230)",
//       "--secondary": "oklch(0.93 0.015 230)",
//       "--secondary-foreground": "oklch(0.2 0.03 230)",
//       "--accent": "oklch(0.93 0.015 230)",
//       "--accent-foreground": "oklch(0.2 0.03 230)",
//     } as React.CSSProperties,
//   },
//   midnight: {
//     name: "Midnight",
//     style: {
//       "--card": "oklch(0.2 0.015 270)",
//       "--card-foreground": "oklch(0.9 0.01 270)",
//       "--foreground": "oklch(0.9 0.01 270)",
//       "--border": "oklch(0.3 0.015 270)",
//       "--muted": "oklch(0.25 0.01 270)",
//       "--muted-foreground": "oklch(0.6 0.015 270)",
//       "--secondary": "oklch(0.25 0.015 270)",
//       "--secondary-foreground": "oklch(0.85 0.01 270)",
//       "--accent": "oklch(0.25 0.015 270)",
//       "--accent-foreground": "oklch(0.85 0.01 270)",
//     } as React.CSSProperties,
//   },
// }

// // ── Section Label ─────────────────────────────────────────────────────────

// function SectionLabel({ children }: { children: React.ReactNode }) {
//   return (
//     <h2 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">
//       {children}
//     </h2>
//   )
// }

// // ── Demo Page ─────────────────────────────────────────────────────────────

// export default function PresentationDemo() {
//   const [ambientTheme, setAmbientTheme] = useState("none")
//   const [presentationEnabled, setPresentationEnabled] = useState(true)
//   const [debug, setDebug] = useState(false)
//   const [selectedMini, setSelectedMini] = useState("a1")

//   const ambient = AMBIENT_THEMES[ambientTheme]

//   return (
//     <div className="min-h-screen bg-background">
//       {/* Controls Bar */}
//       <div className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur px-6 py-3">
//         <div className="max-w-[1200px] mx-auto">
//           <div className="flex items-center justify-between flex-wrap gap-3">
//             <div>
//               <h1 className="text-sm font-bold tracking-tight">
//                 Presentation-as-Data PoC
//               </h1>
//               <p className="text-xs text-muted-foreground">
//                 Real shadcn components · CSS variable scoping · Object-carried
//                 identity
//               </p>
//             </div>

//             <div className="flex gap-3 items-center flex-wrap">
//               {/* Theme picker */}
//               <div className="flex gap-1">
//                 {Object.entries(AMBIENT_THEMES).map(([id, t]) => (
//                   <Button
//                     key={id}
//                     variant={ambientTheme === id ? "default" : "outline"}
//                     size="sm"
//                     className="h-7 text-xs"
//                     onClick={() => setAmbientTheme(id)}
//                   >
//                     {t.name}
//                   </Button>
//                 ))}
//               </div>

//               {/* Toggles */}
//               <Button
//                 variant={presentationEnabled ? "default" : "outline"}
//                 size="sm"
//                 className="h-7 text-xs"
//                 onClick={() => setPresentationEnabled(!presentationEnabled)}
//               >
//                 {presentationEnabled ? "✓ Object Styles" : "✗ Ambient Only"}
//               </Button>
//               <Button
//                 variant={debug ? "secondary" : "outline"}
//                 size="sm"
//                 className="h-7 text-xs"
//                 onClick={() => setDebug(!debug)}
//               >
//                 {debug ? "✓ Debug" : "✗ Debug"}
//               </Button>
//             </div>
//           </div>
//         </div>
//       </div>

//       {/* Content — wrapped in ambient theme */}
//       <main className="max-w-[1200px] mx-auto px-6 py-6">
//         <div
//           style={ambient.style}
//           className="transition-all duration-300"
//         >
//           {/* Explainer */}
//           <div className="rounded-lg border bg-card text-card-foreground p-4 mb-6 text-sm leading-relaxed transition-all duration-300">
//             <strong>What you're seeing:</strong> Every card below is rendered
//             with the real <code className="text-xs bg-muted px-1 py-0.5 rounded">Card</code>,{" "}
//             <code className="text-xs bg-muted px-1 py-0.5 rounded">Badge</code>,{" "}
//             and <code className="text-xs bg-muted px-1 py-0.5 rounded">Avatar</code>{" "}
//             from shadcn. The visual diversity comes from CSS variable overrides
//             applied on a wrapper div — the components themselves are untouched.
//             Toggle "Object Styles" off to see everything flatten to the ambient
//             theme.
//           </div>

//           {/* ── Full Cards Grid ── */}
//           <SectionLabel>Full Variant — Six agents, six personalities</SectionLabel>
//           <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
//             {AGENTS.map((a) => (
//               <AgentCard
//                 key={a.id}
//                 agent={a}
//                 variant="full"
//                 presentationEnabled={presentationEnabled}
//                 debug={debug}
//               />
//             ))}
//           </div>

//           {/* ── Two-column: Compact + Mini/Stack ── */}
//           <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
//             {/* Compact list */}
//             <div>
//               <SectionLabel>Compact Variant — Sidebar density</SectionLabel>
//               <div className="space-y-2">
//                 {AGENTS.filter((a) => a.isEnabled).map((a) => (
//                   <AgentCard
//                     key={a.id}
//                     agent={a}
//                     variant="compact"
//                     presentationEnabled={presentationEnabled}
//                   />
//                 ))}
//               </div>
//             </div>

//             <div className="space-y-6">
//               {/* Mini chips */}
//               <div>
//                 <SectionLabel>Mini Variant — Selection chips</SectionLabel>
//                 <div className="flex flex-wrap gap-1.5 p-3 rounded-lg border bg-card transition-all duration-300">
//                   {AGENTS.map((a) => (
//                     <AgentCard
//                       key={a.id}
//                       agent={a}
//                       variant="mini"
//                       presentationEnabled={presentationEnabled}
//                       isSelected={selectedMini === a.id}
//                       onClick={() => setSelectedMini(a.id)}
//                     />
//                   ))}
//                 </div>
//               </div>

//               {/* Avatar stack */}
//               <div>
//                 <SectionLabel>Avatar Stack — Room header</SectionLabel>
//                 <div className="flex items-center gap-3 p-3 rounded-lg border bg-card transition-all duration-300">
//                   <div className="flex -space-x-2">
//                     {AGENTS.slice(0, 5).map((a) => {
//                       const pres = resolveAgentPresentation(
//                         a.agentType,
//                         presentationEnabled ? a.presentation : null,
//                       )
//                       return (
//                         <div
//                           key={a.id}
//                           className="ring-2 ring-card rounded-full"
//                         >
//                           <AgentAvatar
//                             name={a.name}
//                             size="sm"
//                             presentation={
//                               presentationEnabled ? pres.avatar : undefined
//                             }
//                           />
//                         </div>
//                       )
//                     })}
//                     <div className="flex items-center justify-center size-6 rounded-full bg-muted text-xs font-medium ring-2 ring-card">
//                       +{AGENTS.length - 5}
//                     </div>
//                   </div>
//                   <span className="text-xs text-muted-foreground">
//                     {AGENTS.length} agents in this room
//                   </span>
//                 </div>
//               </div>

//               {/* Same agent, all variants */}
//               <div>
//                 <SectionLabel>Same agent across all variants</SectionLabel>
//                 <div className="p-4 rounded-lg border bg-card space-y-4 transition-all duration-300">
//                   {(() => {
//                     const a =
//                       AGENTS.find((x) => x.id === selectedMini) || AGENTS[0]
//                     return (
//                       <>
//                         <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
//                           FULL
//                         </div>
//                         <AgentCard
//                           agent={a}
//                           variant="full"
//                           presentationEnabled={presentationEnabled}
//                         />
//                         <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mt-3">
//                           COMPACT
//                         </div>
//                         <AgentCard
//                           agent={a}
//                           variant="compact"
//                           presentationEnabled={presentationEnabled}
//                         />
//                         <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mt-3">
//                           MINI
//                         </div>
//                         <AgentCard
//                           agent={a}
//                           variant="mini"
//                           presentationEnabled={presentationEnabled}
//                           isSelected
//                         />
//                       </>
//                     )
//                   })()}
//                 </div>
//               </div>
//             </div>
//           </div>

//           {/* ── Max contrast comparison ── */}
//           <SectionLabel>
//             Maximum contrast — same component, different data
//           </SectionLabel>
//           <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
//             <div>
//               <AgentCard
//                 agent={AGENTS[1]} // Neon Muse
//                 variant="full"
//                 presentationEnabled={presentationEnabled}
//                 debug={debug}
//               />
//               <p className="text-[10px] text-center text-muted-foreground mt-2 font-mono">
//                 Dark · 4px radius · left accent · glow shadow · neon hint
//               </p>
//             </div>
//             <div>
//               <AgentCard
//                 agent={AGENTS[5]} // Whisper
//                 variant="full"
//                 presentationEnabled={presentationEnabled}
//                 debug={debug}
//               />
//               <p className="text-[10px] text-center text-muted-foreground mt-2 font-mono">
//                 Light · 24px radius · no accent · soft shadow · ethereal hint
//               </p>
//             </div>
//           </div>

//           {/* ── Fallback behavior ── */}
//           <SectionLabel>
//             Fallback — agent with no instance presentation
//           </SectionLabel>
//           <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
//             <AgentCard
//               agent={PLAIN_AGENT}
//               variant="full"
//               presentationEnabled={presentationEnabled}
//               debug={debug}
//             />
//             <AgentCard
//               agent={PLAIN_AGENT}
//               variant="compact"
//               presentationEnabled={presentationEnabled}
//             />
//             <div className="flex items-start p-4 rounded-lg border bg-card transition-all duration-300">
//               <AgentCard
//                 agent={PLAIN_AGENT}
//                 variant="mini"
//                 presentationEnabled={presentationEnabled}
//               />
//             </div>
//           </div>

//           {/* ── Token vocabulary ── */}
//           <SectionLabel>Presentation vocabulary</SectionLabel>
//           <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
//             {[
//               {
//                 label: "Card Surface",
//                 tokens: [
//                   "--card",
//                   "--card-foreground",
//                   "--border",
//                   "--muted",
//                   "--muted-foreground",
//                   "--agent-card-shadow",
//                   "--agent-card-radius",
//                 ],
//                 note: "Overrides shadcn's bg-card, text-card-foreground, border color",
//               },
//               {
//                 label: "Accent",
//                 tokens: [
//                   "--agent-accent",
//                   "--agent-accent-foreground",
//                   "--agent-accent-position",
//                   "--agent-accent-width",
//                 ],
//                 note: "Directional emphasis strip + avatar color",
//               },
//               {
//                 label: "Identity",
//                 tokens: [
//                   "avatar.emoji",
//                   "avatar.backgroundColor",
//                   "decorationHint",
//                 ],
//                 note: "Content + typographic personality hint",
//               },
//             ].map((group) => (
//               <div
//                 key={group.label}
//                 className="p-3 rounded-lg border bg-card text-sm transition-all duration-300"
//               >
//                 <div className="font-semibold text-xs mb-2">{group.label}</div>
//                 {group.tokens.map((t) => (
//                   <div
//                     key={t}
//                     className="font-mono text-[10px] text-muted-foreground"
//                   >
//                     {t}
//                   </div>
//                 ))}
//                 <div className="text-[10px] italic text-muted-foreground mt-2 opacity-70">
//                   {group.note}
//                 </div>
//               </div>
//             ))}
//           </div>
//         </div>
//       </main>
//     </div>
//   )
// }
