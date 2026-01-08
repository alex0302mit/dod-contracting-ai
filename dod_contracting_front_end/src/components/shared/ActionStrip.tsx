/**
 * ActionStrip Component
 * 
 * Page-level action bar enforcing the "one primary CTA" rule.
 * Provides a consistent layout for page actions across ACES screens.
 * 
 * Features:
 * - Single primary action (emphasized button)
 * - Multiple secondary actions (ghost/outline buttons)
 * - Slot for custom content (filters, search, toggles)
 * 
 * Dependencies:
 * - Button from shadcn/ui
 * - Loader2 for loading state
 */

import { ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Action configuration type
interface ActionConfig {
  label: string;
  onClick: () => void;
  icon?: ReactNode;
  loading?: boolean;
  disabled?: boolean;
}

interface ActionStripProps {
  /** Primary action - emphasized button (max 1) */
  primaryAction?: ActionConfig;
  /** Secondary actions - ghost/outline buttons */
  secondaryActions?: ActionConfig[];
  /** Custom content slot (filters, search, view toggles) */
  children?: ReactNode;
  /** Additional className for the container */
  className?: string;
  /** Stick to top of container */
  sticky?: boolean;
}

/**
 * ActionStrip provides a consistent action bar layout
 * 
 * Layout:
 * [Custom Content / Children]     [Secondary Actions] [Primary Action]
 */
export function ActionStrip({
  primaryAction,
  secondaryActions = [],
  children,
  className,
  sticky = false,
}: ActionStripProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 py-3 px-4 border-b border-border bg-card",
        sticky && "sticky top-0 z-10",
        className
      )}
    >
      {/* Left section: Custom content */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {children}
      </div>
      
      {/* Right section: Actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Secondary actions */}
        {secondaryActions.map((action, idx) => (
          <Button
            key={idx}
            variant="outline"
            size="sm"
            onClick={action.onClick}
            disabled={action.loading || action.disabled}
            className="gap-2"
          >
            {action.loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              action.icon
            )}
            <span className="hidden sm:inline">{action.label}</span>
          </Button>
        ))}
        
        {/* Primary action */}
        {primaryAction && (
          <Button
            variant="default"
            size="sm"
            onClick={primaryAction.onClick}
            disabled={primaryAction.loading || primaryAction.disabled}
            className="gap-2"
          >
            {primaryAction.loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              primaryAction.icon
            )}
            {primaryAction.label}
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * ActionStripSeparator - Visual separator for action groups
 */
export function ActionStripSeparator() {
  return <div className="h-6 w-px bg-border" />;
}

export default ActionStrip;
