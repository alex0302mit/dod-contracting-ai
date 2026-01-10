/**
 * DashboardView Component
 *
 * Main dashboard container that serves as the default landing page.
 * Combines:
 * - WelcomeHeader: Personalized greeting
 * - MetricsSummary: Project and approval stats
 * - QuickActionsGrid: Role-based action cards
 * - RecentProjectsList: 5 most recent projects
 *
 * Provides a welcoming, actionable home experience.
 */

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useDashboardStats } from '@/hooks/useDashboardStats';
import { WelcomeHeader } from './WelcomeHeader';
import { MetricsSummary } from './MetricsSummary';
import { QuickActionsGrid } from './QuickActionsGrid';
import { RecentProjectsList } from './RecentProjectsList';
import { CreateProjectDialog } from '@/components/procurement/CreateProjectDialog';

// Route type matching AIContractingUI.tsx
type RouteType = "DASHBOARD" | "UPLOAD_CENTER" | "DOCUMENT_WORKFLOW" | "GENERATING" | "EDITOR" | "EXPORT" | "PROCUREMENT_TRACKER" | "PENDING_APPROVALS" | "ADMIN";

interface DashboardViewProps {
  onNavigate: (route: RouteType) => void;
  onSelectProject: (projectId: string) => void;
}

export function DashboardView({ onNavigate, onSelectProject }: DashboardViewProps) {
  const { stats, recentProjects, loading, refresh } = useDashboardStats();
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Handle project creation dialog close
  const handleCreateDialogChange = (open: boolean) => {
    setShowCreateDialog(open);
    if (!open) {
      // Refresh data when dialog closes (project may have been created)
      refresh();
    }
  };

  // Handle project selection - navigate to tracker with project selected
  const handleSelectProject = (projectId: string) => {
    onSelectProject(projectId);
    onNavigate('PROCUREMENT_TRACKER');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <p className="mt-4 text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="container mx-auto px-6 py-6 max-w-7xl">
        {/* Welcome Header */}
        <div className="mb-8">
          <WelcomeHeader />
        </div>

        {/* Metrics Summary */}
        <div className="mb-8">
          <MetricsSummary
            stats={stats}
            onPendingApprovalsClick={() => onNavigate('PENDING_APPROVALS')}
          />
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h2>
          <QuickActionsGrid
            pendingApprovalsCount={stats.pendingApprovals}
            onCreateProject={() => setShowCreateDialog(true)}
            onViewProjects={() => onNavigate('PROCUREMENT_TRACKER')}
            onViewApprovals={() => onNavigate('PENDING_APPROVALS')}
            onUploadDocuments={() => onNavigate('UPLOAD_CENTER')}
          />
        </div>

        {/* Recent Projects */}
        <div className="mb-8">
          <RecentProjectsList
            projects={recentProjects}
            onSelectProject={handleSelectProject}
          />
        </div>
      </div>

      {/* Create Project Dialog */}
      <CreateProjectDialog
        open={showCreateDialog}
        onOpenChange={handleCreateDialogChange}
      />
    </div>
  );
}
