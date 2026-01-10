import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import {
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  AlertCircle,
  Search,
  Loader2,
  Building2,
  ArrowRight,
  Shield,
  User,
} from 'lucide-react';
import { format } from 'date-fns';
import { approvalsApi, phaseTransitionsApi, type PhaseTransitionRequest } from '@/services/api';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Phase display name mapping
const phaseDisplayNames: Record<string, string> = {
  pre_solicitation: 'Pre-Solicitation',
  solicitation: 'Solicitation',
  post_solicitation: 'Post-Solicitation',
  award: 'Award',
};

export function PendingApprovalsView() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterProject, setFilterProject] = useState<string>('all');
  const [selectedApproval, setSelectedApproval] = useState<string | null>(null);
  const [selectedTransition, setSelectedTransition] = useState<string | null>(null);
  const [comments, setComments] = useState<{ [key: string]: string }>({});
  const [transitionComments, setTransitionComments] = useState<{ [key: string]: string }>({});
  const [actionLoading, setActionLoading] = useState<{ [key: string]: boolean }>({});
  const [activeTab, setActiveTab] = useState('documents');

  // Fetch pending document approvals
  const {
    data: approvalsData,
    isLoading: approvalsLoading,
    refetch: refetchApprovals
  } = useQuery({
    queryKey: ['pendingApprovals'],
    queryFn: () => approvalsApi.getPendingApprovals(),
  });

  // Fetch pending phase transitions
  const {
    data: transitionsData,
    isLoading: transitionsLoading,
    refetch: refetchTransitions
  } = useQuery({
    queryKey: ['pendingTransitions'],
    queryFn: () => phaseTransitionsApi.getPendingTransitions(),
  });

  const approvals = approvalsData?.approvals || [];
  const totalCount = approvalsData?.count || 0;
  
  const transitions = transitionsData?.pending_transitions || [];
  const transitionsCount = transitionsData?.count || 0;
  
  const isLoading = approvalsLoading || transitionsLoading;

  // Refetch all data
  const refetch = () => {
    refetchApprovals();
    refetchTransitions();
  };

  // Get unique projects for filtering
  const projects = Array.from(
    new Set(approvals.map(a => a.project?.name).filter(Boolean))
  );

  // Filter approvals
  const filteredApprovals = approvals.filter(approval => {
    const matchesSearch =
      approval.document?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      approval.project?.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesProject =
      filterProject === 'all' ||
      approval.project?.name === filterProject;
    return matchesSearch && matchesProject;
  });

  const handleApprove = async (approvalId: string) => {
    setActionLoading({ [approvalId]: true });
    try {
      const response = await approvalsApi.approve(
        approvalId,
        comments[approvalId] || undefined
      );
      toast.success(response.message);
      setComments(prev => ({ ...prev, [approvalId]: '' }));
      setSelectedApproval(null);
      refetch();
    } catch (error) {
      console.error('Error approving document:', error);
      toast.error('Failed to approve document');
    } finally {
      setActionLoading({});
    }
  };

  const handleReject = async (approvalId: string) => {
    const comment = comments[approvalId];
    if (!comment?.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }

    setActionLoading({ [approvalId]: true });
    try {
      const response = await approvalsApi.reject(approvalId, comment);
      toast.error(response.message);
      setComments(prev => ({ ...prev, [approvalId]: '' }));
      setSelectedApproval(null);
      refetch();
    } catch (error) {
      console.error('Error rejecting document:', error);
      toast.error('Failed to reject document');
    } finally {
      setActionLoading({});
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <Badge className="bg-blue-100 text-blue-800">Uploaded</Badge>;
      case 'under_review':
        return <Badge className="bg-amber-100 text-amber-800">Under Review</Badge>;
      case 'pending':
        return <Badge className="bg-slate-100 text-slate-800">Pending</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Handle phase transition approval
  const handleApproveTransition = async (transitionId: string) => {
    setActionLoading({ [transitionId]: true });
    try {
      const response = await phaseTransitionsApi.approveTransition(
        transitionId,
        transitionComments[transitionId] || undefined
      );
      toast.success(response.message);
      setTransitionComments(prev => ({ ...prev, [transitionId]: '' }));
      setSelectedTransition(null);
      refetch();
    } catch (error) {
      console.error('Error approving transition:', error);
      toast.error('Failed to approve phase transition');
    } finally {
      setActionLoading({});
    }
  };

  // Handle phase transition rejection
  const handleRejectTransition = async (transitionId: string) => {
    const comment = transitionComments[transitionId];
    if (!comment?.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }

    setActionLoading({ [transitionId]: true });
    try {
      const response = await phaseTransitionsApi.rejectTransition(transitionId, comment);
      toast.success(response.message);
      setTransitionComments(prev => ({ ...prev, [transitionId]: '' }));
      setSelectedTransition(null);
      refetch();
    } catch (error) {
      console.error('Error rejecting transition:', error);
      toast.error('Failed to reject phase transition');
    } finally {
      setActionLoading({});
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading pending approvals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Pending Approvals</h1>
          <p className="text-slate-600 mt-1">
            Documents and phase transitions awaiting your approval
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{totalCount}</div>
            <div className="text-xs text-slate-600">Documents</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{transitionsCount}</div>
            <div className="text-xs text-slate-600">Transitions</div>
          </div>
        </div>
      </div>

      {/* Tabs for Documents and Phase Transitions */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="documents" className="gap-2">
            <FileText className="h-4 w-4" />
            Document Approvals
            {totalCount > 0 && (
              <Badge className="ml-1 bg-blue-100 text-blue-800">{totalCount}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="transitions" className="gap-2">
            <Shield className="h-4 w-4" />
            Phase Transitions
            {transitionsCount > 0 && (
              <Badge className="ml-1 bg-purple-100 text-purple-800">{transitionsCount}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Document Approvals Tab */}
        <TabsContent value="documents">
      {/* Filters */}
          <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search documents or projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Filter by project" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
                {projects.map((project) => (
                  <SelectItem key={project} value={project || ''}>
                    {project}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

          {/* No Results for Documents */}
      {filteredApprovals.length === 0 && !isLoading && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-slate-900 mb-2">
                All Caught Up!
              </h2>
              <p className="text-slate-600 max-w-md mx-auto">
                {searchQuery || filterProject !== 'all'
                      ? 'No pending document approvals match your filters'
                      : 'You have no pending document approvals at this time'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

          {/* Document Approvals List */}
      <div className="grid gap-4">
        {filteredApprovals.map((approval) => {
          const isExpanded = selectedApproval === approval.id;
              const loading = actionLoading[approval.id];

          return (
            <Card
              key={approval.id}
              className={`border-l-4 transition-all ${
                isExpanded
                  ? 'border-l-blue-500 shadow-lg'
                  : 'border-l-amber-400 hover:shadow-md'
              }`}
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-5 w-5 text-slate-600" />
                      <CardTitle className="text-lg">
                        {approval.document?.name || 'Unknown Document'}
                      </CardTitle>
                      {getStatusBadge(approval.document?.status || '')}
                    </div>

                    {approval.document?.description && (
                      <p className="text-sm text-slate-600 mb-3">
                        {approval.document.description}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
                      {approval.project && (
                        <div className="flex items-center gap-1">
                          <Building2 className="h-4 w-4" />
                          <span>{approval.project.name}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        <span>Requested {format(new Date(approval.requested_at), 'MMM d, yyyy')}</span>
                      </div>
                      {approval.document?.category && (
                        <Badge variant="outline" className="text-xs">
                          {approval.document.category}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <Button
                    variant={isExpanded ? "secondary" : "default"}
                    onClick={() => setSelectedApproval(isExpanded ? null : approval.id)}
                  >
                    {isExpanded ? 'Collapse' : 'Review'}
                  </Button>
                </div>
              </CardHeader>

              {isExpanded && (
                <>
                  <Separator />
                  <CardContent className="pt-6 space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                        <div>
                          <p className="font-medium text-blue-900 mb-1">
                            Action Required
                          </p>
                          <p className="text-sm text-blue-800">
                            Please review this document and provide your approval or rejection with feedback.
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor={`comments-${approval.id}`}>
                        Comments
                        <span className="text-xs text-slate-500 ml-2">
                          (Optional for approval, required for rejection)
                        </span>
                      </Label>
                      <Textarea
                        id={`comments-${approval.id}`}
                        value={comments[approval.id] || ''}
                        onChange={(e) => setComments(prev => ({
                          ...prev,
                          [approval.id]: e.target.value
                        }))}
                        placeholder="Add your feedback or comments..."
                        rows={4}
                        className="resize-none"
                      />
                    </div>

                    <div className="flex gap-3 pt-2">
                      <Button
                        onClick={() => handleApprove(approval.id)}
                            disabled={loading}
                        className="flex-1 gap-2 bg-green-600 hover:bg-green-700"
                        size="lg"
                      >
                            {loading ? (
                          <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-5 w-5" />
                        )}
                        Approve Document
                      </Button>
                      <Button
                        onClick={() => handleReject(approval.id)}
                            disabled={loading}
                        variant="destructive"
                        className="flex-1 gap-2"
                        size="lg"
                      >
                            {loading ? (
                          <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                          <XCircle className="h-5 w-5" />
                        )}
                        Reject Document
                      </Button>
                    </div>
                  </CardContent>
                </>
              )}
            </Card>
          );
        })}
      </div>
        </TabsContent>

        {/* Phase Transitions Tab */}
        <TabsContent value="transitions">
          {/* No Results for Transitions */}
          {transitions.length === 0 && !isLoading && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto mb-4" />
                  <h2 className="text-2xl font-semibold text-slate-900 mb-2">
                    No Pending Transitions
                  </h2>
                  <p className="text-slate-600 max-w-md mx-auto">
                    There are no phase transition requests awaiting your approval.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Phase Transitions List */}
          <div className="grid gap-4">
            {transitions.map((transition: PhaseTransitionRequest) => {
              const isExpanded = selectedTransition === transition.id;
              const loading = actionLoading[transition.id];

              return (
                <Card
                  key={transition.id}
                  className={`border-l-4 transition-all ${
                    isExpanded
                      ? 'border-l-purple-500 shadow-lg'
                      : 'border-l-purple-400 hover:shadow-md'
                  }`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Shield className="h-5 w-5 text-purple-600" />
                          <CardTitle className="text-lg">
                            Phase Transition Request
                          </CardTitle>
                          <Badge className="bg-purple-100 text-purple-800">
                            Pending
                          </Badge>
                        </div>

                        {/* Phase transition details */}
                        <div className="bg-slate-50 rounded-lg p-3 mb-3">
                          <div className="flex items-center gap-3">
                            <Badge variant="outline" className="text-sm">
                              {phaseDisplayNames[transition.from_phase] || transition.from_phase}
                            </Badge>
                            <ArrowRight className="h-4 w-4 text-slate-400" />
                            <Badge className="bg-purple-100 text-purple-800 text-sm">
                              {phaseDisplayNames[transition.to_phase] || transition.to_phase}
                            </Badge>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
                          {transition.project && (
                            <div className="flex items-center gap-1">
                              <Building2 className="h-4 w-4" />
                              <span>{transition.project.name}</span>
                            </div>
                          )}
                          {transition.requester && (
                            <div className="flex items-center gap-1">
                              <User className="h-4 w-4" />
                              <span>Requested by {transition.requester.name}</span>
                            </div>
                          )}
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            <span>
                              {format(new Date(transition.requested_at), 'MMM d, yyyy')}
                            </span>
                          </div>
                        </div>
                      </div>

                      <Button
                        variant={isExpanded ? "secondary" : "default"}
                        onClick={() => setSelectedTransition(isExpanded ? null : transition.id)}
                      >
                        {isExpanded ? 'Collapse' : 'Review'}
                      </Button>
                    </div>
                  </CardHeader>

                  {isExpanded && (
                    <>
                      <Separator />
                      <CardContent className="pt-6 space-y-4">
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="h-5 w-5 text-purple-600 mt-0.5" />
                            <div>
                              <p className="font-medium text-purple-900 mb-1">
                                Gatekeeper Approval Required
                              </p>
                              <p className="text-sm text-purple-800">
                                This project is requesting to transition to the next procurement phase.
                                Please review the validation results and approve or reject this request.
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Validation Results Summary */}
                        {transition.validation_results && (
                          <div className="space-y-3">
                            <h4 className="font-medium text-slate-900">Validation Results</h4>
                            
                            {/* Warnings */}
                            {transition.validation_results.warnings && 
                             transition.validation_results.warnings.length > 0 && (
                              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                                <h5 className="text-sm font-medium text-amber-800 mb-1">Warnings</h5>
                                <ul className="text-sm text-amber-700 space-y-1">
                                  {transition.validation_results.warnings.map((w: string, i: number) => (
                                    <li key={i}>• {w}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {/* Document Status */}
                            {transition.validation_results.document_status && (
                              <div className="border rounded-lg p-3">
                                <h5 className="text-sm font-medium text-slate-800 mb-2">
                                  Document Status
                                </h5>
                                <div className="space-y-1">
                                  {Object.entries(transition.validation_results.document_status).map(
                                    ([docName, status]: [string, any]) => (
                                      <div key={docName} className="flex items-center justify-between text-sm">
                                        <span className="text-slate-600">{docName}</span>
                                        {status.approved ? (
                                          <Badge className="bg-green-100 text-green-800 gap-1">
                                            <CheckCircle2 className="h-3 w-3" /> Approved
                                          </Badge>
                                        ) : status.exists ? (
                                          <Badge variant="outline" className="text-amber-700">
                                            {status.status || 'Pending'}
                                          </Badge>
                                        ) : (
                                          <Badge variant="destructive" className="gap-1">
                                            <XCircle className="h-3 w-3" /> Missing
                                          </Badge>
                                        )}
                                      </div>
                                    )
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        <div className="space-y-2">
                          <Label htmlFor={`transition-comments-${transition.id}`}>
                            Comments
                            <span className="text-xs text-slate-500 ml-2">
                              (Optional for approval, required for rejection)
                            </span>
                          </Label>
                          <Textarea
                            id={`transition-comments-${transition.id}`}
                            value={transitionComments[transition.id] || ''}
                            onChange={(e) => setTransitionComments(prev => ({
                              ...prev,
                              [transition.id]: e.target.value
                            }))}
                            placeholder="Add your feedback or comments..."
                            rows={4}
                            className="resize-none"
                          />
                        </div>

                        <div className="flex gap-3 pt-2">
                          <Button
                            onClick={() => handleApproveTransition(transition.id)}
                            disabled={loading}
                            className="flex-1 gap-2 bg-green-600 hover:bg-green-700"
                            size="lg"
                          >
                            {loading ? (
                              <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                              <CheckCircle2 className="h-5 w-5" />
                            )}
                            Approve Transition
                          </Button>
                          <Button
                            onClick={() => handleRejectTransition(transition.id)}
                            disabled={loading}
                            variant="destructive"
                            className="flex-1 gap-2"
                            size="lg"
                          >
                            {loading ? (
                              <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                              <XCircle className="h-5 w-5" />
                            )}
                            Reject Transition
                          </Button>
                        </div>
                      </CardContent>
                    </>
                  )}
                </Card>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
