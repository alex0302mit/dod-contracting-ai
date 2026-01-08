/**
 * DocumentCanvas Component
 * 
 * Provides a page-like visual container for the editor content.
 * Creates a Word-document-like appearance with white page on gray background.
 * 
 * Features:
 * - Gray background behind the "page"
 * - White page container with shadow
 * - Adjustable left/right margins (controlled via props)
 * - Zoom scaling support
 * - Responsive scaling for smaller screens
 * 
 * Dependencies:
 *   - editor-styles.css for styling
 */

import { ReactNode, CSSProperties } from 'react';

// Standard DPI for screen calculations
const SCREEN_DPI = 96;

// Default top/bottom margin in pixels (0.75 inches)
const DEFAULT_VERTICAL_MARGIN = 72;

// Props interface for DocumentCanvas
interface DocumentCanvasProps {
  children: ReactNode;
  className?: string;
  zoomLevel?: number;    // Zoom percentage (50-200)
  leftMargin?: number;   // Left margin in inches (default 1)
  rightMargin?: number;  // Right margin in inches (default 1)
}

/**
 * DocumentCanvas - Page-like wrapper for editor content
 * 
 * Creates a visual appearance similar to Microsoft Word's print layout view,
 * with a white document page displayed on a gray background.
 * Supports zoom scaling via CSS transform and adjustable margins.
 */
export function DocumentCanvas({ 
  children, 
  className = '',
  zoomLevel = 100,
  leftMargin = 1,
  rightMargin = 1,
}: DocumentCanvasProps) {
  // Calculate the scale factor from zoom percentage
  const scale = zoomLevel / 100;
  
  // Convert margin inches to pixels (96 DPI standard)
  const leftMarginPx = leftMargin * SCREEN_DPI;
  const rightMarginPx = rightMargin * SCREEN_DPI;
  
  // Page styles with zoom transform
  const pageStyle: CSSProperties = {
    transform: `scale(${scale})`,
    transformOrigin: 'top center',
    // Adjust the effective height to account for scaling
    // This prevents the container from having empty space
    marginBottom: scale < 1 ? `calc(-1056px * ${1 - scale})` : 0,
  };
  
  // Content styles with dynamic margins
  // Uses inline styles to override CSS defaults with user-adjustable values
  const contentStyle: CSSProperties = {
    paddingLeft: `${leftMarginPx}px`,
    paddingRight: `${rightMarginPx}px`,
    paddingTop: `${DEFAULT_VERTICAL_MARGIN}px`,
    paddingBottom: `${DEFAULT_VERTICAL_MARGIN}px`,
  };

  return (
    <div className={`document-canvas-wrapper ${className}`}>
      {/* Background area with subtle pattern */}
      <div className="document-canvas-background">
        {/* Page container - represents the actual document */}
        <div className="document-page" style={pageStyle}>
          {/* Content area with adjustable margins */}
          <div className="document-content" style={contentStyle}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * DocumentCanvasSimple - Simplified version without page appearance
 * 
 * Use this when you want the editor content without the page-like styling.
 * Useful for embedded editors or full-width editing modes.
 */
export function DocumentCanvasSimple({ 
  children, 
  className = '',
  zoomLevel = 100 
}: DocumentCanvasProps) {
  const scale = zoomLevel / 100;
  
  const contentStyle: CSSProperties = zoomLevel !== 100 ? {
    transform: `scale(${scale})`,
    transformOrigin: 'top left',
  } : {};

  return (
    <div className={`document-canvas-simple ${className}`} style={contentStyle}>
      {children}
    </div>
  );
}

export default DocumentCanvas;
