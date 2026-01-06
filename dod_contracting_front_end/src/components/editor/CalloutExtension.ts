/**
 * Callout Extension for Tiptap
 *
 * Visual callout boxes for important information, warnings, tips, etc.
 * Similar to GitHub/Notion callout blocks
 */

import { Node, mergeAttributes } from '@tiptap/core';

export type CalloutType = 'info' | 'warning' | 'success' | 'danger' | 'tip' | 'note' | 'important' | 'caution';

export interface CalloutAttributes {
  type: CalloutType;
  title?: string;
  icon?: string;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    callout: {
      /**
       * Insert a callout block
       */
      insertCallout: (attributes?: Partial<CalloutAttributes>) => ReturnType;
      /**
       * Set callout type
       */
      setCalloutType: (type: CalloutType) => ReturnType;
      /**
       * Toggle callout
       */
      toggleCallout: () => ReturnType;
    };
  }
}

export const Callout = Node.create({
  name: 'callout',

  group: 'block',

  content: 'block+',

  defining: true,

  addAttributes() {
    return {
      type: {
        default: 'info',
        parseHTML: (element) => element.getAttribute('data-callout-type') || 'info',
        renderHTML: (attributes) => ({
          'data-callout-type': attributes.type,
        }),
      },
      title: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-callout-title'),
        renderHTML: (attributes) => {
          if (!attributes.title) return {};
          return {
            'data-callout-title': attributes.title,
          };
        },
      },
      icon: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-callout-icon'),
        renderHTML: (attributes) => {
          if (!attributes.icon) return {};
          return {
            'data-callout-icon': attributes.icon,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-callout]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    const type = HTMLAttributes['data-callout-type'] || 'info';
    const title = HTMLAttributes['data-callout-title'];

    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-callout': '',
        class: `callout callout-${type}`,
      }),
      title
        ? [
            'div',
            { class: 'callout-title' },
            title,
          ]
        : undefined,
      ['div', { class: 'callout-content' }, 0],
    ].filter(Boolean) as any;
  },

  addCommands() {
    return {
      insertCallout:
        (attributes = {}) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: {
              type: attributes.type || 'info',
              title: attributes.title,
              icon: attributes.icon,
            },
            content: [
              {
                type: 'paragraph',
                content: [{ type: 'text', text: 'Enter callout content...' }],
              },
            ],
          });
        },

      setCalloutType:
        (type) =>
        ({ commands }) => {
          return commands.updateAttributes(this.name, { type });
        },

      toggleCallout:
        () =>
        ({ commands }) => {
          return commands.toggleWrap(this.name);
        },
    };
  },

  addKeyboardShortcuts() {
    return {
      'Mod-Shift-c': () => this.editor.commands.toggleCallout(),
    };
  },
});
