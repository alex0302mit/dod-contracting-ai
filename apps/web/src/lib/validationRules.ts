/**
 * Validation Rules for DoD Contracting Documents
 *
 * Comprehensive validation rules for RFP responses, proposals, and contracting documents
 */

import {
  ValidationRule,
  createValidationIssue,
  stripHtml,
  countWords,
  findMatches,
} from './ValidationEngine';

/**
 * All validation rules for DoD contracting documents
 */
export const validationRules: ValidationRule[] = [
  // ==================== COMPLIANCE RULES ====================

  {
    id: 'no-tbd-in-final',
    name: 'No TBD in Final Sections',
    description: 'Final proposal sections should not contain "TBD" or "To Be Determined"',
    category: 'compliance',
    severity: 'error',
    appliesTo: [], // Applies to all sections
    validate: (content) => {
      const text = stripHtml(content);
      const tbdPattern = /\b(TBD|tbd|to be determined|to be defined|pending)\b/gi;
      const matches = findMatches(content, tbdPattern);

      return matches.map((match) =>
        createValidationIssue('no-tbd-in-final', 'error', 'TBD or placeholder text found', {
          description: 'Replace placeholder text with specific information',
          location: {
            from: match.index,
            to: match.index + match.length,
            text: match.text,
          },
          category: 'compliance',
          autoFix: {
            label: 'Remove TBD',
            apply: (content) => content.replace(tbdPattern, '[SPECIFY]'),
          },
        })
      );
    },
  },

  {
    id: 'far-citation-format',
    name: 'FAR Citation Format',
    description: 'FAR citations should follow proper format (FAR X.XXX or DFARS XXX.XXX)',
    category: 'compliance',
    severity: 'warning',
    validate: (content) => {
      const text = stripHtml(content);
      // Find potential FAR references that don't match proper format
      const improperPattern = /\b(FAR|DFARS)\s+(?!(\d+\.\d+))\w+/gi;
      const matches = findMatches(content, improperPattern);

      return matches.map((match) =>
        createValidationIssue('far-citation-format', 'warning', 'Improper FAR citation format', {
          description: 'FAR citations should use format "FAR X.XXX" or "DFARS XXX.XXX"',
          location: {
            from: match.index,
            to: match.index + match.length,
            text: match.text,
          },
          category: 'compliance',
        })
      );
    },
  },

  {
    id: 'required-citations',
    name: 'Required Citations',
    description: 'Compliance statements should include citations to regulations',
    category: 'compliance',
    severity: 'warning',
    validate: (content) => {
      const text = stripHtml(content);
      const issues = [];

      // Look for compliance language without citations
      const compliancePattern = /\b(shall|must|required to|in accordance with)\b[^.]{20,200}[.]/gi;
      const citationPattern = /\b(FAR|DFARS|MIL-STD|DoD|NIST)\s+[\d.-]+/i;

      let match;
      while ((match = compliancePattern.exec(text)) !== null) {
        const sentence = match[0];
        if (!citationPattern.test(sentence)) {
          issues.push(
            createValidationIssue(
              'required-citations',
              'warning',
              'Compliance statement missing citation',
              {
                description: 'Add reference to applicable regulation (FAR, DFARS, etc.)',
                location: {
                  from: match.index,
                  to: match.index + sentence.length,
                  text: sentence.substring(0, 50) + '...',
                },
                category: 'compliance',
              }
            )
          );
        }
      }

      return issues;
    },
  },

  // ==================== FORMAT RULES ====================

  {
    id: 'section-length',
    name: 'Section Length',
    description: 'Sections should meet minimum word count requirements',
    category: 'format',
    severity: 'warning',
    validate: (content, sectionName) => {
      const wordCount = countWords(content);
      const minWords = 50; // Configurable minimum

      if (wordCount < minWords && wordCount > 0) {
        return [
          createValidationIssue('section-length', 'warning', 'Section may be too short', {
            description: `This section has ${wordCount} words. Consider expanding for completeness.`,
            category: 'format',
          }),
        ];
      }

      return [];
    },
  },

  {
    id: 'paragraph-length',
    name: 'Paragraph Length',
    description: 'Paragraphs should not be excessively long',
    category: 'format',
    severity: 'info',
    validate: (content) => {
      const text = stripHtml(content);
      const paragraphs = text.split(/\n\n+/);
      const issues = [];

      paragraphs.forEach((para, index) => {
        const words = para.split(/\s+/).filter(Boolean).length;
        if (words > 200) {
          issues.push(
            createValidationIssue('paragraph-length', 'info', 'Long paragraph detected', {
              description: `Paragraph ${index + 1} has ${words} words. Consider breaking into smaller paragraphs for readability.`,
              category: 'format',
            })
          );
        }
      });

      return issues;
    },
  },

  {
    id: 'consistent-heading-format',
    name: 'Consistent Heading Format',
    description: 'Headings should follow consistent capitalization',
    category: 'format',
    severity: 'info',
    validate: (content) => {
      const headingPattern = /<h[123]>(.*?)<\/h[123]>/gi;
      const headings: string[] = [];
      let match;

      while ((match = headingPattern.exec(content)) !== null) {
        headings.push(match[1]);
      }

      if (headings.length < 2) return [];

      // Check if headings are consistent (all title case or all sentence case)
      const titleCaseCount = headings.filter((h) => /^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$/.test(h)).length;
      const sentenceCaseCount = headings.filter((h) => /^[A-Z][a-z]/.test(h)).length;

      if (titleCaseCount > 0 && sentenceCaseCount > 0 && titleCaseCount !== headings.length) {
        return [
          createValidationIssue(
            'consistent-heading-format',
            'info',
            'Inconsistent heading capitalization',
            {
              description:
                'Headings use mixed capitalization styles. Use either Title Case or Sentence case consistently.',
              category: 'format',
            }
          ),
        ];
      }

      return [];
    },
  },

  // ==================== CONTENT RULES ====================

  {
    id: 'passive-voice',
    name: 'Passive Voice Detection',
    description: 'Minimize use of passive voice for clarity',
    category: 'style',
    severity: 'info',
    validate: (content) => {
      const text = stripHtml(content);
      const passivePattern = /\b(is|are|was|were|be|been|being)\s+\w+(ed|en)\b/gi;
      const matches = findMatches(content, passivePattern);

      // Only report if there are many instances
      if (matches.length > 5) {
        return [
          createValidationIssue('passive-voice', 'info', 'Frequent passive voice usage', {
            description: `Found ${matches.length} instances of passive voice. Consider using active voice for clarity.`,
            category: 'style',
          }),
        ];
      }

      return [];
    },
  },

  {
    id: 'acronym-definition',
    name: 'Acronym Definition',
    description: 'Acronyms should be defined on first use',
    category: 'content',
    severity: 'info',
    validate: (content) => {
      const text = stripHtml(content);
      const acronymPattern = /\b([A-Z]{2,})\b/g;
      const acronymsFound = new Set<string>();
      const issues = [];

      let match;
      while ((match = acronymPattern.exec(text)) !== null) {
        const acronym = match[1];

        // Skip common words that look like acronyms
        if (['US', 'USA', 'DoD', 'FAR', 'RFP', 'IT', 'AI', 'ID'].includes(acronym)) {
          continue;
        }

        // Check if this is the first occurrence
        if (!acronymsFound.has(acronym)) {
          acronymsFound.add(acronym);

          // Look for definition pattern: "Acronym (ACRO)"
          const definitionPattern = new RegExp(`\\w+\\s+\\(${acronym}\\)`, 'i');
          if (!definitionPattern.test(text)) {
            issues.push(
              createValidationIssue('acronym-definition', 'info', `Undefined acronym: ${acronym}`, {
                description: `Define acronym on first use: "Full Name (${acronym})"`,
                category: 'content',
              })
            );
          }
        }
      }

      return issues;
    },
  },

  {
    id: 'quantitative-data',
    name: 'Quantitative Support',
    description: 'Claims should include quantitative data where possible',
    category: 'content',
    severity: 'info',
    validate: (content) => {
      const text = stripHtml(content);
      const issues = [];

      // Look for qualitative claims without numbers
      const claimPattern = /\b(significantly|substantially|greatly|improved|increased|reduced|enhanced)\b/gi;
      const numberPattern = /\d+(\.\d+)?%?/;

      let match;
      while ((match = claimPattern.exec(text)) !== null) {
        // Check surrounding context for numbers
        const contextStart = Math.max(0, match.index - 50);
        const contextEnd = Math.min(text.length, match.index + 100);
        const context = text.substring(contextStart, contextEnd);

        if (!numberPattern.test(context)) {
          issues.push(
            createValidationIssue(
              'quantitative-data',
              'info',
              'Qualitative claim without quantitative support',
              {
                description: `Consider adding specific metrics or percentages to support "${match[0]}"`,
                category: 'content',
              }
            )
          );
        }
      }

      // Limit to first 3 instances to avoid overwhelming
      return issues.slice(0, 3);
    },
  },

  // ==================== STRUCTURE RULES ====================

  {
    id: 'section-l-evaluation-criteria',
    name: 'Section L Evaluation Criteria',
    description: 'Section L should include clear evaluation criteria',
    category: 'structure',
    severity: 'warning',
    appliesTo: ['Section L', 'Section L - Instructions'],
    validate: (content) => {
      const text = stripHtml(content);
      const criteriaPattern = /\b(evaluation\s+criteria|evaluation\s+factors?|criteria\s+for\s+award)\b/i;

      if (!criteriaPattern.test(text)) {
        return [
          createValidationIssue(
            'section-l-evaluation-criteria',
            'warning',
            'Missing evaluation criteria',
            {
              description: 'Section L should clearly state evaluation criteria and factors',
              category: 'structure',
            }
          ),
        ];
      }

      return [];
    },
  },

  {
    id: 'section-m-scoring',
    name: 'Section M Scoring Details',
    description: 'Section M should include scoring methodology',
    category: 'structure',
    severity: 'warning',
    appliesTo: ['Section M', 'Section M - Evaluation'],
    validate: (content) => {
      const text = stripHtml(content);
      const scoringPattern = /\b(scoring|points?|rating|adjectival|evaluation\s+methodology)\b/i;

      if (!scoringPattern.test(text)) {
        return [
          createValidationIssue('section-m-scoring', 'warning', 'Missing scoring methodology', {
            description: 'Section M should describe how proposals will be scored and evaluated',
            category: 'structure',
          }),
        ];
      }

      return [];
    },
  },

  {
    id: 'price-volume-separation',
    name: 'Price Volume Separation',
    description: 'Price information should not appear in technical volume',
    category: 'compliance',
    severity: 'error',
    appliesTo: [
      'Technical Approach',
      'Management Approach',
      'Past Performance',
      'Section L',
      'Section M',
    ],
    validate: (content) => {
      const text = stripHtml(content);
      const pricePattern = /\$\s*[\d,]+(\.\d{2})?|(\d+)\s*(dollars?|USD)/gi;
      const matches = findMatches(content, pricePattern);

      return matches.map((match) =>
        createValidationIssue(
          'price-volume-separation',
          'error',
          'Price information in technical volume',
          {
            description: 'Remove price/cost information from technical sections per RFP requirements',
            location: {
              from: match.index,
              to: match.index + match.length,
              text: match.text,
            },
            category: 'compliance',
            autoFix: {
              label: 'Remove price reference',
              apply: (content) => content.replace(pricePattern, '[PRICING REMOVED]'),
            },
          }
        )
      );
    },
  },
];

/**
 * Get validation rules by category
 */
export function getRulesByCategory(category: ValidationRule['category']): ValidationRule[] {
  return validationRules.filter((rule) => rule.category === category);
}

/**
 * Get validation rules by severity
 */
export function getRulesBySeverity(severity: ValidationRule['severity']): ValidationRule[] {
  return validationRules.filter((rule) => rule.severity === severity);
}

/**
 * Get validation rules for a specific section
 */
export function getRulesForSection(sectionName: string): ValidationRule[] {
  return validationRules.filter(
    (rule) => !rule.appliesTo || rule.appliesTo.length === 0 || rule.appliesTo.includes(sectionName)
  );
}
