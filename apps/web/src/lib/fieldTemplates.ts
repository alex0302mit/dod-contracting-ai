/**
 * Field Templates for DoD Contracting Documents
 *
 * Pre-defined smart field templates for common sections
 */

import { FieldTemplate } from './SmartFieldEngine';

/**
 * All field templates for DoD contracting documents
 */
export const fieldTemplates: FieldTemplate[] = [
  // ==================== TECHNICAL APPROACH ====================
  {
    id: 'solution-overview',
    name: 'Solution Overview',
    description: 'High-level overview of proposed technical solution',
    category: 'technical',
    appliesTo: ['Technical Approach', 'Technical Volume'],
    fields: [
      {
        id: 'solution-name',
        fieldType: 'text',
        label: 'Solution Name',
        description: 'Name or identifier for your proposed solution',
        placeholder: 'e.g., Integrated Cloud Platform Solution',
        validation: { required: true, min: 3, max: 100 },
        category: 'technical',
      },
      {
        id: 'architecture-type',
        fieldType: 'select',
        label: 'Architecture Type',
        description: 'High-level architecture approach',
        options: [
          { value: 'cloud-native', label: 'Cloud-Native', description: 'Built for cloud from ground up' },
          { value: 'hybrid', label: 'Hybrid Cloud', description: 'Mix of on-prem and cloud' },
          { value: 'on-premise', label: 'On-Premise', description: 'Fully on-premise deployment' },
          { value: 'microservices', label: 'Microservices', description: 'Distributed microservices architecture' },
          { value: 'monolithic', label: 'Monolithic', description: 'Single unified application' },
        ],
        validation: { required: true },
        category: 'technical',
      },
      {
        id: 'key-technologies',
        fieldType: 'textarea',
        label: 'Key Technologies',
        description: 'Primary technologies, frameworks, and tools',
        placeholder: 'e.g., Kubernetes, Docker, React, Node.js, PostgreSQL',
        validation: { required: true, min: 10, max: 500 },
        category: 'technical',
      },
      {
        id: 'compliance-standards',
        fieldType: 'multiselect',
        label: 'Compliance Standards',
        description: 'Security and compliance standards met',
        options: [
          { value: 'fedramp', label: 'FedRAMP' },
          { value: 'nist-800-53', label: 'NIST 800-53' },
          { value: 'nist-800-171', label: 'NIST 800-171' },
          { value: 'cmmc', label: 'CMMC Level 3' },
          { value: 'disa-stig', label: 'DISA STIG' },
          { value: 'il4', label: 'Impact Level 4 (IL4)' },
          { value: 'il5', label: 'Impact Level 5 (IL5)' },
        ],
        category: 'technical',
      },
    ],
    outputFormat: (values) => `
## Solution Overview: ${values['solution-name']}

**Architecture Approach:** ${values['architecture-type'] || 'N/A'}

**Key Technologies:**
${values['key-technologies'] || 'N/A'}

**Compliance & Security:**
The proposed solution adheres to the following compliance standards: ${values['compliance-standards'] || 'N/A'}
`.trim(),
  },

  // ==================== PAST PERFORMANCE ====================
  {
    id: 'past-performance-project',
    name: 'Past Performance Project',
    description: 'Details for a past performance reference',
    category: 'technical',
    appliesTo: ['Past Performance', 'Section L'],
    fields: [
      {
        id: 'project-name',
        fieldType: 'text',
        label: 'Project Name',
        placeholder: 'e.g., DoD Cloud Migration Initiative',
        validation: { required: true, min: 5, max: 150 },
        category: 'technical',
      },
      {
        id: 'client-name',
        fieldType: 'text',
        label: 'Client/Agency Name',
        placeholder: 'e.g., U.S. Air Force',
        validation: { required: true },
        category: 'administrative',
      },
      {
        id: 'contract-number',
        fieldType: 'text',
        label: 'Contract Number',
        placeholder: 'e.g., FA8732-19-C-0001',
        validation: {
          required: true,
          pattern: /^[A-Z0-9-]+$/,
        },
        category: 'administrative',
      },
      {
        id: 'period-start',
        fieldType: 'date',
        label: 'Period of Performance Start',
        validation: { required: true },
        category: 'administrative',
      },
      {
        id: 'period-end',
        fieldType: 'date',
        label: 'Period of Performance End',
        validation: { required: true },
        category: 'administrative',
      },
      {
        id: 'contract-value',
        fieldType: 'currency',
        label: 'Contract Value',
        placeholder: '1000000',
        validation: { required: true, min: 0 },
        category: 'pricing',
      },
      {
        id: 'project-description',
        fieldType: 'textarea',
        label: 'Project Description',
        placeholder: 'Brief description of work performed...',
        validation: { required: true, min: 50, max: 1000 },
        category: 'technical',
      },
      {
        id: 'relevance',
        fieldType: 'textarea',
        label: 'Relevance to Current RFP',
        placeholder: 'Explain how this project relates to current requirements...',
        validation: { required: true, min: 50, max: 500 },
        category: 'technical',
      },
    ],
    outputFormat: (values) => `
### ${values['project-name']}

**Client:** ${values['client-name']}
**Contract Number:** ${values['contract-number']}
**Period of Performance:** ${values['period-start']} to ${values['period-end']}
**Contract Value:** $${parseFloat(values['contract-value'] || '0').toLocaleString()}

**Project Description:**
${values['project-description']}

**Relevance:**
${values['relevance']}
`.trim(),
  },

  // ==================== MANAGEMENT APPROACH ====================
  {
    id: 'key-personnel',
    name: 'Key Personnel',
    description: 'Details for key personnel assignment',
    category: 'management',
    appliesTo: ['Management Approach', 'Key Personnel'],
    fields: [
      {
        id: 'person-name',
        fieldType: 'text',
        label: 'Full Name',
        placeholder: 'e.g., John Smith',
        validation: { required: true, min: 2 },
        category: 'management',
      },
      {
        id: 'position',
        fieldType: 'text',
        label: 'Proposed Position',
        placeholder: 'e.g., Program Manager',
        validation: { required: true },
        category: 'management',
      },
      {
        id: 'clearance-level',
        fieldType: 'select',
        label: 'Security Clearance',
        options: [
          { value: 'none', label: 'None' },
          { value: 'confidential', label: 'Confidential' },
          { value: 'secret', label: 'Secret' },
          { value: 'ts', label: 'Top Secret' },
          { value: 'ts-sci', label: 'TS/SCI' },
        ],
        validation: { required: true },
        category: 'compliance',
      },
      {
        id: 'years-experience',
        fieldType: 'number',
        label: 'Years of Relevant Experience',
        validation: { required: true, min: 0, max: 50 },
        category: 'management',
      },
      {
        id: 'education',
        fieldType: 'text',
        label: 'Education',
        placeholder: 'e.g., MS Computer Science, Stanford University',
        validation: { required: true },
        category: 'management',
      },
      {
        id: 'certifications',
        fieldType: 'textarea',
        label: 'Relevant Certifications',
        placeholder: 'e.g., PMP, CISSP, AWS Solutions Architect',
        category: 'management',
      },
      {
        id: 'relevant-experience',
        fieldType: 'textarea',
        label: 'Relevant Experience Summary',
        placeholder: 'Brief summary of relevant experience and qualifications...',
        validation: { required: true, min: 50, max: 500 },
        category: 'management',
      },
    ],
    outputFormat: (values) => `
### ${values['position']}: ${values['person-name']}

**Security Clearance:** ${values['clearance-level']}
**Years of Experience:** ${values['years-experience']} years
**Education:** ${values['education']}
${values['certifications'] ? `**Certifications:** ${values['certifications']}\n` : ''}
**Relevant Experience:**
${values['relevant-experience']}
`.trim(),
  },

  // ==================== SCHEDULE & MILESTONES ====================
  {
    id: 'project-milestone',
    name: 'Project Milestone',
    description: 'Define a project milestone or deliverable',
    category: 'management',
    appliesTo: ['Management Approach', 'Schedule', 'Section L'],
    fields: [
      {
        id: 'milestone-name',
        fieldType: 'text',
        label: 'Milestone Name',
        placeholder: 'e.g., System Design Review Complete',
        validation: { required: true },
        category: 'management',
      },
      {
        id: 'milestone-date',
        fieldType: 'date',
        label: 'Target Completion Date',
        validation: { required: true },
        category: 'management',
      },
      {
        id: 'duration',
        fieldType: 'duration',
        label: 'Duration',
        placeholder: 'e.g., 60 days',
        category: 'management',
      },
      {
        id: 'deliverables',
        fieldType: 'textarea',
        label: 'Associated Deliverables',
        placeholder: 'List deliverables for this milestone...',
        validation: { required: true },
        category: 'management',
      },
      {
        id: 'dependencies',
        fieldType: 'textarea',
        label: 'Dependencies',
        placeholder: 'Prerequisites or dependencies...',
        category: 'management',
      },
    ],
    outputFormat: (values) => `
**Milestone:** ${values['milestone-name']}
**Target Date:** ${values['milestone-date']}
${values['duration'] ? `**Duration:** ${values['duration']}\n` : ''}
**Deliverables:**
${values['deliverables']}
${values['dependencies'] ? `\n**Dependencies:**\n${values['dependencies']}` : ''}
`.trim(),
  },

  // ==================== COMPLIANCE MATRIX ====================
  {
    id: 'compliance-requirement',
    name: 'Compliance Requirement',
    description: 'Map requirement to compliance response',
    category: 'compliance',
    appliesTo: ['Section L', 'Compliance Matrix'],
    fields: [
      {
        id: 'requirement-id',
        fieldType: 'text',
        label: 'Requirement ID',
        placeholder: 'e.g., L-001',
        validation: { required: true },
        category: 'compliance',
      },
      {
        id: 'requirement-text',
        fieldType: 'textarea',
        label: 'Requirement Text',
        placeholder: 'Copy exact requirement from RFP...',
        validation: { required: true, min: 10 },
        category: 'compliance',
      },
      {
        id: 'compliance-status',
        fieldType: 'select',
        label: 'Compliance Status',
        options: [
          { value: 'compliant', label: 'Fully Compliant' },
          { value: 'partial', label: 'Partially Compliant' },
          { value: 'non-compliant', label: 'Non-Compliant' },
          { value: 'not-applicable', label: 'Not Applicable' },
        ],
        validation: { required: true },
        category: 'compliance',
      },
      {
        id: 'response',
        fieldType: 'textarea',
        label: 'Compliance Response',
        placeholder: 'Explain how you meet this requirement...',
        validation: { required: true, min: 20 },
        category: 'compliance',
      },
      {
        id: 'reference-section',
        fieldType: 'text',
        label: 'Reference Section',
        placeholder: 'e.g., Technical Volume Section 3.2',
        category: 'compliance',
      },
    ],
    outputFormat: (values) => `
| ${values['requirement-id']} | ${values['requirement-text']} | ${values['compliance-status']} | ${values['response']} | ${values['reference-section'] || 'N/A'} |
`.trim(),
  },

  // ==================== CONTACT INFORMATION ====================
  {
    id: 'point-of-contact',
    name: 'Point of Contact',
    description: 'Contact information for proposal POC',
    category: 'administrative',
    fields: [
      {
        id: 'poc-name',
        fieldType: 'text',
        label: 'Name',
        placeholder: 'Full name',
        validation: { required: true },
        autoFill: 'poc-name',
        category: 'administrative',
      },
      {
        id: 'poc-title',
        fieldType: 'text',
        label: 'Title',
        placeholder: 'Job title',
        validation: { required: true },
        category: 'administrative',
      },
      {
        id: 'poc-email',
        fieldType: 'email',
        label: 'Email',
        placeholder: 'email@company.com',
        validation: {
          required: true,
          pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        },
        autoFill: 'poc-email',
        category: 'administrative',
      },
      {
        id: 'poc-phone',
        fieldType: 'phone',
        label: 'Phone',
        placeholder: '(555) 123-4567',
        validation: { required: true },
        autoFill: 'poc-phone',
        category: 'administrative',
      },
    ],
    outputFormat: (values) => `
**Point of Contact:**
${values['poc-name']}, ${values['poc-title']}
Email: ${values['poc-email']}
Phone: ${values['poc-phone']}
`.trim(),
  },
];

/**
 * Get templates by category
 */
export function getTemplatesByCategory(category: string): FieldTemplate[] {
  return fieldTemplates.filter((template) => template.category === category);
}

/**
 * Get templates for section
 */
export function getTemplatesForSection(sectionName: string): FieldTemplate[] {
  return fieldTemplates.filter(
    (template) => !template.appliesTo || template.appliesTo.length === 0 || template.appliesTo.includes(sectionName)
  );
}
