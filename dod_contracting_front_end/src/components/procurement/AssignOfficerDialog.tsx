/**
 * AssignOfficerDialog Component
 * 
 * Dialog for assigning/reassigning contracting officers and program managers to projects.
 * 
 * Dependencies:
 * - @/components/ui/dialog - Shadcn dialog components
 * - @/services/api - API calls for users and project updates
 * - sonner - Toast notifications
 */
import { useState, useEffect } from 'react';
import { UserPlus, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { authApi, projectsApi, type User } from '@/services/api';
import { toast } from 'sonner';

// Props interface for the component
interface AssignOfficerDialogProps {
  projectId: string;
  projectName: string;
  currentOfficerId?: string;
  currentProgramManagerId?: string;
  onAssigned: () => void;
  trigger?: React.ReactNode;
}

export function AssignOfficerDialog({
  projectId,
  projectName,
  currentOfficerId,
  currentProgramManagerId,
  onAssigned,
  trigger,
}: AssignOfficerDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // User lists for dropdowns
  const [contractingOfficers, setContractingOfficers] = useState<User[]>([]);
  const [programManagers, setProgramManagers] = useState<User[]>([]);
  
  // Selected values
  const [selectedOfficerId, setSelectedOfficerId] = useState<string>(currentOfficerId || '');
  const [selectedPMId, setSelectedPMId] = useState<string>(currentProgramManagerId || '');

  // Fetch users by role when dialog opens
  useEffect(() => {
    if (open) {
      fetchUsers();
    }
  }, [open]);

  // Reset selections when current values change
  useEffect(() => {
    setSelectedOfficerId(currentOfficerId || '');
    setSelectedPMId(currentProgramManagerId || '');
  }, [currentOfficerId, currentProgramManagerId]);

  // Fetch contracting officers and program managers
  const fetchUsers = async () => {
    setLoading(true);
    try {
      // Fetch both user types in parallel for better performance
      const [coResponse, pmResponse] = await Promise.all([
        authApi.getUsers('contracting_officer'),
        authApi.getUsers('program_manager'),
      ]);
      setContractingOfficers(coResponse.users);
      setProgramManagers(pmResponse.users);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  // Handle assignment submission
  const handleAssign = async () => {
    setSaving(true);
    try {
      // Build update payload with only changed values
      const updates: Record<string, string> = {};
      
      if (selectedOfficerId && selectedOfficerId !== currentOfficerId) {
        updates.contracting_officer_id = selectedOfficerId;
      }
      
      if (selectedPMId !== currentProgramManagerId) {
        // Empty string means unassign
        updates.program_manager_id = selectedPMId || '';
      }

      // Only update if there are changes
      if (Object.keys(updates).length > 0) {
        await projectsApi.update(projectId, updates);
        toast.success('Project assignments updated successfully');
        onAssigned();
      }
      
      setOpen(false);
    } catch (error) {
      console.error('Error updating assignments:', error);
      toast.error('Failed to update project assignments');
    } finally {
      setSaving(false);
    }
  };

  // Wrap in div to stop propagation at container level - prevents card navigation
  return (
    <div onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          {trigger || (
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 border-slate-200 text-slate-600 hover:text-blue-600 hover:bg-blue-50 hover:border-blue-200"
              aria-label="Assign officers"
              title="Assign officers"
            >
              <UserPlus className="h-5 w-5 shrink-0" />
            </Button>
          )}
        </DialogTrigger>
        <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Assign Officers</DialogTitle>
          <DialogDescription>
            Assign or reassign contracting officer and program manager for "{projectName}"
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="space-y-4 py-4">
            {/* Contracting Officer Selection */}
            <div className="space-y-2">
              <Label htmlFor="contracting-officer">Contracting Officer *</Label>
              <Select value={selectedOfficerId} onValueChange={setSelectedOfficerId}>
                <SelectTrigger id="contracting-officer">
                  <SelectValue placeholder="Select contracting officer" />
                </SelectTrigger>
                <SelectContent>
                  {contractingOfficers.length === 0 ? (
                    <SelectItem value="none" disabled>
                      No contracting officers available
                    </SelectItem>
                  ) : (
                    contractingOfficers.map((user) => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.name} ({user.email})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">
                The contracting officer responsible for this procurement
              </p>
            </div>

            {/* Program Manager Selection */}
            <div className="space-y-2">
              <Label htmlFor="program-manager">Program Manager (Optional)</Label>
              <Select value={selectedPMId} onValueChange={setSelectedPMId}>
                <SelectTrigger id="program-manager">
                  <SelectValue placeholder="Select program manager (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">
                    <span className="text-slate-500">None (unassign)</span>
                  </SelectItem>
                  {programManagers.map((user) => (
                    <SelectItem key={user.id} value={user.id}>
                      {user.name} ({user.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">
                The program manager overseeing this project
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleAssign} disabled={loading || saving || !selectedOfficerId}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Assignments'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </div>
  );
}

