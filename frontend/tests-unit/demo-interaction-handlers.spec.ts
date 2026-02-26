import { expect, test } from "@playwright/test"
import {
  buildClickPromptDispatchMessage,
  CLICK_PROMPT_DISPATCH_KIND,
  createClickPromptDispatchStarterConfig,
  parseClickPromptDispatchConfig,
  resolveInteractionReceiverRegistration,
} from "@/components/Demo/demoInteractionHandlers"

test.describe("demo interaction handler schema", () => {
  test("starter config parses into normalized click-prompt-dispatch contract", async () => {
    const starter = createClickPromptDispatchStarterConfig()
    const parsed = parseClickPromptDispatchConfig(starter)
    expect(parsed).toBeTruthy()
    expect(parsed?.kind).toBe(CLICK_PROMPT_DISPATCH_KIND)
    expect(parsed?.enabled).toBe(true)
    expect(parsed?.trigger.selector).toBe("pre code, code")
    expect(parsed?.dispatch.target).toBe("hidden_chat_panel")
    expect(parsed?.dispatch.format).toBe("json")
    expect(parsed?.dispatch.enforceRegisteredReceiver).toBe(false)
  })

  test("parser returns null for blocks without interaction contract", async () => {
    const parsed = parseClickPromptDispatchConfig({
      show_config_json: true,
    })
    expect(parsed).toBeNull()
  })

  test("dispatch message includes block context + user message envelope", async () => {
    const parsed = parseClickPromptDispatchConfig(
      createClickPromptDispatchStarterConfig(),
    )
    expect(parsed).toBeTruthy()

    const message = buildClickPromptDispatchMessage({
      block: {
        id: "content-block-a",
        title: "Code Sample",
        type: "content",
      },
      config: parsed!,
      selectedSource: "console.log('hello world')",
      userMessage: "Explain this line.",
    })

    const parsedMessage = JSON.parse(message) as {
      event: string
      block: { id: string; title: string; type: string }
      selected_source: string
      user_message: string
      target_panel_id: string | null
    }
    expect(parsedMessage.event).toBe("demo_block_click_prompt_dispatch.v1")
    expect(parsedMessage.block.id).toBe("content-block-a")
    expect(parsedMessage.block.title).toBe("Code Sample")
    expect(parsedMessage.block.type).toBe("content")
    expect(parsedMessage.selected_source).toBe("console.log('hello world')")
    expect(parsedMessage.user_message).toBe("Explain this line.")
    expect(parsedMessage.target_panel_id).toBeNull()
  })

  test("resolves interaction receiver registration from chat panel options", async () => {
    const registration = resolveInteractionReceiverRegistration({
      id: "hidden-chat-panel",
      kind: "chat",
      options: {
        interaction_receiver: {
          enabled: true,
          receiver_id: "hidden-chat-panel",
          accepts: ["click_prompt_dispatch.v1"],
        },
      },
    })
    expect(registration).toBeTruthy()
    expect(registration?.receiverId).toBe("hidden-chat-panel")
    expect(registration?.panelId).toBe("hidden-chat-panel")
    expect(registration?.panelKind).toBe("chat")
    expect(registration?.accepts).toContain("click_prompt_dispatch.v1")
  })
})
