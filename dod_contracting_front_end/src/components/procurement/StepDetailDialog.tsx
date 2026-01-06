import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { stepsApi } from '@/services/api';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { Calendar, User, FileText, CheckCircle2 } from 'lucide-react';

interface Step {
  id: string;
  step_name: string;
  step_description: string | null;
  status: string;
  deadline: string | null;
  completion_date: string | null;
  notes: string | null;
  assigned_user: { name: string; email: string } | null;
  requires_approval: boolean;
}

interface StepDetailDialogProps {
  step: Step;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate: () => void;
  canEdit: boolean;
}

export function StepDetailDialog({ step, open, onOpenChange, onUpdate, canEdit }: StepDetailDialogProps) {
  const [notes, setNotes] = useState(step.notes || '');
  const [deadline, setDeadline] = useState(step.deadline || '');
  const [loading, setLoading] = useState(false);

  // Update state when step changes (but only when dialog is opened)
  useEffect(() => {
    if (open) {
      setNotes(step.notes || '');
      setDeadline(step.deadline || '');
    }
  }, [step.id, open]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await stepsApi.update(step.id, {
        notes,
        // Only include deadline if it's not empty
        ...(deadline && { deadline }),
      });

      toast.success('Step updated successfully');
      onUpdate();
      onOpenChange(false);
    } catch (error) {
      console.error('Error updating step:', error);
      toast.error('Failed to update step');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      await stepsApi.update(step.id, {
        status: 'completed',
        completion_date: new Date().toISOString().split('T')[0],
        notes,
      });

      toast.success('Step completed successfully');
      onUpdate();
      onOpenChange(false);
    } catch (error) {
      console.error('Error completing step:', error);
      toast.error('Failed to complete step');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" aria-describedby={step.step_description ? undefined : undefined}>
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="text-xl">{step.step_name}</DialogTitle>
              {step.step_description && (
                <p className="text-sm text-slate-600 mt-2">{step.step_description}</p>
              )}
            </div>
            <Badge className={getStatusColor(step.status)} variant="outline">
              {step.status.replace('_', ' ')}
            </Badge>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {step.assigned_user && (
              <div className="flex items-center gap-2 text-sm">
                <User className="h-4 w-4 text-slate-400" />
                <div>
                  <p className="text-slate-600">Assigned to</p>
                  <p className="font-medium">{step.assigned_user.name}</p>
                </div>
              </div>
            )}

            {step.deadline && (
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-slate-400" />
                <div>
                  <p className="text-slate-600">Deadline</p>
                  <p className="font-medium">{format(new Date(step.deadline), 'MMM d, yyyy')}</p>
                </div>
              </div>
            )}

            {step.completion_date && (
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <div>
                  <p className="text-slate-600">Completed on</p>
                  <p className="font-medium text-green-600">{format(new Date(step.completion_date), 'MMM d, yyyy')}</p>
                </div>
              </div>
            )}

            {step.requires_approval && (
              <div className="flex items-center gap-2 text-sm">
                <FileText className="h-4 w-4 text-slate-400" />
                <div>
                  <p className="text-slate-600">Approval Required</p>
                  <p className="font-medium">Yes</p>
                </div>
              </div>
            )}
          </div>

          {canEdit && step.status !== 'completed' && (
            <div className="space-y-4 pt-4 border-t">
              <div className="space-y-2">
                <Label htmlFor="deadline">Deadline</Label>
                <Input
                  id="deadline"
                  type="date"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about this step..."
                  rows={4}
                />
              </div>
            </div>
          )}

          {!canEdit && step.notes && (
            <div className="space-y-2 pt-4 border-t">
              <Label>Notes</Label>
              <div className="p-3 bg-slate-50 rounded-lg text-sm text-slate-700">
                {step.notes}
              </div>
            </div>
          )}
        </div>

        {canEdit && step.status !== 'completed' && (
          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              Cancel
            </Button>
            <Button variant="outline" onClick={handleSave} disabled={loading}>
              Save Changes
            </Button>
            <Button onClick={handleComplete} disabled={loading}>
              {loading ? 'Completing...' : 'Complete Step'}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}

function getStatusColor(status: string) {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-800 border-green-200';
    case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'blocked': return 'bg-red-100 text-red-800 border-red-200';
    case 'skipped': return 'bg-slate-100 text-slate-800 border-slate-200';
    default: return 'bg-slate-100 text-slate-800 border-slate-200';
  }
}
