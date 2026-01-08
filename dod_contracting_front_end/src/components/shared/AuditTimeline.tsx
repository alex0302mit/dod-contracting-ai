/**
 * AuditTimeline Component
 * 
 * Displays a minimal timeline of audit events for approvals and documents.
 * Shows timestamps, actors, actions, and optional details.
 * 
 * Dependencies:
 * - ApprovalAuditLog type from api.ts
 * - date-fns for timestamp formatting
 * - ScrollArea for long lists
 */

import { format, formatDistanceToNow } from 'date-fns';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  User, 
  Edit, 
  Send,
  RotateCcw
} from 'lucide-react';

// Audit event type (matches ApprovalAuditLog from api.ts)
export interface AuditEvent {
  id: string;
  action: string;
  performed_by: string;
  timestamp: string;
  details?: string;
  performed_by_user?: {
    id?: string;
    name: string;
    email?: string;
    role?: string;
  };
}

interface AuditTimelineProps {
  /** List of audit events to display */
  events: AuditEvent[];
  /** Click handler for event details */
  onEventClick?: (event: AuditEvent) => void;
  /** Maximum height before scrolling */
  maxHeight?: string;
  /** Show relative timestamps */
  relativeTime?: boolean;
  /** Additional className */
  className?: string;
}

// Action type to icon mapping
const actionIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  'approved': CheckCircle,
  'rejected': XCircle,
  'requested': Send,
  'delegated': RotateCcw,
  'created': Clock,
  'updated': Edit,
  'submitted': Send,
};

// Action type to color mapping
const actionColors: Record<string, string> = {
  'approved': 'text-success bg-success/10',
  'rejected': 'text-destructive bg-destructive/10',
  'requested': 'text-info bg-info/10',
  'delegated': 'text-warning bg-warning/10',
  'created': 'text-muted-foreground bg-muted',
  'updated': 'text-info bg-info/10',
  'submitted': 'text-info bg-info/10',
};

/**
 * Get icon for action type
 */
function getActionIcon(action: string): React.ComponentType<{ className?: string }> {
  const normalizedAction = action.toLowerCase();
  for (const [key, Icon] of Object.entries(actionIcons)) {
    if (normalizedAction.includes(key)) {
      return Icon;
    }
  }
  return Clock;
}

/**
 * Get color for action type
 */
function getActionColor(action: string): string {
  const normalizedAction = action.toLowerCase();
  for (const [key, color] of Object.entries(actionColors)) {
    if (normalizedAction.includes(key)) {
      return color;
    }
  }
  return 'text-muted-foreground bg-muted';
}

/**
 * AuditTimeline displays chronological audit events
 */
export function AuditTimeline({
  events,
  onEventClick,
  maxHeight = '400px',
  relativeTime = true,
  className,
}: AuditTimelineProps) {
  if (events.length === 0) {
    return (
      <div className={cn("text-center py-8 text-muted-foreground", className)}>
        <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No audit history</p>
        <p className="text-xs mt-1">Events will appear here as actions occur</p>
      </div>
    );
  }
  
  // Sort events by timestamp (most recent first)
  const sortedEvents = [...events].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  
  return (
    <ScrollArea style={{ maxHeight }} className={className}>
      <div className="relative pl-6 pr-2 py-2">
        {/* Vertical timeline line */}
        <div className="absolute left-[11px] top-4 bottom-4 w-0.5 bg-border" />
        
        {/* Events */}
        <div className="space-y-4">
          {sortedEvents.map((event, idx) => {
            const Icon = getActionIcon(event.action);
            const colorClass = getActionColor(event.action);
            const actorName = event.performed_by_user?.name || event.performed_by;
            
            return (
              <div
                key={event.id || idx}
                className={cn(
                  "relative group",
                  onEventClick && "cursor-pointer"
                )}
                onClick={() => onEventClick?.(event)}
              >
                {/* Timeline dot */}
                <div className={cn(
                  "absolute -left-6 w-5 h-5 rounded-full flex items-center justify-center",
                  "border-2 border-background",
                  colorClass
                )}>
                  <Icon className="h-3 w-3" />
                </div>
                
                {/* Event content */}
                <div className={cn(
                  "pl-2 pb-2",
                  onEventClick && "group-hover:bg-muted/50 rounded-lg -ml-1 pl-3 transition-colors"
                )}>
                  {/* Action */}
                  <p className="font-medium text-sm">{event.action}</p>
                  
                  {/* Actor */}
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                    <User className="h-3 w-3" />
                    <span>{actorName}</span>
                    {event.performed_by_user?.role && (
                      <Badge variant="outline" className="text-[10px] px-1 py-0">
                        {event.performed_by_user.role.replace('_', ' ')}
                      </Badge>
                    )}
                  </div>
                  
                  {/* Timestamp */}
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {relativeTime 
                      ? formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })
                      : format(new Date(event.timestamp), 'MMM d, yyyy h:mm a')
                    }
                  </p>
                  
                  {/* Details */}
                  {event.details && (
                    <p className="text-xs text-muted-foreground mt-1 bg-muted/50 rounded p-2">
                      {event.details}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </ScrollArea>
  );
}

/**
 * AuditTimelineCompact - Condensed version for small spaces
 */
export function AuditTimelineCompact({
  events,
  maxEvents = 3,
  className,
}: {
  events: AuditEvent[];
  maxEvents?: number;
  className?: string;
}) {
  const displayEvents = events.slice(0, maxEvents);
  const remaining = events.length - maxEvents;
  
  return (
    <div className={cn("space-y-2", className)}>
      {displayEvents.map((event, idx) => (
        <div key={event.id || idx} className="flex items-center gap-2 text-xs">
          <div className={cn(
            "w-1.5 h-1.5 rounded-full",
            getActionColor(event.action).split(' ')[0].replace('text-', 'bg-')
          )} />
          <span className="font-medium truncate flex-1">{event.action}</span>
          <span className="text-muted-foreground">
            {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
          </span>
        </div>
      ))}
      {remaining > 0 && (
        <p className="text-xs text-muted-foreground">
          +{remaining} more events
        </p>
      )}
    </div>
  );
}

export default AuditTimeline;
