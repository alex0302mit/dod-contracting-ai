/**
 * Issue Highlighting Utilities
 *
 * Functions to highlight issues in the TipTap editor when user clicks on issue cards.
 * Uses TipTap's native mark system for reliable highlighting.
 */

import { Editor } from '@tiptap/react';

/**
 * Issue kind types for categorizing document issues
 * - error: Critical issues like TBD placeholders (red)
 * - warning: Non-critical issues needing attention (amber)
 * - info: Informational suggestions (blue)
 * - compliance: FAR/DFARS compliance issues (purple)
 * - hallucination: Potentially unsourced or fabricated claims (orange)
 */
export type IssueKind = 'error' | 'warning' | 'info' | 'compliance' | 'hallucination';

export interface HighlightPosition {
  from: number;
  to: number;
}

export interface HighlightResult {
  positions: HighlightPosition[];
  targetPosition?: HighlightPosition;
}

/**
 * Find sentence boundaries in the text around a given position
 * Sentences end with . ! ? followed by space or end of text
 */
function findSentenceBoundaries(
  textContent: string,
  matchStart: number,
  matchEnd: number
): { sentenceStart: number; sentenceEnd: number } {
  // Sentence ending patterns
  const sentenceEnders = /[.!?]/;

  // Find sentence start - look backwards for sentence ender + space, or start of text
  let sentenceStart = 0;
  for (let i = matchStart - 1; i >= 0; i--) {
    if (sentenceEnders.test(textContent[i])) {
      // Found a sentence ender, start after it (skip trailing whitespace)
      sentenceStart = i + 1;
      while (sentenceStart < matchStart && /\s/.test(textContent[sentenceStart])) {
        sentenceStart++;
      }
      break;
    }
    // Also break on paragraph boundaries (double newlines)
    if (i > 0 && textContent[i] === '\n' && textContent[i - 1] === '\n') {
      sentenceStart = i + 1;
      break;
    }
  }

  // Find sentence end - look forwards for sentence ender
  let sentenceEnd = textContent.length;
  for (let i = matchEnd; i < textContent.length; i++) {
    if (sentenceEnders.test(textContent[i])) {
      // Include the sentence ender
      sentenceEnd = i + 1;
      break;
    }
    // Also break on paragraph boundaries
    if (i < textContent.length - 1 && textContent[i] === '\n' && textContent[i + 1] === '\n') {
      sentenceEnd = i;
      break;
    }
  }

  return { sentenceStart, sentenceEnd };
}

/**
 * Convert a text index to a document position using the position map
 */
function textIndexToDocPos(
  textIndex: number,
  positionMap: { textIndex: number; docPos: number }[],
  textContentLength: number
): number | null {
  for (let i = 0; i < positionMap.length; i++) {
    const { textIndex: mapTextIndex, docPos } = positionMap[i];
    const nextTextIndex = i + 1 < positionMap.length
      ? positionMap[i + 1].textIndex
      : textContentLength;

    if (textIndex >= mapTextIndex && textIndex <= nextTextIndex) {
      return docPos + (textIndex - mapTextIndex);
    }
  }
  return null;
}

/**
 * Find all occurrences of a pattern in the editor's text content
 * Returns document positions (1-indexed for TipTap)
 * @param expandToSentence - If true, expands the match to the full sentence
 */
export function findPatternInEditor(
  editor: Editor,
  pattern: string,
  expandToSentence: boolean = false
): HighlightPosition[] {
  const positions: HighlightPosition[] = [];
  const doc = editor.state.doc;

  // Get the full text content with position tracking
  let textContent = '';
  const positionMap: { textIndex: number; docPos: number }[] = [];

  doc.descendants((node, pos) => {
    if (node.isText && node.text) {
      positionMap.push({ textIndex: textContent.length, docPos: pos });
      textContent += node.text;
    }
    return true;
  });

  // Find all matches of the pattern
  const escapedPattern = pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(escapedPattern, 'gi');
  let match;

  while ((match = regex.exec(textContent)) !== null) {
    let matchTextStart = match.index;
    let matchTextEnd = matchTextStart + match[0].length;

    // Expand to sentence boundaries if requested
    if (expandToSentence) {
      const { sentenceStart, sentenceEnd } = findSentenceBoundaries(
        textContent,
        matchTextStart,
        matchTextEnd
      );
      matchTextStart = sentenceStart;
      matchTextEnd = sentenceEnd;
    }

    // Convert text indices to document positions
    const docStart = textIndexToDocPos(matchTextStart, positionMap, textContent.length);
    const docEnd = textIndexToDocPos(matchTextEnd, positionMap, textContent.length);

    if (docStart !== null && docEnd !== null) {
      positions.push({ from: docStart, to: docEnd });
    }
  }

  return positions;
}

/**
 * Apply highlight styling using TipTap's setMark with Highlight extension
 * Falls back to adding inline styles if Highlight isn't available
 * @param expandToSentence - If true, expands highlights to cover the full sentence
 */
export function applyHighlightsWithEditor(
  editor: Editor,
  pattern: string,
  kind: IssueKind,
  targetOccurrence?: number,
  expandToSentence: boolean = false
): HighlightResult {
  const positions = findPatternInEditor(editor, pattern, expandToSentence);
  let targetPosition: HighlightPosition | undefined;

  if (positions.length === 0) {
    return { positions: [], targetPosition: undefined };
  }

  // Get the highlight color based on kind
  // Orange colors (#f97316) for hallucination issues - potentially unsourced claims
  const highlightColors: Record<IssueKind, string> = {
    error: '#fecaca',        // red-200
    warning: '#fde68a',      // amber-200
    info: '#bfdbfe',         // blue-200
    compliance: '#e9d5ff',   // purple-200
    hallucination: '#fed7aa', // orange-200 - for unsourced/fabricated claims
  };

  const targetColors: Record<IssueKind, string> = {
    error: '#fca5a5',        // red-300
    warning: '#fcd34d',      // amber-300
    info: '#93c5fd',         // blue-300
    compliance: '#d8b4fe',   // purple-300
    hallucination: '#fdba74', // orange-300 - target highlight for hallucination
  };

  // Apply highlights using TipTap's chain commands
  const chain = editor.chain();

  positions.forEach((pos, index) => {
    const isTarget = targetOccurrence !== undefined && index === targetOccurrence;

    if (isTarget) {
      targetPosition = pos;
    }

    // Use TipTap's highlight mark if available, or textStyle with background
    chain
      .setTextSelection({ from: pos.from, to: pos.to })
      .setHighlight({ color: isTarget ? targetColors[kind] : highlightColors[kind] });
  });

  // Execute the chain and reset selection
  chain.setTextSelection(editor.state.selection.from).run();

  return { positions, targetPosition };
}

/**
 * Clear all highlights from the editor
 */
export function clearHighlightsWithEditor(editor: Editor): void {
  // Select all and remove highlight marks
  const { from, to } = { from: 0, to: editor.state.doc.content.size };

  editor
    .chain()
    .setTextSelection({ from: 1, to: to - 1 })
    .unsetHighlight()
    .setTextSelection(editor.state.selection.from)
    .run();
}

/**
 * Alternative: Apply highlights by directly manipulating the DOM after render
 * This approach adds highlight spans without going through TipTap's state
 */
export function applyHighlightsDOM(
  editorElement: HTMLElement,
  pattern: string,
  kind: IssueKind,
  targetOccurrence?: number
): HighlightResult {
  // First clear any existing highlights
  clearHighlightsDOM(editorElement);

  const positions: HighlightPosition[] = [];
  let targetPosition: HighlightPosition | undefined;

  // Use Range and TreeWalker for safer DOM manipulation
  const treeWalker = document.createTreeWalker(
    editorElement,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: (node) => {
        // Skip empty text nodes and nodes inside existing highlights
        if (!node.textContent?.trim()) return NodeFilter.FILTER_REJECT;
        if (node.parentElement?.closest('[data-issue-highlight]')) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  // Collect all text nodes first (to avoid mutation issues during iteration)
  const textNodes: Text[] = [];
  let currentNode: Node | null;
  while ((currentNode = treeWalker.nextNode())) {
    textNodes.push(currentNode as Text);
  }

  const escapedPattern = pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(escapedPattern, 'gi');
  let globalOccurrenceIndex = 0;

  // Process each text node
  for (const textNode of textNodes) {
    const text = textNode.textContent || '';
    let lastIndex = 0;
    const fragments: (Text | HTMLSpanElement)[] = [];
    let hasMatch = false;

    // Reset regex for each node
    regex.lastIndex = 0;

    let match;
    while ((match = regex.exec(text)) !== null) {
      hasMatch = true;
      const isTarget = targetOccurrence !== undefined && globalOccurrenceIndex === targetOccurrence;

      // Add text before match
      if (match.index > lastIndex) {
        fragments.push(document.createTextNode(text.substring(lastIndex, match.index)));
      }

      // Create highlight wrapper
      const wrapper = document.createElement('span');
      wrapper.className = `issue-highlight issue-highlight-${kind}${isTarget ? ' issue-highlight-target' : ''}`;
      wrapper.setAttribute('data-issue-highlight', 'true');
      wrapper.textContent = match[0];
      fragments.push(wrapper);

      positions.push({ from: globalOccurrenceIndex, to: globalOccurrenceIndex });

      if (isTarget) {
        targetPosition = { from: globalOccurrenceIndex, to: globalOccurrenceIndex };
      }

      lastIndex = match.index + match[0].length;
      globalOccurrenceIndex++;
    }

    // If we found matches in this node, replace it
    if (hasMatch) {
      // Add remaining text after last match
      if (lastIndex < text.length) {
        fragments.push(document.createTextNode(text.substring(lastIndex)));
      }

      // Replace the text node with fragments
      const parent = textNode.parentNode;
      if (parent) {
        const container = document.createDocumentFragment();
        fragments.forEach(f => container.appendChild(f));
        parent.replaceChild(container, textNode);
      }
    }
  }

  return { positions, targetPosition };
}

/**
 * Clear all issue highlights from the editor DOM
 */
export function clearHighlightsDOM(editorElement: HTMLElement): void {
  const highlights = editorElement.querySelectorAll('[data-issue-highlight]');

  highlights.forEach(highlight => {
    const parent = highlight.parentNode;
    if (parent) {
      // Replace the span with just its text content
      const textNode = document.createTextNode(highlight.textContent || '');
      parent.replaceChild(textNode, highlight);

      // Normalize to merge adjacent text nodes
      parent.normalize();
    }
  });
}

/**
 * Scroll to the target highlight in the editor
 */
export function scrollToHighlight(editorElement: HTMLElement): void {
  // Find the target highlight
  const targetHighlight = editorElement.querySelector('.issue-highlight-target') as HTMLElement;

  if (targetHighlight) {
    targetHighlight.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
      inline: 'nearest'
    });
  } else {
    // Fall back to first highlight
    const firstHighlight = editorElement.querySelector('.issue-highlight');
    if (firstHighlight) {
      firstHighlight.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });
    }
  }
}

/**
 * Get color classes for issue kinds (for use in components)
 * Each kind has its own color theme for consistent visual distinction
 */
export function getIssueColors(kind: IssueKind) {
  const colors = {
    error: {
      ring: 'ring-red-500',
      bg: 'bg-red-500',
      bgLight: 'bg-red-50',
      border: 'border-red-100',
      gradient: 'from-red-50 to-orange-50/50',
      text: 'text-red-600',
    },
    warning: {
      ring: 'ring-amber-500',
      bg: 'bg-amber-500',
      bgLight: 'bg-amber-50',
      border: 'border-amber-100',
      gradient: 'from-amber-50 to-yellow-50/50',
      text: 'text-amber-600',
    },
    info: {
      ring: 'ring-blue-500',
      bg: 'bg-blue-500',
      bgLight: 'bg-blue-50',
      border: 'border-blue-100',
      gradient: 'from-blue-50 to-cyan-50/50',
      text: 'text-blue-600',
    },
    compliance: {
      ring: 'ring-purple-500',
      bg: 'bg-purple-500',
      bgLight: 'bg-purple-50',
      border: 'border-purple-100',
      gradient: 'from-purple-50 to-pink-50/50',
      text: 'text-purple-600',
    },
    // Hallucination issues - orange theme for potentially unsourced claims
    hallucination: {
      ring: 'ring-orange-500',
      bg: 'bg-orange-500',
      bgLight: 'bg-orange-50',
      border: 'border-orange-100',
      gradient: 'from-orange-50 to-amber-50/50',
      text: 'text-orange-600',
    },
  };

  return colors[kind] || colors.warning;
}
