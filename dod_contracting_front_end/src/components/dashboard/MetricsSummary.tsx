/**
 * MetricsSummary Component
 *
 * Displays project statistics in a responsive card grid:
 * - Total Projects (blue)
 * - In Progress (amber)
 * - Completed (green)
 * - Pending Approvals (purple)
 *
 * Pattern follows ProjectDashboard.tsx stats cards.
 */

import { Card, CardContent } from '@/components/ui/card';
import { Clock, AlertCircle, CheckCircle2, UserCheck } from 'lucide-react';
import type { DashboardStats } from '@/hooks/useDashboardStats';

interface MetricsSummaryProps {
  stats: DashboardStats;
  onPendingApprovalsClick?: () => void;
}

export function MetricsSummary({ stats, onPendingApprovalsClick }: MetricsSummaryProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Projects */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Total Projects</p>
              <p className="text-2xl font-bold text-slate-900">{stats.projects.total}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* In Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">In Progress</p>
              <p className="text-2xl font-bold text-slate-900">{stats.projects.in_progress}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
              <AlertCircle className="h-6 w-6 text-amber-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Completed */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Completed</p>
              <p className="text-2xl font-bold text-slate-900">{stats.projects.completed}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pending Approvals */}
      <Card
        className={onPendingApprovalsClick ? 'cursor-pointer hover:border-purple-300 transition-colors' : ''}
        onClick={onPendingApprovalsClick}
      >
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Pending Approvals</p>
              <p className="text-2xl font-bold text-slate-900">{stats.pendingApprovals}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
              <UserCheck className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
