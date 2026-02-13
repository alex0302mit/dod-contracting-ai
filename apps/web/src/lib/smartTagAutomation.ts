/**
 * Smart Tag Automation
 *
 * AI-powered detection of smart tags in document content
 * Analyzes text patterns to suggest requirements, assumptions, risks, decisions, and action items
 */

export interface SmartTagSuggestion {
  text: string;
  tagType: 'requirement' | 'assumption' | 'risk' | 'decision' | 'action-item' | 'note';
  tagLabel: string;
  tagDescription?: string;
  confidence: number;
}

/**
 * Auto-detect smart tags in document content
 */
export async function autoDetectSmartTags(content: string): Promise<SmartTagSuggestion[]> {
  const suggestions: SmartTagSuggestion[] = [];

  // Strip HTML tags for analysis
  const plainText = content.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ');

  // Detect Requirements
  const requirementPatterns = [
    {
      pattern: /\b(shall|must|will|is required to|are required to)\b[^.!?]{10,150}[.!?]/gi,
      label: 'REQ',
      description: 'Mandatory requirement statement',
    },
    {
      pattern: /\b(contractor shall|contractor must|offeror shall|offeror must)\b[^.!?]{10,150}[.!?]/gi,
      label: 'REQ',
      description: 'Contractor requirement',
    },
    {
      pattern: /\b(deliverable|milestone|performance standard|technical requirement)\b[^.!?]{10,100}[.!?]/gi,
      label: 'REQ',
      description: 'Performance or deliverable requirement',
    },
  ];

  requirementPatterns.forEach(({ pattern, label, description }) => {
    const matches = plainText.match(pattern);
    if (matches) {
      matches.slice(0, 5).forEach((match, index) => {
        suggestions.push({
          text: match.trim(),
          tagType: 'requirement',
          tagLabel: `${label}-${suggestions.filter(s => s.tagType === 'requirement').length + 1}`,
          tagDescription: description,
          confidence: 0.85,
        });
      });
    }
  });

  // Detect Assumptions
  const assumptionPatterns = [
    {
      pattern: /\b(assume[sd]?|assuming|presumed|it is assumed|we assume|assumption)\b[^.!?]{10,150}[.!?]/gi,
      label: 'ASMP',
      description: 'Stated assumption',
    },
    {
      pattern: /\b(if|provided that|given that|contingent upon|depends on)\b[^.!?]{10,100}[.!?]/gi,
      label: 'ASMP',
      description: 'Conditional assumption',
    },
  ];

  assumptionPatterns.forEach(({ pattern, label, description }) => {
    const matches = plainText.match(pattern);
    if (matches) {
      matches.slice(0, 5).forEach((match) => {
        suggestions.push({
          text: match.trim(),
          tagType: 'assumption',
          tagLabel: `${label}-${suggestions.filter(s => s.tagType === 'assumption').length + 1}`,
          tagDescription: description,
          confidence: 0.8,
        });
      });
    }
  });

  // Detect Risks
  const riskPatterns = [
    {
      pattern: /\b(risk|potential issue|concern|challenge|may affect|could impact|may result in)\b[^.!?]{10,150}[.!?]/gi,
      label: 'RISK',
      description: 'Identified risk or concern',
    },
    {
      pattern: /\b(if not|failure to|unable to|inadequate|insufficient|may not)\b[^.!?]{10,100}[.!?]/gi,
      label: 'RISK',
      description: 'Potential failure scenario',
    },
    {
      pattern: /\b(mitigation|contingency|backup plan|alternative approach)\b[^.!?]{10,100}[.!?]/gi,
      label: 'RISK',
      description: 'Risk mitigation strategy',
    },
  ];

  riskPatterns.forEach(({ pattern, label, description }) => {
    const matches = plainText.match(pattern);
    if (matches) {
      matches.slice(0, 5).forEach((match) => {
        suggestions.push({
          text: match.trim(),
          tagType: 'risk',
          tagLabel: `${label}-${suggestions.filter(s => s.tagType === 'risk').length + 1}`,
          tagDescription: description,
          confidence: 0.75,
        });
      });
    }
  });

  // Detect Decisions
  const decisionPatterns = [
    {
      pattern: /\b(decided|determined|selected|chosen|approved|authorized)\b[^.!?]{10,150}[.!?]/gi,
      label: 'DEC',
      description: 'Decision made',
    },
    {
      pattern: /\b(will use|will implement|will adopt|approach is|method is|strategy is)\b[^.!?]{10,100}[.!?]/gi,
      label: 'DEC',
      description: 'Strategic decision',
    },
  ];

  decisionPatterns.forEach(({ pattern, label, description }) => {
    const matches = plainText.match(pattern);
    if (matches) {
      matches.slice(0, 5).forEach((match) => {
        suggestions.push({
          text: match.trim(),
          tagType: 'decision',
          tagLabel: `${label}-${suggestions.filter(s => s.tagType === 'decision').length + 1}`,
          tagDescription: description,
          confidence: 0.8,
        });
      });
    }
  });

  // Detect Action Items
  const actionPatterns = [
    {
      pattern: /\b(TBD|to be determined|to be completed|pending|action required|needs to|must complete)\b[^.!?]{10,150}[.!?]/gi,
      label: 'ACTION',
      description: 'Action item or pending task',
    },
    {
      pattern: /\b(will be provided|will be submitted|will be developed|will be conducted|will be performed)\b[^.!?]{10,100}[.!?]/gi,
      label: 'ACTION',
      description: 'Future action',
    },
  ];

  actionPatterns.forEach(({ pattern, label, description }) => {
    const matches = plainText.match(pattern);
    if (matches) {
      matches.slice(0, 5).forEach((match) => {
        suggestions.push({
          text: match.trim(),
          tagType: 'action-item',
          tagLabel: `${label}-${suggestions.filter(s => s.tagType === 'action-item').length + 1}`,
          tagDescription: description,
          confidence: 0.85,
        });
      });
    }
  });

  // Remove duplicates and low-confidence suggestions
  const uniqueSuggestions = suggestions
    .filter((s, index, self) =>
      index === self.findIndex((t) => t.text === s.text && t.tagType === s.tagType)
    )
    .filter(s => s.confidence >= 0.7)
    .sort((a, b) => b.confidence - a.confidence);

  return uniqueSuggestions;
}

/**
 * Detect specific types of tags in content
 */
export function detectRequirements(content: string): SmartTagSuggestion[] {
  const allSuggestions = autoDetectSmartTags(content);
  return allSuggestions.then(suggestions =>
    suggestions.filter(s => s.tagType === 'requirement')
  ) as any;
}

export function detectAssumptions(content: string): SmartTagSuggestion[] {
  const allSuggestions = autoDetectSmartTags(content);
  return allSuggestions.then(suggestions =>
    suggestions.filter(s => s.tagType === 'assumption')
  ) as any;
}

export function detectRisks(content: string): SmartTagSuggestion[] {
  const allSuggestions = autoDetectSmartTags(content);
  return allSuggestions.then(suggestions =>
    suggestions.filter(s => s.tagType === 'risk')
  ) as any;
}
