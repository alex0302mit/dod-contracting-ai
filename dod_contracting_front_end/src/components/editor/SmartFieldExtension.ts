/**
 * Smart Field Extension for Tiptap
 *
 * Node extension for interactive form fields in documents
 */

import { Node, mergeAttributes } from '@tiptap/core';
import { ReactNodeViewRenderer } from '@tiptap/react';

export interface SmartFieldAttributes {
  fieldId: string;
  templateId: string;
  isComplete: boolean;
  values: string; // JSON stringified values
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    smartField: {
      /**
       * Insert a smart field
       */
      insertSmartField: (attributes: Omit<SmartFieldAttributes, 'values'>) => ReturnType;
      /**
       * Update smart field values
       */
      updateSmartField: (fieldId: string, values: Record<string, string>) => ReturnType;
      /**
       * Delete a smart field
       */
      deleteSmartField: (fieldId: string) => ReturnType;
    };
  }
}

export const SmartField = Node.create({
  name: 'smartField',

  group: 'block',

  atom: true,

  addAttributes() {
    return {
      fieldId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-field-id'),
        renderHTML: (attributes) => ({
          'data-field-id': attributes.fieldId,
        }),
      },
      templateId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-template-id'),
        renderHTML: (attributes) => ({
          'data-template-id': attributes.templateId,
        }),
      },
      isComplete: {
        default: false,
        parseHTML: (element) => element.getAttribute('data-complete') === 'true',
        renderHTML: (attributes) => ({
          'data-complete': attributes.isComplete.toString(),
        }),
      },
      values: {
        default: '{}',
        parseHTML: (element) => element.getAttribute('data-values') || '{}',
        renderHTML: (attributes) => ({
          'data-values': attributes.values,
        }),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-smart-field]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-smart-field': '',
        class: 'smart-field-block',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      insertSmartField:
        (attributes) =>
        ({ commands }) => {
          const fieldAttrs: SmartFieldAttributes = {
            ...attributes,
            values: '{}',
            isComplete: false,
          };

          return commands.insertContent({
            type: this.name,
            attrs: fieldAttrs,
          });
        },

      updateSmartField:
        (fieldId, values) =>
        ({ tr, state }) => {
          const { doc } = state;
          let updated = false;

          doc.descendants((node, pos) => {
            if (node.type.name === this.name && node.attrs.fieldId === fieldId) {
              tr.setNodeMarkup(pos, undefined, {
                ...node.attrs,
                values: JSON.stringify(values),
                isComplete: true, // Would need proper validation
              });
              updated = true;
            }
          });

          return updated;
        },

      deleteSmartField:
        (fieldId) =>
        ({ tr, state }) => {
          const { doc } = state;
          let deleted = false;

          doc.descendants((node, pos) => {
            if (node.type.name === this.name && node.attrs.fieldId === fieldId) {
              tr.delete(pos, pos + node.nodeSize);
              deleted = true;
            }
          });

          return deleted;
        },
    };
  },
});
