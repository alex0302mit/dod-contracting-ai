import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { Loader2, UserCheck, Users } from 'lucide-react';
import { approvalsApi, authApi, type User } from '@/services/api';

interface DelegateApprovalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  approvalId: string;
  approvalName: string;
  onSuccess: () => void;
}

export function DelegateApprovalDialog({
  open,
  onOpenChange,
  approvalId,
  approvalName,
  onSuccess,
}: DelegateApprovalDialogProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingUsers, setFetchingUsers] = useState(true);

  useEffect(() => {
    if (open) {
      fetchUsers();
      setSelectedUser(null);
      setReason('');
    }
  }, [open]);

  const fetchUsers = async () => {
    try {
      setFetchingUsers(true);
      const response = await authApi.getUsers();
      // Filter to only show users who can approve
      const approvers = response.users.filter((user: User) =>
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

  const handleSubmit = async () => {
    if (!selectedUser) {
      toast.error('Please select a user to delegate to');
      return;
    }

    setLoading(true);
    try {
      const response = await approvalsApi.delegate(
        approvalId,
        selectedUser,
        reason || undefined
      );

      toast.success(response.message);
      onSuccess();
      onOpenChange(false);
    } catch (error) {
      console.error('Error delegating approval:', error);
      toast.error('Failed to delegate approval');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Delegate Approval
          </DialogTitle>
          <DialogDescription>
            Delegate the approval for "{approvalName}" to another user
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {fetchingUsers ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-8 text-slate-600">
              <UserCheck className="h-12 w-12 mx-auto mb-2 text-slate-400" />
              <p>No eligible users available for delegation</p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <Label className="text-sm font-medium">Select Delegate</Label>
                <div className="space-y-2 max-h-64 overflow-y-auto border rounded-lg p-2">
                  {users.map((user) => (
                    <div
                      key={user.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedUser === user.id
                          ? 'bg-blue-50 border-blue-300'
                          : 'hover:bg-slate-50 border-slate-200'
                      }`}
                      onClick={() => setSelectedUser(user.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{user.name}</div>
                          <div className="text-xs text-slate-600">{user.email}</div>
                          <div className="text-xs text-slate-500 capitalize mt-1">
                            {user.role.replace('_', ' ')}
                            {user.department && ` • ${user.department}`}
                          </div>
                        </div>
                        {selectedUser === user.id && (
                          <UserCheck className="h-5 w-5 text-blue-600" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="reason">Reason for Delegation (Optional)</Label>
                <Textarea
                  id="reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Provide a reason for delegating this approval..."
                  rows={3}
                />
              </div>

              {selectedUser && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-900">
                    This approval will be transferred to the selected user
                  </p>
                </div>
              )}
            </>
          )}
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
            disabled={loading || !selectedUser}
          >
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Delegate Approval
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
