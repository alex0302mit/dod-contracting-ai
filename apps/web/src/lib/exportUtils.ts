/**
 * Export Utilities
 *
 * Functions for exporting documents in multiple formats
 */

const API_BASE_URL = 'http://localhost:8000';

export interface ExportPrepareRequest {
  sections: Record<string, string>;
  citations: any[];
  metadata: any;
  section_order?: string[];
  selected_sections?: string[];  // Optional: Filter to specific sections only
}

export interface ExportPrepareResponse {
  export_id: string;
  file_sizes: {
    pdf: string;
    docx: string;
    json: string;
  };
  status: string;
  sections_exported?: string[];  // List of sections that were actually exported
}

export interface ExportHistoryItem {
  export_id: string;
  export_date: string;
  project_name: string;
  files: string[];
}

export interface ExportHistoryResponse {
  exports: ExportHistoryItem[];
}

/**
 * Prepare export by sending document data to backend
 * 
 * @param sections - All sections available for export
 * @param citations - Citation list
 * @param metadata - Document metadata
 * @param sectionOrder - Optional custom section order
 * @param selectedSections - Optional list of specific sections to export (null/undefined = all)
 */
export async function prepareExport(
  sections: Record<string, string>,
  citations: any[] = [],
  metadata: any = {},
  sectionOrder?: string[],
  selectedSections?: string[]
): Promise<ExportPrepareResponse> {
  const response = await fetch(`${API_BASE_URL}/api/export/prepare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sections,
      citations,
      metadata,
      section_order: sectionOrder,
      selected_sections: selectedSections,  // Pass selected sections to backend
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to prepare export');
  }

  return response.json();
}

/**
 * Download PDF file
 */
export async function downloadPDF(exportId: string): Promise<void> {
  const url = `${API_BASE_URL}/api/export/${exportId}/pdf`;
  await downloadFile(url, 'document.pdf');
}

/**
 * Download DOCX file
 */
export async function downloadDOCX(exportId: string, programName?: string): Promise<void> {
  let url = `${API_BASE_URL}/api/export/${exportId}/docx`;
  if (programName) {
    url += `?program_name=${encodeURIComponent(programName)}`;
  }
  await downloadFile(url, 'document.docx');
}

/**
 * Download JSON metadata file
 */
export async function downloadJSON(exportId: string): Promise<void> {
  const url = `${API_BASE_URL}/api/export/${exportId}/json`;
  await downloadFile(url, 'metadata.json');
}

/**
 * Generate and download compliance report
 */
export async function downloadComplianceReport(complianceAnalysis: any): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/export/compliance-report`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      compliance_analysis: complianceAnalysis,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate compliance report');
  }

  // Download the PDF blob
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = 'compliance_report.pdf';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

/**
 * Get export history
 */
export async function getExportHistory(maxCount: number = 10): Promise<ExportHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/export/history?max_count=${maxCount}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get export history');
  }

  return response.json();
}

/**
 * Clean up old exports
 */
export async function cleanupOldExports(maxAgeHours: number = 24): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/export/cleanup?max_age_hours=${maxAgeHours}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to cleanup exports');
  }
}

/**
 * Download all formats (PDF, DOCX, JSON)
 */
export async function downloadAllFormats(exportId: string, programName?: string): Promise<void> {
  // Download files sequentially to avoid overwhelming the browser
  await downloadPDF(exportId);
  await new Promise(resolve => setTimeout(resolve, 500)); // Small delay
  await downloadDOCX(exportId, programName);
  await new Promise(resolve => setTimeout(resolve, 500)); // Small delay
  await downloadJSON(exportId);
}

/**
 * Helper function to download a file from URL
 */
async function downloadFile(url: string, filename: string): Promise<void> {
  const response = await fetch(url);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to download ${filename}`);
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

/**
 * Calculate total document size from sections
 */
export function calculateDocumentSize(sections: Record<string, string>): number {
  let totalChars = 0;

  for (const content of Object.values(sections)) {
    // Strip HTML tags for more accurate size estimate
    const plainText = content.replace(/<[^>]*>/g, '');
    totalChars += plainText.length;
  }

  // Add overhead for title page, TOC, formatting (5KB)
  const overhead = 5000;

  return totalChars + overhead;
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(sizeBytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = sizeBytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Estimate file sizes for different formats
 */
export function estimateFileSizes(sections: Record<string, string>): {
  pdf: string;
  docx: string;
  json: string;
} {
  const baseSize = calculateDocumentSize(sections);

  return {
    pdf: formatFileSize(baseSize * 3),   // PDF is roughly 3x markdown
    docx: formatFileSize(baseSize * 2),  // DOCX is roughly 2x markdown
    json: formatFileSize(baseSize * 0.8) // JSON is slightly smaller
  };
}

/**
 * Validate export data before sending
 */
export function validateExportData(
  sections: Record<string, string>,
  citations: any[],
  metadata: any
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check sections
  if (!sections || Object.keys(sections).length === 0) {
    errors.push('No sections to export');
  }

  // Check for empty sections
  const emptySections = Object.entries(sections)
    .filter(([_, content]) => !content || content.trim().length === 0)
    .map(([name, _]) => name);

  if (emptySections.length > 0) {
    errors.push(`Empty sections: ${emptySections.join(', ')}`);
  }

  // Warn if no citations (not an error, just a warning)
  if (!citations || citations.length === 0) {
    console.warn('No citations provided for export');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
