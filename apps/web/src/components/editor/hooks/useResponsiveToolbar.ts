/**
 * useResponsiveToolbar Hook
 * 
 * Provides responsive behavior for the RibbonToolbar component.
 * Uses ResizeObserver to detect container width changes and determines
 * which toolbar groups should be collapsed into dropdown menus.
 * 
 * Similar to Microsoft Word's ribbon behavior where groups collapse
 * into compact dropdown buttons when space is limited.
 * 
 * Dependencies:
 * - ResizeObserver API (browser native)
 */

import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Breakpoints define at what container width each group should collapse.
 * Groups are ordered by collapse priority (first to collapse = least essential).
 * Values are in pixels.
 */
const COLLAPSE_BREAKPOINTS: Record<string, number> = {
  ACTIONS: 1200,    // Save, Download, Print - collapse first (least used during editing)
  VIEW: 1100,       // Zoom controls
  DOCUMENT: 1000,   // Word/char count display
  EDITING: 900,     // Undo/Redo/Search
  STYLES: 800,      // Normal Text dropdown
  PARAGRAPH: 700,   // Alignment, lists, indent
  // FONT never collapses - it's the most essential group
};

/**
 * Type for the groups that can be collapsed
 */
export type CollapsibleGroup = 'ACTIONS' | 'VIEW' | 'DOCUMENT' | 'EDITING' | 'STYLES' | 'PARAGRAPH' | 'FONT';

/**
 * Return type for the useResponsiveToolbar hook
 */
interface UseResponsiveToolbarReturn {
  /** Ref to attach to the toolbar container element */
  containerRef: React.RefObject<HTMLDivElement>;
  /** Set of currently collapsed group names */
  collapsedGroups: Set<string>;
  /** Helper function to check if a specific group is collapsed */
  isCollapsed: (group: string) => boolean;
  /** Current container width in pixels */
  containerWidth: number;
}

/**
 * useResponsiveToolbar - Hook for responsive toolbar behavior
 * 
 * @returns Object containing containerRef, collapsedGroups Set, and isCollapsed helper
 * 
 * @example
 * ```tsx
 * const { containerRef, isCollapsed } = useResponsiveToolbar();
 * 
 * return (
 *   <div ref={containerRef} className="toolbar">
 *     {isCollapsed('FONT') ? (
 *       <CollapsedGroup label="Font" icon={Type}>...</CollapsedGroup>
 *     ) : (
 *       <RibbonGroup label="Font">...</RibbonGroup>
 *     )}
 *   </div>
 * );
 * ```
 */
export function useResponsiveToolbar(): UseResponsiveToolbarReturn {
  // Ref for the container element to observe
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Track current container width
  const [containerWidth, setContainerWidth] = useState<number>(1200);
  
  // Set of currently collapsed groups
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  
  // Memoized helper to check if a group is collapsed
  const isCollapsed = useCallback((group: string): boolean => {
    return collapsedGroups.has(group);
  }, [collapsedGroups]);
  
  useEffect(() => {
    // Create ResizeObserver to watch container width changes
    const observer = new ResizeObserver((entries) => {
      // Get the content width of the observed element
      const width = entries[0].contentRect.width;
      setContainerWidth(width);
      
      // Determine which groups should be collapsed based on current width
      const newCollapsed = new Set<string>();
      
      Object.entries(COLLAPSE_BREAKPOINTS).forEach(([group, breakpoint]) => {
        if (width < breakpoint) {
          newCollapsed.add(group);
        }
      });
      
      // Only update state if the collapsed set has changed
      setCollapsedGroups(prevCollapsed => {
        // Check if sets are equal
        if (prevCollapsed.size !== newCollapsed.size) {
          return newCollapsed;
        }
        for (const item of newCollapsed) {
          if (!prevCollapsed.has(item)) {
            return newCollapsed;
          }
        }
        return prevCollapsed;
      });
    });
    
    // Start observing the container element
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    
    // Cleanup observer on unmount
    return () => {
      observer.disconnect();
    };
  }, []);
  
  return {
    containerRef,
    collapsedGroups,
    isCollapsed,
    containerWidth,
  };
}

export default useResponsiveToolbar;
