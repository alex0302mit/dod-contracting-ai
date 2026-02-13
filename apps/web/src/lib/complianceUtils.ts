/**
 * Compliance Analysis Utilities
 *
 * Functions for analyzing document compliance with FAR/DFARS regulations
 */

import { computeQualityScore, computeIssues } from './editorUtils';

export interface ComplianceIssue {
  id: string;
  sectionName: string;
  kind: 'error' | 'warning' | 'info' | 'compliance';
  label: string;
  pattern: string;
  fix?: {
    label: string;
    apply: (text: string) => string;
  };
}

export interface SectionCompliance {
  sectionName: string;
  score: number;
  status: 'pass' | 'review' | 'fail';
  issues: ComplianceIssue[];
  qualityBreakdown: {
    readability: number;
    citations: number;
    compliance: number;
    length: number;
  };
  wordCount: number;
}

export interface FARReference {
  clause: string;
  sections: string[];
  description?: string;
}

export interface DFARSReference {
  clause: string;
  sections: string[];
  description?: string;
}

export interface ComplianceAnalysis {
  overallScore: number;
  overallStatus: 'pass' | 'review' | 'fail';
  sectionsAnalyzed: number;
  sectionCompliance: SectionCompliance[];
  criticalIssues: ComplianceIssue[];
  farCoverage: FARReference[];
  dfarsCoverage: DFARSReference[];
  missingFAR: string[];
  missingDFARS: string[];
}

/**
 * Analyze document sections for compliance
 */
export function analyzeDocumentCompliance(
  sections: Record<string, string>,
  citations: any[]
): SectionCompliance[] {
  const sectionCompliance: SectionCompliance[] = [];

  Object.entries(sections).forEach(([sectionName, content]) => {
    // Strip HTML for analysis
    const plainText = content.replace(/<[^>]*>/g, '');

    // Compute quality score
    const quality = computeQualityScore(content, citations);

    // Compute issues
    const rawIssues = computeIssues(content);

    // Convert issues to compliance issues with section context
    const issues: ComplianceIssue[] = rawIssues.map((issue, idx) => ({
      id: `${sectionName}-${issue.id || idx}`,
      sectionName,
      kind: issue.kind,
      label: issue.label,
      pattern: issue.pattern,
      fix: issue.fix,
    }));

    // Determine status based on score
    let status: 'pass' | 'review' | 'fail';
    if (quality.total >= 85) {
      status = 'pass';
    } else if (quality.total >= 70) {
      status = 'review';
    } else {
      status = 'fail';
    }

    sectionCompliance.push({
      sectionName,
      score: quality.total,
      status,
      issues,
      qualityBreakdown: quality.breakdown,
      wordCount: plainText.split(/\s+/).filter(Boolean).length,
    });
  });

  return sectionCompliance;
}

/**
 * Analyze FAR coverage across sections
 */
export function analyzeFARCoverage(
  sections: Record<string, string>,
  citations: any[]
): { found: FARReference[]; missing: string[] } {
  const farMap = new Map<string, Set<string>>();
  const allSectionNames = Object.keys(sections);

  // Extract FAR references from text content
  Object.entries(sections).forEach(([sectionName, content]) => {
    const plainText = content.replace(/<[^>]*>/g, '');

    // Match FAR XX.XXX or FAR Part XX patterns
    const farMatches = plainText.match(/FAR\s+(?:Part\s+)?(\d+(?:\.\d+)*)/gi);

    if (farMatches) {
      farMatches.forEach((match) => {
        const clause = match.replace(/\s+/g, ' ').trim();
        if (!farMap.has(clause)) {
          farMap.set(clause, new Set());
        }
        farMap.get(clause)!.add(sectionName);
      });
    }
  });

  // Extract FAR references from citations
  citations.forEach((citation) => {
    if (citation.source && citation.source.toUpperCase().includes('FAR')) {
      const clause = citation.source;
      if (!farMap.has(clause)) {
        farMap.set(clause, new Set());
      }
      // Citations don't have specific section association in current data model
      // Mark as "Referenced in citations"
      farMap.get(clause)!.add('Citations');
    }
  });

  const found: FARReference[] = Array.from(farMap.entries()).map(([clause, sectionsSet]) => ({
    clause,
    sections: Array.from(sectionsSet),
  }));

  // Check for required FAR references
  const requiredFAR = [
    'FAR 15.304', // Evaluation factors
    'FAR 15.305', // Proposal evaluation
    'FAR Part 15', // Contracting by negotiation
    'FAR 52.204', // CAGE code requirements
    'FAR 5.2',    // Synopses of proposed contract actions
  ];

  const foundClauses = new Set(found.map((f) => f.clause));
  const missing = requiredFAR.filter((required) => {
    // Check if any found clause contains this required reference
    return !Array.from(foundClauses).some((clause) =>
      clause.toUpperCase().includes(required.toUpperCase().replace('FAR ', ''))
    );
  });

  return { found, missing };
}

/**
 * Analyze DFARS coverage across sections
 */
export function analyzeDFARSCoverage(
  sections: Record<string, string>,
  citations: any[]
): { found: DFARSReference[]; missing: string[] } {
  const dfarsMap = new Map<string, Set<string>>();

  // Extract DFARS references from text content
  Object.entries(sections).forEach(([sectionName, content]) => {
    const plainText = content.replace(/<[^>]*>/g, '');

    // Match DFARS XXX.XXX-XXXX patterns
    const dfarsMatches = plainText.match(/DFARS\s+(\d+(?:\.\d+)*(?:-\d+)*)/gi);

    if (dfarsMatches) {
      dfarsMatches.forEach((match) => {
        const clause = match.replace(/\s+/g, ' ').trim();
        if (!dfarsMap.has(clause)) {
          dfarsMap.set(clause, new Set());
        }
        dfarsMap.get(clause)!.add(sectionName);
      });
    }
  });

  // Extract DFARS references from citations
  citations.forEach((citation) => {
    if (citation.source && citation.source.toUpperCase().includes('DFARS')) {
      const clause = citation.source;
      if (!dfarsMap.has(clause)) {
        dfarsMap.set(clause, new Set());
      }
      dfarsMap.get(clause)!.add('Citations');
    }
  });

  const found: DFARSReference[] = Array.from(dfarsMap.entries()).map(([clause, sectionsSet]) => ({
    clause,
    sections: Array.from(sectionsSet),
  }));

  // Check for required DFARS references (context-dependent)
  const requiredDFARS: string[] = [];

  // Check if CUI is mentioned - requires DFARS 252.204-7012
  Object.values(sections).forEach((content) => {
    const plainText = content.replace(/<[^>]*>/g, '');
    if (plainText.toLowerCase().includes('cui') || plainText.toLowerCase().includes('controlled unclassified')) {
      requiredDFARS.push('DFARS 252.204-7012');
    }
  });

  const foundClauses = new Set(found.map((f) => f.clause));
  const missing = requiredDFARS.filter((required) => {
    return !Array.from(foundClauses).some((clause) =>
      clause.toUpperCase().includes(required.toUpperCase().replace('DFARS ', ''))
    );
  });

  return { found, missing: Array.from(new Set(missing)) }; // Remove duplicates
}

/**
 * Compute overall compliance score from section scores
 */
export function computeOverallComplianceScore(
  sectionCompliance: SectionCompliance[]
): { score: number; status: 'pass' | 'review' | 'fail' } {
  if (sectionCompliance.length === 0) {
    return { score: 0, status: 'fail' };
  }

  // Weight sections by word count (longer sections have more weight)
  const totalWords = sectionCompliance.reduce((sum, s) => sum + s.wordCount, 0);

  const weightedScore = sectionCompliance.reduce((sum, section) => {
    const weight = section.wordCount / totalWords;
    return sum + section.score * weight;
  }, 0);

  const score = Math.round(weightedScore);

  let status: 'pass' | 'review' | 'fail';
  if (score >= 85) {
    status = 'pass';
  } else if (score >= 70) {
    status = 'review';
  } else {
    status = 'fail';
  }

  return { score, status };
}

/**
 * Categorize and extract critical compliance issues
 */
export function categorizeComplianceIssues(
  sectionCompliance: SectionCompliance[]
): ComplianceIssue[] {
  const criticalIssues: ComplianceIssue[] = [];

  sectionCompliance.forEach((section) => {
    section.issues.forEach((issue) => {
      // Critical issues are errors or compliance-type issues
      if (issue.kind === 'error' || issue.kind === 'compliance') {
        criticalIssues.push(issue);
      }
    });
  });

  return criticalIssues;
}

/**
 * Perform complete compliance analysis
 */
export function performComplianceAnalysis(
  sections: Record<string, string>,
  citations: any[]
): ComplianceAnalysis {
  // Analyze each section
  const sectionCompliance = analyzeDocumentCompliance(sections, citations);

  // Compute overall score
  const overall = computeOverallComplianceScore(sectionCompliance);

  // Extract critical issues
  const criticalIssues = categorizeComplianceIssues(sectionCompliance);

  // Analyze FAR coverage
  const farAnalysis = analyzeFARCoverage(sections, citations);

  // Analyze DFARS coverage
  const dfarsAnalysis = analyzeDFARSCoverage(sections, citations);

  return {
    overallScore: overall.score,
    overallStatus: overall.status,
    sectionsAnalyzed: sectionCompliance.length,
    sectionCompliance,
    criticalIssues,
    farCoverage: farAnalysis.found,
    dfarsCoverage: dfarsAnalysis.found,
    missingFAR: farAnalysis.missing,
    missingDFARS: dfarsAnalysis.missing,
  };
}
