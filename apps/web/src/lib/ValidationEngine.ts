/**
 * Validation Engine
 *
 * Core validation system for DoD contracting documents
 * Provides real-time validation with auto-fix suggestions
 */

export type ValidationSeverity = 'error' | 'warning' | 'info';

export interface ValidationIssue {
  id: string;
  ruleId: string;
  severity: ValidationSeverity;
  message: string;
  description?: string;
  location?: {
    from: number;
    to: number;
    text: string;
  };
  autoFix?: {
    label: string;
    apply: (content: string) => string;
  };
  category: 'compliance' | 'format' | 'content' | 'structure' | 'style';
}

export interface ValidationRule {
  id: string;
  name: string;
  description: string;
  category: 'compliance' | 'format' | 'content' | 'structure' | 'style';
  severity: ValidationSeverity;
  appliesTo?: string[]; // Section names this rule applies to (empty = all sections)
  validate: (content: string, sectionName?: string) => ValidationIssue[];
}

export interface ValidationResult {
  isValid: boolean;
  score: number; // 0-100
  issues: ValidationIssue[];
  errorCount: number;
  warningCount: number;
  infoCount: number;
}

/**
 * Validation Engine - runs validation rules on document content
 */
export class ValidationEngine {
  private rules: Map<string, ValidationRule> = new Map();

  /**
   * Register a validation rule
   */
  registerRule(rule: ValidationRule): void {
    this.rules.set(rule.id, rule);
  }

  /**
   * Register multiple validation rules
   */
  registerRules(rules: ValidationRule[]): void {
    rules.forEach((rule) => this.registerRule(rule));
  }

  /**
   * Get all registered rules
   */
  getRules(): ValidationRule[] {
    return Array.from(this.rules.values());
  }

  /**
   * Get rules applicable to a specific section
   */
  getRulesForSection(sectionName: string): ValidationRule[] {
    return this.getRules().filter(
      (rule) => !rule.appliesTo || rule.appliesTo.length === 0 || rule.appliesTo.includes(sectionName)
    );
  }

  /**
   * Validate content against all applicable rules
   */
  validate(content: string, sectionName?: string): ValidationResult {
    const applicableRules = sectionName ? this.getRulesForSection(sectionName) : this.getRules();

    const allIssues: ValidationIssue[] = [];

    // Run each rule
    applicableRules.forEach((rule) => {
      try {
        const issues = rule.validate(content, sectionName);
        allIssues.push(...issues);
      } catch (error) {
        console.error(`Error running validation rule ${rule.id}:`, error);
      }
    });

    // Calculate counts
    const errorCount = allIssues.filter((i) => i.severity === 'error').length;
    const warningCount = allIssues.filter((i) => i.severity === 'warning').length;
    const infoCount = allIssues.filter((i) => i.severity === 'info').length;

    // Calculate validation score
    const score = this.calculateScore(errorCount, warningCount, infoCount);

    return {
      isValid: errorCount === 0,
      score,
      issues: allIssues,
      errorCount,
      warningCount,
      infoCount,
    };
  }

  /**
   * Calculate validation score (0-100)
   */
  private calculateScore(errors: number, warnings: number, infos: number): number {
    // Start with 100
    let score = 100;

    // Deduct points for issues
    score -= errors * 10; // Each error: -10 points
    score -= warnings * 3; // Each warning: -3 points
    score -= infos * 1; // Each info: -1 point

    // Clamp to 0-100
    return Math.max(0, Math.min(100, score));
  }

  /**
   * Get auto-fixable issues
   */
  getFixableIssues(issues: ValidationIssue[]): ValidationIssue[] {
    return issues.filter((issue) => issue.autoFix !== undefined);
  }

  /**
   * Apply all auto-fixes to content
   */
  applyAllFixes(content: string, issues: ValidationIssue[]): string {
    let fixedContent = content;

    // Apply fixes in order
    const fixableIssues = this.getFixableIssues(issues);
    fixableIssues.forEach((issue) => {
      if (issue.autoFix) {
        fixedContent = issue.autoFix.apply(fixedContent);
      }
    });

    return fixedContent;
  }
}

/**
 * Create a validation issue
 */
export function createValidationIssue(
  ruleId: string,
  severity: ValidationSeverity,
  message: string,
  options?: {
    description?: string;
    location?: { from: number; to: number; text: string };
    autoFix?: { label: string; apply: (content: string) => string };
    category?: ValidationIssue['category'];
  }
): ValidationIssue {
  return {
    id: `${ruleId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    ruleId,
    severity,
    message,
    description: options?.description,
    location: options?.location,
    autoFix: options?.autoFix,
    category: options?.category || 'content',
  };
}

/**
 * Helper to strip HTML tags for text analysis
 */
export function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

/**
 * Helper to count words in text
 */
export function countWords(text: string): number {
  const stripped = stripHtml(text);
  return stripped.split(/\s+/).filter(Boolean).length;
}

/**
 * Helper to find pattern matches in text
 */
export function findMatches(
  text: string,
  pattern: RegExp
): Array<{ text: string; index: number; length: number }> {
  const matches: Array<{ text: string; index: number; length: number }> = [];
  const stripped = stripHtml(text);

  let match;
  while ((match = pattern.exec(stripped)) !== null) {
    matches.push({
      text: match[0],
      index: match.index,
      length: match[0].length,
    });
  }

  return matches;
}
