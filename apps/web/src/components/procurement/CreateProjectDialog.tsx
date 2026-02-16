import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useProcurementProjects } from '@/hooks/useProcurementProjects';
import { useAuth } from '@/contexts/AuthContext';
import { authApi, type User } from '@/services/api';
import { toast } from 'sonner';

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectDialog({ open, onOpenChange }: CreateProjectDialogProps) {
  const { createProject } = useProcurementProjects();
  const { user, activeOrgId, userOrganizations } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loadingOfficers, setLoadingOfficers] = useState(false);
  const [loadingPMs, setLoadingPMs] = useState(false);
  const [contractingOfficers, setContractingOfficers] = useState<User[]>([]);
  const [programManagers, setProgramManagers] = useState<User[]>([]);
  const [selectedOfficerId, setSelectedOfficerId] = useState<string>('');
  const [selectedPMId, setSelectedPMId] = useState<string>('');
  const [selectedOrgId, setSelectedOrgId] = useState<string>(activeOrgId ?? '');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_type: 'rfp' as 'rfp' | 'rfq' | 'task_order' | 'idiq' | 'other',
    estimated_value: '',
    target_completion_date: '',
  });

  // Fetch contracting officers and PMs when dialog opens
  useEffect(() => {
    if (open) {
      fetchContractingOfficers();
      fetchProgramManagers();
      if (activeOrgId) setSelectedOrgId(activeOrgId);
    }
  }, [open, activeOrgId]);

  // Default to current user if they are a contracting officer
  useEffect(() => {
    if (user && contractingOfficers.length > 0) {
      const isCurrentUserCO = contractingOfficers.find(co => co.id === user.id);
      if (isCurrentUserCO && !selectedOfficerId) {
        setSelectedOfficerId(user.id);
      }
    }
  }, [user, contractingOfficers, selectedOfficerId]);

  const fetchContractingOfficers = async () => {
    setLoadingOfficers(true);
    try {
      const response = await authApi.getUsers('contracting_officer');
      setContractingOfficers(response.users);
    } catch (error) {
      console.error('Error fetching contracting officers:', error);
      toast.error('Failed to load contracting officers');
    } finally {
      setLoadingOfficers(false);
    }
  };

  const fetchProgramManagers = async () => {
    setLoadingPMs(true);
    try {
      const response = await authApi.getUsers('program_manager');
      setProgramManagers(response.users);
    } catch (error) {
      console.error('Error fetching program managers:', error);
    } finally {
      setLoadingPMs(false);
    }
  };

  const fillMockData = () => {
    const mockDate = new Date();
    mockDate.setMonth(mockDate.getMonth() + 6);

    setFormData({
      name: 'Enterprise Cloud Infrastructure Services',
      description: 'Procurement for comprehensive cloud infrastructure services including compute, storage, networking, and managed database services to support agency-wide digital transformation initiatives.',
      project_type: 'rfp',
      estimated_value: '15000000',
      target_completion_date: mockDate.toISOString().split('T')[0],
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    // Validate contracting officer is selected
    if (!selectedOfficerId) {
      toast.error('Please select a contracting officer');
      return;
    }

    setLoading(true);
    try {
      await createProject({
        name: formData.name,
        description: formData.description || '',
        project_type: formData.project_type,
        estimated_value: formData.estimated_value ? parseFloat(formData.estimated_value) : 0,
        contracting_officer_id: selectedOfficerId,
        program_manager_id: selectedPMId || undefined,
        organization_id: selectedOrgId || undefined,
      });

      toast.success('Project created successfully');
      onOpenChange(false);
      // Reset form
      setFormData({
        name: '',
        description: '',
        project_type: 'rfp',
        estimated_value: '',
        target_completion_date: '',
      });
      setSelectedOfficerId('');
      setSelectedPMId('');
    } catch (error) {
      console.error('Error creating project:', error);
      toast.error('Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create New Procurement Project</DialogTitle>
          <DialogDescription>
            Set up a new procurement project to track through all phases
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="flex justify-end mb-2">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={fillMockData}
                className="text-blue-600 hover:text-blue-700"
              >
                Fill with Example Data
              </Button>
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Project Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Cloud Infrastructure Services RFP"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Provide a brief description of the procurement"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="project_type">Project Type *</Label>
                <Select
                  value={formData.project_type}
                  onValueChange={(value: 'rfp' | 'rfq' | 'task_order' | 'idiq' | 'other') => setFormData({ ...formData, project_type: value })}
                >
                  <SelectTrigger id="project_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="rfp">Request for Proposal (RFP)</SelectItem>
                    <SelectItem value="rfq">Request for Quote (RFQ)</SelectItem>
                    <SelectItem value="task_order">Task Order</SelectItem>
                    <SelectItem value="idiq">IDIQ Contract</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="estimated_value">Estimated Value ($)</Label>
                <Input
                  id="estimated_value"
                  type="number"
                  value={formData.estimated_value}
                  onChange={(e) => setFormData({ ...formData, estimated_value: e.target.value })}
                  placeholder="5000000"
                  min="0"
                  step="1000"
                />
              </div>
            </div>

            {/* Contracting Officer Selection */}
            <div className="space-y-2">
              <Label htmlFor="contracting_officer">Contracting Officer *</Label>
              {loadingOfficers ? (
                <div className="flex items-center gap-2 h-10 px-3 border rounded-md bg-slate-50">
                  <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                  <span className="text-sm text-slate-500">Loading officers...</span>
                </div>
              ) : (
                <Select value={selectedOfficerId} onValueChange={setSelectedOfficerId}>
                  <SelectTrigger id="contracting_officer">
                    <SelectValue placeholder="Select contracting officer" />
                  </SelectTrigger>
                  <SelectContent>
                    {contractingOfficers.length === 0 ? (
                      <SelectItem value="none" disabled>
                        No contracting officers available
                      </SelectItem>
                    ) : (
                      contractingOfficers.map((officer) => (
                        <SelectItem key={officer.id} value={officer.id}>
                          {officer.name} ({officer.email})
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              )}
              <p className="text-xs text-slate-500">
                The contracting officer responsible for this procurement
              </p>
            </div>

            {/* Program Manager Selection */}
            <div className="space-y-2">
              <Label htmlFor="program_manager">Program Manager</Label>
              {loadingPMs ? (
                <div className="flex items-center gap-2 h-10 px-3 border rounded-md bg-slate-50">
                  <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                  <span className="text-sm text-slate-500">Loading PMs...</span>
                </div>
              ) : (
                <Select value={selectedPMId} onValueChange={setSelectedPMId}>
                  <SelectTrigger id="program_manager">
                    <SelectValue placeholder="Select program manager (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    {programManagers.map((pm) => (
                      <SelectItem key={pm.id} value={pm.id}>
                        {pm.name} ({pm.email})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Organization Selection */}
            {userOrganizations.length > 1 && (
              <div className="space-y-2">
                <Label htmlFor="organization">Organization</Label>
                <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                  <SelectTrigger id="organization">
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    {userOrganizations.map((membership) => (
                      <SelectItem key={membership.organization_id} value={membership.organization_id}>
                        {membership.organization?.name ?? membership.organization_id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-slate-500">
                  The organization this project belongs to
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="target_completion_date">Target Completion Date</Label>
              <Input
                id="target_completion_date"
                type="date"
                value={formData.target_completion_date}
                onChange={(e) => setFormData({ ...formData, target_completion_date: e.target.value })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
