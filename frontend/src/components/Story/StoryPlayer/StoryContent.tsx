/**
 * StoryContent
 *
 * Renders the current node's content and available choices.
 * Consumes StoryPlayerContext for all data.
 *
 * CONTENT FORMATS:
 * - html: Sanitized via DOMPurify, rendered with prose styling
 * - markdown: Rendered via ReactMarkdown with prose styling
 * - json: Formatted as preformatted code block
 * - text: Plain text with whitespace preserved
 */
import { ChevronRight, Play } from "lucide-react";
import {
  ContentRenderer,
  nodeToContent,
} from "@/components/Common/ContentRenderer";
// import type { StoryNodePublic } from "@/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useStoryPlayerContext } from "./useStoryPlayerContext";

/**
 * Renders node content based on format.
 *
 * ARCHITECTURE DECISION: This is extracted as a helper function rather than
 * a component because it's tightly coupled to node data structure and
 * doesn't need its own lifecycle or state.
 */

export function StoryContent() {
  const {
    startNode,
    currentNode,
    availableChoices,
    isEndNode,
    handleChoice,
    handleRestart,
  } = useStoryPlayerContext();

  // No start node configured
  if (!startNode) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <Card className="max-w-md">
          <CardContent className="py-8 text-center">
            <p className="text-destructive font-medium">No start node found</p>
            <p className="text-muted-foreground mt-2 text-sm">
              Add a node marked as "Start" to begin the story
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Current node not found (edge case)
  if (!currentNode) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <Card className="max-w-md">
          <CardContent className="text-center">
            <p className="text-destructive">Node not found</p>
            <Button className="mt-4" onClick={handleRestart}>
              Restart
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Normal content rendering
  return (
    <div className="p-8">
      <div className="flex items-center h-full justify-between mx-auto max-w-xxl">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex-1 min-h-0">
                {currentNode.title}
              </CardTitle>
              {isEndNode && <Badge>The End</Badge>}
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Node Content */}
            <ContentRenderer
              content={nodeToContent(currentNode, "page")}
              safeMode={true}
            />

            {/* Choices Section */}
            {!isEndNode && availableChoices.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-muted-foreground text-sm font-medium uppercase mb-3">
                    What do you do?
                  </h3>
                  <div className="space-y-3">
                    {availableChoices
                      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                      .map((choice) => (
                        <button
                          key={choice.id}
                          type="button"
                          onClick={() => handleChoice(choice)}
                          className="hover:bg-muted border-border bg-background flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors"
                        >
                          <span>{choice.text}</span>
                          <ChevronRight className="text-muted-foreground h-5 w-5 shrink-0" />
                        </button>
                      ))}
                  </div>
                </div>
              </>
            )}

            {/* End State */}
            {isEndNode && currentNode.is_end_node && (
              <>
                <Separator />
                <div className="text-center space-y-3">
                  <p className="text-lg font-medium text-muted-foreground">
                    You've reached an ending!
                  </p>
                  <Button onClick={handleRestart}>
                    <Play className="mr-2 h-4 w-4" />
                    Play Again
                  </Button>
                </div>
              </>
            )}

            {/* Dead End Warning */}
            {!currentNode.is_end_node && availableChoices.length === 0 && (
              <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-4 text-center">
                <p className="text-amber-700 dark:text-amber-400 text-sm">
                  No choices available from this node (dead end or conditions
                  not met). Use Undo or Restart to continue.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
