import { useEffect, useState } from 'react';
import { projectsApi, stepsApi, type Step } from '@/services/api';

export function useProcurementSteps(projectId: string | null) {
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!projectId) {
      setSteps([]);
      setLoading(false);
      return;
    }

    fetchSteps();

    // Poll for updates every 30 seconds (replacing Supabase real-time subscription)
    const intervalId = setInterval(fetchSteps, 30000);

    return () => {
      clearInterval(intervalId);
    };
  }, [projectId]);

  const fetchSteps = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      const response = await projectsApi.getSteps(projectId);
      setSteps(response.steps || []);
      setError(null);
    } catch (err) {
      setError(err as Error);
      console.error('Error fetching steps:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateStep = async (stepId: string, updates: {
    status?: string;
    completion_date?: string;
    notes?: string;
    assigned_user_id?: string;
  }) => {
    try {
      await stepsApi.update(stepId, updates);
      await fetchSteps();
    } catch (err) {
      console.error('Error updating step:', err);
      throw err;
    }
  };

  const completeStep = async (stepId: string, notes?: string) => {
    await updateStep(stepId, {
      status: 'completed',
      completion_date: new Date().toISOString().split('T')[0],
      notes,
    });
  };

  const assignStep = async (stepId: string, userId: string) => {
    await updateStep(stepId, {
      assigned_user_id: userId,
    });
  };

  return {
    steps,
    loading,
    error,
    updateStep,
    completeStep,
    assignStep,
    refresh: fetchSteps,
  };
}
