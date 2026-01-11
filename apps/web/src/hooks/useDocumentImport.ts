import { useState, useCallback } from 'react';
import mammoth from 'mammoth';

export type ImportPlacement = 'new_section' | 'replace_current' | 'append_current';

export interface ImportResult {
  html: string;
  filename: string;
  fileType: 'pdf' | 'docx';
  warnings?: string[];
}

export interface ImportOptions {
  placement: ImportPlacement;
  sectionName?: string; // Required when placement is 'new_section'
}

const SUPPORTED_TYPES = {
  'application/pdf': 'pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
} as const;

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB

export function useDocumentImport() {
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  /**
   * Validate file before processing
   */
  const validateFile = useCallback((file: File): { valid: boolean; error?: string; fileType?: 'pdf' | 'docx' } => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return { valid: false, error: `File size exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit` };
    }

    // Check file type
    const fileType = SUPPORTED_TYPES[file.type as keyof typeof SUPPORTED_TYPES];
    if (!fileType) {
      // Also check by extension as fallback
      const ext = file.name.toLowerCase().split('.').pop();
      if (ext === 'pdf') {
        return { valid: true, fileType: 'pdf' };
      } else if (ext === 'docx') {
        return { valid: true, fileType: 'docx' };
      }
      return { valid: false, error: 'Unsupported file type. Please use PDF or DOCX files.' };
    }

    return { valid: true, fileType };
  }, []);

  /**
   * Enhance HTML with better table styling for Tiptap
   */
  const enhanceHtml = (html: string): string => {
    return html
      // Add styling to tables for better rendering
      .replace(/<table>/g, '<table class="border-collapse w-full">')
      .replace(/<td>/g, '<td class="border border-slate-300 p-2">')
      .replace(/<td /g, '<td class="border border-slate-300 p-2" ')
      .replace(/<th>/g, '<th class="border border-slate-300 p-2 bg-slate-100 font-semibold">')
      .replace(/<th /g, '<th class="border border-slate-300 p-2 bg-slate-100 font-semibold" ');
  };

  /**
   * Detect bold-only paragraphs and convert to headings
   * Heuristics:
   * - Paragraph contains only <strong> or <b> tag (no other text outside)
   * - Text is short (< 100 chars, typically < 10 words)
   * - Not ending with : (likely a label like "Program Name:")
   * - Not a single short word (like "Note" or "Warning")
   */
  const detectAndConvertHeadings = (html: string): string => {
    // Pattern: <p><strong>Short text</strong></p> or <p><b>Short text</b></p>
    const boldParagraphPattern = /<p>\s*<(strong|b)>([^<]+)<\/\1>\s*<\/p>/gi;

    return html.replace(boldParagraphPattern, (match, tag, text) => {
      const trimmedText = text.trim();

      // Skip if too long (probably not a heading)
      if (trimmedText.length > 100) return match;

      // Skip if it ends with : (likely a label like "Program Name:")
      if (trimmedText.endsWith(':')) return match;

      // Skip single words under 15 chars (like "Note" or "Warning")
      if (!trimmedText.includes(' ') && trimmedText.length < 15) return match;

      // Convert to h2 (most common heading level for section titles)
      return `<h2>${trimmedText}</h2>`;
    });
  };

  /**
   * Convert DOCX to HTML using mammoth.js (frontend)
   */
  const convertDocxToHtml = useCallback(async (file: File): Promise<ImportResult> => {
    setProgress(20);

    const arrayBuffer = await file.arrayBuffer();
    setProgress(40);

    const result = await mammoth.convertToHtml(
      { arrayBuffer },
      {
        styleMap: [
          "p[style-name='Heading 1'] => h1:fresh",
          "p[style-name='Heading 2'] => h2:fresh",
          "p[style-name='Heading 3'] => h3:fresh",
          "p[style-name='Heading 4'] => h4:fresh",
          "p[style-name='Title'] => h1:fresh",
          "p[style-name='Subtitle'] => h2:fresh",
          "b => strong",
          "i => em",
          "u => u",
          "strike => s",
          "p[style-name='List Paragraph'] => li:fresh",
        ],
        // Convert images to embedded base64
        convertImage: mammoth.images.imgElement(async (image) => {
          const buffer = await image.read();
          const bytes = new Uint8Array(buffer);
          let binary = '';
          for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
          }
          const base64 = btoa(binary);
          const mimeType = image.contentType || 'image/png';
          return { src: `data:${mimeType};base64,${base64}` };
        }),
      }
    );

    setProgress(80);

    // Clean up and enhance the HTML for Tiptap compatibility
    let html = result.value;

    // Ensure paragraphs are wrapped
    if (!html.includes('<p>') && !html.includes('<h')) {
      html = `<p>${html}</p>`;
    }

    // Enhance tables with styling
    html = enhanceHtml(html);

    // Detect bold paragraphs that should be headings
    html = detectAndConvertHeadings(html);

    setProgress(100);

    return {
      html,
      filename: file.name,
      fileType: 'docx',
      warnings: result.messages.map(m => m.message),
    };
  }, []);

  /**
   * Convert PDF to HTML using backend Docling (with OCR support)
   */
  const convertPdfToHtml = useCallback(async (file: File): Promise<ImportResult> => {
    setProgress(10);

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const token = localStorage.getItem('auth_token');

    const formData = new FormData();
    formData.append('file', file);

    setProgress(30);

    const response = await fetch(`${API_BASE_URL}/api/documents/convert-to-html`, {
      method: 'POST',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    setProgress(70);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `PDF conversion failed: ${response.statusText}`);
    }

    const data = await response.json();
    setProgress(100);

    return {
      html: data.html,
      filename: file.name,
      fileType: 'pdf',
      warnings: data.warnings,
    };
  }, []);

  /**
   * Main conversion function - routes to appropriate converter
   */
  const convertFile = useCallback(async (file: File): Promise<ImportResult | null> => {
    setError(null);
    setConverting(true);
    setProgress(0);

    try {
      // Validate file
      const validation = validateFile(file);
      if (!validation.valid) {
        setError(validation.error || 'Invalid file');
        return null;
      }

      // Route to appropriate converter
      if (validation.fileType === 'docx') {
        return await convertDocxToHtml(file);
      } else if (validation.fileType === 'pdf') {
        return await convertPdfToHtml(file);
      }

      setError('Unknown file type');
      return null;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Conversion failed';
      setError(message);
      console.error('Document conversion error:', err);
      return null;
    } finally {
      setConverting(false);
      setTimeout(() => setProgress(0), 500);
    }
  }, [validateFile, convertDocxToHtml, convertPdfToHtml]);

  /**
   * Check if a file is supported for import
   */
  const isSupported = useCallback((file: File): boolean => {
    return validateFile(file).valid;
  }, [validateFile]);

  /**
   * Get accepted file types for input elements
   */
  const acceptedTypes = '.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document';

  return {
    convertFile,
    isSupported,
    validateFile,
    converting,
    progress,
    error,
    acceptedTypes,
    clearError: () => setError(null),
  };
}
