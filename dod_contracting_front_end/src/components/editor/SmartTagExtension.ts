/**
 * Smart Tag Extension for Tiptap
 *
 * Inline metadata tags with colored badges for categorizing content
 * Tag types: requirement, assumption, risk, decision, action-item, note
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export interface SmartTagAttributes {
  tagId: string;
  tagType: 'requirement' | 'assumption' | 'risk' | 'decision' | 'action-item' | 'note';
  tagLabel: string;
  tagDescription?: string;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    smartTag: {
      /**
       * Insert a smart tag at the current cursor position
       */
      insertSmartTag: (attributes: SmartTagAttributes) => ReturnType;
      /**
       * Update an existing smart tag
       */
      updateSmartTag: (tagId: string, attributes: Partial<SmartTagAttributes>) => ReturnType;
      /**
       * Remove a smart tag
       */
      removeSmartTag: (tagId: string) => ReturnType;
    };
  }
}

export const SmartTag = Mark.create({
  name: 'smartTag',

  addAttributes() {
    return {
      tagId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-tag-id'),
        renderHTML: (attributes) => {
          if (!attributes.tagId) {
            return {};
          }
          return {
            'data-tag-id': attributes.tagId,
          };
        },
      },
      tagType: {
        default: 'note',
        parseHTML: (element) => element.getAttribute('data-tag-type'),
        renderHTML: (attributes) => {
          return {
            'data-tag-type': attributes.tagType,
          };
        },
      },
      tagLabel: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-tag-label'),
        renderHTML: (attributes) => {
          return {
            'data-tag-label': attributes.tagLabel,
          };
        },
      },
      tagDescription: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-tag-description'),
        renderHTML: (attributes) => {
          if (!attributes.tagDescription) {
            return {};
          }
          return {
            'data-tag-description': attributes.tagDescription,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-smart-tag]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-smart-tag': '',
        class: `smart-tag smart-tag-${HTMLAttributes['data-tag-type'] || 'note'}`,
        title: HTMLAttributes['data-tag-description'] || HTMLAttributes['data-tag-label'] || 'Smart Tag',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      insertSmartTag:
        (attributes) =>
        ({ commands, state }) => {
          const { from, to } = state.selection;

          // Generate unique tag ID if not provided
          if (!attributes.tagId) {
            attributes.tagId = `tag-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
          }

          // If there's a selection, wrap it
          if (from !== to) {
            return commands.setMark(this.name, attributes);
          }

          // Otherwise, insert the tag label as text and apply the mark
          return commands.insertContent({
            type: 'text',
            text: `[${attributes.tagLabel}]`,
            marks: [
              {
                type: this.name,
                attrs: attributes,
              },
            ],
          });
        },

      updateSmartTag:
        (tagId, newAttributes) =>
        ({ tr, state }) => {
          const { doc } = state;
          let updated = false;

          doc.descendants((node, pos) => {
            if (!node.marks) return;

            node.marks.forEach((mark) => {
              if (mark.type.name === this.name && mark.attrs.tagId === tagId) {
                const from = pos;
                const to = pos + node.nodeSize;

                tr.removeMark(from, to, mark);
                tr.addMark(from, to, this.type.create({
                  ...mark.attrs,
                  ...newAttributes,
                }));

                updated = true;
              }
            });
          });

          return updated;
        },

      removeSmartTag:
        (tagId) =>
        ({ tr, state }) => {
          const { doc } = state;
          let removed = false;

          doc.descendants((node, pos) => {
            if (!node.marks) return;

            node.marks.forEach((mark) => {
              if (mark.type.name === this.name && mark.attrs.tagId === tagId) {
                const from = pos;
                const to = pos + node.nodeSize;

                tr.removeMark(from, to, mark);
                removed = true;
              }
            });
          });

          return removed;
        },
    };
  },
});
