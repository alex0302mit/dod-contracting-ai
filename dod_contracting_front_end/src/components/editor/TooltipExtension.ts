/**
 * Tooltip Extension for Tiptap
 *
 * Provides contextual hover help text for terms, acronyms, and concepts
 * Renders with dotted underline indicator and shows tooltip on hover
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export interface TooltipAttributes {
  tooltipId: string;
  tooltipText: string;
  tooltipType?: 'definition' | 'acronym' | 'reference' | 'help';
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    tooltip: {
      /**
       * Add a tooltip to the current selection
       */
      addTooltip: (attributes: TooltipAttributes) => ReturnType;
      /**
       * Remove a tooltip by ID
       */
      removeTooltip: (tooltipId: string) => ReturnType;
      /**
       * Update tooltip text
       */
      updateTooltip: (tooltipId: string, newText: string) => ReturnType;
    };
  }
}

export const Tooltip = Mark.create({
  name: 'tooltip',

  addAttributes() {
    return {
      tooltipId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-tooltip-id'),
        renderHTML: (attributes) => {
          if (!attributes.tooltipId) {
            return {};
          }
          return {
            'data-tooltip-id': attributes.tooltipId,
          };
        },
      },
      tooltipText: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-tooltip-text'),
        renderHTML: (attributes) => {
          return {
            'data-tooltip-text': attributes.tooltipText,
          };
        },
      },
      tooltipType: {
        default: 'help',
        parseHTML: (element) => element.getAttribute('data-tooltip-type'),
        renderHTML: (attributes) => {
          return {
            'data-tooltip-type': attributes.tooltipType || 'help',
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-tooltip]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    const tooltipText = HTMLAttributes['data-tooltip-text'] || '';
    const tooltipType = HTMLAttributes['data-tooltip-type'] || 'help';

    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-tooltip': '',
        class: `tooltip-mark tooltip-${tooltipType}`,
        title: tooltipText, // Fallback for browsers without CSS tooltips
        'aria-label': tooltipText,
      }),
      0,
    ];
  },

  addCommands() {
    return {
      addTooltip:
        (attributes) =>
        ({ commands, state }) => {
          const { from, to } = state.selection;

          // Generate unique tooltip ID if not provided
          if (!attributes.tooltipId) {
            attributes.tooltipId = `tooltip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
          }

          // Must have a selection
          if (from === to) {
            return false;
          }

          return commands.setMark(this.name, attributes);
        },

      removeTooltip:
        (tooltipId) =>
        ({ tr, state }) => {
          const { doc } = state;
          let removed = false;

          doc.descendants((node, pos) => {
            if (!node.marks) return;

            node.marks.forEach((mark) => {
              if (mark.type.name === this.name && mark.attrs.tooltipId === tooltipId) {
                const from = pos;
                const to = pos + node.nodeSize;

                tr.removeMark(from, to, mark);
                removed = true;
              }
            });
          });

          return removed;
        },

      updateTooltip:
        (tooltipId, newText) =>
        ({ tr, state }) => {
          const { doc } = state;
          let updated = false;

          doc.descendants((node, pos) => {
            if (!node.marks) return;

            node.marks.forEach((mark) => {
              if (mark.type.name === this.name && mark.attrs.tooltipId === tooltipId) {
                const from = pos;
                const to = pos + node.nodeSize;

                tr.removeMark(from, to, mark);
                tr.addMark(from, to, this.type.create({
                  ...mark.attrs,
                  tooltipText: newText,
                }));

                updated = true;
              }
            });
          });

          return updated;
        },
    };
  },
});
