import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useQuery } from '@tanstack/react-query';
import { Loader2, History, CheckCircle2, XCircle, UserCheck, Users, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { approvalsApi, type Approval, type ApprovalAuditLog } from '@/services/api';

interface ApprovalHistoryViewProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  documentId: string;
}

export function ApprovalHistoryView({
  open,
  onOpenChange,
  documentId,
}: ApprovalHistoryViewProps) {
  const { data: historyData, isLoading } = useQuery({
    queryKey: ['approvalHistory', documentId],
    queryFn: () => approvalsApi.getApprovalHistory(documentId),
    enabled: open,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-amber-600" />;
      default:
        return <UserCheck className="h-4 w-4 text-slate-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const classes: Record<string, string> = {
      approved: 'bg-green-100 text-green-800 border-green-200',
      rejected: 'bg-red-100 text-red-800 border-red-200',
      pending: 'bg-amber-100 text-amber-800 border-amber-200',
      requested_changes: 'bg-blue-100 text-blue-800 border-blue-200',
    };
    return classes[status] || 'bg-slate-100 text-slate-800 border-slate-200';
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'approved':
        return <CheckCircle2 className="h-3 w-3 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-3 w-3 text-red-600" />;
      case 'delegated':
        return <Users className="h-3 w-3 text-blue-600" />;
      case 'requested':
        return <UserCheck className="h-3 w-3 text-slate-600" />;
      default:
        return <History className="h-3 w-3 text-slate-400" />;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <History className="h-5 w-5" />
            <DialogTitle>Approval History</DialogTitle>
          </div>
          {historyData && (
            <p className="text-sm text-slate-600 mt-2">
              Document: {historyData.document_name}
            </p>
          )}
        </DialogHeader>

        <ScrollArea className="h-[600px] pr-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : !historyData || historyData.history.length === 0 ? (
            <div className="text-center py-12 text-slate-600">
              <History className="h-12 w-12 mx-auto mb-4 text-slate-400" />
              <p>No approval history found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {historyData.history.map((approval: Approval) => (
                <Card key={approval.id} className="border-2">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {getStatusIcon(approval.approval_status)}
                          <h3 className="font-semibold">
                            {approval.approver?.name || 'Unknown Approver'}
                          </h3>
                          <Badge className={getStatusBadge(approval.approval_status)} variant="outline">
                            {approval.approval_status.replace('_', ' ')}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-600">{approval.approver?.email}</p>
                        <p className="text-xs text-slate-500 capitalize mt-1">
                          {approval.approver?.role?.replace('_', ' ')}
                        </p>

                        {approval.delegated_from && (
                          <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                            <Users className="h-3 w-3 inline mr-1" />
                            Delegated from {approval.delegated_from.name}
                          </div>
                        )}
                      </div>
                      <div className="text-right text-sm text-slate-600">
                        <div>Requested</div>
                        <div className="font-medium">
                          {format(new Date(approval.requested_at), 'MMM d, yyyy')}
                        </div>
                        {approval.approval_date && (
                          <>
                            <div className="mt-2">Responded</div>
                            <div className="font-medium">
                              {format(new Date(approval.approval_date), 'MMM d, yyyy')}
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    {approval.comments && (
                      <div className="bg-slate-50 rounded-lg p-3 mb-3">
                        <div className="text-xs font-medium text-slate-600 mb-1">Comments:</div>
                        <p className="text-sm text-slate-700">{approval.comments}</p>
                      </div>
                    )}

                    {approval.audit_trail && approval.audit_trail.length > 0 && (
                      <>
                        <Separator className="my-3" />
                        <div className="space-y-2">
                          <div className="text-xs font-medium text-slate-600 flex items-center gap-1">
                            <History className="h-3 w-3" />
                            Audit Trail
                          </div>
                          <div className="space-y-1">
                            {approval.audit_trail.map((log: ApprovalAuditLog) => (
                              <div key={log.id} className="flex items-start gap-2 text-xs text-slate-600 p-2 bg-slate-50 rounded">
                                {getActionIcon(log.action)}
                                <div className="flex-1">
                                  <span className="font-medium capitalize">{log.action}</span>
                                  {log.performed_by_user && (
                                    <span> by {log.performed_by_user.name}</span>
                                  )}
                                  {log.details && (
                                    <span className="text-slate-500"> - {log.details}</span>
                                  )}
                                </div>
                                <span className="text-slate-400">
                                  {format(new Date(log.timestamp), 'MMM d, h:mm a')}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
