/**
 * Comment Thread Component
 *
 * Display and manage a thread of comments
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  MessageSquare,
  AlertCircle,
  HelpCircle,
  Lightbulb,
  Check,
  X,
  MoreVertical,
  Trash2,
} from 'lucide-react';
import {
  CommentThread as CommentThreadType,
  Comment,
  CommentType,
  createComment,
  formatRelativeTime,
} from '@/lib/commentTypes';

interface CommentThreadProps {
  thread: CommentThreadType;
  currentUser: string;
  onAddComment: (threadId: string, comment: Comment) => void;
  onResolveThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
  onDeleteComment?: (threadId: string, commentId: string) => void;
}

const TYPE_CONFIG: Record<CommentType, { icon: any; label: string; color: string }> = {
  comment: { icon: MessageSquare, label: 'Comment', color: 'blue' },
  suggestion: { icon: Lightbulb, label: 'Suggestion', color: 'purple' },
  question: { icon: HelpCircle, label: 'Question', color: 'orange' },
  issue: { icon: AlertCircle, label: 'Issue', color: 'red' },
};

export function CommentThread({
  thread,
  currentUser,
  onAddComment,
  onResolveThread,
  onDeleteThread,
  onDeleteComment,
}: CommentThreadProps) {
  const [replyText, setReplyText] = useState('');
  const [isReplying, setIsReplying] = useState(false);

  const config = TYPE_CONFIG[thread.type];
  const Icon = config.icon;

  const handleAddReply = () => {
    if (!replyText.trim()) return;

    const newComment = createComment(currentUser, replyText.trim(), thread.id);
    onAddComment(thread.id, newComment);

    setReplyText('');
    setIsReplying(false);
  };

  const handleResolve = () => {
    onResolveThread(thread.id);
  };

  const handleDelete = () => {
    if (confirm('Delete this entire thread? This cannot be undone.')) {
      onDeleteThread(thread.id);
    }
  };

  return (
    <div
      className={`border rounded-lg p-3 ${
        thread.status === 'resolved'
          ? 'bg-green-50 border-green-200'
          : `bg-${config.color}-50/50 border-${config.color}-200`
      }`}
    >
      {/* Thread Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Icon className={`h-4 w-4 text-${config.color}-600`} />
            <Badge variant="outline" className={`text-xs bg-${config.color}-100 text-${config.color}-800`}>
              {config.label}
            </Badge>
            {thread.status === 'resolved' && (
              <Badge variant="outline" className="text-xs bg-green-100 text-green-800">
                <Check className="h-3 w-3 mr-1" />
                Resolved
              </Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground font-mono line-clamp-2">
            "{thread.highlightedText}"
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={handleDelete}
        >
          <Trash2 className="h-3 w-3 text-muted-foreground" />
        </Button>
      </div>

      <Separator className="mb-3" />

      {/* Comments */}
      <div className="space-y-3">
        {thread.comments.map((comment, index) => (
          <div key={comment.id} className="space-y-1">
            <div className="flex items-start gap-2">
              <div
                className="h-6 w-6 rounded-full flex items-center justify-center text-white text-[10px] font-semibold flex-shrink-0"
                style={{ backgroundColor: comment.authorColor }}
              >
                {comment.authorInitials}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="text-xs font-semibold">{comment.author}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {formatRelativeTime(comment.createdAt)}
                  </span>
                  {comment.isEdited && (
                    <span className="text-[10px] text-muted-foreground italic">(edited)</span>
                  )}
                </div>
                <p className="text-xs mt-1 whitespace-pre-wrap">{comment.content}</p>
              </div>
              {onDeleteComment && comment.author === currentUser && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100"
                  onClick={() => onDeleteComment(thread.id, comment.id)}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
            {index < thread.comments.length - 1 && <Separator className="my-2" />}
          </div>
        ))}
      </div>

      {/* Reply Section */}
      {thread.status !== 'resolved' && (
        <>
          <Separator className="my-3" />
          {isReplying ? (
            <div className="space-y-2">
              <Textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Add a reply..."
                className="text-xs resize-none"
                rows={3}
                autoFocus
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleAddReply} className="flex-1 h-7 text-xs">
                  Reply
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setReplyText('');
                    setIsReplying(false);
                  }}
                  className="flex-1 h-7 text-xs"
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsReplying(true)}
                className="flex-1 h-7 text-xs"
              >
                Reply
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleResolve}
                className="flex-1 h-7 text-xs gap-1 bg-green-50 hover:bg-green-100 border-green-300"
              >
                <Check className="h-3 w-3" />
                Resolve
              </Button>
            </div>
          )}
        </>
      )}

      {/* Resolved By */}
      {thread.status === 'resolved' && thread.resolvedBy && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-[10px] text-muted-foreground">
            Resolved by {thread.resolvedBy} • {formatRelativeTime(thread.resolvedAt!)}
          </p>
        </div>
      )}
    </div>
  );
}
