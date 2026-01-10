import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { Calendar, User, FileText, Download, Upload, CheckCircle2, Clock, History, UserCheck, Sparkles, GitBranch } from 'lucide-react';
import { ProjectDocument } from '@/hooks/useProjectDocuments';
import { useDocumentUploads, DocumentUpload } from '@/hooks/useDocumentUploads';
import { projectsApi, approvalsApi, type Approval } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
// useEditorNavigation hook for navigating to the Live Editor with content
import { useEditorNavigation } from '@/contexts/EditorNavigationContext';
import { DocumentUploadDialog } from './DocumentUploadDialog';
import { ApprovalRequestDialog } from './ApprovalRequestDialog';
import { ApprovalActionsCard } from './ApprovalActionsCard';
import { ApprovalHistoryView } from './ApprovalHistoryView';
import { DocumentGenerateTab } from './DocumentGenerateTab';
// DocumentLineagePanel for showing source documents that influenced AI generation
import { DocumentLineagePanel } from '@/components/documents/DocumentLineagePanel';

interface DocumentDetailDialogProps {
  document: ProjectDocument;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate: () => void;
  canEdit: boolean;
}

export function DocumentDetailDialog({
  document,
  open,
  onOpenChange,
  onUpdate,
  canEdit,
}: DocumentDetailDialogProps) {
  const { user } = useAuth();
  const { downloadDocument, getUploadHistory } = useDocumentUploads();
  // Get the navigateToEditor function from context to open content in the Live Editor
  const { navigateToEditor } = useEditorNavigation();
  const [notes, setNotes] = useState(document.notes || '');
  const [deadline, setDeadline] = useState(document.deadline || '');
  const [expirationDate, setExpirationDate] = useState(document.expiration_date || '');
  const [status, setStatus] = useState(document.status);
  const [loading, setLoading] = useState(false);
  const [uploadHistory, setUploadHistory] = useState<DocumentUpload[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showApprovalRequestDialog, setShowApprovalRequestDialog] = useState(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);

  useEffect(() => {
    if (open) {
      fetchUploadHistory();
      fetchApprovals();
      setNotes(document.notes || '');
      setDeadline(document.deadline || '');
      setExpirationDate(document.expiration_date || '');
      setStatus(document.status);
    }
  }, [open, document]);

  const fetchUploadHistory = async () => {
    try {
      const history = await getUploadHistory(document.id);
      setUploadHistory(history);
    } catch (error) {
      console.error('Error fetching upload history:', error);
    }
  };

  const fetchApprovals = async () => {
    try {
      const response = await approvalsApi.getDocumentApprovals(document.id);
      setApprovals(response.approvals);
    } catch (error) {
      console.error('Error fetching approvals:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await projectsApi.updateDocument(document.id, {
        notes,
        deadline: deadline || undefined,
        expiration_date: expirationDate || undefined,
        status,
      });

      toast.success('Document updated successfully');
      onUpdate();
      onOpenChange(false);
    } catch (error) {
      console.error('Error updating document:', error);
      toast.error('Failed to update document');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (upload: DocumentUpload) => {
    try {
      await downloadDocument(upload.file_path, upload.file_name);
    } catch (error) {
      toast.error('Failed to download document');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800 border-green-200';
      case 'uploaded': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'under_review': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'rejected': return 'bg-red-100 text-red-800 border-red-200';
      case 'expired': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <DialogTitle className="text-xl mb-2">
                  {document.document_name}
                  {document.is_required && <span className="text-red-600 ml-1">*</span>}
                </DialogTitle>
                {document.description && (
                  <p className="text-sm text-slate-600">{document.description}</p>
                )}
              </div>
              <Badge className={getStatusColor(document.status)} variant="outline">
                {document.status.replace('_', ' ')}
              </Badge>
            </div>
          </DialogHeader>

          <Tabs defaultValue="details" className="w-full">
            {/* Show 6 columns if AI-generated, 5 otherwise */}
            <TabsList className={`grid w-full ${document.generation_status === 'generated' ? 'grid-cols-6' : 'grid-cols-5'}`}>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="generate" className="gap-1">
                <Sparkles className="h-3 w-3" />
                Generate
              </TabsTrigger>
              <TabsTrigger value="files">Files ({uploadHistory.length})</TabsTrigger>
              <TabsTrigger value="approvals">
                Approvals ({approvals.filter(a => a.approval_status === 'pending').length})
              </TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
              {/* Lineage tab - only shows for AI-generated documents */}
              {document.generation_status === 'generated' && (
                <TabsTrigger value="lineage" className="gap-1">
                  <GitBranch className="h-3 w-3" />
                  Sources
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="details" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-4 w-4 text-slate-400" />
                      <Label className="text-sm font-medium">Category</Label>
                    </div>
                    <p className="text-sm">{document.category}</p>
                  </CardContent>
                </Card>

                {document.phase && (
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="h-4 w-4 text-slate-400" />
                        <Label className="text-sm font-medium">Phase</Label>
                      </div>
                      <p className="text-sm capitalize">{document.phase.replace('_', ' ')}</p>
                    </CardContent>
                  </Card>
                )}

                {document.assigned_user && (
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2 mb-2">
                        <User className="h-4 w-4 text-slate-400" />
                        <Label className="text-sm font-medium">Assigned To</Label>
                      </div>
                      <p className="text-sm">{document.assigned_user.name}</p>
                      <p className="text-xs text-slate-500">{document.assigned_user.email}</p>
                    </CardContent>
                  </Card>
                )}

                {document.requires_approval && (
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle2 className="h-4 w-4 text-slate-400" />
                        <Label className="text-sm font-medium">Approval Status</Label>
                      </div>
                      <p className="text-sm">
                        {document.pending_approvals && document.pending_approvals > 0
                          ? `${document.pending_approvals} pending approval(s)`
                          : 'No pending approvals'}
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>

              {canEdit ? (
                <div className="space-y-4 pt-4 border-t">
                  <div className="space-y-2">
                    <Label htmlFor="status">Status</Label>
                    <Select value={status} onValueChange={(value: any) => setStatus(value)}>
                      <SelectTrigger id="status">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="uploaded">Uploaded</SelectItem>
                        <SelectItem value="under_review">Under Review</SelectItem>
                        <SelectItem value="approved">Approved</SelectItem>
                        <SelectItem value="rejected">Rejected</SelectItem>
                        <SelectItem value="expired">Expired</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
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
                      <Label htmlFor="expiration_date">Expiration Date</Label>
                      <Input
                        id="expiration_date"
                        type="date"
                        value={expirationDate}
                        onChange={(e) => setExpirationDate(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="notes">Notes</Label>
                    <Textarea
                      id="notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add notes about this document..."
                      rows={4}
                    />
                  </div>
                </div>
              ) : (
                document.notes && (
                  <div className="space-y-2 pt-4 border-t">
                    <Label>Notes</Label>
                    <div className="p-3 bg-slate-50 rounded-lg text-sm text-slate-700">
                      {document.notes}
                    </div>
                  </div>
                )
              )}
            </TabsContent>

            <TabsContent value="generate" className="space-y-4 mt-4">
              <DocumentGenerateTab
                document={document}
                projectId={document.project_id}
                onGenerated={(content, openInEditor) => {
                  if (openInEditor && content) {
                    // Navigate to the Live Editor with the generated content
                    navigateToEditor(content, document.document_name);
                    // Close the dialog
                    onOpenChange(false);
                  }
                  onUpdate();
                }}
                onUpdate={onUpdate}
              />
            </TabsContent>

            <TabsContent value="files" className="space-y-4 mt-4">
              {canEdit && (
                <Button onClick={() => setShowUploadDialog(true)} className="w-full gap-2">
                  <Upload className="h-4 w-4" />
                  Upload New Version
                </Button>
              )}

              {uploadHistory.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                  <p className="text-slate-600">No files uploaded yet</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {uploadHistory.map((upload: any) => (
                    <Card key={upload.id}>
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium">{upload.file_name}</h4>
                              {upload.is_current_version && (
                                <Badge variant="outline" className="text-xs">Current</Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-600">
                              <span>Version {upload.version_number}</span>
                              <span>{(upload.file_size / 1024).toFixed(1)} KB</span>
                              <span>Uploaded {format(new Date(upload.upload_date), 'MMM d, yyyy')}</span>
                              {upload.uploader && <span>by {upload.uploader.name}</span>}
                            </div>
                            {upload.notes && (
                              <p className="text-sm text-slate-600 mt-2">{upload.notes}</p>
                            )}
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDownload(upload)}
                            className="gap-2"
                          >
                            <Download className="h-4 w-4" />
                            Download
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="approvals" className="space-y-4 mt-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Approval Workflow</h3>
                  <p className="text-sm text-slate-600">
                    {approvals.length > 0
                      ? `${approvals.filter(a => a.approval_status === 'approved').length} of ${approvals.length} approvers have approved`
                      : 'No approval requests yet'}
                  </p>
                </div>
                <div className="flex gap-2">
                  {approvals.length > 0 && (
                    <Button
                      onClick={() => setShowHistoryDialog(true)}
                      variant="outline"
                      className="gap-2"
                    >
                      <History className="h-4 w-4" />
                      View History
                    </Button>
                  )}
                  {canEdit && (document.status === 'uploaded' || document.status === 'pending') && (
                    <Button
                      onClick={() => setShowApprovalRequestDialog(true)}
                      className="gap-2"
                    >
                      <UserCheck className="h-4 w-4" />
                      Request Approval
                    </Button>
                  )}
                </div>
              </div>

              {approvals.length === 0 ? (
                <div className="text-center py-12">
                  <UserCheck className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900 mb-2">No Approvals Requested</h3>
                  <p className="text-slate-600 mb-4">
                    {canEdit
                      ? 'Request approval from team members to review this document'
                      : 'No approval requests have been made for this document yet'}
                  </p>
                  {canEdit && (document.status === 'uploaded' || document.status === 'pending') && (
                    <Button
                      onClick={() => setShowApprovalRequestDialog(true)}
                      className="gap-2"
                    >
                      <UserCheck className="h-4 w-4" />
                      Request Approval
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  {approvals.map((approval) => (
                    <ApprovalActionsCard
                      key={approval.id}
                      approval={approval}
                      currentUserId={user?.id || ''}
                      onUpdate={() => {
                        fetchApprovals();
                        onUpdate();
                      }}
                    />
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="history" className="space-y-4 mt-4">
              <div className="space-y-2">
                {document.created_at && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <History className="h-4 w-4" />
                  <span>Created {format(new Date(document.created_at), 'MMM d, yyyy h:mm a')}</span>
                </div>
                )}
                {document.updated_at && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Calendar className="h-4 w-4" />
                  <span>Last updated {format(new Date(document.updated_at), 'MMM d, yyyy h:mm a')}</span>
                </div>
                )}
                {!document.created_at && !document.updated_at && (
                  <p className="text-sm text-slate-500">No history available yet</p>
                )}
              </div>
            </TabsContent>

            {/* Lineage Tab - Shows source documents that influenced AI generation */}
            {document.generation_status === 'generated' && (
              <TabsContent value="lineage" className="mt-4">
                <DocumentLineagePanel
                  documentId={document.id}
                  documentName={document.document_name}
                />
              </TabsContent>
            )}
          </Tabs>

          {canEdit && (
            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={loading}>
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>

      <DocumentUploadDialog
        open={showUploadDialog}
        onOpenChange={setShowUploadDialog}
        documentId={document.id}
        documentName={document.document_name}
        onUploadComplete={() => {
          fetchUploadHistory();
          onUpdate();
        }}
      />

      <ApprovalRequestDialog
        open={showApprovalRequestDialog}
        onOpenChange={setShowApprovalRequestDialog}
        documentId={document.id}
        documentName={document.document_name}
        uploadId={document.latest_upload?.id}
        onSuccess={() => {
          fetchApprovals();
          onUpdate();
        }}
      />

      <ApprovalHistoryView
        open={showHistoryDialog}
        onOpenChange={setShowHistoryDialog}
        documentId={document.id}
      />
    </>
  );
}
