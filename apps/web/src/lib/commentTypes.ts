/**
 * Comment and Annotation Types
 *
 * Data models for collaborative document review
 */

export type CommentStatus = 'open' | 'resolved' | 'archived';
export type CommentType = 'comment' | 'suggestion' | 'question' | 'issue';

export interface Comment {
  id: string;
  threadId: string;
  author: string;
  authorInitials: string;
  authorColor?: string;
  content: string;
  createdAt: string;
  updatedAt?: string;
  isEdited?: boolean;
}

export interface CommentThread {
  id: string;
  type: CommentType;
  status: CommentStatus;
  position: {
    from: number;
    to: number;
  };
  highlightedText: string;
  comments: Comment[];
  createdAt: string;
  resolvedAt?: string;
  resolvedBy?: string;
  tags?: string[];
}

export interface AnnotationState {
  threads: CommentThread[];
  activeThreadId: string | null;
}

/**
 * Create a new comment
 */
export function createComment(
  author: string,
  content: string,
  threadId: string
): Comment {
  return {
    id: `comment-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    threadId,
    author,
    authorInitials: getInitials(author),
    authorColor: getAuthorColor(author),
    content,
    createdAt: new Date().toISOString(),
  };
}

/**
 * Create a new comment thread
 */
export function createCommentThread(
  type: CommentType,
  position: { from: number; to: number },
  highlightedText: string,
  initialComment: Comment
): CommentThread {
  return {
    id: `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type,
    status: 'open',
    position,
    highlightedText,
    comments: [initialComment],
    createdAt: new Date().toISOString(),
  };
}

/**
 * Get initials from name
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Get consistent color for author
 */
export function getAuthorColor(author: string): string {
  const colors = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#f59e0b', // amber
    '#10b981', // green
    '#06b6d4', // cyan
    '#f97316', // orange
    '#6366f1', // indigo
  ];

  let hash = 0;
  for (let i = 0; i < author.length; i++) {
    hash = author.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}

/**
 * Format relative time
 */
export function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}
