/**
 * Markdown to HTML Converter
 *
 * Converts markdown-formatted text to HTML for the rich text editor.
 * Supports tables, headers, lists, bold, italic, links, and more.
 * 
 * Dependencies:
 * - contentSanitizer.ts: For final cleanup of empty list items
 */

import { sanitizeListContent, sanitizeMarkdownLists } from './contentSanitizer';

export function markdownToHtml(markdown: string): string {
  if (!markdown) return '';

  // Pre-process: Sanitize markdown to remove blank lines between list items
  // This prevents empty bullets from being created during conversion
  let html = sanitizeMarkdownLists(markdown);

  // Process tables FIRST (before other conversions can interfere with | characters)
  html = processTables(html);

  // Convert headers (must be done before other conversions)
  // H3 headers (###)
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');

  // H2 headers (##)
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');

  // H1 headers (#)
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Convert bold (**text** or __text__) - do this before italic to handle overlap
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // Convert italic (*text* or _text_) - but not if it's a list marker
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)\*(?!\*)/g, '<em>$1</em>');
  html = html.replace(/(?<!_)_(?!_)(.+?)_(?!_)/g, '<em>$1</em>');

  // Convert horizontal rules BEFORE processing lists (---, ***, ___)
  // But NOT table separator lines (which contain |)
  html = html.replace(/^---$/gm, '<hr>');
  html = html.replace(/^\*\*\*$/gm, '<hr>');
  html = html.replace(/^___$/gm, '<hr>');

  // Convert blockquotes BEFORE lists
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

  // Convert code blocks BEFORE inline processing
  html = html.replace(/```(.+?)```/gs, '<pre><code>$1</code></pre>');

  // Convert inline code
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');

  // Convert links [text](url)
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>');

  // Process lists by finding consecutive list item blocks
  // This avoids the double-wrapping issue
  html = processLists(html);

  // Convert line breaks to paragraphs
  const paragraphs = html.split(/\n\n+/);
  html = paragraphs.map(para => {
    para = para.trim();

    // Don't wrap if already has block-level tags
    if (
      para.startsWith('<h1>') ||
      para.startsWith('<h2>') ||
      para.startsWith('<h3>') ||
      para.startsWith('<ul>') ||
      para.startsWith('<ol>') ||
      para.startsWith('<blockquote>') ||
      para.startsWith('<pre>') ||
      para.startsWith('<hr>') ||
      para.startsWith('<table')  // Don't wrap tables in paragraphs
    ) {
      return para;
    }

    // Wrap in paragraph tag
    return para ? `<p>${para}</p>` : '';
  }).join('\n');

  // Convert single newlines to <br> within paragraphs only
  html = html.replace(/(<p>)(.*?)(<\/p>)/gs, (_match, open, content, close) => {
    return open + content.replace(/\n/g, '<br>') + close;
  });

  // Post-process: Remove empty list items and empty lists
  // This catches any edge cases where empty bullets slip through
  // Run multiple passes to catch nested empty elements
  
  // Pass 1: Remove obviously empty list items
  html = html.replace(/<li>\s*<\/li>/g, '');           // Remove empty <li> elements
  html = html.replace(/<li><br\s*\/?><\/li>/g, '');    // Remove <li> with only <br>
  
  // Pass 2: Remove <li> with only whitespace or non-breaking spaces
  html = html.replace(/<li>[\s\u00A0]*<\/li>/g, '');   // Remove <li> with whitespace/nbsp only
  
  // Pass 3: Remove <li> containing only empty paragraphs
  html = html.replace(/<li><p>\s*<\/p><\/li>/g, '');   // Remove <li><p></p></li>
  html = html.replace(/<li>\s*<p>\s*<\/p>\s*<\/li>/g, ''); // Remove with surrounding whitespace
  html = html.replace(/<li><p>[\s\u00A0]*<\/p><\/li>/g, ''); // Remove with nbsp in paragraph
  
  // Pass 4: Remove <li> with only <br> inside paragraphs
  html = html.replace(/<li><p><br\s*\/?><\/p><\/li>/g, ''); // Remove <li><p><br></p></li>
  
  // Pass 5: Remove empty lists left behind after removing items
  html = html.replace(/<ul>\s*<\/ul>/g, '');           // Remove empty <ul> lists
  html = html.replace(/<ol>\s*<\/ol>/g, '');           // Remove empty <ol> lists
  html = html.replace(/<ul>\n*<\/ul>/g, '');           // Remove <ul> with only newlines
  html = html.replace(/<ol>\n*<\/ol>/g, '');           // Remove <ol> with only newlines

  // Final pass: Use comprehensive sanitizer to catch any remaining edge cases
  // This handles TipTap/ProseMirror artifacts and complex nested empty elements
  html = sanitizeListContent(html);

  return html;
}

/**
 * Process markdown tables and convert to HTML tables
 * Handles GFM-style tables with | delimiters
 */
function processTables(text: string): string {
  const lines = text.split('\n');
  const result: string[] = [];
  let tableLines: string[] = [];
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Check if line looks like a table row (contains | and has content)
    const isTableRow = /^\|.*\|$/.test(line) || /^[^|]+\|[^|]+/.test(line);
    // Check if line is a separator row (|---|---|) - allows :, -, |, and spaces
    const isSeparator = /^[\|\s]*[-:]+[\s\-:|]+[\|\s]*$/.test(line) && line.includes('-');

    if (isTableRow || (inTable && isSeparator)) {
      if (!inTable) {
        inTable = true;
        tableLines = [];
      }
      tableLines.push(line);
    } else {
      if (inTable && tableLines.length >= 2) {
        // End of table, convert it
        result.push(convertTableToHtml(tableLines));
        tableLines = [];
        inTable = false;
      } else if (inTable) {
        // Not enough lines for a valid table, output as-is
        result.push(...tableLines);
        tableLines = [];
        inTable = false;
      }
      result.push(lines[i]); // Keep original line (not trimmed)
    }
  }

  // Handle table at end of text
  if (inTable && tableLines.length >= 2) {
    result.push(convertTableToHtml(tableLines));
  } else if (tableLines.length > 0) {
    result.push(...tableLines);
  }

  return result.join('\n');
}

/**
 * Convert collected table lines to HTML table
 * Creates proper table structure for TipTap table extension
 */
function convertTableToHtml(tableLines: string[]): string {
  if (tableLines.length < 2) return tableLines.join('\n');

  // Parse cells from a row
  const parseRow = (row: string): string[] => {
    // Handle both |col1|col2| and col1|col2 formats
    let cells = row.split('|');
    
    // If row starts with |, first element is empty
    if (row.trim().startsWith('|')) {
      cells = cells.slice(1);
    }
    // If row ends with |, last element is empty
    if (row.trim().endsWith('|')) {
      cells = cells.slice(0, -1);
    }
    
    return cells.map(cell => cell.trim());
  };

  // Find separator row (the row with --- patterns)
  const separatorIndex = tableLines.findIndex(line => 
    /^[\|\s]*[-:]+[\s\-:|]+[\|\s]*$/.test(line.trim()) && line.includes('-')
  );
  
  if (separatorIndex === -1 || separatorIndex === 0) {
    // No separator found or separator is first line - not a valid table
    return tableLines.join('\n');
  }

  // Parse header row (everything before separator)
  const headerRow = parseRow(tableLines[0]);
  
  // Parse alignment from separator row
  const separatorCells = parseRow(tableLines[separatorIndex]);
  const alignments = separatorCells.map(cell => {
    const trimmed = cell.trim();
    if (trimmed.startsWith(':') && trimmed.endsWith(':')) return 'center';
    if (trimmed.endsWith(':')) return 'right';
    return 'left';
  });

  // Build HTML table with TipTap-compatible structure
  // Using proper semantic HTML: <thead> for headers, <tbody> for body rows
  let html = '<table class="tiptap-table">\n';
  
  // Header row - wrapped in <thead> for proper semantics and accessibility
  html += '  <thead>\n';
  html += '    <tr>\n';
  headerRow.forEach((cell, i) => {
    const align = alignments[i] || 'left';
    // Use th for header cells
    html += `      <th style="text-align: ${align}"><p>${cell}</p></th>\n`;
  });
  html += '    </tr>\n';
  html += '  </thead>\n';

  // Body rows (skip header and separator) - wrapped in <tbody>
  html += '  <tbody>\n';
  const bodyRows = tableLines.slice(separatorIndex + 1);
  bodyRows.forEach(row => {
    const cells = parseRow(row);
    if (cells.length === 0 || cells.every(c => !c)) return; // Skip empty rows
    
    html += '    <tr>\n';
    cells.forEach((cell, i) => {
      const align = alignments[i] || 'left';
      // Use td for body cells, wrap content in p for TipTap
      html += `      <td style="text-align: ${align}"><p>${cell}</p></td>\n`;
    });
    html += '    </tr>\n';
  });
  html += '  </tbody>\n';
  html += '</table>';
  
  return html;
}

/**
 * Process markdown lists and convert to HTML
 * Handles both ordered and unordered lists correctly
 * Properly handles blank lines within lists without creating empty items
 * Supports Unicode bullet characters: •, ◦, ▪, ▸
 */
function processLists(text: string): string {
  const lines = text.split('\n');
  const result: string[] = [];
  let currentList: { type: 'ul' | 'ol' | null; items: string[] } = { type: null, items: [] };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trim();

    // Check if line is an unordered list item
    // Supports: - * and Unicode bullets (•, ◦, ▪, ▸)
    // Allows optional leading whitespace (for indented lists like in Document Metadata)
    // Uses \s* after marker to handle bullets with or without space after marker
    const ulMatch = line.match(/^\s*[-*•◦▪▸]\s*(.*)$/);

    // Check if line is an ordered list item (1. 2. 3.)
    // Allows optional leading whitespace for indented ordered lists
    const olMatch = line.match(/^\s*\d+\.\s+(.*)$/);

    // Check if line is blank/empty OR is just a bullet marker without content
    // This prevents empty list items from being created
    // Extended to catch: empty lines, lone bullets, bullets with only whitespace, and whitespace-only lines
    const isBlankLine = trimmedLine === '' || 
      /^[-*•◦▪▸]\s*$/.test(trimmedLine) ||  // bullet with optional trailing whitespace only
      /^\s+$/.test(trimmedLine);              // line with only whitespace

    if (ulMatch && !isBlankLine) {
      // Unordered list item
      if (currentList.type === 'ol') {
        // Close previous ordered list
        result.push(wrapList(currentList));
        currentList = { type: null, items: [] };
      }

      if (currentList.type !== 'ul') {
        currentList = { type: 'ul', items: [] };
      }

      // Only add non-empty items
      // Strip non-breaking spaces (\u00A0) and normalize whitespace before checking
      const itemContent = ulMatch[1].trim().replace(/\u00A0/g, '').replace(/\s+/g, ' ').trim();
      if (itemContent && itemContent.length > 0) {
        currentList.items.push(ulMatch[1].trim()); // Push original trimmed content (preserve formatting)
      }

    } else if (olMatch) {
      // Ordered list item
      if (currentList.type === 'ul') {
        // Close previous unordered list
        result.push(wrapList(currentList));
        currentList = { type: null, items: [] };
      }

      if (currentList.type !== 'ol') {
        currentList = { type: 'ol', items: [] };
      }

      // Only add non-empty items
      // Strip non-breaking spaces (\u00A0) and normalize whitespace before checking
      const itemContent = olMatch[1].trim().replace(/\u00A0/g, '').replace(/\s+/g, ' ').trim();
      if (itemContent && itemContent.length > 0) {
        currentList.items.push(olMatch[1].trim()); // Push original trimmed content (preserve formatting)
      }

    } else if (isBlankLine && currentList.type) {
      // Blank line while in a list - skip it but don't close the list
      // This keeps list items together even with blank lines between them
      continue;

    } else {
      // Not a list item and not a blank line within a list
      if (currentList.type) {
        // Close any open list
        result.push(wrapList(currentList));
        currentList = { type: null, items: [] };
      }

      result.push(line);
    }
  }

  // Close any remaining list
  if (currentList.type) {
    result.push(wrapList(currentList));
  }

  return result.join('\n');
}

/**
 * Wrap list items in appropriate list tags
 * Filters out any empty items to prevent empty bullets
 * Strips non-breaking spaces and normalizes whitespace for validation
 */
function wrapList(list: { type: 'ul' | 'ol' | null; items: string[] }): string {
  if (!list.type) {
    return '';
  }

  // Filter out empty items - strip non-breaking spaces and check for actual content
  const validItems = list.items.filter(item => {
    if (!item) return false;
    // Normalize whitespace and remove non-breaking spaces for validation
    const normalized = item.trim().replace(/\u00A0/g, '').replace(/\s+/g, ' ').trim();
    return normalized.length > 0;
  });

  if (validItems.length === 0) {
    return '';
  }

  const tag = list.type;
  const listItems = validItems.map(item => `<li>${item}</li>`).join('\n');

  return `<${tag}>\n${listItems}\n</${tag}>`;
}

/**
 * Convert a record of markdown sections to HTML
 */
export function convertSectionsToHtml(sections: Record<string, string>): Record<string, string> {
  const htmlSections: Record<string, string> = {};

  for (const [key, markdown] of Object.entries(sections)) {
    htmlSections[key] = markdownToHtml(markdown);
  }

  return htmlSections;
}

/**
 * Alias for markdownToHtml for clearer import naming
 * Converts a single markdown string to HTML for the editor
 */
export const convertMarkdownToHtml = markdownToHtml;
