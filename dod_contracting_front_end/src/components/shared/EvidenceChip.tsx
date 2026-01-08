/**
 * EvidenceChip Component
 * 
 * Inline citation chip that displays as [1], [2], etc.
 * Hover shows a preview of the source in a HoverCard.
 * Click opens ConsoleRail to Citations tab.
 * 
 * Dependencies:
 * - HoverCard from shadcn/ui
 * - ConsoleRailContext for rail integration
 * - Badge component
 */

import { Badge } from '@/components/ui/badge';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { useConsoleRail } from '@/contexts/ConsoleRailContext';
import { cn } from '@/lib/utils';
import { FileText, BookOpen, Folder } from 'lucide-react';

// Source type definitions
export type SourceType = 'regulation' | 'template' | 'past_contract' | 'market_research' | 'other';

interface EvidenceChipProps {
  /** Citation ID number to display */
  citationId: number;
  /** Source document name/title */
  source: string;
  /** Preview text snippet */
  text: string;
  /** Type of source document */
  sourceType?: SourceType;
  /** Page number if applicable */
  page?: number;
  /** Click handler - defaults to opening ConsoleRail */
  onClick?: () => void;
  /** Additional className */
  className?: string;
}

// Source type configuration for display
const sourceTypeConfig: Record<SourceType, {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}> = {
  regulation: { label: 'Regulation', icon: BookOpen, color: 'text-info' },
  template: { label: 'Template', icon: FileText, color: 'text-ai' },
  past_contract: { label: 'Past Contract', icon: Folder, color: 'text-success' },
  market_research: { label: 'Market Research', icon: FileText, color: 'text-warning' },
  other: { label: 'Source', icon: FileText, color: 'text-muted-foreground' },
};

/**
 * EvidenceChip displays an inline citation that shows source details on hover
 */
export function EvidenceChip({ 
  citationId,
  source,
  text,
  sourceType = 'other',
  page,
  onClick,
  className 
}: EvidenceChipProps) {
  const { openRail } = useConsoleRail();
  const typeConfig = sourceTypeConfig[sourceType];
  const Icon = typeConfig.icon;
  
  // Default click handler opens ConsoleRail to citations tab
  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      openRail('citations');
    }
  };
  
  return (
    <HoverCard openDelay={200} closeDelay={100}>
      <HoverCardTrigger asChild>
        <button
          onClick={handleClick}
          className={cn(
            "inline-flex items-center px-1.5 py-0.5 rounded text-xs",
            "bg-muted hover:bg-primary/10 text-muted-foreground hover:text-primary",
            "cursor-pointer transition-colors font-mono",
            className
          )}
        >
          [{citationId}]
        </button>
      </HoverCardTrigger>
      <HoverCardContent className="w-80" side="top" align="center">
        <div className="space-y-2">
          {/* Source header */}
          <div className="flex items-start gap-2">
            <Icon className={cn("h-4 w-4 mt-0.5 flex-shrink-0", typeConfig.color)} />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{source}</p>
              {page && (
                <p className="text-xs text-muted-foreground">Page {page}</p>
              )}
            </div>
          </div>
          
          {/* Text preview */}
          <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
            "{text}"
          </p>
          
          {/* Source type badge */}
          <Badge variant="secondary" className="text-xs">
            {typeConfig.label}
          </Badge>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}

/**
 * EvidenceChipInline - A simpler version for use in text content
 * Without hover card, just a styled number
 */
export function EvidenceChipInline({ 
  citationId,
  onClick,
  className 
}: Pick<EvidenceChipProps, 'citationId' | 'onClick' | 'className'>) {
  const { openRail } = useConsoleRail();
  
  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      openRail('citations');
    }
  };
  
  return (
    <button
      onClick={handleClick}
      className={cn(
        "inline-flex items-center px-1 py-0 rounded text-[10px]",
        "bg-muted hover:bg-primary/10 text-muted-foreground hover:text-primary",
        "cursor-pointer transition-colors font-mono align-super",
        className
      )}
    >
      [{citationId}]
    </button>
  );
}

export default EvidenceChip;
