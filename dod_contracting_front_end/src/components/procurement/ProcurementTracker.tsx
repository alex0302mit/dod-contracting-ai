import { useState, useEffect, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, FileText, Loader2, ArrowRight, Shield, Sparkles, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { projectsApi } from '@/services/api';
import { PhaseSteps } from './PhaseSteps';
import { ProcurementTrackerBar } from './SegmentedTrackerBar';
import { DocumentChecklist } from './DocumentChecklist';
// GeneratedDocumentsGallery - AI Documents gallery view for viewing/exporting generated content
import { GeneratedDocumentsGallery } from './GeneratedDocumentsGallery';
// KnowledgeTab - Project-scoped document library for RAG-indexed reference materials
import { KnowledgeTab } from './KnowledgeTab';
import { PhaseTransitionDialog } from './PhaseTransitionDialog';
import { useAuth } from '@/contexts/AuthContext';

interface ProcurementTrackerProps {
  projectId: string;
  onBack: () => void;
}

export function ProcurementTracker({ projectId, onBack }: ProcurementTrackerProps) {
  const { canEditProject, user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedPhase, setSelectedPhase] = useState<any | null>(null);
  const [canEdit, setCanEdit] = useState(false);
  // State for phase transition dialog
  const [transitionDialogOpen, setTransitionDialogOpen] = useState(false);

  // Fetch project data with React Query
  const { data: project, isLoading: projectLoading, isFetching: projectFetching } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const response: any = await projectsApi.get(projectId);
      return response.project || response;
    },
  });

  // Fetch phases data with React Query
  const { data: phases = [], isLoading: phasesLoading, isFetching: phasesFetching } = useQuery({
    queryKey: ['phases', projectId],
    queryFn: async () => {
      const response = await projectsApi.getPhases(projectId);
      return response.phases || [];
    },
  });

  // Auto-select current phase when phases load
  useEffect(() => {
    if (!selectedPhase && phases.length > 0) {
      const currentPhase = phases.find((p: any) => p.status === 'in_progress') || phases[0];
      setSelectedPhase(currentPhase);
    }
  }, [phases, selectedPhase]);

  // Fetch steps data with React Query (centralized)
  const { data: steps = [], isFetching: stepsFetching } = useQuery({
    queryKey: ['steps', projectId],
    queryFn: async () => {
      const response = await projectsApi.getSteps(projectId);
      return response.steps || [];
    },
  });

  // Fetch documents data with React Query (centralized)
  const { data: documents = [], isFetching: documentsFetching } = useQuery({
    queryKey: ['documents', projectId],
    queryFn: async () => {
      const response = await projectsApi.getDocuments(projectId);
      return response.documents || [];
    },
  });

  // Check edit permissions (only runs once, not on every poll)
  useQuery({
    queryKey: ['canEdit', projectId],
    queryFn: async () => {
      const result = await canEditProject(projectId);
      setCanEdit(result);
      return result;
    },
    staleTime: Infinity, // Permissions don't change during session
    refetchInterval: false,
  });

  // Callback to refetch all data after updates
  const handleDataUpdate = () => {
    queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    queryClient.invalidateQueries({ queryKey: ['phases', projectId] });
    queryClient.invalidateQueries({ queryKey: ['steps', projectId] });
    queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
  };

  const calculateProgress = () => {
    const completedPhases = phases.filter((p) => p.status === 'completed').length;
    return phases.length > 0 ? (completedPhases / phases.length) * 100 : 0;
  };

  // Count of AI-generated documents for badge in tab
  const generatedDocsCount = useMemo(() => {
    return documents.filter((doc: any) => doc.generation_status === 'generated').length;
  }, [documents]);

  const loading = projectLoading || phasesLoading;
  const refreshing = !loading && (projectFetching || phasesFetching || stepsFetching || documentsFetching);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading tracker...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-slate-600">Project not found</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <div className="border-b bg-white px-6 py-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold text-slate-900">{project.name}</h2>
              {refreshing && (
                <div title="Refreshing data...">
                  <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                </div>
              )}
            </div>
            <p className="text-sm text-slate-600 mt-1">{project.description || 'Procurement tracking'}</p>
          </div>
          <Badge className={getStatusColor(project.overall_status)} variant="outline">
            {project.overall_status.replace('_', ' ')}
          </Badge>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          <Card className="overflow-hidden shadow-xl">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8 text-white">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold">Procurement Progress Tracker</h3>
                  <p className="text-blue-100 text-sm mt-2">Track your procurement through all phases</p>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold">{Math.round(calculateProgress())}%</div>
                  <div className="text-blue-100 text-sm mt-1">Complete</div>
                </div>
              </div>
            </div>

            <div className="p-10 bg-white">
              <ProcurementTrackerBar currentPhase={project.current_phase} />
              
              {/* Phase Transition Button - shown for CO, PM, and Admin roles */}
              {canEdit && selectedPhase && (
                <div className="mt-6 flex justify-end">
                  <Button
                    onClick={() => setTransitionDialogOpen(true)}
                    className="gap-2 bg-blue-600 hover:bg-blue-700"
                    aria-label="Request phase transition"
                    title="Request approval to move to the next phase"
                  >
                    <Shield className="h-4 w-4" />
                    Request Phase Transition
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </Card>
          
          {/* Phase Transition Dialog */}
          {selectedPhase && (
            <PhaseTransitionDialog
              open={transitionDialogOpen}
              onOpenChange={setTransitionDialogOpen}
              phaseId={selectedPhase.id}
              phaseName={selectedPhase.phase_name}
              projectName={project.name}
              onSuccess={handleDataUpdate}
            />
          )}

          <Tabs defaultValue="phases" className="w-full">
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="phases">Phase Steps</TabsTrigger>
              <TabsTrigger value="documents" className="gap-2">
                <FileText className="h-4 w-4" />
                Document Checklist
              </TabsTrigger>
              <TabsTrigger value="ai-docs" className="gap-2">
                <Sparkles className="h-4 w-4" />
                AI Documents
                {generatedDocsCount > 0 && (
                  <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs bg-purple-100 text-purple-700">
                    {generatedDocsCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="knowledge" className="gap-2">
                <FolderOpen className="h-4 w-4" />
                Knowledge
              </TabsTrigger>
            </TabsList>

            <TabsContent value="phases">
              {selectedPhase && (
                <PhaseSteps
                  projectId={projectId}
                  phase={selectedPhase}
                  steps={steps.filter((s: any) => s.phase_id === selectedPhase.id) as any}
                  onPhaseUpdate={handleDataUpdate}
                  canEdit={canEdit}
                />
              )}
            </TabsContent>

            <TabsContent value="documents">
              <DocumentChecklist
                projectId={projectId}
                documents={documents}
                canEdit={canEdit}
                onUpdate={handleDataUpdate}
              />
            </TabsContent>

            <TabsContent value="ai-docs">
              <GeneratedDocumentsGallery
                projectId={projectId}
                documents={documents}
                onUpdate={handleDataUpdate}
              />
            </TabsContent>

            {/* Knowledge Tab - Project-scoped document library for AI context */}
            <TabsContent value="knowledge">
              <KnowledgeTab
                projectId={projectId}
                currentPhase={selectedPhase?.phase_name?.toLowerCase().replace(' ', '_')}
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

function getStatusColor(status: string) {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-800 border-green-200';
    case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'delayed': return 'bg-red-100 text-red-800 border-red-200';
    case 'on_hold': return 'bg-amber-100 text-amber-800 border-amber-200';
    default: return 'bg-slate-100 text-slate-800 border-slate-200';
  }
}
