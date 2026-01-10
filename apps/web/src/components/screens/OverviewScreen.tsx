/**
 * OverviewScreen Component
 * 
 * Main dashboard/overview screen for ACES.
 * Displays project metrics, quick actions, and recent projects.
 * 
 * Wraps existing DashboardView components with ACES styling
 * and InstrumentCards for metrics display.
 * 
 * Dependencies:
 * - useDashboardStats for data
 * - InstrumentCard for metrics
 * - AppShellWithoutRail (no ConsoleRail on Overview)
 */

import { useState } from 'react';
import { 
  FolderKanban, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  Plus, 
  TrendingUp,
  UserCheck,
  FileText,
  Loader2
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useDashboardStats } from '@/hooks/useDashboardStats';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigation } from '@/contexts/NavigationContext';
import { InstrumentCard, InstrumentCardGrid } from '@/components/shared';
import { CreateProjectDialog } from '@/components/procurement/CreateProjectDialog';
import { StatusChip, normalizeStatus } from '@/components/shared/StatusChip';
import { formatDistanceToNow } from 'date-fns';

/**
 * WelcomeHeader - Personalized greeting
 */
function WelcomeHeader() {
  const { user } = useAuth();
  
  // Get time-appropriate greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };
  
  return (
    <div className="mb-8">
      <h1 className="text-2xl font-bold text-foreground">
        {getGreeting()}, {user?.name?.split(' ')[0] || 'there'}
      </h1>
      <p className="text-muted-foreground mt-1">
        Welcome to ACES - Acquisition Contracting Enterprise System
      </p>
    </div>
  );
}

/**
 * QuickActionsGrid - Role-based action cards
 */
interface QuickActionsGridProps {
  onCreateProject: () => void;
  onViewProjects: () => void;
  onViewApprovals: () => void;
  onQuickGenerate: () => void;
  pendingApprovalsCount: number;
}

function QuickActionsGrid({
  onCreateProject,
  onViewProjects,
  onViewApprovals,
  onQuickGenerate,
  pendingApprovalsCount,
}: QuickActionsGridProps) {
  const actions = [
    {
      title: 'New Project',
      description: 'Start a new procurement project',
      icon: Plus,
      onClick: onCreateProject,
      variant: 'primary' as const,
    },
    {
      title: 'Quick Generate',
      description: 'Generate documents without a project',
      icon: FileText,
      onClick: onQuickGenerate,
      variant: 'default' as const,
    },
    {
      title: 'View Projects',
      description: 'Browse all active projects',
      icon: TrendingUp,
      onClick: onViewProjects,
      variant: 'default' as const,
    },
    {
      title: 'Pending Approvals',
      description: `${pendingApprovalsCount} items awaiting review`,
      icon: UserCheck,
      onClick: onViewApprovals,
      variant: 'default' as const,
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined,
    },
  ];
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Card
            key={action.title}
            className={`cursor-pointer transition-all hover:shadow-md ${
              action.variant === 'primary' 
                ? 'bg-primary text-primary-foreground hover:bg-primary/90' 
                : 'hover:bg-muted/50'
            }`}
            onClick={action.onClick}
          >
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                  action.variant === 'primary' ? 'bg-primary-foreground/20' : 'bg-muted'
                }`}>
                  <Icon className={`h-5 w-5 ${
                    action.variant === 'primary' ? 'text-primary-foreground' : 'text-muted-foreground'
                  }`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{action.title}</h3>
                    {action.badge && (
                      <span className="h-5 w-5 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center">
                        {action.badge}
                      </span>
                    )}
                  </div>
                  <p className={`text-sm ${
                    action.variant === 'primary' ? 'text-primary-foreground/80' : 'text-muted-foreground'
                  }`}>
                    {action.description}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/**
 * RecentProjectsList - Shows 5 most recent projects
 */
interface RecentProjectsListProps {
  projects: Array<{
    id: string;
    name: string;
    description?: string;
    overall_status: string;
    current_phase: string;
    updated_at?: string;
    created_at?: string;
  }>;
  onSelectProject: (projectId: string) => void;
}

function RecentProjectsList({ projects, onSelectProject }: RecentProjectsListProps) {
  if (projects.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <FolderKanban className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground">No projects yet</p>
          <p className="text-sm text-muted-foreground">Create your first project to get started</p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Recent Projects</CardTitle>
        <CardDescription>Your most recently updated projects</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {projects.map((project) => (
            <div
              key={project.id}
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
              onClick={() => onSelectProject(project.id)}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <FolderKanban className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{project.name}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {project.current_phase?.replace(/_/g, ' ')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <StatusChip 
                  status={normalizeStatus(project.overall_status)} 
                  size="sm" 
                  showIcon={false} 
                />
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {formatDistanceToNow(new Date(project.updated_at || project.created_at || new Date()), { addSuffix: true })}
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * OverviewScreen - Main dashboard screen
 */
export function OverviewScreen() {
  const { stats, recentProjects, loading, refresh } = useDashboardStats();
  const { navigate, navigateToProject } = useNavigation();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  
  // Handle project creation dialog close
  const handleCreateDialogChange = (open: boolean) => {
    setShowCreateDialog(open);
    if (!open) {
      // Refresh data when dialog closes (project may have been created)
      refresh();
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full overflow-auto">
      <div className="container mx-auto px-6 py-6 max-w-7xl">
        {/* Welcome Header */}
        <WelcomeHeader />
        
        {/* Metrics Summary - Using InstrumentCards */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">Project Overview</h2>
          <InstrumentCardGrid columns={4}>
            <InstrumentCard
              label="Total Projects"
              value={stats.projects.total}
              showProgress={false}
              showPercent={false}
              icon={<FolderKanban className="h-4 w-4" />}
            />
            <InstrumentCard
              label="In Progress"
              value={stats.projects.in_progress}
              showProgress={false}
              showPercent={false}
              icon={<Clock className="h-4 w-4" />}
            />
            <InstrumentCard
              label="Completed"
              value={stats.projects.completed}
              showProgress={false}
              showPercent={false}
              icon={<CheckCircle className="h-4 w-4" />}
            />
            <InstrumentCard
              label="Pending Approvals"
              value={stats.pendingApprovals}
              showProgress={false}
              showPercent={false}
              icon={<AlertTriangle className="h-4 w-4" />}
              riskLevel={stats.pendingApprovals > 5 ? 'HIGH' : stats.pendingApprovals > 0 ? 'MEDIUM' : 'LOW'}
            />
          </InstrumentCardGrid>
        </div>
        
        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <QuickActionsGrid
            onCreateProject={() => setShowCreateDialog(true)}
            onViewProjects={() => navigate('TRACKER')}
            onViewApprovals={() => navigate('APPROVALS')}
            onQuickGenerate={() => navigate('QUICK_GENERATE')}
            pendingApprovalsCount={stats.pendingApprovals}
          />
        </div>
        
        {/* Recent Projects */}
        <div className="mb-8">
          <RecentProjectsList
            projects={recentProjects}
            onSelectProject={navigateToProject}
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

export default OverviewScreen;
