import { useState, useEffect, useCallback } from 'react';
import { CheckCircle2, Clock, PlayCircle, User, Calendar, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

import { StepDetailDialog } from './StepDetailDialog';
import { format, isPast } from 'date-fns';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { projectsApi, stepsApi, phasesApi } from '@/services/api';

interface Phase {
  id: string;
  phase_name: string;
  status: string;
}

interface Step {
  id: string;
  step_name: string;
  step_description: string | null;
  step_order: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'skipped';
  deadline: string | null;
  completion_date: string | null;
  assigned_user_id: string | null;
  requires_approval: boolean;
  notes: string | null;
  assigned_user: { name: string; email: string } | null;
}

interface PhaseStepsProps {
  projectId: string;
  phase: Phase;
  steps: Step[];
  onPhaseUpdate: () => void;
  canEdit: boolean;
}

export function PhaseSteps({ projectId, phase, steps: propSteps, onPhaseUpdate, canEdit }: PhaseStepsProps) {
  const [steps, setSteps] = useState<Step[]>(propSteps);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<{ [key: string]: boolean }>({});
  const [selectedStep, setSelectedStep] = useState<Step | null>(null);
  const [showStepDialog, setShowStepDialog] = useState(false);

  // Memoized function to create default steps
  const createDefaultSteps = useCallback(async () => {
    try {
      setLoading(true);
      const createResponse = await phasesApi.createDefaultSteps(phase.id);

      if (createResponse.created && createResponse.steps) {
        setSteps(createResponse.steps as Step[]);
        onPhaseUpdate(); // Trigger parent refetch
      }
    } catch (error) {
      console.error('Error creating default steps:', error);
      toast.error('Failed to create default steps');
    } finally {
      setLoading(false);
    }
  }, [phase.id, onPhaseUpdate]);

  // Update local steps when props change
  useEffect(() => {
    setSteps(propSteps);

    // Create default steps if none exist
    if (propSteps.length === 0 && !loading) {
      createDefaultSteps();
    }
  }, [propSteps, phase.id, loading, createDefaultSteps]);

  const handleStartPhase = async () => {
    setActionLoading({ phase_start: true });
    try {
      // Update phase status
      await phasesApi.update(phase.id, {
        status: 'in_progress',
        start_date: new Date().toISOString().split('T')[0],
      });

      // Update project current phase
      await projectsApi.update(projectId, {
        current_phase: phase.phase_name,
      });

      toast.success('Phase started successfully');
      onPhaseUpdate();
    } catch (error) {
      console.error('Error starting phase:', error);
      toast.error('Failed to start phase');
    } finally {
      setActionLoading({});
    }
  };

  const handleCompleteStep = async (stepId: string) => {
    // Optimistic update - update UI immediately
    const previousSteps = [...steps];
    const updatedSteps = steps.map((s) =>
      s.id === stepId ? { ...s, status: 'completed' as const, completion_date: new Date().toISOString().split('T')[0] } : s
    );
    setSteps(updatedSteps);
    setActionLoading({ [`complete_${stepId}`]: true });

    try {
      await stepsApi.update(stepId, {
        status: 'completed',
        completion_date: new Date().toISOString().split('T')[0],
      });

      // If all steps completed, mark phase as completed
      if (updatedSteps.every((s) => s.status === 'completed')) {
        await phasesApi.update(phase.id, {
          status: 'completed',
          end_date: new Date().toISOString().split('T')[0],
        });
      }

      toast.success('Step completed');
      onPhaseUpdate(); // Trigger parent refetch
    } catch (error) {
      // Rollback optimistic update on error
      setSteps(previousSteps);
      console.error('Error completing step:', error);
      toast.error('Failed to complete step');
    } finally {
      setActionLoading({});
    }
  };

  const handleStartStep = async (stepId: string) => {
    // Optimistic update
    const previousSteps = [...steps];
    const updatedSteps = steps.map(s =>
      s.id === stepId ? { ...s, status: 'in_progress' as const } : s
    );
    setSteps(updatedSteps);
    setActionLoading({ [`start_${stepId}`]: true });

    try {
      await stepsApi.update(stepId, { status: 'in_progress' });
      toast.success('Step started');
      onPhaseUpdate();
    } catch (error) {
      // Rollback on error
      setSteps(previousSteps);
      console.error('Error starting step:', error);
      toast.error('Failed to start step');
    } finally {
      setActionLoading({});
    }
  };

  const completedCount = steps.filter((s) => s.status === 'completed').length;
  const progressPercentage = steps.length > 0 ? (completedCount / steps.length) * 100 : 0;

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-slate-600">Loading steps...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Phase Steps</CardTitle>
              <p className="text-sm text-slate-600 mt-1">
                {completedCount} of {steps.length} steps completed
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-2xl font-bold text-slate-900">{Math.round(progressPercentage)}%</div>
                <div className="text-xs text-slate-600">Progress</div>
              </div>
              {phase.status === 'not_started' && canEdit && (
                <Button
                  onClick={handleStartPhase}
                  size="sm"
                  className="gap-2"
                  disabled={actionLoading.phase_start}
                >
                  {actionLoading.phase_start ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <PlayCircle className="h-4 w-4" />
                  )}
                  {actionLoading.phase_start ? 'Starting...' : 'Start Phase'}
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={cn(
                  'flex items-center gap-4 p-4 rounded-lg border-2 transition-all cursor-pointer hover:shadow-md',
                  step.status === 'completed'
                    ? 'bg-green-50 border-green-200'
                    : step.status === 'in_progress'
                    ? 'bg-blue-50 border-blue-300'
                    : step.status === 'blocked'
                    ? 'bg-red-50 border-red-200'
                    : 'bg-white border-slate-200 hover:border-blue-300'
                )}
                onClick={() => {
                  setSelectedStep(step);
                  setShowStepDialog(true);
                }}
              >
                <div className="flex-shrink-0">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold',
                      step.status === 'completed'
                        ? 'bg-green-500 text-white'
                        : step.status === 'in_progress'
                        ? 'bg-blue-600 text-white'
                        : step.status === 'blocked'
                        ? 'bg-red-500 text-white'
                        : 'bg-slate-300 text-slate-700'
                    )}
                  >
                    {step.status === 'completed' ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : step.status === 'in_progress' ? (
                      <Clock className="h-5 w-5" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-slate-900">{step.step_name}</h4>
                    {step.requires_approval && (
                      <Badge variant="outline" className="text-xs">Requires Approval</Badge>
                    )}
                  </div>
                  {step.step_description && (
                    <p className="text-sm text-slate-600 line-clamp-1">{step.step_description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                    {step.assigned_user && (
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {step.assigned_user.name}
                      </div>
                    )}
                    {step.deadline && (
                      <div className={cn(
                        'flex items-center gap-1',
                        isPast(new Date(step.deadline)) && step.status !== 'completed' && 'text-red-600 font-medium'
                      )}>
                        <Calendar className="h-3 w-3" />
                        Due {format(new Date(step.deadline), 'MMM d, yyyy')}
                      </div>
                    )}
                    {step.completion_date && (
                      <div className="flex items-center gap-1 text-green-600">
                        <CheckCircle2 className="h-3 w-3" />
                        Completed {format(new Date(step.completion_date), 'MMM d, yyyy')}
                      </div>
                    )}
                  </div>
                </div>

                {canEdit && step.status !== 'completed' && step.status !== 'blocked' && (
                  <Button
                    size="sm"
                    variant={step.status === 'in_progress' ? 'default' : 'outline'}
                    disabled={actionLoading[`start_${step.id}`] || actionLoading[`complete_${step.id}`]}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (step.status === 'in_progress') {
                        handleCompleteStep(step.id);
                      } else {
                        handleStartStep(step.id);
                      }
                    }}
                  >
                    {(actionLoading[`start_${step.id}`] || actionLoading[`complete_${step.id}`]) && (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    )}
                    {step.status === 'in_progress' ? 'Complete' : 'Start'}
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {selectedStep && (
        <StepDetailDialog
          step={selectedStep}
          open={showStepDialog}
          onOpenChange={setShowStepDialog}
          onUpdate={onPhaseUpdate}
          canEdit={canEdit}
        />
      )}
    </>
  );
}
