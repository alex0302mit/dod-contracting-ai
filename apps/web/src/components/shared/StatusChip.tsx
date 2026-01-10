/**
 * StatusChip Component
 * 
 * Semantic status badge that maps document/workflow status to ACES colors.
 * 
 * Strict color rules:
 * - Green (success) = approved/verified
 * - Blue (info) = active/in progress
 * - Amber (warning) = needs review/risk
 * - Red (destructive) = blocking/noncompliance
 * - Violet (ai) = AI-only actions (NEVER for risk)
 * 
 * Dependencies:
 * - Badge component from shadcn/ui
 * - lucide-react icons
 */

import { 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  XCircle, 
  Sparkles,
  CircleDot
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

// Status type definition
export type StatusType = 
  | 'approved' 
  | 'in_progress' 
  | 'needs_review' 
  | 'blocking' 
  | 'ai_generated' 
  | 'pending'
  | 'uploaded'
  | 'under_review'
  | 'rejected'
  | 'expired'
  | 'generated'
  | 'generating'
  | 'failed';

// Status configuration mapping
const statusConfig: Record<StatusType, {
  bg: string;
  fg: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}> = {
  approved: { 
    bg: 'bg-success', 
    fg: 'text-success-foreground', 
    icon: CheckCircle, 
    label: 'Approved' 
  },
  in_progress: { 
    bg: 'bg-info', 
    fg: 'text-info-foreground', 
    icon: Clock, 
    label: 'In Progress' 
  },
  needs_review: { 
    bg: 'bg-warning', 
    fg: 'text-warning-foreground', 
    icon: AlertTriangle, 
    label: 'Needs Review' 
  },
  blocking: { 
    bg: 'bg-destructive', 
    fg: 'text-destructive-foreground', 
    icon: XCircle, 
    label: 'Blocking' 
  },
  ai_generated: { 
    bg: 'bg-ai', 
    fg: 'text-ai-foreground', 
    icon: Sparkles, 
    label: 'AI Generated' 
  },
  pending: { 
    bg: 'bg-muted', 
    fg: 'text-muted-foreground', 
    icon: CircleDot, 
    label: 'Pending' 
  },
  // Additional status mappings for document states
  uploaded: { 
    bg: 'bg-info', 
    fg: 'text-info-foreground', 
    icon: CheckCircle, 
    label: 'Uploaded' 
  },
  under_review: { 
    bg: 'bg-warning', 
    fg: 'text-warning-foreground', 
    icon: Clock, 
    label: 'Under Review' 
  },
  rejected: { 
    bg: 'bg-destructive', 
    fg: 'text-destructive-foreground', 
    icon: XCircle, 
    label: 'Rejected' 
  },
  expired: { 
    bg: 'bg-muted', 
    fg: 'text-muted-foreground', 
    icon: Clock, 
    label: 'Expired' 
  },
  generated: { 
    bg: 'bg-ai', 
    fg: 'text-ai-foreground', 
    icon: Sparkles, 
    label: 'Generated' 
  },
  generating: { 
    bg: 'bg-info', 
    fg: 'text-info-foreground', 
    icon: Clock, 
    label: 'Generating' 
  },
  failed: { 
    bg: 'bg-destructive', 
    fg: 'text-destructive-foreground', 
    icon: XCircle, 
    label: 'Failed' 
  },
};

interface StatusChipProps {
  /** Status to display */
  status: StatusType;
  /** Size variant */
  size?: 'sm' | 'md';
  /** Whether to show the icon */
  showIcon?: boolean;
  /** Custom label override */
  label?: string;
  /** Additional className */
  className?: string;
}

/**
 * StatusChip displays a colored badge with icon based on status
 */
export function StatusChip({ 
  status, 
  size = 'md', 
  showIcon = true,
  label,
  className 
}: StatusChipProps) {
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;
  const displayLabel = label || config.label;
  
  return (
    <Badge
      className={cn(
        config.bg,
        config.fg,
        "gap-1 font-medium",
        size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-xs px-2 py-1',
        className
      )}
    >
      {showIcon && (
        <Icon className={cn(
          "flex-shrink-0",
          size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'
        )} />
      )}
      {displayLabel}
    </Badge>
  );
}

/**
 * Helper function to convert various status strings to StatusType
 */
export function normalizeStatus(status: string): StatusType {
  const normalized = status.toLowerCase().replace(/[_-]/g, '_');
  
  // Map common status strings to StatusType
  const statusMap: Record<string, StatusType> = {
    'approved': 'approved',
    'completed': 'approved',
    'in_progress': 'in_progress',
    'active': 'in_progress',
    'needs_review': 'needs_review',
    'review': 'needs_review',
    'blocking': 'blocking',
    'blocked': 'blocking',
    'ai_generated': 'ai_generated',
    'ai': 'ai_generated',
    'pending': 'pending',
    'not_started': 'pending',
    'uploaded': 'uploaded',
    'under_review': 'under_review',
    'rejected': 'rejected',
    'expired': 'expired',
    'generated': 'generated',
    'generating': 'generating',
    'failed': 'failed',
    'error': 'failed',
  };
  
  return statusMap[normalized] || 'pending';
}

export default StatusChip;
