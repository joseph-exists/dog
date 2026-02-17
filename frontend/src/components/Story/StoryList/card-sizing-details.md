
  Card Sizing Configuration

  File: src/components/Story/StoryList/StoryCard.tsx

  Line ~430 - The Card height:
  "h-[200px] flex flex-col",  // ← Change 200px to your desired height

  Tuning options:
  ┌───────────┬───────────────────────────────────────────────┐
  │  Height   │                   Best For                    │
  ├───────────┼───────────────────────────────────────────────┤
  │ h-[180px] │ Compact, title + 2-line description           │
  ├───────────┼───────────────────────────────────────────────┤
  │ h-[200px] │ Current default, title + 3-4 line description │
  ├───────────┼───────────────────────────────────────────────┤
  │ h-[240px] │ More room for longer descriptions             │
  ├───────────┼───────────────────────────────────────────────┤
  │ h-[280px] │ Full descriptions + linked rooms + actions    │
  └───────────┴───────────────────────────────────────────────┘
  Related constraints:
  ┌──────────┬──────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┐
  │ Location │                  Class                   │                                  Purpose                                   │
  ├──────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┤
  │ Line     │ CardHeader → flex-1 min-h-0              │ Header fills remaining space, clips overflow                               │
  │ ~444     │ overflow-hidden                          │                                                                            │
  ├──────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┤
  │ Line     │ CardDescription → line-clamp-4           │ Limits description to 4 lines (change to line-clamp-2 or line-clamp-3 for  │
  │ ~468     │                                          │ shorter)                                                                   │
  ├──────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┤
  │ Line     │ CardContent → shrink-0                   │ Linked rooms section won't shrink                                          │
  │ ~493     │                                          │                                                                            │
  ├──────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┤
  │ Line     │ CardFooter → shrink-0                    │ Actions section won't shrink                                               │
  │ ~498     │                                          │                                                                            │
  └──────────┴──────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┘
  ★ Insight ─────────────────────────────────────
  The flex layout ensures consistent sizing:
  - Card has fixed h-[200px] + flex flex-col
  - CardHeader gets flex-1 to fill available space
  - CardContent/CardFooter get shrink-0 to stay at natural size
  - Description uses line-clamp-4 to prevent overflow

  If cards with LinkedRooms or Actions feel cramped, increase the height or reduce line-clamp-4 to line-clamp-2.
