/**
 * Comment Extension for Tiptap
 *
 * Inline comment markers with thread support
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export interface CommentAttributes {
  threadId: string;
  commentType: 'comment' | 'suggestion' | 'question' | 'issue';
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    comment: {
      /**
       * Add a comment to selection
       */
      addComment: (attributes: CommentAttributes) => ReturnType;
      /**
       * Remove comment
       */
      removeComment: (threadId: string) => ReturnType;
      /**
       * Set active comment
       */
      setActiveComment: (threadId: string | null) => ReturnType;
    };
  }
}

export const CommentMark = Mark.create({
  name: 'comment',

  addAttributes() {
    return {
      threadId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-thread-id'),
        renderHTML: (attributes) => ({
          'data-thread-id': attributes.threadId,
        }),
      },
      commentType: {
        default: 'comment',
        parseHTML: (element) => element.getAttribute('data-comment-type') || 'comment',
        renderHTML: (attributes) => ({
          'data-comment-type': attributes.commentType,
        }),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-comment]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-comment': '',
        class: `comment-mark comment-${HTMLAttributes['data-comment-type'] || 'comment'}`,
      }),
      0,
    ];
  },

  addCommands() {
    return {
      addComment:
        (attributes) =>
        ({ commands, state }) => {
          const { from, to } = state.selection;

          // Must have selection
          if (from === to) {
            return false;
          }

          return commands.setMark(this.name, attributes);
        },

      removeComment:
        (threadId) =>
        ({ tr, state }) => {
          const { doc } = state;
          let removed = false;

          doc.descendants((node, pos) => {
            if (!node.marks) return;

            node.marks.forEach((mark) => {
              if (mark.type.name === this.name && mark.attrs.threadId === threadId) {
                const from = pos;
                const to = pos + node.nodeSize;
                tr.removeMark(from, to, mark);
                removed = true;
              }
            });
          });

          return removed;
        },

      setActiveComment:
        (threadId) =>
        ({ commands }) => {
          // This would update editor state to highlight active comment
          // Implementation would depend on state management approach
          return true;
        },
    };
  },
});
