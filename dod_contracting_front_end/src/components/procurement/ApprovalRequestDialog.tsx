/**
 * ApprovalRequestDialog - Enhanced dialog for requesting document approvals
 * 
 * Features smart routing support:
 * - auto_co: Automatically routes to project's Contracting Officer
 * - default: Routes to document's configured default approver
 * - manual: User manually selects approvers from a list
 * 
 * Dependencies:
 * - @/components/ui/dialog, radio-group, button, label, checkbox
 * - @/services/api for approvalsApi and authApi
 * - lucide-react for icons
 */
import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { toast } from 'sonner';
import { Loader2, UserCheck, Building2, User, List, Info } from 'lucide-react';
import { approvalsApi, authApi, type User as UserType, type ApprovalRouting } from '@/services/api';

interface ApprovalRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  documentId: string;
  documentName: string;
  uploadId?: string;
  // Smart routing props
  documentRouting?: ApprovalRouting;    // Current routing setting from document
  defaultApproverId?: string;           // Current default approver ID
  defaultApproverName?: string;         // Display name for default approver
  projectCoName?: string;               // Project's Contracting Officer name for display
  onSuccess: () => void;
}

export function ApprovalRequestDialog({
  open,
  onOpenChange,
  documentId,
  documentName,
  uploadId,
  documentRouting = 'auto_co',          // Default to auto_co routing
  defaultApproverId,
  defaultApproverName,
  projectCoName,
  onSuccess,
}: ApprovalRequestDialogProps) {
  // State for user list and manual selection
  const [users, setUsers] = useState<UserType[]>([]);
  const [selectedApprovers, setSelectedApprovers] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingUsers, setFetchingUsers] = useState(true);

  // Routing selection state
  const [routingMethod, setRoutingMethod] = useState<ApprovalRouting>(documentRouting);
  const [showManualSelection, setShowManualSelection] = useState(documentRouting === 'manual');

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      fetchUsers();
      setSelectedApprovers([]);
      setRoutingMethod(documentRouting);
      setShowManualSelection(documentRouting === 'manual');
    }
  }, [open, documentRouting]);

  // Fetch users who can approve documents
  const fetchUsers = async () => {
    try {
      setFetchingUsers(true);
      const response = await authApi.getUsers();
      // Filter to only show users who can approve (contracting officers, program managers, approvers)
      const approvers = response.users.filter((user: UserType) =>
        ['contracting_officer', 'program_manager', 'approver'].includes(user.role) &&
        user.is_active
      );
      setUsers(approvers);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setFetchingUsers(false);
    }
  };

  // Toggle approver selection for manual mode
  const toggleApprover = (userId: string) => {
    setSelectedApprovers(prev =>
      prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  // Handle routing method change
  const handleRoutingChange = (value: ApprovalRouting) => {
    setRoutingMethod(value);
    setShowManualSelection(value === 'manual');
  };

  // Submit approval request
  const handleSubmit = async () => {
    // Validate manual selection has approvers
    if (routingMethod === 'manual' && selectedApprovers.length === 0) {
      toast.error('Please select at least one approver');
      return;
    }

    setLoading(true);
    try {
      const response = await approvalsApi.requestApproval(
        documentId,
        routingMethod === 'manual' ? selectedApprovers : undefined,
        uploadId,
        routingMethod
      );

      // Show success with routing info
      toast.success(response.message);
      if (response.routing_info) {
        toast.info(response.routing_info);
      }
      onSuccess();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Error requesting approval:', error);
      toast.error(error.message || 'Failed to request approval');
    } finally {
      setLoading(false);
    }
  };

  // Get info text based on current routing selection
  const getRoutingInfoText = () => {
    switch (routingMethod) {
      case 'auto_co':
        return projectCoName 
          ? `Approval will be automatically sent to the project's Contracting Officer (${projectCoName})`
          : 'Approval will be automatically sent to the project\'s Contracting Officer';
      case 'default':
        return defaultApproverName
          ? `Approval will be sent to the configured default approver (${defaultApproverName})`
          : 'Approval will be sent to the configured default approver';
      case 'manual':
        return 'Approval will be sent to your selected approver(s)';
      default:
        return '';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Request Approval</DialogTitle>
          <DialogDescription>
            Choose how to route "{documentName}" for approval
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Routing Method Selection */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Approval Routing</Label>
            <RadioGroup
              value={routingMethod}
              onValueChange={(value) => handleRoutingChange(value as ApprovalRouting)}
              className="space-y-2"
            >
              {/* Auto-CO Option */}
              <div 
                className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors
                  ${routingMethod === 'auto_co' ? 'border-blue-500 bg-blue-50' : 'hover:bg-slate-50'}`}
                onClick={() => handleRoutingChange('auto_co')}
              >
                <RadioGroupItem value="auto_co" id="auto_co" className="mt-1" />
                <div className="flex-1">
                  <Label htmlFor="auto_co" className="font-medium flex items-center gap-2 cursor-pointer">
                    <Building2 className="h-4 w-4 text-blue-600" />
                    Project Contracting Officer
                  </Label>
                  <p className="text-sm text-slate-600 mt-1">
                    Route to: <span className="font-medium">{projectCoName || 'Project CO (auto-detected)'}</span>
                  </p>
                </div>
              </div>

              {/* Default Approver Option (only show if configured) */}
              {defaultApproverId && (
                <div 
                  className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors
                    ${routingMethod === 'default' ? 'border-green-500 bg-green-50' : 'hover:bg-slate-50'}`}
                  onClick={() => handleRoutingChange('default')}
                >
                  <RadioGroupItem value="default" id="default" className="mt-1" />
                  <div className="flex-1">
                    <Label htmlFor="default" className="font-medium flex items-center gap-2 cursor-pointer">
                      <User className="h-4 w-4 text-green-600" />
                      Default Approver
                    </Label>
                    <p className="text-sm text-slate-600 mt-1">
                      Route to: <span className="font-medium">{defaultApproverName || 'Configured approver'}</span>
                    </p>
                  </div>
                </div>
              )}

              {/* Manual Selection Option */}
              <div 
                className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors
                  ${routingMethod === 'manual' ? 'border-orange-500 bg-orange-50' : 'hover:bg-slate-50'}`}
                onClick={() => handleRoutingChange('manual')}
              >
                <RadioGroupItem value="manual" id="manual" className="mt-1" />
                <div className="flex-1">
                  <Label htmlFor="manual" className="font-medium flex items-center gap-2 cursor-pointer">
                    <List className="h-4 w-4 text-orange-600" />
                    Manual Selection
                  </Label>
                  <p className="text-sm text-slate-600 mt-1">
                    Choose specific approvers from the list below
                  </p>
                </div>
              </div>
            </RadioGroup>
          </div>

          {/* Manual Approver Selection (shown when manual is selected) */}
          {showManualSelection && (
            <div className="space-y-2 border-t pt-4">
              <Label className="text-sm font-medium">Select Approvers</Label>
          {fetchingUsers ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-8 text-slate-600">
              <UserCheck className="h-12 w-12 mx-auto mb-2 text-slate-400" />
              <p>No approvers available</p>
            </div>
          ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
              {users.map((user) => (
                <div
                  key={user.id}
                      className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors
                        ${selectedApprovers.includes(user.id) ? 'border-blue-500 bg-blue-50' : 'hover:bg-slate-50'}`}
                  onClick={() => toggleApprover(user.id)}
                >
                  <Checkbox
                    checked={selectedApprovers.includes(user.id)}
                    onCheckedChange={() => toggleApprover(user.id)}
                  />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{user.name}</div>
                    <div className="text-xs text-slate-600">{user.email}</div>
                    <div className="text-xs text-slate-500 capitalize mt-1">
                      {user.role.replace('_', ' ')}
                      {user.department && ` • ${user.department}`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedApprovers.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-900">
                {selectedApprovers.length} approver(s) selected
              </p>
            </div>
          )}
            </div>
          )}

          {/* Routing Info Box */}
          <div className="bg-slate-50 border rounded-lg p-3 flex items-start gap-2">
            <Info className="h-4 w-4 text-slate-500 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-slate-600">
              {getRoutingInfoText()}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading || (routingMethod === 'manual' && selectedApprovers.length === 0)}
          >
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Request Approval
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
