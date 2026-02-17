/**
 * StoryCard - Individual story display card
 *
 * Features:
 * - Status badge: Published (primary), Unpublished (secondary), Draft (outline)
 * - Editing badge when current_version > published_version
 * - Action buttons: Edit, Publish/Unpublish, Delete
 * - Linked rooms display with navigation
 * - Relative timestamp formatting
 */

import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { Edit, MessageSquare, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { RoomsService, type StoryPublic } from "@/client";
import AddRoom from "@/components/Room/Dialogs/AddRoom";
// import {
//   presentationToStyle,
//   resolveStoryPresentation,
//   STORY_TYPE_PRESENTATIONS,
// } from "@/components/Common/Themes/resolve";
// import type { StoryPresentation } from "@/components/Common/Themes/types";
//import { isStoryTypeKey } from "@/components/Common/Themes/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  useDeleteStory,
  usePublishStory,
  useUnpublishStory,
} from "@/hooks/stories/useStories";

interface StoryCardProps {
  story: StoryPublic;
}

const StoryCard = ({ story }: StoryCardProps) => {
  const navigate = useNavigate();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const publishMutation = usePublishStory();
  const unpublishMutation = useUnpublishStory();
  const deleteMutation = useDeleteStory();

  // Fetch linked rooms for this story
  const { data: roomsData } = useQuery({
    queryKey: ["rooms", "story", story.id],
    queryFn: () => RoomsService.getRoomsForStory({ storyId: story.id }),
  });

  // Determine story lifecycle state for badge
  const getStatusBadge = () => {
    if (story.is_published && story.published_version !== null) {
      return (
        <Badge variant="default">Published v{story.published_version}</Badge>
      );
    }
    if (!story.is_published && story.published_version !== null) {
      return <Badge variant="secondary">Unpublished</Badge>;
    }
    return <Badge variant="outline">Draft v{story.current_version}</Badge>;
  };

  // Show editing badge if current version > published version
  const getEditingBadge = () => {
    if (
      story.published_version &&
      story.current_version > story.published_version
    ) {
      return (
        <Badge
          variant="secondary"
          className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
        >
          Draft v{story.current_version}
        </Badge>
      );
    }
    return null;
  };

  const handleEdit = () => {
    navigate({ to: "/stories/$storyId/edit", params: { storyId: story.id } });
  };

  const handleTogglePublish = () => {
    if (story.is_published) {
      unpublishMutation.mutate(story.id);
    } else {
      publishMutation.mutate(story.id);
    }
  };

  const handleDelete = () => {
    deleteMutation.mutate(story.id);
    setShowDeleteDialog(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (diffInDays === 0) return "Today";
    if (diffInDays === 1) return "Yesterday";
    if (diffInDays < 7) return `${diffInDays} days ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  const linkedRooms = roomsData?.data ?? [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-xl">{story.title}</CardTitle>
          <div className="flex gap-2">
            {getStatusBadge()}
            {getEditingBadge()}
          </div>
        </div>
        <CardDescription className="min-h-4">
          {story.description || "No description"}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        {/* Version Info */}
        <div className="text-muted-foreground flex gap-4 text-xs">
          <span>Current: v{story.current_version}</span>
          {story.published_version && (
            <span>Published: v{story.published_version}</span>
          )}
        </div>

        {/* Timestamp */}
        <p className="text-muted-foreground text-xs">
          Updated {formatDate(story.updated_at)}
        </p>

        {/* Linked Rooms */}
        {linkedRooms.length > 0 && (
          <div className="flex flex-col gap-2 pt-2">
            <div className="text-muted-foreground flex items-center gap-1 text-xs">
              <MessageSquare className="h-3 w-3" />
              <span>Linked Rooms:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {linkedRooms.map((room) => (
                <Link
                  key={room.room_id}
                  to="/r/$roomId"
                  params={{ roomId: room.room_id }}
                >
                  <Badge
                    variant="secondary"
                    className="cursor-pointer hover:opacity-80"
                  >
                    {room.title || "Untitled Room"}
                  </Badge>
                </Link>
              ))}
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex-wrap gap-2">
        {/* Edit Button */}
        <Button size="sm" onClick={handleEdit}>
          <Edit className="mr-1 h-4 w-4" />
          Edit
        </Button>

        {/* Create Room Button - only for published stories */}
        {story.is_published && (
          <AddRoom
            defaultStoryId={story.id}
            trigger={
              <Button size="sm" variant="outline">
                <Plus className="mr-1 h-4 w-4" />
                Room
              </Button>
            }
          />
        )}

        {/* Publish/Unpublish Button */}
        <Button
          size="sm"
          variant="outline"
          onClick={handleTogglePublish}
          disabled={publishMutation.isPending || unpublishMutation.isPending}
        >
          {publishMutation.isPending || unpublishMutation.isPending
            ? "..."
            : story.is_published
              ? "Unpublish"
              : "Publish"}
        </Button>

        {/* Delete Button with Confirmation Dialog */}
        <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Story</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{story.title}"? This action
                cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  );
};

export default StoryCard;
