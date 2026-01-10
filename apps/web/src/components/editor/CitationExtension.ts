/**
 * TipTap Extension for Citation Marks
 *
 * Renders citations like [1], [2] as styled inline elements
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export const CitationMark = Mark.create({
  name: 'citation',

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      citationId: {
        default: null,
        parseHTML: element => element.getAttribute('data-citation-id'),
        renderHTML: attributes => {
          if (!attributes.citationId) {
            return {};
          }
          return {
            'data-citation-id': attributes.citationId,
          };
        },
      },
      citationSource: {
        default: '',
        parseHTML: element => element.getAttribute('data-citation-source'),
        renderHTML: attributes => {
          return {
            'data-citation-source': attributes.citationSource,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span.citation',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'citation',
        title: HTMLAttributes['data-citation-source'] || 'Citation',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      insertCitation:
        (citationId: number, source: string) =>
        ({ commands }: any) => {
          const citationText = `[${citationId}]`;

          // Insert the citation text with citation mark
          return commands.insertContent({
            type: 'text',
            text: citationText,
            marks: [
              {
                type: this.name,
                attrs: {
                  citationId: citationId.toString(),
                  citationSource: source,
                },
              },
            ],
          });
        },
    } as any;
  },
});
