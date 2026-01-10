/**
 * HorizontalRuler Component
 * 
 * Microsoft Word-style horizontal ruler with inch markings.
 * Displays margin indicators and measurement ticks.
 * 
 * Features:
 * - Inch markings (0-8.5 for letter size)
 * - Sub-tick marks for half and quarter inches
 * - Margin indicators (left/right margins)
 * - Draggable margin handles for real-time adjustment
 * - Scales with zoom level
 * 
 * Dependencies:
 *   - React hooks (useState, useRef, useEffect, useCallback)
 *   - editor-styles.css for styling
 */

import { useState, useRef, useEffect, useCallback } from 'react';

// Margin constraints (in inches)
const MIN_MARGIN = 0.5;  // Minimum margin: 0.5 inches (48px)
const MAX_MARGIN = 3;    // Maximum margin: 3 inches (288px)

// Props interface for HorizontalRuler
interface HorizontalRulerProps {
  zoomLevel?: number;
  leftMargin?: number;  // in inches
  rightMargin?: number; // in inches
  pageWidth?: number;   // in inches (8.5 for letter)
  onLeftMarginChange?: (margin: number) => void;   // Callback when left margin changes
  onRightMarginChange?: (margin: number) => void;  // Callback when right margin changes
}

/**
 * Generate tick marks for the ruler
 * @param pageWidth - Width in inches
 * @returns Array of tick mark data
 */
function generateTicks(pageWidth: number) {
  const ticks: { position: number; type: 'major' | 'half' | 'quarter'; label?: string }[] = [];
  
  for (let inch = 0; inch <= pageWidth; inch++) {
    // Major tick (full inch)
    ticks.push({ position: inch, type: 'major', label: inch > 0 ? String(inch) : undefined });
    
    // Quarter ticks
    if (inch < pageWidth) {
      ticks.push({ position: inch + 0.25, type: 'quarter' });
      ticks.push({ position: inch + 0.5, type: 'half' });
      ticks.push({ position: inch + 0.75, type: 'quarter' });
    }
  }
  
  return ticks;
}

/**
 * HorizontalRuler - Document ruler with measurement marks
 * 
 * Provides visual reference for document margins and alignment.
 * Styled to match Microsoft Word's ruler appearance.
 * Supports draggable margin handles for real-time margin adjustment.
 */
export function HorizontalRuler({
  zoomLevel = 100,
  leftMargin = 1,
  rightMargin = 1,
  pageWidth = 8.5,
  onLeftMarginChange,
  onRightMarginChange,
}: HorizontalRulerProps) {
  // Ref for the ruler track element to calculate mouse positions
  const rulerTrackRef = useRef<HTMLDivElement>(null);
  
  // Track which margin handle is currently being dragged
  const [dragging, setDragging] = useState<'left' | 'right' | null>(null);
  
  // Calculate pixels per inch based on zoom
  // 96 DPI is standard for screens
  const pixelsPerInch = (96 * zoomLevel) / 100;
  
  // Calculate ruler width
  const rulerWidthPx = pageWidth * pixelsPerInch;
  
  // Generate tick marks
  const ticks = generateTicks(pageWidth);
  
  // Calculate margin positions
  const leftMarginPx = leftMargin * pixelsPerInch;
  const rightMarginPx = rightMargin * pixelsPerInch;
  const contentWidth = rulerWidthPx - leftMarginPx - rightMarginPx;

  /**
   * Handle mouse move during drag
   * Calculates new margin based on mouse position relative to ruler
   */
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!dragging || !rulerTrackRef.current) return;
    
    const rulerRect = rulerTrackRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rulerRect.left;
    
    if (dragging === 'left') {
      // Calculate new left margin in inches
      const newMarginInches = mouseX / pixelsPerInch;
      // Clamp to valid range (also ensure left + right margins don't exceed page width)
      const maxLeftMargin = Math.min(MAX_MARGIN, pageWidth - rightMargin - 1);
      const clampedMargin = Math.max(MIN_MARGIN, Math.min(maxLeftMargin, newMarginInches));
      // Round to nearest 0.125 inch (1/8 inch) for snapping
      const snappedMargin = Math.round(clampedMargin * 8) / 8;
      onLeftMarginChange?.(snappedMargin);
    } else if (dragging === 'right') {
      // Calculate new right margin in inches (from right edge)
      const newMarginInches = (rulerWidthPx - mouseX) / pixelsPerInch;
      // Clamp to valid range (also ensure left + right margins don't exceed page width)
      const maxRightMargin = Math.min(MAX_MARGIN, pageWidth - leftMargin - 1);
      const clampedMargin = Math.max(MIN_MARGIN, Math.min(maxRightMargin, newMarginInches));
      // Round to nearest 0.125 inch (1/8 inch) for snapping
      const snappedMargin = Math.round(clampedMargin * 8) / 8;
      onRightMarginChange?.(snappedMargin);
    }
  }, [dragging, pixelsPerInch, rulerWidthPx, pageWidth, leftMargin, rightMargin, onLeftMarginChange, onRightMarginChange]);

  /**
   * Handle mouse up to end drag
   */
  const handleMouseUp = useCallback(() => {
    setDragging(null);
  }, []);

  // Add/remove global mouse listeners when dragging
  useEffect(() => {
    if (dragging) {
      // Add listeners to window so drag continues even if mouse leaves ruler
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      // Add cursor style to body during drag
      document.body.style.cursor = 'ew-resize';
      // Prevent text selection during drag
      document.body.style.userSelect = 'none';
    }
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [dragging, handleMouseMove, handleMouseUp]);

  /**
   * Start dragging the left margin handle
   */
  const handleLeftMarginMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setDragging('left');
  };

  /**
   * Start dragging the right margin handle
   */
  const handleRightMarginMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setDragging('right');
  };

  return (
    <div className="horizontal-ruler bg-gray-100 border-b border-gray-300 h-6 overflow-hidden flex justify-center">
      {/* Ruler track - ref used for calculating mouse position during drag */}
      <div 
        ref={rulerTrackRef}
        className="ruler-track relative h-full bg-white"
        style={{ width: rulerWidthPx }}
      >
        {/* Left margin indicator */}
        <div 
          className="ruler-margin-left absolute top-0 bottom-0 bg-gray-200"
          style={{ width: leftMarginPx, left: 0 }}
        />
        
        {/* Right margin indicator */}
        <div 
          className="ruler-margin-right absolute top-0 bottom-0 bg-gray-200"
          style={{ width: rightMarginPx, right: 0 }}
        />
        
        {/* Content area (lighter) */}
        <div 
          className="ruler-content absolute top-0 bottom-0 bg-white"
          style={{ left: leftMarginPx, width: contentWidth }}
        />
        
        {/* Tick marks */}
        {ticks.map((tick, index) => {
          const left = tick.position * pixelsPerInch;
          const height = tick.type === 'major' ? 12 : tick.type === 'half' ? 8 : 4;
          
          return (
            <div
              key={index}
              className="ruler-tick absolute bottom-0"
              style={{
                left: left,
                height: height,
                width: 1,
                backgroundColor: '#6b7280',
              }}
            >
              {/* Label for major ticks */}
              {tick.label && (
                <span
                  className="absolute text-[9px] text-gray-600 font-medium"
                  style={{
                    top: -12,
                    left: '50%',
                    transform: 'translateX(-50%)',
                  }}
                >
                  {tick.label}
                </span>
              )}
            </div>
          );
        })}
        
        {/* Left margin handle - draggable */}
        <div
          className={`ruler-handle absolute top-1 cursor-ew-resize z-10 ${dragging === 'left' ? 'scale-110' : 'hover:scale-110'} transition-transform`}
          style={{ left: leftMarginPx - 4 }}
          title={`Left margin: ${leftMargin}" (drag to adjust)`}
          onMouseDown={handleLeftMarginMouseDown}
        >
          <div className={`w-0 h-0 border-l-4 border-r-4 border-b-4 border-l-transparent border-r-transparent ${dragging === 'left' ? 'border-b-blue-600' : 'border-b-gray-500 hover:border-b-blue-500'} transition-colors`} />
        </div>
        
        {/* Right margin handle - draggable */}
        <div
          className={`ruler-handle absolute top-1 cursor-ew-resize z-10 ${dragging === 'right' ? 'scale-110' : 'hover:scale-110'} transition-transform`}
          style={{ right: rightMarginPx - 4 }}
          title={`Right margin: ${rightMargin}" (drag to adjust)`}
          onMouseDown={handleRightMarginMouseDown}
        >
          <div className={`w-0 h-0 border-l-4 border-r-4 border-b-4 border-l-transparent border-r-transparent ${dragging === 'right' ? 'border-b-blue-600' : 'border-b-gray-500 hover:border-b-blue-500'} transition-colors`} />
        </div>
      </div>
    </div>
  );
}

export default HorizontalRuler;
