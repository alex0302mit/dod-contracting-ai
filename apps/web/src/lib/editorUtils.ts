/**
 * Local quality score breakdown (4 categories)
 * Used as fallback when API is not available or loading
 */
export interface LocalQualityBreakdown {
  readability: number;
  citations: number;
  compliance: number;
  length: number;
}

/**
 * Local quality score result
 * Simple client-side calculation as fallback
 */
export interface LocalQualityScore {
  total: number;
  breakdown: LocalQualityBreakdown;
}

/**
 * API quality score breakdown (5 categories from backend QualityAgent)
 * This is the comprehensive AI-powered analysis
 */
export interface APIQualityBreakdown {
  hallucination: {
    score: number;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
    issues: string[];
    suggestions: string[];
  };
  vague_language: {
    score: number;
    count: number;
    issues: string[];
    suggestions: string[];
  };
  citations: {
    score: number;
    valid: number;
    invalid: number;
    issues: string[];
    suggestions: string[];
  };
  compliance: {
    score: number;
    level: 'COMPLIANT' | 'MINOR ISSUES' | 'MAJOR ISSUES';
    issues: string[];
    suggestions: string[];
  };
  completeness: {
    score: number;
    word_count: number;
    paragraph_count: number;
    issues: string[];
    suggestions: string[];
  };
}

/**
 * Full API quality score result from backend QualityAgent
 */
export interface APIQualityScore {
  score: number;
  grade: string;
  breakdown: APIQualityBreakdown;
  issues: string[];
  suggestions: string[];
  weights: {
    hallucination: number;
    vague_language: number;
    citations: number;
    compliance: number;
    completeness: number;
  };
}

/**
 * Compute local quality score (fallback when API is not available)
 * 
 * This is a simple client-side calculation using 4 categories:
 * - Readability (30%): Based on sentence length
 * - Citations (20%): Density of [#] references
 * - Compliance (30%): FAR/DFARS presence, TBD placeholders
 * - Length (20%): Word count thresholds
 * 
 * For comprehensive AI-powered analysis with 5 categories, use the qualityApi.analyze() endpoint.
 */
export function computeQualityScore(text: string, _citations: any[]): LocalQualityScore {
  // Strip HTML tags before calculating word count to avoid counting markup
  const plainText = text.replace(/<[^>]*>/g, '');
  const wordCount = plainText.split(/\s+/).filter(Boolean).length;

  let lengthScore = 100;
  if (wordCount < 50) lengthScore = 40;
  else if (wordCount < 100) lengthScore = 70;
  else if (wordCount > 500) lengthScore = 85;

  const citationMatches = (plainText.match(/\[\d+\]/g) || []).length;
  let citationsScore = Math.min(100, (citationMatches / Math.max(wordCount / 100, 1)) * 50);

  let complianceScore = 80;
  if (!plainText.includes("FAR") && !plainText.includes("DFARS")) complianceScore -= 20;
  if (/TBD/i.test(plainText)) complianceScore -= 15;

  const sentences = plainText.split(/[.!?]+/).filter(Boolean);
  const avgSentenceLength = wordCount / Math.max(sentences.length, 1);
  let readabilityScore = 100;
  if (avgSentenceLength > 30) readabilityScore -= (avgSentenceLength - 30) * 2;
  readabilityScore = Math.max(40, readabilityScore);

  const breakdown: LocalQualityBreakdown = {
    readability: Math.round(readabilityScore),
    citations: Math.round(citationsScore),
    compliance: Math.round(complianceScore),
    length: Math.round(lengthScore),
  };

  const total = readabilityScore * 0.3 + citationsScore * 0.2 + complianceScore * 0.3 + lengthScore * 0.2;

  return { total: Math.round(total), breakdown };
}

/**
 * Issue fix type - supports both static replacements and AI-powered fixes
 * 
 * Static fix: Uses `apply` function for simple regex replacements
 * AI fix: Uses `requiresAI: true` to indicate async AI generation is needed
 * 
 * Dependencies:
 * - For AI fixes, the FixPreviewModal component handles the AI call
 * - occurrenceIndex is used to replace only a specific instance of a pattern
 */
export interface IssueFix {
  label: string;
  // Static fix function (for simple, predictable replacements)
  apply?: (text: string) => string;
  // Flag indicating this fix requires AI-powered contextual generation
  requiresAI?: boolean;
  // The pattern/text that needs to be replaced (used by AI to understand what to fix)
  pattern?: string;
  // Which occurrence of the pattern to replace (0-indexed)
  // When set, only the Nth occurrence will be replaced instead of all occurrences
  occurrenceIndex?: number;
}

/**
 * Document issue type - represents a single issue found in the document
 * 
 * Each issue has a unique ID and can optionally have a fix associated with it.
 * The context field provides surrounding text to help identify which specific
 * instance of an issue this refers to (e.g., which TBD placeholder).
 * 
 * Issue kinds:
 * - error: Critical issues like TBD placeholders (red)
 * - warning: Non-critical issues needing attention (amber)
 * - info: Informational suggestions (blue)
 * - compliance: FAR/DFARS compliance issues (purple)
 * - hallucination: Potentially unsourced or fabricated claims (orange)
 */
export interface DocumentIssue {
  id: string;
  kind: 'error' | 'warning' | 'info' | 'compliance' | 'hallucination';
  label: string;
  pattern?: string;
  // Surrounding text context for display - helps user identify which instance
  context?: string;
  fix?: IssueFix;
}

/**
 * Compute issues in the document text
 * 
 * This function analyzes the document for various issues including:
 * - TBD placeholders (each occurrence is a separate issue)
 * - Missing FAR/DFARS compliance references
 * - Vague instructions that need clarification
 * - Missing citations
 * 
 * For TBD placeholders, each occurrence is tracked individually with:
 * - Unique ID (tbd-0, tbd-1, etc.)
 * - Surrounding context for display
 * - occurrenceIndex for targeted replacement
 */
export function computeIssues(text: string): DocumentIssue[] {
  // Strip HTML tags before analyzing for issues
  const plainText = text.replace(/<[^>]*>/g, '');
  const issues: DocumentIssue[] = [];

  // Find ALL TBD occurrences and create individual issues for each
  // This allows users to fix each TBD with context-appropriate values
  const tbdRegex = /TBD/gi;
  let match;
  let tbdIndex = 0;
  
  while ((match = tbdRegex.exec(plainText)) !== null) {
    // Extract surrounding context (40 chars before and after for display)
    const contextStart = Math.max(0, match.index - 40);
    const contextEnd = Math.min(plainText.length, match.index + match[0].length + 40);
    let context = plainText.substring(contextStart, contextEnd).trim();
    
    // Add ellipsis if truncated to indicate more text exists
    if (contextStart > 0) context = '...' + context;
    if (contextEnd < plainText.length) context = context + '...';
    
    // Create a unique issue for each TBD occurrence
    issues.push({
      id: `tbd-${tbdIndex}`,
      kind: "error",
      // Show context in label so user knows which TBD this is
      label: `TBD placeholder #${tbdIndex + 1}: "${context}"`,
      pattern: "TBD",
      context: context,
      fix: {
        label: "Generate AI suggestion for this TBD",
        // Flag indicating this needs AI to generate contextual replacement
        requiresAI: true,
        // The pattern helps AI understand what to replace
        pattern: "TBD",
        // Store which occurrence to replace (0-indexed)
        // This ensures only THIS specific TBD gets replaced
        occurrenceIndex: tbdIndex,
      },
    });
    tbdIndex++;
  }

  // Compliance issues (purple indicators) - AI-powered fixes to add proper citations
  if (!plainText.match(/FAR\s+\d+/i)) {
    issues.push({
      id: "c1",
      kind: "compliance",
      label: "Missing FAR reference - Add FAR citation for procurement authority",
      pattern: "Government",
      fix: {
        label: "Add FAR citation with AI",
        requiresAI: true,
        pattern: "Government",
        occurrenceIndex: 0,
      },
    });
  }

  if (plainText.toLowerCase().includes("evaluation") && !plainText.match(/FAR\s+15\.3/i)) {
    issues.push({
      id: "c2",
      kind: "compliance",
      label: "Compliance: Evaluation procedures must cite FAR 15.304",
      pattern: "evaluation",
      fix: {
        label: "Add FAR 15.304 citation with AI",
        requiresAI: true,
        pattern: "evaluation",
        occurrenceIndex: 0,
      },
    });
  }

  if (plainText.toLowerCase().includes("cui") && !plainText.toLowerCase().includes("dfars")) {
    issues.push({
      id: "c3",
      kind: "compliance",
      label: "CUI handling requires DFARS 252.204-7012 reference",
      pattern: "CUI",
      fix: {
        label: "Add DFARS citation with AI",
        requiresAI: true,
        pattern: "CUI",
        occurrenceIndex: 0,
      },
    });
  }

  if (plainText.toLowerCase().includes("award") && !plainText.match(/FAR\s+15\./i)) {
    issues.push({
      id: "c4",
      kind: "compliance",
      label: "Award decisions must reference FAR Part 15 procedures",
      pattern: "award",
      fix: {
        label: "Add FAR Part 15 citation with AI",
        requiresAI: true,
        pattern: "award",
        occurrenceIndex: 0,
      },
    });
  }

  // Warning issues - simple static fix is appropriate here
  if (plainText.includes("instructions provided") && !plainText.includes("Section L")) {
    issues.push({
      id: "i2",
      kind: "warning",
      label: "Clarify which instructions (specify Section L)",
      pattern: "instructions provided",
      fix: {
        label: "Add Section L reference",
        // Static fix - predictable replacement
        apply: (t: string) => t.replace("instructions provided", "instructions in Section L"),
      },
    });
  }

  if (!plainText.match(/\[\d+\]/)) {
    issues.push({
      id: "i3",
      kind: "info",
      label: "Consider adding citations to support statements",
      pattern: "section",
    });
  }

  return issues;
}

export function renderInlineCitations(text: string, citations: any[], _onClick: (id: number) => void) {
  return text.replace(/\[(\d+)\]/g, (match, num) => {
    const id = parseInt(num);
    const exists = citations.some((c) => c.id === id);
    if (!exists) return match;
    return `<button onclick="window.citationClick(${id})" class="inline-flex items-center px-1.5 py-0.5 border border-blue-300 rounded text-[11px] bg-blue-50 hover:bg-blue-100 font-mono font-bold text-blue-700">[${id}]</button>`;
  });
}

/**
 * Highlight issues in the document HTML
 * 
 * Adds visual highlighting to detected issues like TBD placeholders
 * and vague instructions that need clarification.
 */
export function highlightIssues(html: string) {
  return html
    .replace(/TBD/gi, '<mark class="bg-amber-200 px-1 rounded">TBD</mark>')
    .replace(/instructions provided(?!\s+in\s+Section)/gi, '<mark class="bg-amber-200 px-1 rounded">instructions provided</mark>');
}

/**
 * Highlight fillable fields in the document HTML with DocuSign-style styling
 * 
 * Applies amber/yellow highlighting to detected fillable fields:
 * - Underscore fields (e.g., "Company Name: __")
 * - Bracket placeholders (e.g., "[Company Name]")
 * - TBD placeholders
 * 
 * The activeFieldId parameter adds special styling to the currently focused field
 * with a pulsing border effect.
 * 
 * @param html - The document HTML content
 * @param activeFieldId - Optional ID of the currently active field for special highlighting
 * @returns HTML with fillable fields highlighted
 */
export function highlightFillableFields(html: string, activeFieldId?: string): string {
  let result = html;
  
  // DocuSign-style base classes for fillable fields
  // Amber background with subtle border, cursor pointer to indicate clickable
  const baseClasses = 'fillable-field bg-amber-100 border-b-2 border-amber-400 px-1 py-0.5 rounded cursor-pointer hover:bg-amber-200 transition-colors';
  
  // Active field classes with pulsing animation
  const activeClasses = 'fillable-field-active bg-amber-200 border-2 border-amber-500 px-1 py-0.5 rounded animate-pulse shadow-md shadow-amber-200';
  
  // Pattern 1: Highlight underscore fields (e.g., "Company Name: __")
  // Wraps the entire "Label: __" in a span
  result = result.replace(
    /([A-Za-z][A-Za-z\s]*?):\s*(_{2,})/g,
    (match, label, underscores) => {
      const fieldId = `field-underscore-${label.toLowerCase().replace(/\s+/g, '-')}`;
      const classes = activeFieldId === fieldId ? activeClasses : baseClasses;
      return `<span class="${classes}" data-field-type="underscore" data-field-name="${label.trim()}">${label}: <span class="text-amber-600 font-mono">${underscores}</span></span>`;
    }
  );
  
  // Pattern 2: Highlight bracket placeholders (e.g., "[Company Name]")
  // Excludes citation patterns like [1], [2]
  result = result.replace(
    /\[([A-Za-z][A-Za-z\s]*?)\]/g,
    (match, content) => {
      // Skip if it's a citation reference (just numbers)
      if (/^\d+$/.test(content)) return match;
      
      const fieldId = `field-bracket-${content.toLowerCase().replace(/\s+/g, '-')}`;
      const classes = activeFieldId === fieldId ? activeClasses : baseClasses;
      return `<span class="${classes}" data-field-type="bracket" data-field-name="${content.trim()}">[${content}]</span>`;
    }
  );
  
  // Pattern 3: Highlight TBD placeholders
  // Uses a distinct styling to indicate it needs replacement
  result = result.replace(
    /TBD/gi,
    (match) => {
      const classes = activeFieldId === 'field-tbd' ? activeClasses : baseClasses;
      return `<span class="${classes}" data-field-type="tbd" data-field-name="TBD">TBD</span>`;
    }
  );
  
  return result;
}

/**
 * CSS styles for fillable field highlighting
 * 
 * These styles should be added to a global CSS file or style tag.
 * Includes the pulse animation for active fields.
 */
export const fillableFieldStyles = `
  /* Base fillable field styles */
  .fillable-field {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.2s ease;
  }
  
  .fillable-field:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(251, 191, 36, 0.3);
  }
  
  /* Active field with pulsing effect */
  .fillable-field-active {
    animation: fieldPulse 1.5s ease-in-out infinite;
  }
  
  @keyframes fieldPulse {
    0%, 100% {
      box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.4);
    }
    50% {
      box-shadow: 0 0 0 8px rgba(251, 191, 36, 0);
    }
  }
  
  /* Field type icons (added via pseudo-elements if needed) */
  .fillable-field[data-field-type="signature"]::before {
    content: "✍️";
    font-size: 0.75rem;
    margin-right: 0.25rem;
  }
  
  .fillable-field[data-field-type="date"]::before {
    content: "📅";
    font-size: 0.75rem;
    margin-right: 0.25rem;
  }
`;

export function autoImproveText(text: string, quality: any, issues: DocumentIssue[]) {
  let improved = text;

  // Only apply static fixes (not AI-powered ones which need user confirmation)
  issues.forEach((issue) => {
    if (issue.fix && issue.fix.apply && !issue.fix.requiresAI) {
      improved = issue.fix.apply(improved);
    }
  });

  if (quality.total < 85) {
    if (!improved.match(/\[\d+\]/)) {
      improved = improved.replace(/evaluation/i, "evaluation [1]");
    }

    improved = improved.replace(/may/gi, "will");
    improved = improved.replace(/should/gi, "shall");
  }

  return improved;
}

export function generateDiff(before: string, after: string) {
  const beforeLines = before.split("\n");
  const afterLines = after.split("\n");
  const maxLines = Math.max(beforeLines.length, afterLines.length);

  const diff: string[] = [];
  for (let i = 0; i < maxLines; i++) {
    const b = beforeLines[i] || "";
    const a = afterLines[i] || "";

    if (b === a) {
      diff.push(`  ${a}`);
    } else if (!b && a) {
      diff.push(`+ ${a}`);
    } else if (b && !a) {
      diff.push(`- ${b}`);
    } else {
      diff.push(`- ${b}`);
      diff.push(`+ ${a}`);
    }
  }

  return diff.join("\n");
}

/**
 * Structured diff line for inline diff display
 * 
 * Used by CompareView to render GitHub-style inline diffs with color highlighting.
 * Each line includes its type (for styling) and content (HTML to render).
 * 
 * Dependencies:
 * - Used by CompareView component in LiveEditor.tsx
 * - Rendered with dangerouslySetInnerHTML after sanitization
 */
export interface DiffLine {
  type: 'unchanged' | 'added' | 'removed';
  content: string;
  lineNumber?: { before?: number; after?: number };
}

/**
 * Generate structured inline diff for GitHub-style comparison view
 * 
 * Unlike generateDiff which returns a plain string, this returns structured data
 * that can be styled with different colors for added/removed content.
 * 
 * @param before - The original HTML content (from previous version)
 * @param after - The current HTML content
 * @returns Array of DiffLine objects for rendering with appropriate styling
 * 
 * Dependencies:
 * - Used by CompareView in LiveEditor.tsx
 * - Pairs with sanitizeHtml for safe rendering
 */
export function generateInlineDiff(before: string, after: string): DiffLine[] {
  // Strip HTML tags for comparison, but keep original for display
  const stripHtml = (html: string) => html.replace(/<[^>]*>/g, '');
  
  // Split by paragraphs/blocks for better semantic diffing
  // Match on block-level elements or double newlines
  const splitIntoBlocks = (html: string): string[] => {
    // Split on closing block tags or double newlines, keeping the delimiter
    const blocks = html
      .split(/(?<=<\/(?:p|h[1-6]|div|li|ul|ol|blockquote)>)|(?=<(?:p|h[1-6]|div|li|ul|ol|blockquote)[^>]*>)/g)
      .map(b => b.trim())
      .filter(b => b.length > 0);
    
    // If no blocks found, fall back to line-based splitting
    if (blocks.length <= 1) {
      return html.split('\n').filter(line => line.trim().length > 0);
    }
    return blocks;
  };

  const beforeBlocks = splitIntoBlocks(before);
  const afterBlocks = splitIntoBlocks(after);
  
  const diff: DiffLine[] = [];
  let beforeIdx = 0;
  let afterIdx = 0;
  let beforeLineNum = 1;
  let afterLineNum = 1;

  // Simple LCS-based diff for blocks
  while (beforeIdx < beforeBlocks.length || afterIdx < afterBlocks.length) {
    const beforeBlock = beforeBlocks[beforeIdx] || '';
    const afterBlock = afterBlocks[afterIdx] || '';
    
    // Compare stripped content for equality
    const beforeStripped = stripHtml(beforeBlock);
    const afterStripped = stripHtml(afterBlock);

    if (beforeIdx >= beforeBlocks.length) {
      // Only after content remains - all additions
      diff.push({
        type: 'added',
        content: afterBlock,
        lineNumber: { after: afterLineNum++ }
      });
      afterIdx++;
    } else if (afterIdx >= afterBlocks.length) {
      // Only before content remains - all removals
      diff.push({
        type: 'removed',
        content: beforeBlock,
        lineNumber: { before: beforeLineNum++ }
      });
      beforeIdx++;
    } else if (beforeStripped === afterStripped) {
      // Content matches - unchanged
      diff.push({
        type: 'unchanged',
        content: afterBlock, // Use after version (may have minor HTML differences)
        lineNumber: { before: beforeLineNum++, after: afterLineNum++ }
      });
      beforeIdx++;
      afterIdx++;
    } else {
      // Content differs - check if it's a modification or insertion/deletion
      // Look ahead to find if beforeBlock appears later in after
      const afterMatchIdx = afterBlocks.slice(afterIdx + 1).findIndex(
        b => stripHtml(b) === beforeStripped
      );
      const beforeMatchIdx = beforeBlocks.slice(beforeIdx + 1).findIndex(
        b => stripHtml(b) === afterStripped
      );

      if (beforeMatchIdx !== -1 && (afterMatchIdx === -1 || beforeMatchIdx <= afterMatchIdx)) {
        // Current after block is an addition
        diff.push({
          type: 'added',
          content: afterBlock,
          lineNumber: { after: afterLineNum++ }
        });
        afterIdx++;
      } else if (afterMatchIdx !== -1) {
        // Current before block is a deletion
        diff.push({
          type: 'removed',
          content: beforeBlock,
          lineNumber: { before: beforeLineNum++ }
        });
        beforeIdx++;
      } else {
        // Both changed - show as removal then addition
        diff.push({
          type: 'removed',
          content: beforeBlock,
          lineNumber: { before: beforeLineNum++ }
        });
        diff.push({
          type: 'added',
          content: afterBlock,
          lineNumber: { after: afterLineNum++ }
        });
        beforeIdx++;
        afterIdx++;
      }
    }
  }

  return diff;
}

/**
 * Fillable field type for DocuSign-style field navigation
 * 
 * Represents a single fillable field detected in the document.
 * Fields can be text inputs, signature pads, or date pickers based on context.
 * 
 * Dependencies:
 * - Used by FieldNavigator component for guided field filling
 * - type determines which input component to render
 * - Context fields provide user-friendly hints about what to enter
 */
export interface FillableField {
  // Unique identifier for the field (e.g., "field-0", "field-1")
  id: string;
  // Human-readable name extracted from context (e.g., "Company Name", "Date")
  name: string;
  // Input type determines which component to render
  type: 'text' | 'signature' | 'date';
  // The original pattern/text that was detected (e.g., "__", "[Company Name]", "TBD")
  pattern: string;
  // Full match including label context (e.g., "Company Name: __")
  fullMatch: string;
  // Character position in the document for scrolling
  position: number;
  // Which occurrence of this pattern (0-indexed) for targeted replacement
  occurrenceIndex: number;
  // Current value if already filled
  value?: string;
  
  // === Context Enhancement Fields ===
  // Text appearing before the field (50 chars) for context preview
  contextBefore: string;
  // Text appearing after the field (50 chars) for context preview
  contextAfter: string;
  // Detected section/heading name where the field is located
  section?: string;
  // Expected value type hint (e.g., "company name", "dollar amount", "date")
  expectedType?: string;
  // User-friendly hint about what value to enter
  hint?: string;
}

/**
 * Infer the field type based on the field name/context
 * 
 * Uses keyword matching to determine if a field should be:
 * - signature: for fields containing "signature", "sign", "authorized"
 * - date: for fields containing "date", "dated"
 * - text: default for all other fields
 */
function inferFieldType(fieldName: string): 'text' | 'signature' | 'date' {
  const lowerName = fieldName.toLowerCase();
  
  // Signature field detection keywords
  if (lowerName.includes('signature') || 
      lowerName.includes('sign') || 
      lowerName.includes('authorized by')) {
    return 'signature';
  }
  
  // Date field detection keywords
  if (lowerName.includes('date') || 
      lowerName.includes('dated') ||
      lowerName.includes('effective')) {
    return 'date';
  }
  
  // Default to text input
  return 'text';
}

/**
 * Infer the expected value type and generate a user-friendly hint
 * 
 * Analyzes the field name and surrounding context to determine what
 * kind of value the user should enter, providing helpful guidance.
 * 
 * @param fieldName - The extracted field name
 * @param context - Surrounding text for additional context
 * @returns Object with expectedType and hint string
 */
function inferExpectedTypeAndHint(fieldName: string, context: string): { expectedType: string; hint: string } {
  const lowerName = fieldName.toLowerCase();
  const lowerContext = context.toLowerCase();
  
  // Signature fields
  if (lowerName.includes('signature') || lowerName.includes('sign')) {
    return { 
      expectedType: 'signature', 
      hint: 'Enter your signature (draw or type your name)' 
    };
  }
  
  // Date fields
  if (lowerName.includes('date') || lowerName.includes('dated') || lowerName.includes('effective')) {
    return { 
      expectedType: 'date', 
      hint: 'Select a date (e.g., November 28, 2025)' 
    };
  }
  
  // Company/Organization name
  if (lowerName.includes('company') || lowerName.includes('organization') || 
      lowerName.includes('contractor') || lowerName.includes('vendor') ||
      lowerName.includes('offeror') || lowerName.includes('firm')) {
    return { 
      expectedType: 'company name', 
      hint: 'Enter the company or organization name' 
    };
  }
  
  // Person name
  if (lowerName.includes('name') || lowerName.includes('printed') || 
      lowerName.includes('representative') || lowerName.includes('officer') ||
      lowerName.includes('contact')) {
    return { 
      expectedType: 'person name', 
      hint: 'Enter the full name of the person' 
    };
  }
  
  // Title/Position
  if (lowerName.includes('title') || lowerName.includes('position') || lowerName.includes('role')) {
    return { 
      expectedType: 'job title', 
      hint: 'Enter the job title or position' 
    };
  }
  
  // Dollar amounts
  if (lowerName.includes('amount') || lowerName.includes('price') || 
      lowerName.includes('cost') || lowerName.includes('value') ||
      lowerName.includes('total') || lowerContext.includes('$')) {
    return { 
      expectedType: 'dollar amount', 
      hint: 'Enter the dollar amount (e.g., $50,000.00)' 
    };
  }
  
  // Quantities/Numbers
  if (lowerName.includes('quantity') || lowerName.includes('number') || 
      lowerName.includes('count') || lowerName.includes('qty')) {
    return { 
      expectedType: 'number', 
      hint: 'Enter a numeric value' 
    };
  }
  
  // Address
  if (lowerName.includes('address') || lowerName.includes('location') || lowerName.includes('street')) {
    return { 
      expectedType: 'address', 
      hint: 'Enter the full address' 
    };
  }
  
  // Phone
  if (lowerName.includes('phone') || lowerName.includes('telephone') || lowerName.includes('fax')) {
    return { 
      expectedType: 'phone number', 
      hint: 'Enter the phone number (e.g., (555) 123-4567)' 
    };
  }
  
  // Email
  if (lowerName.includes('email') || lowerName.includes('e-mail')) {
    return { 
      expectedType: 'email', 
      hint: 'Enter the email address' 
    };
  }
  
  // Contract/Solicitation numbers
  if (lowerName.includes('solicitation') || lowerName.includes('contract') || 
      lowerName.includes('award') || lowerName.includes('requisition')) {
    return { 
      expectedType: 'reference number', 
      hint: 'Enter the reference or contract number' 
    };
  }
  
  // Period/Duration
  if (lowerName.includes('period') || lowerName.includes('duration') || 
      lowerName.includes('term') || lowerName.includes('days') ||
      lowerName.includes('months') || lowerName.includes('years')) {
    return { 
      expectedType: 'time period', 
      hint: 'Enter the time period or duration' 
    };
  }
  
  // Default - generic text
  return { 
    expectedType: 'text', 
    hint: `Enter the ${fieldName.toLowerCase() || 'value'}` 
  };
}

/**
 * Detect the section/heading where a field is located
 * 
 * Looks backward from the field position to find the nearest heading
 * using common markdown/document patterns.
 * 
 * @param plainText - The document text
 * @param position - Character position of the field
 * @returns Section name or undefined if not found
 */
function detectSection(plainText: string, position: number): string | undefined {
  // Get text before the field position
  const textBefore = plainText.substring(0, position);
  
  // Pattern 1: Markdown headings (# Heading, ## Heading)
  const markdownHeading = textBefore.match(/#+\s+([^\n]+)\n[^#]*$/);
  if (markdownHeading) {
    return markdownHeading[1].trim();
  }
  
  // Pattern 2: Bold headings (**Heading**)
  const boldHeading = textBefore.match(/\*\*([^*]+)\*\*[^*]*$/);
  if (boldHeading) {
    return boldHeading[1].trim();
  }
  
  // Pattern 3: Section labels (Section X:, Part X:, SECTION B, etc.)
  const sectionLabel = textBefore.match(/(?:Section|Part|Article|SECTION|PART)\s+[A-Z0-9]+[:\s]+([^\n]+)\n[^\n]*$/i);
  if (sectionLabel) {
    return sectionLabel[1].trim();
  }
  
  // Pattern 4: Numbered sections (1.0 Title, 1.1 Subtitle)
  const numberedSection = textBefore.match(/\d+\.\d*\s+([A-Z][^\n]+)\n[^\d]*$/);
  if (numberedSection) {
    return numberedSection[1].trim();
  }
  
  // Pattern 5: All-caps heading on its own line
  const capsHeading = textBefore.match(/\n([A-Z][A-Z\s]{3,}[A-Z])\n[^A-Z]*$/);
  if (capsHeading) {
    return capsHeading[1].trim();
  }
  
  return undefined;
}

/**
 * Extract a human-readable field name from the matched text
 * 
 * Enhanced version with multiple pattern detection strategies:
 * - Colon-based labels: "Company Name: TBD"
 * - Table cell context: looks for table headers
 * - List item labels: "1. Field Name: TBD"
 * - Surrounding text analysis for unlabeled fields
 * 
 * @param match - The matched pattern text
 * @param plainText - Full document text for context extraction
 * @param position - Character position of the match
 * @returns Human-readable field name
 */
function extractFieldName(match: string, plainText: string, position: number): string {
  // For underscore patterns like "Company Name: __"
  const underscoreMatch = match.match(/^(.+?):\s*_+$/);
  if (underscoreMatch) {
    return underscoreMatch[1].trim();
  }
  
  // For bracket patterns like "[Company Name]"
  const bracketMatch = match.match(/^\[([^\]]+)\]$/);
  if (bracketMatch) {
    return bracketMatch[1].trim();
  }
  
  // For TBD, use enhanced context extraction
  if (match.toUpperCase() === 'TBD') {
    // Get surrounding context
    const contextStart = Math.max(0, position - 100);
    const contextEnd = Math.min(plainText.length, position + 50);
    const context = plainText.substring(contextStart, contextEnd);
    
    // Pattern 1: Label immediately before TBD (e.g., "Company Name: TBD")
    const colonLabel = context.match(/([A-Za-z][A-Za-z\s]+):\s*TBD/i);
    if (colonLabel) {
      return colonLabel[1].trim();
    }
    
    // Pattern 2: Table cell - look for pipe characters (| Label | TBD |)
    const tableMatch = context.match(/\|\s*([^|]+?)\s*\|\s*TBD/i);
    if (tableMatch) {
      const cellContent = tableMatch[1].trim();
      // Skip if it's just dashes (table separator)
      if (!/^-+$/.test(cellContent)) {
        return cellContent;
      }
    }
    
    // Pattern 3: List item with label (e.g., "1. Field Name: TBD" or "- Field: TBD")
    const listMatch = context.match(/(?:\d+\.|[-•])\s*([A-Za-z][A-Za-z\s]+?):\s*TBD/i);
    if (listMatch) {
      return listMatch[1].trim();
    }
    
    // Pattern 4: Parenthetical context (e.g., "TBD (enter company name)")
    const parenMatch = context.match(/TBD\s*\(([^)]+)\)/i);
    if (parenMatch) {
      return parenMatch[1].trim();
    }
    
    // Pattern 5: Look for the nearest label-like word before TBD
    const nearbyLabel = context.match(/([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?::|=|is|are)?\s*TBD/);
    if (nearbyLabel) {
      return nearbyLabel[1].trim();
    }
    
    // Pattern 6: If in a table row, try to find what column this is
    // Look for common document field patterns in the surrounding area
    const docPatterns = [
      { pattern: /company|contractor|vendor|offeror/i, name: 'Company Name' },
      { pattern: /signature/i, name: 'Signature' },
      { pattern: /date/i, name: 'Date' },
      { pattern: /title|position/i, name: 'Title' },
      { pattern: /name|printed/i, name: 'Name' },
      { pattern: /amount|price|cost|total/i, name: 'Amount' },
      { pattern: /address|location/i, name: 'Address' },
      { pattern: /phone|telephone/i, name: 'Phone' },
      { pattern: /email/i, name: 'Email' },
      { pattern: /period|duration/i, name: 'Period' },
      { pattern: /number|no\./i, name: 'Number' },
    ];
    
    for (const { pattern, name } of docPatterns) {
      if (pattern.test(context)) {
        return name;
      }
    }
    
    // Fallback: return a position-based name
    return 'Field';
  }
  
  return match;
}

/**
 * Extract context before and after a field position
 * 
 * @param plainText - The document text
 * @param position - Character position of the field
 * @param matchLength - Length of the matched pattern
 * @returns Object with contextBefore and contextAfter strings
 */
function extractContext(plainText: string, position: number, matchLength: number): { contextBefore: string; contextAfter: string } {
  // Get 50 characters before the field
  const beforeStart = Math.max(0, position - 50);
  let contextBefore = plainText.substring(beforeStart, position).trim();
  if (beforeStart > 0) {
    contextBefore = '...' + contextBefore;
  }
  
  // Get 50 characters after the field
  const afterEnd = Math.min(plainText.length, position + matchLength + 50);
  let contextAfter = plainText.substring(position + matchLength, afterEnd).trim();
  if (afterEnd < plainText.length) {
    contextAfter = contextAfter + '...';
  }
  
  return { contextBefore, contextAfter };
}

/**
 * Detect all fillable fields in the document
 * 
 * Scans document text for three types of fillable fields:
 * 1. Underscore fields: "Label: __" or "Label: ___"
 * 2. Bracket placeholders: "[Field Name]" or "[Enter Value]"
 * 3. TBD placeholders: "TBD" (already detected by computeIssues)
 * 
 * Each field is assigned a type (text/signature/date) based on its name,
 * and includes context information for user-friendly display.
 * 
 * @param text - The document text (can include HTML which will be stripped)
 * @returns Array of FillableField objects sorted by position
 */
export function detectFillableFields(text: string): FillableField[] {
  // Strip HTML tags for consistent pattern matching
  const plainText = text.replace(/<[^>]*>/g, '');
  const fields: FillableField[] = [];
  let fieldIndex = 0;
  
  // Pattern 1: Underscore fields (e.g., "Company Name: __", "Date: ___")
  // Matches: Label followed by colon and 2+ underscores
  const underscoreRegex = /([A-Za-z][A-Za-z\s]*?):\s*_{2,}/g;
  let match;
  
  while ((match = underscoreRegex.exec(plainText)) !== null) {
    const fieldName = match[1].trim();
    const fieldType = inferFieldType(fieldName);
    const { contextBefore, contextAfter } = extractContext(plainText, match.index, match[0].length);
    const section = detectSection(plainText, match.index);
    const { expectedType, hint } = inferExpectedTypeAndHint(fieldName, contextBefore + contextAfter);
    
    fields.push({
      id: `field-${fieldIndex}`,
      name: fieldName,
      type: fieldType,
      pattern: match[0].match(/_+/)?.[0] || '__', // Just the underscores
      fullMatch: match[0],
      position: match.index,
      occurrenceIndex: fieldIndex,
      contextBefore,
      contextAfter,
      section,
      expectedType,
      hint,
    });
    fieldIndex++;
  }
  
  // Pattern 2: Bracket placeholders (e.g., "[Company Name]", "[Enter Date]")
  // Excludes citation patterns like [1], [2] which are numbers only
  const bracketRegex = /\[([A-Za-z][A-Za-z\s]*?)\]/g;
  
  while ((match = bracketRegex.exec(plainText)) !== null) {
    // Skip if it's a citation reference (just numbers)
    if (/^\d+$/.test(match[1])) continue;
    
    const fieldName = match[1].trim();
    const fieldType = inferFieldType(fieldName);
    const { contextBefore, contextAfter } = extractContext(plainText, match.index, match[0].length);
    const section = detectSection(plainText, match.index);
    const { expectedType, hint } = inferExpectedTypeAndHint(fieldName, contextBefore + contextAfter);
    
    fields.push({
      id: `field-${fieldIndex}`,
      name: fieldName,
      type: fieldType,
      pattern: match[0],
      fullMatch: match[0],
      position: match.index,
      occurrenceIndex: fieldIndex,
      contextBefore,
      contextAfter,
      section,
      expectedType,
      hint,
    });
    fieldIndex++;
  }
  
  // Pattern 3: TBD placeholders with context
  // Note: We include these for the field navigator even though they're also in issues
  const tbdRegex = /TBD/gi;
  let tbdOccurrence = 0;
  
  while ((match = tbdRegex.exec(plainText)) !== null) {
    // Extract surrounding context for display
    const { contextBefore, contextAfter } = extractContext(plainText, match.index, match[0].length);
    const fullContext = contextBefore + match[0] + contextAfter;
    
    // Try to extract a meaningful name from context using enhanced extraction
    const fieldName = extractFieldName('TBD', plainText, match.index);
    const fieldType = inferFieldType(fullContext);
    const section = detectSection(plainText, match.index);
    const { expectedType, hint } = inferExpectedTypeAndHint(fieldName, fullContext);
    
    // Use extracted name, or create a more descriptive fallback
    let displayName = fieldName;
    if (fieldName === 'Field') {
      // Try to create a better name from context
      const shortContext = contextBefore.slice(-30).trim();
      if (shortContext) {
        // Extract last few meaningful words
        const words = shortContext.split(/\s+/).slice(-3).join(' ');
        displayName = words || `Field ${tbdOccurrence + 1}`;
      } else {
        displayName = `Field ${tbdOccurrence + 1}`;
      }
    }
    
    fields.push({
      id: `field-${fieldIndex}`,
      name: displayName,
      type: fieldType,
      pattern: 'TBD',
      fullMatch: match[0],
      position: match.index,
      occurrenceIndex: tbdOccurrence,
      contextBefore,
      contextAfter,
      section,
      expectedType,
      hint,
    });
    fieldIndex++;
    tbdOccurrence++;
  }
  
  // Priority-based sorting: signatures first, then dates, then other fields, TBD last
  // Within each priority group, sort by document position
  const getFieldPriority = (field: FillableField): number => {
    // Signature fields - highest priority (fill first)
    if (field.type === 'signature') return 1;
    // Date fields - second priority
    if (field.type === 'date') return 2;
    // TBD placeholders - lowest priority (fill last)
    if (field.pattern === 'TBD') return 99;
    // All other text fields - normal priority
    return 3;
  };

  fields.sort((a, b) => {
    const priorityA = getFieldPriority(a);
    const priorityB = getFieldPriority(b);

    // First sort by priority
    if (priorityA !== priorityB) {
      return priorityA - priorityB;
    }

    // Within same priority, sort by position in document
    return a.position - b.position;
  });

  // Re-index after sorting to ensure sequential IDs
  fields.forEach((field, index) => {
    field.id = `field-${index}`;
  });

  return fields;
}

/**
 * Replace a specific fillable field with a value
 * 
 * Uses the field's pattern and occurrence index to replace only
 * the targeted field instance in the document.
 * 
 * @param text - The document text
 * @param field - The field to replace
 * @param value - The new value to insert
 * @returns Updated document text
 */
export function replaceFillableField(text: string, field: FillableField, value: string): string {
  // For underscore patterns, we need to replace the full match (including label)
  // but only insert the value portion
  if (field.pattern.match(/^_+$/)) {
    // Replace "Label: __" with "Label: value"
    const labelPart = field.fullMatch.replace(/_+$/, '');
    return text.replace(field.fullMatch, labelPart + value);
  }
  
  // For bracket patterns and TBD, replace the pattern directly
  let count = 0;
  const targetIndex = field.occurrenceIndex;
  
  // Create a regex from the pattern (escape special chars for brackets)
  const escapedPattern = field.pattern.replace(/[[\]]/g, '\\$&');
  const regex = new RegExp(escapedPattern, 'gi');
  
  return text.replace(regex, (match) => {
    if (count === targetIndex) {
      count++;
      return value;
    }
    count++;
    return match;
  });
}
