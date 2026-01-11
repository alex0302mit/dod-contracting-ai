/**
 * CollapsedGroup Component
 * 
 * A compact dropdown button that displays collapsed toolbar group contents.
 * Used when the toolbar width is too narrow to display the full group.
 * Mimics Microsoft Word's ribbon collapse behavior.
 * 
 * Features:
 * - Compact vertical button with icon and label
 * - Dropdown popover showing full group contents when clicked
 * - ChevronDown indicator showing it's expandable
 * 
 * Dependencies:
 * - Popover, PopoverContent, PopoverTrigger from shadcn/ui
 * - Button from shadcn/ui
 * - lucide-react icons
 */

import { ReactNode } from 'react';
import { ChevronDown, LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

/**
 * Props for the CollapsedGroup component
 */
interface CollapsedGroupProps {
  /** Label displayed below the icon */
  label: string;
  /** Icon component from lucide-react */
  icon: LucideIcon;
  /** The full group content to show in the dropdown */
  children: ReactNode;
  /** Optional additional className for the trigger button */
  className?: string;
}

/**
 * CollapsedGroup - Compact dropdown for collapsed toolbar groups
 * 
 * Displays as a small vertical button with an icon, label, and dropdown arrow.
 * When clicked, opens a popover containing the full group contents.
 * 
 * @example
 * ```tsx
 * <CollapsedGroup label="Font" icon={Type}>
 *   <FontFamilySelect editor={editor} />
 *   <FontSizeSelect editor={editor} />
 *   <BoldButton onClick={...} />
 * </CollapsedGroup>
 * ```
 */
export function CollapsedGroup({ 
  label, 
  icon: Icon, 
  children,
  className = ''
}: CollapsedGroupProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className={`h-[70px] px-2 flex flex-col items-center justify-center gap-0.5 rounded-md 
            hover:bg-slate-100 transition-colors ${className}`}
          title={`${label} (click to expand)`}
        >
          {/* Icon */}
          <Icon className="h-5 w-5 text-slate-600" />
          
          {/* Label */}
          <span className="text-[9px] uppercase tracking-wider text-slate-500 font-medium">
            {label}
          </span>
          
          {/* Dropdown indicator */}
          <ChevronDown className="h-3 w-3 text-slate-400" />
        </Button>
      </PopoverTrigger>
      
      <PopoverContent 
        className="w-auto p-3 shadow-lg rounded-lg border border-slate-200"
        align="start"
        sideOffset={4}
      >
        {/* Group label at top of dropdown */}
        <div className="text-xs font-semibold text-slate-600 mb-2 pb-2 border-b border-slate-100">
          {label}
        </div>
        
        {/* Full group contents */}
        <div className="flex flex-col gap-2">
          {children}
        </div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * CollapsedGroupDivider - Vertical divider between collapsed groups
 */
export function CollapsedGroupDivider() {
  return (
    <div className="w-px h-12 bg-slate-200 mx-1 self-center" />
  );
}

export default CollapsedGroup;
