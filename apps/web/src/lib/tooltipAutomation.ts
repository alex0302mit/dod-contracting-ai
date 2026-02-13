/**
 * Tooltip Automation
 *
 * AI-powered generation of contextual tooltips for acronyms, technical terms, and references
 */

export interface TooltipSuggestion {
  text: string;
  tooltipText: string;
  tooltipType: 'definition' | 'acronym' | 'reference' | 'help';
  confidence: number;
}

/**
 * Common government/DoD acronyms dictionary
 */
const ACRONYM_DICTIONARY: Record<string, string> = {
  // Federal Acquisition Regulation
  'FAR': 'Federal Acquisition Regulation - The primary regulation for use by all federal executive agencies in their acquisition of supplies and services',
  'DFARS': 'Defense Federal Acquisition Regulation Supplement - DoD supplement to the FAR',
  'AFFARS': 'Air Force Federal Acquisition Regulation Supplement',
  'DFAR': 'Defense Federal Acquisition Regulation',

  // Contract types
  'FFP': 'Firm-Fixed-Price - A contract type that provides for a price that is not subject to adjustment',
  'CPFF': 'Cost-Plus-Fixed-Fee - A cost-reimbursement contract with a fixed fee',
  'CPAF': 'Cost-Plus-Award-Fee - A cost-reimbursement contract with an award fee based on performance',
  'T&M': 'Time and Materials - A contract type that provides for payment on a per-hour basis',
  'IDIQ': 'Indefinite Delivery/Indefinite Quantity - A contract for an indefinite quantity of supplies or services',

  // Proposal sections
  'SOW': 'Statement of Work - Detailed description of work requirements',
  'PWS': 'Performance Work Statement - Description of required performance outcomes',
  'CDR': 'Contract Data Requirements - Data items required to be delivered',
  'CDRL': 'Contract Data Requirements List - List of required deliverable data items',
  'RFP': 'Request for Proposal - Solicitation document for competitive proposals',
  'RFI': 'Request for Information - Document to gather market information',
  'RFQ': 'Request for Quote - Solicitation for price quotes',

  // Management and oversight
  'KO': 'Contracting Officer - Government official authorized to enter into and administer contracts',
  'COR': 'Contracting Officer\'s Representative - Individual designated to assist in contract administration',
  'ACO': 'Administrative Contracting Officer - Performs contract administration functions',
  'PCO': 'Procuring Contracting Officer - Responsible for awarding and executing contracts',
  'PM': 'Program Manager - Individual responsible for managing a program',

  // Quality and compliance
  'QA': 'Quality Assurance - Systematic activities to ensure quality requirements are met',
  'QC': 'Quality Control - Operational techniques to fulfill quality requirements',
  'CAR': 'Corrective Action Report - Document detailing corrective actions for deficiencies',
  'CPSR': 'Contractor Purchasing System Review - Evaluation of contractor purchasing system',

  // Performance
  'SLA': 'Service Level Agreement - Commitment between service provider and customer',
  'KPI': 'Key Performance Indicator - Measurable value demonstrating effectiveness',
  'OLA': 'Operational Level Agreement - Agreement between internal support groups',

  // Security and clearances
  'OPSEC': 'Operations Security - Process to protect critical information',
  'INFOSEC': 'Information Security - Protection of information and information systems',
  'COMSEC': 'Communications Security - Protection of telecommunications',
  'NISPOM': 'National Industrial Security Program Operating Manual - Security requirements for classified contracts',
  'DD254': 'DoD Contract Security Classification Specification - Document specifying security requirements',

  // Financial
  'BOA': 'Basic Ordering Agreement - Written instrument of understanding for future orders',
  'BPA': 'Blanket Purchase Agreement - Simplified method for filling recurring needs',
  'LOE': 'Level of Effort - Basis of payment for services where outcome is undefined',
  'ODC': 'Other Direct Costs - Direct costs other than labor and materials',

  // Technical
  'API': 'Application Programming Interface - Set of protocols for building software',
  'GUI': 'Graphical User Interface - Visual interface for user interaction',
  'SaaS': 'Software as a Service - Software licensing and delivery model',
  'IaaS': 'Infrastructure as a Service - Online services providing compute resources',
  'PaaS': 'Platform as a Service - Cloud computing services for application development',
  'CI/CD': 'Continuous Integration/Continuous Deployment - Automated software delivery practices',

  // Testing
  'DT': 'Developmental Testing - Testing during development phase',
  'OT': 'Operational Testing - Testing in operational environment',
  'IOT&E': 'Initial Operational Test and Evaluation - Combined DT and OT evaluation',
  'T&E': 'Test and Evaluation - Process of testing and evaluating systems',

  // Common terms
  'POC': 'Point of Contact - Designated contact person',
  'SME': 'Subject Matter Expert - Person with expertise in a particular area',
  'COTS': 'Commercial Off-The-Shelf - Commercial products available for purchase',
  'GOTS': 'Government Off-The-Shelf - Government-developed products',
  'O&M': 'Operations and Maintenance - Ongoing operational support',
  'R&D': 'Research and Development - Investigative activities for innovation',
  'TBD': 'To Be Determined - Information to be provided later',
  'TBS': 'To Be Specified - Specification to be provided later',
};

/**
 * Common technical terms and definitions
 */
const TECHNICAL_TERMS: Record<string, string> = {
  'evaluation factor': 'Criteria used to assess and compare proposals submitted in response to a solicitation',
  'evaluation criteria': 'Standards by which proposals are judged and compared',
  'past performance': 'Record of contractor performance on previous contracts',
  'technical approach': 'Methodology and strategy for accomplishing the work requirements',
  'management approach': 'Strategy for organizing, directing, and controlling project activities',
  'price reasonableness': 'Determination that proposed prices are fair and reasonable',
  'responsibility determination': 'Assessment that contractor has capability to perform',
  'best value': 'Expected outcome providing greatest overall benefit in response to requirements',
  'technically acceptable': 'Proposal meets minimum technical requirements',
  'competitive range': 'Range of proposals that have reasonable chance of award',
  'discussions': 'Negotiations after receipt of proposals but before award',
  'clarifications': 'Limited exchanges to clarify proposal provisions',
  'source selection': 'Process of evaluating proposals and selecting contractor for award',
  'award fee': 'Fee paid based on contractor performance against specific criteria',
  'incentive fee': 'Fee based on relationship between target and actual performance',
  'base period': 'Initial contract period before option periods',
  'option period': 'Additional contract period that may be exercised at government discretion',
  'period of performance': 'Time span during which contract work is to be performed',
  'deliverable': 'Any measurable, tangible, verifiable outcome produced to complete project',
  'milestone': 'Significant point or event in the project schedule',
  'warranty': 'Contractor\'s assurance that supplies or services will meet contract requirements',
};

/**
 * Auto-generate tooltips for acronyms and technical terms
 */
export async function autoGenerateTooltips(content: string): Promise<TooltipSuggestion[]> {
  const suggestions: TooltipSuggestion[] = [];

  // Strip HTML tags for analysis
  const plainText = content.replace(/<[^>]*>/g, ' ');

  // Detect acronyms (2-8 capital letters, possibly with numbers)
  const acronymPattern = /\b([A-Z]{2,8}(?:\/[A-Z]{2,8})?)\b/g;
  const acronymMatches = plainText.match(acronymPattern);

  if (acronymMatches) {
    const uniqueAcronyms = [...new Set(acronymMatches)];

    uniqueAcronyms.forEach((acronym) => {
      // Check if we have a definition for this acronym
      if (ACRONYM_DICTIONARY[acronym]) {
        suggestions.push({
          text: acronym,
          tooltipText: ACRONYM_DICTIONARY[acronym],
          tooltipType: 'acronym',
          confidence: 0.95,
        });
      } else {
        // For unknown acronyms, suggest a generic help tooltip
        suggestions.push({
          text: acronym,
          tooltipText: `${acronym} - Definition to be added`,
          tooltipType: 'acronym',
          confidence: 0.5,
        });
      }
    });
  }

  // Detect technical terms
  Object.entries(TECHNICAL_TERMS).forEach(([term, definition]) => {
    const termPattern = new RegExp(`\\b${term}\\b`, 'gi');
    const matches = plainText.match(termPattern);

    if (matches) {
      // Only add first occurrence to avoid too many tooltips
      suggestions.push({
        text: matches[0], // Use actual case from document
        tooltipText: definition,
        tooltipType: 'definition',
        confidence: 0.9,
      });
    }
  });

  // Detect FAR/DFARS references
  const farPattern = /\b(FAR|DFARS)\s+(\d+\.\d+(?:-\d+)?)\b/gi;
  const farMatches = plainText.match(farPattern);

  if (farMatches) {
    const uniqueRefs = [...new Set(farMatches)];

    uniqueRefs.forEach((ref) => {
      suggestions.push({
        text: ref,
        tooltipText: `Federal regulation reference - Click to view full text`,
        tooltipType: 'reference',
        confidence: 0.9,
      });
    });
  }

  // Detect date references that might need clarification
  const datePattern = /\b(within \d+ days?|within \d+ months?|by [A-Z][a-z]+ \d+|due date)\b/gi;
  const dateMatches = plainText.match(datePattern);

  if (dateMatches) {
    const uniqueDates = [...new Set(dateMatches)];

    uniqueDates.slice(0, 5).forEach((date) => {
      suggestions.push({
        text: date,
        tooltipText: 'Important deadline or timeframe requirement',
        tooltipType: 'help',
        confidence: 0.7,
      });
    });
  }

  // Remove low-confidence suggestions and duplicates
  const filteredSuggestions = suggestions
    .filter((s, index, self) =>
      index === self.findIndex((t) => t.text.toLowerCase() === s.text.toLowerCase())
    )
    .filter(s => s.confidence >= 0.7)
    .sort((a, b) => b.confidence - a.confidence);

  return filteredSuggestions;
}

/**
 * Get definition for a specific acronym
 */
export function getAcronymDefinition(acronym: string): string | null {
  return ACRONYM_DICTIONARY[acronym.toUpperCase()] || null;
}

/**
 * Get definition for a technical term
 */
export function getTechnicalTermDefinition(term: string): string | null {
  return TECHNICAL_TERMS[term.toLowerCase()] || null;
}

/**
 * Add custom acronym to dictionary (for user extensions)
 */
export function addCustomAcronym(acronym: string, definition: string): void {
  ACRONYM_DICTIONARY[acronym.toUpperCase()] = definition;
}

/**
 * Add custom technical term (for user extensions)
 */
export function addCustomTerm(term: string, definition: string): void {
  TECHNICAL_TERMS[term.toLowerCase()] = definition;
}
