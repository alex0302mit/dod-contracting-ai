/**
 * Annotation Panel Component
 *
 * Sidebar for managing all document annotations and comments
 */

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  MessageSquare,
  AlertCircle,
  HelpCircle,
  Lightbulb,
  Filter,
  Plus,
  CheckCircle2,
} from 'lucide-react';
import { Editor } from '@tiptap/react';
import {
  CommentThread as CommentThreadType,
  Comment,
  CommentType,
  CommentStatus,
  createComment,
  createCommentThread,
} from '@/lib/commentTypes';
import { CommentThread } from './CommentThread';

interface AnnotationPanelProps {
  editor: Editor | null;
  threads: CommentThreadType[];
  currentUser: string;
  onAddThread: (thread: CommentThreadType) => void;
  onAddComment: (threadId: string, comment: Comment) => void;
  onResolveThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
}

export function AnnotationPanel({
  editor,
  threads,
  currentUser,
  onAddThread,
  onAddComment,
  onResolveThread,
  onDeleteThread,
}: AnnotationPanelProps) {
  const [filterStatus, setFilterStatus] = useState<CommentStatus | 'all'>('all');
  const [filterType, setFilterType] = useState<CommentType | 'all'>('all');
  const [showNewComment, setShowNewComment] = useState(false);
  const [newCommentType, setNewCommentType] = useState<CommentType>('comment');
  const [newCommentText, setNewCommentText] = useState('');

  // Filter threads
  const filteredThreads = useMemo(() => {
    let filtered = threads;

    if (filterStatus !== 'all') {
      filtered = filtered.filter((t) => t.status === filterStatus);
    }

    if (filterType !== 'all') {
      filtered = filtered.filter((t) => t.type === filterType);
    }

    // Sort by creation date (newest first)
    return filtered.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }, [threads, filterStatus, filterType]);

  // Statistics
  const stats = useMemo(() => {
    return {
      total: threads.length,
      open: threads.filter((t) => t.status === 'open').length,
      resolved: threads.filter((t) => t.status === 'resolved').length,
      comments: threads.filter((t) => t.type === 'comment').length,
      suggestions: threads.filter((t) => t.type === 'suggestion').length,
      questions: threads.filter((t) => t.type === 'question').length,
      issues: threads.filter((t) => t.type === 'issue').length,
    };
  }, [threads]);

  const handleCreateComment = () => {
    if (!editor || !newCommentText.trim()) return;

    const { from, to } = editor.state.selection;

    if (from === to) {
      alert('Please select some text to comment on.');
      return;
    }

    // Get selected text
    const selectedText = editor.state.doc.textBetween(from, to, ' ');

    // Create initial comment
    const initialComment = createComment(currentUser, newCommentText.trim(), '');

    // Create thread
    const thread = createCommentThread(
      newCommentType,
      { from, to },
      selectedText,
      initialComment
    );

    // Update initial comment with thread ID
    initialComment.threadId = thread.id;

    // Add thread
    onAddThread(thread);

    // Add comment mark to editor
    editor
      .chain()
      .focus()
      .addComment({
        threadId: thread.id,
        commentType: newCommentType,
      })
      .run();

    // Reset form
    setNewCommentText('');
    setNewCommentType('comment');
    setShowNewComment(false);
  };

  return (
    <div className="space-y-4">
      {/* Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Annotations
          </CardTitle>
          <CardDescription className="text-xs">
            {stats.total} total • {stats.open} open • {stats.resolved} resolved
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="text-center p-2 rounded-lg bg-blue-50 border border-blue-200">
              <div className="text-lg font-bold text-blue-700">{stats.comments}</div>
              <div className="text-[10px] text-blue-600 uppercase font-medium">Comments</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-purple-50 border border-purple-200">
              <div className="text-lg font-bold text-purple-700">{stats.suggestions}</div>
              <div className="text-[10px] text-purple-600 uppercase font-medium">Suggestions</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-orange-50 border border-orange-200">
              <div className="text-lg font-bold text-orange-700">{stats.questions}</div>
              <div className="text-[10px] text-orange-600 uppercase font-medium">Questions</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-red-50 border border-red-200">
              <div className="text-lg font-bold text-red-700">{stats.issues}</div>
              <div className="text-[10px] text-red-600 uppercase font-medium">Issues</div>
            </div>
          </div>

          {/* New Comment Button */}
          <Button
            size="sm"
            className="w-full gap-2"
            onClick={() => setShowNewComment(!showNewComment)}
          >
            <Plus className="h-4 w-4" />
            New Comment
          </Button>
        </CardContent>
      </Card>

      {/* New Comment Form */}
      {showNewComment && (
        <Card className="border-blue-300 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="text-sm">Add Comment</CardTitle>
            <CardDescription className="text-xs">
              Select text in the editor, then add your comment
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <label className="text-xs font-medium">Type</label>
              <Select value={newCommentType} onValueChange={(v) => setNewCommentType(v as CommentType)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="comment">💬 Comment</SelectItem>
                  <SelectItem value="suggestion">💡 Suggestion</SelectItem>
                  <SelectItem value="question">❓ Question</SelectItem>
                  <SelectItem value="issue">⚠️ Issue</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium">Comment</label>
              <Textarea
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                placeholder="Enter your comment..."
                className="text-xs resize-none"
                rows={4}
              />
            </div>

            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreateComment} className="flex-1 h-7 text-xs">
                Add Comment
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setShowNewComment(false);
                  setNewCommentText('');
                }}
                className="flex-1 h-7 text-xs"
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <label className="text-xs font-medium">Status</label>
            <Select value={filterStatus} onValueChange={(v) => setFilterStatus(v as any)}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">Open Only</SelectItem>
                <SelectItem value="resolved">Resolved Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium">Type</label>
            <Select value={filterType} onValueChange={(v) => setFilterType(v as any)}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="comment">Comments</SelectItem>
                <SelectItem value="suggestion">Suggestions</SelectItem>
                <SelectItem value="question">Questions</SelectItem>
                <SelectItem value="issue">Issues</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Thread List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            Threads ({filteredThreads.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-3 pr-3">
              {filteredThreads.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-xs">
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  No threads match your filters
                </div>
              ) : (
                filteredThreads.map((thread) => (
                  <CommentThread
                    key={thread.id}
                    thread={thread}
                    currentUser={currentUser}
                    onAddComment={onAddComment}
                    onResolveThread={onResolveThread}
                    onDeleteThread={onDeleteThread}
                  />
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
