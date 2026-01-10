import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { CheckCircle2, XCircle, Loader2, MessageSquare, Calendar, Users } from 'lucide-react';
import { format } from 'date-fns';
import { approvalsApi, type Approval } from '@/services/api';
import { DelegateApprovalDialog } from './DelegateApprovalDialog';

interface ApprovalActionsCardProps {
  approval: Approval;
  currentUserId: string;
  onUpdate: () => void;
}

export function ApprovalActionsCard({
  approval,
  currentUserId,
  onUpdate,
}: ApprovalActionsCardProps) {
  const [comments, setComments] = useState('');
  const [loading, setLoading] = useState(false);
  const [showDelegateDialog, setShowDelegateDialog] = useState(false);

  const isApprover = approval.approver_id === currentUserId;
  const isPending = approval.approval_status === 'pending';
  const canTakeAction = isApprover && isPending;

  const handleApprove = async () => {
    setLoading(true);
    try {
      const response = await approvalsApi.approve(approval.id, comments || undefined);
      toast.success(response.message);
      onUpdate();
    } catch (error) {
      console.error('Error approving document:', error);
      toast.error('Failed to approve document');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!comments.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }

    setLoading(true);
    try {
      const response = await approvalsApi.reject(approval.id, comments);
      toast.error(response.message);
      onUpdate();
    } catch (error) {
      console.error('Error rejecting document:', error);
      toast.error('Failed to reject document');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    switch (approval.approval_status) {
      case 'approved':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Approved</Badge>;
      case 'rejected':
        return <Badge className="bg-red-100 text-red-800 border-red-200">Rejected</Badge>;
      case 'requested_changes':
        return <Badge className="bg-amber-100 text-amber-800 border-amber-200">Changes Requested</Badge>;
      default:
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Pending</Badge>;
    }
  };

  return (
    <Card className={canTakeAction ? 'border-blue-300 bg-blue-50/50' : ''}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">
              {approval.approver?.name || 'Unknown Approver'}
            </CardTitle>
            <p className="text-sm text-slate-600 mt-1">
              {approval.approver?.email}
            </p>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            <span>Requested {format(new Date(approval.requested_at), 'MMM d, yyyy')}</span>
          </div>
          {approval.approval_date && (
            <div className="flex items-center gap-1">
              <CheckCircle2 className="h-4 w-4" />
              <span>Responded {format(new Date(approval.approval_date), 'MMM d, yyyy')}</span>
            </div>
          )}
        </div>

        {approval.comments && (
          <div className="bg-slate-100 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <MessageSquare className="h-4 w-4 text-slate-600" />
              <Label className="text-sm font-medium">Comments</Label>
            </div>
            <p className="text-sm text-slate-700">{approval.comments}</p>
          </div>
        )}

        {canTakeAction && (
          <div className="space-y-3 pt-3 border-t">
            <div className="bg-blue-100 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-900 font-medium">
                Action Required: Please review and approve or reject this document
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor={`comments-${approval.id}`}>
                Comments {approval.approval_status === 'pending' && '(optional for approval, required for rejection)'}
              </Label>
              <Textarea
                id={`comments-${approval.id}`}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Add your comments or feedback..."
                rows={3}
              />
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleApprove}
                disabled={loading}
                className="flex-1 gap-2 bg-green-600 hover:bg-green-700"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4" />
                )}
                Approve
              </Button>
              <Button
                onClick={handleReject}
                disabled={loading}
                variant="destructive"
                className="flex-1 gap-2"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <XCircle className="h-4 w-4" />
                )}
                Reject
              </Button>
            </div>

            <div className="mt-2">
              <Button
                onClick={() => setShowDelegateDialog(true)}
                disabled={loading}
                variant="outline"
                className="w-full gap-2"
                size="sm"
              >
                <Users className="h-4 w-4" />
                Delegate to Another User
              </Button>
            </div>
          </div>
        )}
      </CardContent>

      <DelegateApprovalDialog
        open={showDelegateDialog}
        onOpenChange={setShowDelegateDialog}
        approvalId={approval.id}
        approvalName={approval.document?.name || 'this document'}
        onSuccess={onUpdate}
      />
    </Card>
  );
}
