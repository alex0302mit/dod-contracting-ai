import { useState, useMemo } from 'react';
import { Plus, Search, Filter, Clock, CheckCircle2, AlertCircle, Pause, Trash2, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { useProcurementProjects } from '@/hooks/useProcurementProjects';
import { useAuth } from '@/contexts/AuthContext';
import { CreateProjectDialog } from './CreateProjectDialog';
import { AssignOfficerDialog } from './AssignOfficerDialog';
import { SegmentedTrackerBar } from './SegmentedTrackerBar';
import { DocumentChecklistSummary } from './DocumentChecklistSummary';
import { format } from 'date-fns';
import { toast } from 'sonner';

interface ProjectDashboardProps {
  onSelectProject: (projectId: string) => void;
}

export function ProjectDashboard({ onSelectProject }: ProjectDashboardProps) {
  const { projects, loading, deleteProject, refresh } = useProcurementProjects();
  const { hasRole } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [phaseFilter, setPhaseFilter] = useState<string>('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const filteredProjects = useMemo(() => {
    return projects.filter((project) => {
      const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.description?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || project.overall_status === statusFilter;
      const matchesPhase = phaseFilter === 'all' || project.current_phase === phaseFilter;
      return matchesSearch && matchesStatus && matchesPhase;
    });
  }, [projects, searchQuery, statusFilter, phaseFilter]);

  const statusCounts = useMemo(() => {
    return {
      total: projects.length,
      in_progress: projects.filter((p) => p.overall_status === 'in_progress').length,
      completed: projects.filter((p) => p.overall_status === 'completed').length,
      delayed: projects.filter((p) => p.overall_status === 'delayed').length,
    };
  }, [projects]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Procurement Projects</h2>
            <p className="text-sm text-slate-600 mt-1">Manage and track all procurement activities</p>
          </div>
          {hasRole(['contracting_officer', 'program_manager']) && (
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              New Project
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Total Projects</p>
                  <p className="text-2xl font-bold text-slate-900">{statusCounts.total}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <Clock className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">In Progress</p>
                  <p className="text-2xl font-bold text-slate-900">{statusCounts.in_progress}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
                  <AlertCircle className="h-6 w-6 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Completed</p>
                  <p className="text-2xl font-bold text-slate-900">{statusCounts.completed}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle2 className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Delayed</p>
                  <p className="text-2xl font-bold text-slate-900">{statusCounts.delayed}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
                  <Pause className="h-6 w-6 text-red-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full md:w-48">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="not_started">Not Started</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="delayed">Delayed</SelectItem>
              <SelectItem value="on_hold">On Hold</SelectItem>
            </SelectContent>
          </Select>
          <Select value={phaseFilter} onValueChange={setPhaseFilter}>
            <SelectTrigger className="w-full md:w-48">
              <SelectValue placeholder="Filter by phase" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Phases</SelectItem>
              <SelectItem value="pre_solicitation">Pre-Solicitation</SelectItem>
              <SelectItem value="solicitation">Solicitation</SelectItem>
              <SelectItem value="post_solicitation">Post-Solicitation</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {filteredProjects.length === 0 ? (
          <div className="text-center py-12">
            <Filter className="h-12 w-12 text-slate-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No projects found</h3>
            <p className="text-slate-600">
              {searchQuery || statusFilter !== 'all' || phaseFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first procurement project to get started'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredProjects.map((project) => (
              <ProjectCard 
                key={project.id} 
                project={project} 
                onSelect={onSelectProject}
                onDelete={deleteProject}
                onRefresh={refresh}
                canDelete={hasRole(['contracting_officer', 'program_manager'])}
                canAssign={hasRole(['contracting_officer', 'program_manager'])}
              />
            ))}
          </div>
        )}
      </div>

      <CreateProjectDialog open={showCreateDialog} onOpenChange={setShowCreateDialog} />
    </div>
  );
}

// Props interface for ProjectCard component
interface ProjectCardProps {
  project: {
    id: string;
    name: string;
    description?: string;
    overall_status: string;
    current_phase: string;
    project_type: string;
    estimated_value?: number;
    target_completion_date?: string;
    contracting_officer_id?: string;
    program_manager_id?: string;
    contracting_officer?: { name: string };
    organization?: { name: string; slug: string } | null;
  };
  onSelect: (id: string) => void;
  onDelete: (id: string) => Promise<void>;
  onRefresh: () => void;
  canDelete: boolean;
  canAssign: boolean;
}

function ProjectCard({ project, onSelect, onDelete, onRefresh, canDelete, canAssign }: ProjectCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Returns Tailwind CSS classes for status badge styling
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'delayed': return 'bg-red-100 text-red-800 border-red-200';
      case 'on_hold': return 'bg-amber-100 text-amber-800 border-amber-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  // Handle project deletion with confirmation
  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click from triggering
    setIsDeleting(true);
    try {
      await onDelete(project.id);
      toast.success(`Project "${project.name}" deleted successfully`);
    } catch (error) {
      console.error('Error deleting project:', error);
      toast.error('Failed to delete project');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => onSelect(project.id)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg mb-1">{project.name}</CardTitle>
            <CardDescription className="line-clamp-2">
              {project.description || 'No description provided'}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
          <Badge className={getStatusColor(project.overall_status)} variant="outline">
            {project.overall_status.replace('_', ' ')}
          </Badge>
            {project.organization && (
              <Badge variant="outline" className="gap-1 text-xs bg-slate-50">
                <Building2 className="h-3 w-3" />
                {project.organization.name}
              </Badge>
            )}
            {/* Assign Officer button */}
            {canAssign && (
              <AssignOfficerDialog
                projectId={project.id}
                projectName={project.name}
                currentOfficerId={project.contracting_officer_id}
                currentProgramManagerId={project.program_manager_id}
                onAssigned={onRefresh}
              />
            )}
            {/* Delete button with confirmation dialog */}
            {canDelete && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8 border-slate-200 text-slate-600 hover:text-red-600 hover:bg-red-50 hover:border-red-200"
                    onClick={(e) => e.stopPropagation()}
                    disabled={isDeleting}
                    aria-label="Delete project"
                    title="Delete project"
                  >
                    <Trash2 className="h-5 w-5 shrink-0" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent onClick={(e) => e.stopPropagation()}>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Project</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to delete "{project.name}"? This will permanently remove the project and all its phases, steps, and documents. This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDelete}
                      className="bg-red-600 hover:bg-red-700"
                      disabled={isDeleting}
                    >
                      {isDeleting ? 'Deleting...' : 'Delete Project'}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="mb-4">
            <SegmentedTrackerBar
              segments={[
                { id: '1', label: 'Reqmts', status: ['pre_solicitation', 'solicitation', 'post_solicitation'].includes(project.current_phase) ? 'completed' : project.current_phase === 'requirements' ? 'active' : 'pending' },
                { id: '2', label: 'Pre-Sol', status: ['solicitation', 'post_solicitation'].includes(project.current_phase) ? 'completed' : project.current_phase === 'pre_solicitation' ? 'active' : 'pending' },
                { id: '3', label: 'Solicit', status: project.current_phase === 'post_solicitation' ? 'completed' : project.current_phase === 'solicitation' ? 'active' : 'pending' },
                { id: '4', label: 'Award', status: project.current_phase === 'post_solicitation' ? 'active' : 'pending' },
              ]}
              className="scale-75 origin-left"
            />
          </div>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <p className="text-slate-600">Type</p>
              <p className="font-medium">{project.project_type.toUpperCase()}</p>
            </div>
            <div>
              <p className="text-slate-600">Est. Value</p>
              <p className="font-medium">
                {project.estimated_value
                  ? `$${(project.estimated_value / 1000000).toFixed(1)}M`
                  : 'TBD'}
              </p>
            </div>
          </div>

          {project.target_completion_date && (
            <div className="text-sm">
              <p className="text-slate-600">Target Completion</p>
              <p className="font-medium">{format(new Date(project.target_completion_date), 'MMM d, yyyy')}</p>
            </div>
          )}

          <div className="text-sm pt-2 border-t">
            <p className="text-slate-600">Contracting Officer</p>
            <p className="font-medium">{project.contracting_officer?.name || 'Unassigned'}</p>
          </div>

          <div className="pt-3 border-t">
            <DocumentChecklistSummary projectId={project.id} compact />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
