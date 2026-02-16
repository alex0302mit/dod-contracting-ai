/**
 * ActivityFeed - Timeline view of project activities.
 * Shows user actions with timestamps in a chronological feed.
 */
import { Loader2, FileText, Users, ArrowRight, Share2, Sparkles, CheckCircle2 } from 'lucide-react';
import { useProjectActivities } from '@/hooks/useProjectActivities';
import { formatDistanceToNow } from 'date-fns';

interface ActivityFeedProps {
  projectId: string;
}

const ACTIVITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  project_created: FileText,
  document_generated: Sparkles,
  phase_changed: ArrowRight,
  member_added: Users,
  member_removed: Users,
  member_updated: Users,
  project_shared: Share2,
  share_revoked: Share2,
  document_approved: CheckCircle2,
  document_rejected: CheckCircle2,
};

const ACTIVITY_COLORS: Record<string, string> = {
  project_created: 'bg-blue-100 text-blue-600',
  document_generated: 'bg-purple-100 text-purple-600',
  phase_changed: 'bg-green-100 text-green-600',
  member_added: 'bg-indigo-100 text-indigo-600',
  member_removed: 'bg-red-100 text-red-600',
  member_updated: 'bg-amber-100 text-amber-600',
  project_shared: 'bg-cyan-100 text-cyan-600',
  share_revoked: 'bg-slate-100 text-slate-600',
  document_approved: 'bg-green-100 text-green-600',
  document_rejected: 'bg-red-100 text-red-600',
};

export function ActivityFeed({ projectId }: ActivityFeedProps) {
  const { activities, loading, total } = useProjectActivities(projectId);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No activity yet</p>
        <p className="text-xs mt-1">Activities will appear here as you work on this project</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <p className="text-sm text-muted-foreground mb-4">{total} activities</p>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-2 bottom-2 w-px bg-border" />

        <div className="space-y-4">
          {activities.map((activity) => {
            const Icon = ACTIVITY_ICONS[activity.activity_type] ?? FileText;
            const colorClass = ACTIVITY_COLORS[activity.activity_type] ?? 'bg-slate-100 text-slate-600';

            return (
              <div key={activity.id} className="flex gap-3 relative">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 z-10 ${colorClass}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0 pt-0.5">
                  <p className="text-sm">
                    {activity.user && (
                      <span className="font-medium">{activity.user.name}</span>
                    )}
                    {activity.user && ' '}
                    {activity.title}
                  </p>
                  {activity.description && (
                    <p className="text-xs text-muted-foreground mt-0.5">{activity.description}</p>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
