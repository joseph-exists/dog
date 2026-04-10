<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Yes, turn it into a terminal hardening RFC

Title: Browser Terminal Hardening for Hermes TUI
Status: Draft
Audience: Infra \& LLM engineers
Last updated: 2026-04-10

***

## 1. Context and problem

We have a **custom browser terminal** built on xterm.js and websockets that connects to a PTY inside each workspace. Hermes Agent’s CLI is a **full terminal UI (TUI)** built on `prompt_toolkit`, not a simple line-based CLI or web UI. It features multiline editing, slash-command autocomplete, conversation history, interrupts, and streaming tool output.[^1][^2][^3]

Today, when we run Hermes TUI inside our browser terminal, users see:

- Broken or confusing multiline input behavior.
- Occasional redraw glitches or garbled characters, especially after resize or reconnect.
- Unreliable keyboard shortcuts (Alt/Meta, Ctrl+J, etc.).
- Janky paste behavior for multiline prompts and code.

These issues degrade the experience enough that engineers are questioning whether we should switch to ttyd or other terminal stacks instead of fixing our PTY bridge.

This RFC treats the **browser terminal as a product primitive** and defines the changes needed to make it a reliable host for Hermes TUI and other TUIs.

***

## 2. Goals and non-goals

### 2.1 Goals

- Make Hermes TUI **work well** in the browser terminal:

    - Stable, flicker-free drawing during normal use and after resize.
    - Predictable behavior across reconnects.
    - Good performance under streaming output.
- Strengthen the **terminal abstraction** so it supports other terminal-native tools.
- Provide a **testable compatibility contract** between the browser terminal and terminal-based applications like Hermes.

Deferred:     - Correct keyboard semantics for Hermes keybindings.

### 2.2 Non-goals

- Rebuild the browser terminal from scratch or change from xterm.js to a different frontend.
- Modify Hermes internals or prompt_toolkit.
- Implement new user-facing features beyond what is needed to make TUI usage reliable.

***

## 3. Requirements from Hermes and prompt_toolkit

Hermes CLI’s docs describe it as a full TUI built for terminal users with multiline editing, slash-command autocomplete, history, interrupts, and streaming tool output, explicitly noting that it is **not a web UI**.[^2][^3]

Key requirements from Hermes’ side:

- **Real TTY**: Hermes expects to be attached to a genuine PTY, not just stdin/stdout pipes.[^2]
- **Keybindings**:
    - `Enter` — send message.
    - `Alt+Enter` or `Ctrl+J` — insert newline for multiline input.
    - `Ctrl+C` — interrupt, double-press to force exit.
    - `Ctrl+V` / `Alt+V` — paste text/images.
    - `Tab` — autocomplete slash commands.
    - Arrow keys — navigate history.[^4][^2]
- **Multiline input and paste**:
    - Multi-line messages via `Alt+Enter`, `Ctrl+J`, or backslash continuation.
    - Pasting multiline text should “just work” with bracketed paste.[^5][^6][^1][^2]

`prompt_toolkit` adds more expectations: bracketed paste support, mouse support, Unicode double-width character handling, full-screen applications, and robust input editing.[^7][^1]

From this we derive: our terminal stack must behave like a reasonably complete **xterm-256color** terminal with proper PTY semantics, key translation, paste handling, and resizing, especially under reconnects and scrolling.[^8][^1]

***

## 4. Problem analysis

The issues we see are consistent with known failure modes in xterm.js + PTY stacks:

- **Weird characters after reconnect** when using xterm.js attach addons and reconnecting websockets, often due to parser state or sequences emitted on reconnect.[^9][^10]
- **Scrollback performance and memory issues** when scrollback is set extremely high and the buffer implementation is naive.[^11][^12]
- **Broken bracketed paste** or missing support in custom glue code, causing extra characters or wrong line breaks.[^13][^5]
- **Prompt_toolkit misbehaving on “dumb” or incomplete terminals**, e.g., when TERM is wrong, arrow keys aren’t supported, or alt-screen usage is broken.[^1][^8]

In short:

> Our browser terminal is “good enough for a bash shell” but **not sufficiently spec’d or tested for TUIs like Hermes**.

***

## 5. Design: terminal hardening areas

We will harden the browser terminal across seven areas:

1. PTY allocation and terminal capabilities.
2. Keyboard and input semantics.
3. Resize and viewport synchronization.
4. Reconnect and session continuity.
5. Backpressure and streaming performance.
6. Hermes-aware UX affordances.
7. Observability and testing.

### 5.1 PTY allocation and terminal capabilities

**Objective**: Give Hermes and prompt_toolkit a genuine, well-described terminal environment.

Requirements:

- **Real PTY**:
    - Use OS-level PTYs for Hermes; do not run Hermes on a pipe or fake PTY. Hermes is a TUI that needs full terminal features.[^1][^2]
- **TERM and locale**:
    - Set `TERM=xterm-256color`.[^1]
    - Ensure a UTF-8 locale (e.g., `LANG=en_US.UTF-8`), so Unicode handling is correct.[^1]
- **Alt-screen and cursor control**:
    - Ensure we do not intercept or strip escape sequences that handle alternate screen buffers, cursor movement, or screen clear. prompt_toolkit uses these for full-screen apps.[^7][^1]
- **Bracketed paste**:
    - Support the VT sequence to enable bracketed paste (OSC 2004) and treat pasted text accordingly; prompt_toolkit uses bracketed paste to distinguish paste from typing.[^14][^5][^1]
    - Ensure our xterm.js integration doesn’t disable or mis-handle bracketed paste sequences.[^13][^1]

Implementation:

- Centralize the environment that we pass to Hermes (TERM, locale).
- Verify with a minimal prompt_toolkit script that tests bracketed paste, alt-screen usage, and key handling.[^15][^7][^1]


### 5.2 Keyboard and input semantics

**Objective**: Make terminal key behavior match Hermes’ documented keybindings.[^4][^2]

Requirements:

- Ensure correct mapping of:
    - `Enter`
    - `Alt+Enter` and/or `Ctrl+J` for newline
    - `Ctrl+C`, `Ctrl+D`
    - arrow keys, Home/End, PageUp/PageDown
    - `Tab`
- Browser caveats:
    - Many browsers intercept certain key combos (e.g., Alt-based shortcuts, Cmd on macOS).
    - We must decide which keybindings we **normalize** at the frontend level.

Hermes specifics:[^4][^2]

- Use `Alt+Enter` or `Ctrl+J` to insert newline.
- Pasting multiline text should work naturally.
- `Ctrl+C` interrupts agent, with double press to force exit.
- Arrow keys navigate history; Tab autocompletes slash commands.

Design decisions:

- **Normalized newline behavior**:
    - Map `Shift+Enter` to `Ctrl+J` before sending to the PTY. This adds a browser-native newline binding that Hermes already supports and avoids relying on Meta/Alt, which is more fragile across OSes.[^2]
- **Cross-platform Alt behavior**:
    - On macOS, map Option+Enter to `Alt+Enter`.
    - On Windows/Linux, preserve Alt+Enter for Hermes.
- **Browser event handling**:
    - At the xterm.js integration layer, intercept key events and transform them into the ANSI sequences Hermes expects before sending over websocket.

Implementation:

- Implement an explicit **“Hermes input mode”** in our terminal component that:
    - Enables the above key translations only when Hermes is active.
    - Logs key events and resulting sequences (for debugging and tests).


### 5.3 Resize and viewport synchronization

**Objective**: Avoid TUI corruption when the browser resizes or zooms.

Requirements:

- **Initial size ordering**:
    - Create PTY.
    - Compute terminal cols/rows from xterm.js once fonts are loaded.
    - Set PTY size.
    - Start Hermes.
This ensures prompt_toolkit sees the correct terminal size from startup.[^8][^7]
- **Resize synchronization**:
    - Debounce resize events from the browser.
    - Send resize to server promptly, before sending any new input.
    - Apply PTY size before writing pending output to the client.

Lessons from xterm.js reconnect examples show that incorrectly ordered resize requests and data writes can lead to garbled output or weird characters.[^10][^9]

Implementation:

- Add a resize controller:
    - Uses a short debounce (e.g., 50–100 ms) on browser resize.
    - For each resize:
        - compute new cols/rows from xterm.js,
        - send a dedicated “resize” message over websocket,
        - have the PTY server apply PTY resize immediately.


### 5.4 Reconnect and session continuity

**Objective**: Hermes TUI should survive temporary network issues and page reloads within a defined TTL without ending up in a corrupted state.

Requirements:

- **Server-side session**:
    - Maintain PTY sessions keyed by workspace + terminal ID.
    - On websocket reconnect, attempt to reattach **if** the PTY session is still alive.
- **Reconnect protocol**:
    - On reconnect:
        - Client sends workspace ID + terminal ID.
        - Server verifies PTY session exists and attaches.
        - Client re-sends current cols/rows.
        - Optionally, client resets its parser/view (clear screen or soft reset) to avoid weird characters discovered in xterm.js reconnect scenarios.[^9]
- **TTL semantics**:
    - Define a PTY session TTL after websocket disconnect.
    - If TTL expired, reconnect should yield a clean “session ended” state.

Known xterm.js issues show that if the client tries to preserve terminal object state across reconnections without careful handling, it can send unexpected sequences that cause weird characters when reconnecting to TUIs.[^10][^9]

Implementation:

- Introduce a **TerminalSessionManager** on the server:
    - Create PTY + Hermes process.
    - Track PTY lifetime independent of websocket.
    - Clean up PTY after TTL or explicit close.
- On client, on reconnect:
    - Re-create xterm.js instance (fresh parser state) instead of reusing it.
    - Reattach to PTY with same ID.
    - Optionally request server to send a short transcript snapshot or just rely on Hermes’ own display redraw.


### 5.5 Backpressure and streaming performance

**Objective**: Maintain a smooth experience under streaming output and long logs.

Hermes TUI emits streaming model and tool output; xterm.js scrollback and buffer behavior can become a bottleneck if not configured carefully.[^12][^16][^11][^2]

Requirements:

- **Bounded scrollback**:
    - Set xterm.js scrollback to a reasonable number (e.g., 5–10k lines) rather than “infinite” or millions; extremely large values are known to hurt performance.[^11][^12]
- **Write coalescing**:
    - Batch PTY data writes on the client, e.g., accumulate output for 10–16 ms and flush to xterm.js in a single write per frame.
- **Backpressure**:
    - Implement a simple heuristic: if client buffers exceed some size, start dropping from the **oldest** buffered content, not from the newest, per-session.

Implementation:

- Add a `TerminalOutputBuffer` that queues data and writes to xterm.js on animation frames or short intervals.
- Track buffer size; when above threshold, log a warning and prune oldest data (or simply stop growing until drained).


### 5.6 Hermes-aware UX affordances

**Objective**: Reduce the cognitive load on users by acknowledging that they are interacting with a **Hermes-specific TUI**, not a generic shell.

Requirements:

- Show **inline hints** in the UI near the terminal when Hermes is active:
    - “Enter sends. Shift+Enter: newline. Ctrl+C: interrupt.”[^4][^2]
- Provide explicit UI controls:
    - A “Send” button that simply sends `Enter`.
    - A “New line” button that sends `Ctrl+J`.[^2]
    - An “Interrupt” button that sends `Ctrl+C`.
    - A “Restart Hermes” action (kill and restart PTY+Hermes).
- Optionally, detect Hermes process and show a small “Hermes TUI mode” chip or banner with keybindings.

Implementation:

- Add a small Hermes-specific toolbar component that appears when the active PTY command is Hermes.
- Keep these shortcuts purely as UX sugar over the same PTY protocol; avoid special-case logic inside Hermes itself.


### 5.7 Observability and testing

**Objective**: Make terminal/TUI failures diagnosable and prevent regressions.

Requirements:

- **Telemetry**:
    - PTY lifecycle: created / resized / closed.
    - Websocket lifecycle: connect / disconnect / reconnect.
    - Bytes in/out per session.
    - Key events mapping stats (e.g., counts of Shift+Enter mapped to Ctrl+J).
    - Buffer size and dropped output metrics.
    - TERM, cols/rows over time.
- **Hermes compatibility test suite**:
    - Automated checks (see next section) that run a small prompt_toolkit/Hermes script inside the terminal and verify:
        - correct redraw after resize,
        - correct newline behavior,
        - working bracketed paste,
        - reconnect survival.

Implementation:

- Add structured logging at PTY and browser terminal boundary.
- Build a **Hermes TUI compatibility test harness** used in CI to validate new terminal changes.

***

## 6. Implementation plan

### Phase 1 — PTY \& TERM hardening

- Set `TERM=xterm-256color` and UTF-8 locale for Hermes sessions.[^8][^1]
- Confirm we use a real PTY for Hermes processes, not pipes.
- Validate alt-screen behavior using a small prompt_toolkit full-screen demo.[^7][^1]


### Phase 2 — Keyboard and UX layer

- Implement Hermes-specific input mode in frontend:
    - Map Shift+Enter → Ctrl+J when Hermes is active.[^2]
    - Normalize Alt/Meta across OSes.
- Add Hermes toolbar (Send, New line, Interrupt).
- Add inline keybinding hints near the terminal.[^4][^2]


### Phase 3 — Resize \& reconnect

- Introduce a resize controller with ordering as in §5.3.
- Implement TerminalSessionManager on the server.
- Change client reconnect logic to:
    - re-create xterm.js,
    - reattach to PTY,
    - reapply cols/rows.


### Phase 4 — Performance and buffering

- Configure scrollback to a sane default (e.g., 5–10k).[^12][^11]
- Add write batching in client output path.
- Add buffer size telemetry and backpressure heuristics.


### Phase 5 — Observability \& CI tests

- Instrument telemetry (PTY + websocket).
- Build a small automated harness:
    - Boot Hermes in a test workspace.
    - Run scripted key sequences through the PTY.
    - Assert expected screen content after operations like:
        - newline insertion,
        - paste,
        - resize,
        - reconnect.

***

## 7. Alternatives

- **ttyd**: A standalone terminal-sharing tool that could replace parts of our PTY/websocket stack. It is simpler to integrate but reduces our control over identity, reconnect, telemetry, and product-native UX. It has also had security advisories in the past, so we’d still need to wrap it carefully.[^17][^18][^19]
- **WeTTY or other terminal gateways**: Similar tradeoffs to ttyd; stronger “app” layer, weaker fit as a bare primitive.[^20][^21]

Given we already have a custom PTY bridge, this RFC assumes we **harden our existing stack** rather than replace it.

***

## 8. Decision

We will:

1. Treat browser terminal support as a **first-class compatibility problem for Hermes and prompt_toolkit**, not an afterthought.[^1][^2]
2. Harden the current xterm.js + PTY implementation along the seven dimensions defined above.
3. Introduce a Hermes-aware input/UX mode to normalize newline and interrupt behavior.
4. Add telemetry and a Hermes compatibility test harness so that terminal regressions become visible and testable.

This is the most direct path to making Hermes TUI “just work” in our existing architecture, while preserving the flexibility to use the same terminal primitive for other TUIs in the future.

If you’d like, next step I can define a **Hermes compatibility test matrix** with specific scripted PTY sequences and expected outcomes to drop straight into CI.
<span style="display:none">[^22]</span>

<div align="center">⁂</div>

[^1]: https://pypi.org/project/prompt-toolkit/

[^2]: https://hermes-agent.nousresearch.com/docs/user-guide/cli

[^3]: https://github.com/NousResearch/hermes-agent/blob/main/README.md

[^4]: https://www.mintlify.com/NousResearch/hermes-agent/user-guide/cli

[^5]: https://github.com/prompt-toolkit/python-prompt-toolkit/issues/190

[^6]: https://discuss.python.org/t/multiline-input-in-terminal/72807?page=3

[^7]: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/full_screen_apps.html

[^8]: https://github.com/prompt-toolkit/python-prompt-toolkit/issues/1032

[^9]: https://stackoverflow.com/questions/44894059/xterm-js-pty-websocket-weird-characters-after-reconnect

[^10]: https://github.com/xtermjs/xterm.js/issues/677

[^11]: https://dev.to/ubinix_warun/xtermjs-setting-scrollback-to-9999999-for-enable-scroll-buffer-1ei2

[^12]: https://github.com/xtermjs/xterm.js/issues/361

[^13]: https://invisible-island.net/xterm/xterm-paste64.html

[^14]: https://www.asmeurer.com/mypython/

[^15]: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/reference.html

[^16]: https://www.reddit.com/r/electronjs/comments/1s5r047/built_a_terminal_ide_with_electron_xtermjs/

[^17]: https://github.com/tsl0922/ttyd

[^18]: https://www.nccgroup.com/research/technical-advisory-remote-shell-commands-execution-in-ttyd/

[^19]: https://tsl0922.github.io/ttyd/

[^20]: https://www.libhunt.com/compare-wetty-vs-ttyd

[^21]: https://www.x-cmd.com/install/wetty/

[^22]: https://github.com/Kilo-Org/cloud/issues/1195

