/**
 * RecentProjectsList Component
 *
 * Displays the 5 most recent projects with:
 * - Project name
 * - Status badge (color-coded)
 * - Current phase indicator
 * - Last updated date
 * - Click to navigate to project tracker
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FolderOpen, ArrowRight, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { RecentProject } from '@/hooks/useDashboardStats';

interface RecentProjectsListProps {
  projects: RecentProject[];
  onSelectProject: (projectId: string) => void;
}

// Status badge configuration
const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  not_started: { label: 'Not Started', className: 'bg-slate-100 text-slate-700' },
  in_progress: { label: 'In Progress', className: 'bg-blue-100 text-blue-700' },
  completed: { label: 'Completed', className: 'bg-green-100 text-green-700' },
  delayed: { label: 'Delayed', className: 'bg-red-100 text-red-700' },
  on_hold: { label: 'On Hold', className: 'bg-amber-100 text-amber-700' },
};

// Phase display configuration
const PHASE_CONFIG: Record<string, { label: string; shortLabel: string }> = {
  pre_solicitation: { label: 'Pre-Solicitation', shortLabel: 'Pre-Sol' },
  solicitation: { label: 'Solicitation', shortLabel: 'Solicit' },
  post_solicitation: { label: 'Post-Solicitation', shortLabel: 'Post-Sol' },
  award: { label: 'Award', shortLabel: 'Award' },
};

export function RecentProjectsList({ projects, onSelectProject }: RecentProjectsListProps) {
  if (projects.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FolderOpen className="h-5 w-5 text-slate-500" />
            Recent Projects
          </CardTitle>
          <CardDescription>Your most recently updated projects</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
              <FolderOpen className="h-6 w-6 text-slate-400" />
            </div>
            <p className="text-sm text-slate-600">No projects yet</p>
            <p className="text-xs text-slate-500 mt-1">Create your first project to get started</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FolderOpen className="h-5 w-5 text-slate-500" />
          Recent Projects
        </CardTitle>
        <CardDescription>Your most recently updated projects</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {projects.map((project) => {
          const statusConfig = STATUS_CONFIG[project.overall_status] || STATUS_CONFIG.not_started;
          const phaseConfig = PHASE_CONFIG[project.current_phase] || { label: project.current_phase, shortLabel: project.current_phase };
          const updatedAt = project.updated_at || project.created_at;

          return (
            <div
              key={project.id}
              className="flex items-center justify-between p-3 rounded-lg border bg-white hover:bg-slate-50 hover:border-blue-200 cursor-pointer transition-all group"
              onClick={() => onSelectProject(project.id)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-slate-900 truncate group-hover:text-blue-600 transition-colors">
                    {project.name}
                  </h4>
                  <Badge className={`${statusConfig.className} border-0 text-xs`}>
                    {statusConfig.label}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1">
                    <span className="font-medium text-slate-600">{phaseConfig.shortLabel}</span>
                  </span>
                  {updatedAt && (
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDistanceToNow(new Date(updatedAt), { addSuffix: true })}
                    </span>
                  )}
                </div>
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
