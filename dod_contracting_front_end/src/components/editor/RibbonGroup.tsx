/**
 * RibbonGroup Component
 * 
 * Microsoft Word-style ribbon group container with bottom label.
 * Groups related toolbar buttons together with a descriptive label.
 * 
 * Features:
 * - Vertical separator on the right side
 * - Bottom label for group identification
 * - Flexible content area for buttons
 * 
 * Usage:
 *   <RibbonGroup label="Font">
 *     <FontFamilySelect />
 *     <FontSizeSelect />
 *     <BoldButton />
 *   </RibbonGroup>
 */

import { ReactNode } from 'react';

// Props interface for RibbonGroup
interface RibbonGroupProps {
  label: string;
  children: ReactNode;
  className?: string;
  showSeparator?: boolean;
}

/**
 * RibbonGroup - Container for grouping related ribbon controls
 * 
 * Creates visual separation between different toolbar sections
 * with a label at the bottom identifying the group's purpose.
 */
export function RibbonGroup({
  label,
  children,
  className = '',
  showSeparator = true
}: RibbonGroupProps) {
  return (
    <div className={`ribbon-group flex flex-col ${className}`}>
      {/* Controls area - horizontal row of buttons/controls */}
      <div className="ribbon-group-controls flex items-center gap-1 px-2 py-1.5 min-h-[56px]">
        {children}
      </div>

      {/* Group label */}
      <div className="ribbon-group-label text-center pb-1">
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium leading-none">
          {label}
        </span>
      </div>

      {/* Vertical separator (optional) */}
      {showSeparator && (
        <div className="ribbon-group-separator absolute right-0 top-2 bottom-2 w-px bg-gradient-to-b from-transparent via-slate-200 to-transparent" />
      )}
    </div>
  );
}

/**
 * RibbonGroupRow - Horizontal sub-row within a RibbonGroup
 * 
 * Used for stacking multiple rows of controls within a single group.
 * Word uses this pattern for the Font group (family/size on top, B/I/U below).
 */
interface RibbonGroupRowProps {
  children: ReactNode;
  className?: string;
}

export function RibbonGroupRow({ children, className = '' }: RibbonGroupRowProps) {
  return (
    <div className={`ribbon-group-row flex items-center gap-0.5 ${className}`}>
      {children}
    </div>
  );
}

/**
 * RibbonDivider - Vertical divider between ribbon groups
 *
 * Standalone divider component for use between groups.
 */
export function RibbonDivider() {
  return (
    <div className="ribbon-divider w-px h-14 bg-gradient-to-b from-transparent via-slate-300/60 to-transparent mx-1.5 self-center" />
  );
}

export default RibbonGroup;
