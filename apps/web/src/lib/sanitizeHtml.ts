/**
 * HTML Sanitization Utility
 *
 * Provides safe HTML rendering using DOMPurify - a battle-tested XSS sanitizer.
 * This replaces the custom implementation for better security.
 *
 * Dependencies:
 * - Used by CompareView in LiveEditor.tsx for safe diff rendering
 * - Used anywhere HTML content needs to be rendered with dangerouslySetInnerHTML
 *
 * Security Notes:
 * - Uses DOMPurify for proven XSS protection
 * - Removes script, iframe, object, embed, form, input tags
 * - Strips event handlers (onclick, onerror, etc.)
 * - Removes javascript: and data: URLs
 */

import DOMPurify from 'dompurify';

// Allowed HTML tags for document content
const ALLOWED_TAGS = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'p', 'br', 'hr',
  'ul', 'ol', 'li',
  'strong', 'b', 'em', 'i', 'u', 's', 'strike',
  'span', 'div',
  'blockquote', 'pre', 'code',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'a', 'img',
  'sup', 'sub',
  'mark', 'small'
];

// Allowed attributes
const ALLOWED_ATTR = [
  'href', 'title', 'target', 'rel',
  'src', 'alt', 'width', 'height',
  'colspan', 'rowspan', 'scope',
  'class', 'style',
  'start', 'type'
];

// Forbidden tags (explicitly blocked for safety)
const FORBID_TAGS = ['script', 'style', 'iframe', 'form', 'input', 'object', 'embed'];

// Forbidden attributes (event handlers)
const FORBID_ATTR = ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur'];

/**
 * Sanitize HTML content for safe rendering
 *
 * Uses DOMPurify for proven XSS protection instead of custom regex parsing.
 *
 * @param html - Raw HTML string that may contain unsafe content
 * @returns Sanitized HTML string safe for dangerouslySetInnerHTML
 *
 * @example
 * ```tsx
 * <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(untrustedContent) }} />
 * ```
 */
export function sanitizeHtml(html: string): string {
  if (!html || typeof html !== 'string') {
    return '';
  }

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    ADD_ATTR: ['target'], // Allow target on links
    FORBID_TAGS,
    FORBID_ATTR,
    // Additional security options
    KEEP_CONTENT: true, // Keep text content when removing tags
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
  });
}

/**
 * Strip all HTML tags, leaving only text content
 *
 * Useful for plain text previews or search indexing.
 *
 * @param html - HTML string to strip
 * @returns Plain text without any HTML tags
 */
export function stripHtmlTags(html: string): string {
  if (!html || typeof html !== 'string') {
    return '';
  }

  // Use DOMPurify with no allowed tags to strip everything
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [],
    KEEP_CONTENT: true,
  }).trim();
}

/**
 * Convert plain text to safe HTML with line breaks
 *
 * @param text - Plain text to convert
 * @returns HTML with <br> tags for line breaks and escaped special chars
 */
export function textToHtml(text: string): string {
  if (!text || typeof text !== 'string') {
    return '';
  }

  // First escape HTML entities, then convert newlines to <br>
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

  return escaped.replace(/\n/g, '<br />');
}

/**
 * Sanitize HTML with custom configuration
 *
 * For cases where you need different allowed tags/attributes than the default.
 *
 * @param html - Raw HTML string
 * @param config - DOMPurify configuration options
 * @returns Sanitized HTML string
 */
export function sanitizeHtmlWithConfig(
  html: string,
  config: DOMPurify.Config
): string {
  if (!html || typeof html !== 'string') {
    return '';
  }

  return DOMPurify.sanitize(html, config);
}
