/**
 * TipTap Extension for Quality & Compliance Issue Highlighting
 *
 * This extension marks text with quality/compliance issues using decorations
 * and shows tooltips on hover with issue details.
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export interface QualityIssue {
  id: string;
  kind: 'error' | 'warning' | 'info' | 'compliance';
  label: string;
  from: number;
  to: number;
  fix?: {
    label: string;
    apply: (text: string) => string;
  };
}

export const QualityIssueMark = Mark.create({
  name: 'qualityIssue',

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      issueId: {
        default: null,
        parseHTML: element => element.getAttribute('data-issue-id'),
        renderHTML: attributes => {
          if (!attributes.issueId) {
            return {};
          }
          return {
            'data-issue-id': attributes.issueId,
          };
        },
      },
      issueKind: {
        default: 'warning',
        parseHTML: element => element.getAttribute('data-issue-kind'),
        renderHTML: attributes => {
          return {
            'data-issue-kind': attributes.issueKind,
          };
        },
      },
      issueLabel: {
        default: '',
        parseHTML: element => element.getAttribute('data-issue-label'),
        renderHTML: attributes => {
          return {
            'data-issue-label': attributes.issueLabel,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-issue-id]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    const issueKind = HTMLAttributes['data-issue-kind'] || 'warning';

    const classes: Record<string, string> = {
      error: 'quality-issue-error',
      warning: 'quality-issue-warning',
      info: 'quality-issue-info',
      compliance: 'quality-issue-compliance',
    };

    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: `quality-issue ${classes[issueKind]}`,
        'data-issue-label': HTMLAttributes['data-issue-label'],
        title: HTMLAttributes['data-issue-label'],
      }),
      0,
    ];
  },

  addCommands() {
    return {
      setQualityIssue:
        (attributes: { issueId: string; issueKind: string; issueLabel: string }) =>
        ({ commands }: any) => {
          return commands.setMark(this.name, attributes);
        },
      unsetQualityIssue:
        () =>
        ({ commands }: any) => {
          return commands.unsetMark(this.name);
        },
    } as any;
  },
});
