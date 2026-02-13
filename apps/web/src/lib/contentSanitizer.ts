/**
 * Content Sanitizer Utility
 * 
 * Provides functions to clean up HTML content, particularly for removing
 * empty list items that can occur from AI-generated markdown conversion
 * or TipTap/ProseMirror editor artifacts.
 * 
 * Dependencies:
 * - Used by markdownToHtml.ts for final cleanup after conversion
 * - Used by RichTextEditor.tsx to ensure clean content before display
 * 
 * Problem Solved:
 * AI-generated documents often contain blank lines between list items,
 * which can result in empty bullet points (just "•" with no text).
 * This sanitizer removes those empty list items while preserving
 * legitimate content.
 */

/**
 * Sanitize HTML content to remove empty list items
 * 
 * Removes empty <li> elements that can occur from:
 * 1. AI generating markdown with blank lines between list items
 * 2. TipTap/ProseMirror adding trailing breaks or empty paragraphs
 * 3. Markdown-to-HTML conversion edge cases
 * 
 * @param html - HTML string that may contain empty list items
 * @returns Sanitized HTML string with empty list items removed
 * 
 * @example
 * ```typescript
 * const clean = sanitizeListContent('<ul><li>Item 1</li><li></li><li>Item 2</li></ul>');
 * // Returns: '<ul><li>Item 1</li><li>Item 2</li></ul>'
 * ```
 */
export function sanitizeListContent(html: string): string {
  if (!html) return '';
  
  let sanitized = html;
  
  // Run multiple passes to catch nested empty elements
  // Each pass can reveal new empty elements after inner ones are removed
  for (let i = 0; i < 3; i++) {
    // Standard empty list items
    sanitized = sanitized.replace(/<li>\s*<\/li>/gi, '');
    
    // Items with only whitespace or non-breaking spaces
    sanitized = sanitized.replace(/<li>[\s\u00A0]*<\/li>/gi, '');
    
    // Items with only line breaks (various formats)
    sanitized = sanitized.replace(/<li>\s*<br\s*\/?>\s*<\/li>/gi, '');
    sanitized = sanitized.replace(/<li><br\s*class="[^"]*"\s*\/?><\/li>/gi, '');
    
    // Items with empty paragraphs (TipTap wraps content in <p> tags)
    sanitized = sanitized.replace(/<li><p>\s*<\/p><\/li>/gi, '');
    sanitized = sanitized.replace(/<li><p>[\s\u00A0]*<\/p><\/li>/gi, '');
    sanitized = sanitized.replace(/<li>\s*<p>\s*<\/p>\s*<\/li>/gi, '');
    
    // Items with paragraphs containing only line breaks
    sanitized = sanitized.replace(/<li><p><br\s*\/?><\/p><\/li>/gi, '');
    sanitized = sanitized.replace(/<li><p><br\s*class="[^"]*"\s*\/?><\/p><\/li>/gi, '');
    sanitized = sanitized.replace(/<li>\s*<p>\s*<br\s*\/?>\s*<\/p>\s*<\/li>/gi, '');
    
    // ProseMirror-specific artifacts (trailing breaks with special classes)
    sanitized = sanitized.replace(/<li>\s*<p>\s*<br\s*class="ProseMirror[^"]*"\s*\/?>\s*<\/p>\s*<\/li>/gi, '');
    sanitized = sanitized.replace(/<li><p><br\s*class="ProseMirror-trailingBreak"\s*\/?><\/p><\/li>/gi, '');
  }
  
  // Remove empty lists that may be left behind after removing all items
  sanitized = sanitized.replace(/<ul>\s*<\/ul>/gi, '');
  sanitized = sanitized.replace(/<ol>\s*<\/ol>/gi, '');
  sanitized = sanitized.replace(/<ul>\n*<\/ul>/gi, '');
  sanitized = sanitized.replace(/<ol>\n*<\/ol>/gi, '');
  
  return sanitized;
}

/**
 * Sanitize markdown content to remove blank lines between list items
 * 
 * This function works on raw markdown before conversion to HTML.
 * It removes double newlines between consecutive list items while
 * preserving the list structure.
 * 
 * @param markdown - Markdown string with potential blank lines in lists
 * @returns Markdown with blank lines between list items removed
 */
export function sanitizeMarkdownLists(markdown: string): string {
  if (!markdown) return '';
  
  // Remove blank lines between consecutive bullet points
  // Matches: "- item1\n\n- item2" and converts to "- item1\n- item2"
  let sanitized = markdown;
  
  // Handle unordered lists (-, *, •)
  sanitized = sanitized.replace(/^(\s*[-*•]\s+.+)\n\n+(\s*[-*•]\s+)/gm, '$1\n$2');
  
  // Handle ordered lists (1., 2., etc.)
  sanitized = sanitized.replace(/^(\s*\d+\.\s+.+)\n\n+(\s*\d+\.\s+)/gm, '$1\n$2');
  
  // Remove lines that are just bullet markers without content
  sanitized = sanitized.replace(/^\s*[-*•]\s*$/gm, '');
  
  return sanitized;
}
