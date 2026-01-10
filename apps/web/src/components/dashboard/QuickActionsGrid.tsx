/**
 * QuickActionsGrid Component
 *
 * Displays role-based quick action cards:
 * - Create Project (CO, PM)
 * - View Projects (All)
 * - Pending Approvals (All) - with badge count
 * - Upload Documents (CO, PM)
 *
 * Uses hasRole() from AuthContext for visibility control.
 */

import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus, TrendingUp, UserCheck, Upload, ArrowRight } from 'lucide-react';

interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  iconBg: string;
  roles: string[] | 'all';
  badge?: number;
  onClick: () => void;
}

interface QuickActionsGridProps {
  pendingApprovalsCount?: number;
  onCreateProject: () => void;
  onViewProjects: () => void;
  onViewApprovals: () => void;
  onUploadDocuments: () => void;
}

export function QuickActionsGrid({
  pendingApprovalsCount = 0,
  onCreateProject,
  onViewProjects,
  onViewApprovals,
  onUploadDocuments,
}: QuickActionsGridProps) {
  const { hasRole } = useAuth();

  const quickActions: QuickAction[] = [
    {
      id: 'create_project',
      label: 'Create New Project',
      description: 'Start a new procurement project',
      icon: <Plus className="h-6 w-6 text-blue-600" />,
      iconBg: 'bg-blue-100',
      roles: ['contracting_officer', 'program_manager', 'admin'],
      onClick: onCreateProject,
    },
    {
      id: 'view_projects',
      label: 'View All Projects',
      description: 'Browse and manage projects',
      icon: <TrendingUp className="h-6 w-6 text-emerald-600" />,
      iconBg: 'bg-emerald-100',
      roles: 'all',
      onClick: onViewProjects,
    },
    {
      id: 'pending_approvals',
      label: 'Pending Approvals',
      description: 'Review documents awaiting approval',
      icon: <UserCheck className="h-6 w-6 text-purple-600" />,
      iconBg: 'bg-purple-100',
      roles: 'all',
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined,
      onClick: onViewApprovals,
    },
    {
      id: 'upload_documents',
      label: 'Upload Documents',
      description: 'Add documents to knowledge base',
      icon: <Upload className="h-6 w-6 text-amber-600" />,
      iconBg: 'bg-amber-100',
      roles: ['contracting_officer', 'program_manager', 'admin'],
      onClick: onUploadDocuments,
    },
  ];

  // Filter actions based on user role
  const visibleActions = quickActions.filter((action) => {
    if (action.roles === 'all') return true;
    return hasRole(action.roles);
  });

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {visibleActions.map((action) => (
        <Card
          key={action.id}
          className="cursor-pointer hover:shadow-md hover:border-blue-200 transition-all group"
          onClick={action.onClick}
        >
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-3">
              <div className={`h-12 w-12 rounded-lg ${action.iconBg} flex items-center justify-center`}>
                {action.icon}
              </div>
              {action.badge && (
                <Badge className="bg-red-500 text-white border-0">
                  {action.badge}
                </Badge>
              )}
            </div>
            <h3 className="font-semibold text-slate-900 mb-1 group-hover:text-blue-600 transition-colors">
              {action.label}
            </h3>
            <p className="text-sm text-slate-600 mb-3">{action.description}</p>
            <div className="flex items-center text-sm text-blue-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              Get started <ArrowRight className="h-4 w-4 ml-1" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
