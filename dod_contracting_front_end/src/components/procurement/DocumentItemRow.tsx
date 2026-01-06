import { CheckCircle2, Circle, FileText, AlertCircle, XCircle, Clock, Calendar, User, ChevronRight, Sparkles, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { format, isPast } from 'date-fns';
import { ProjectDocument } from '@/hooks/useProjectDocuments';

interface DocumentItemRowProps {
  document: ProjectDocument;
  onSelect: (document: ProjectDocument) => void;
  canEdit?: boolean;
  onQuickGenerate?: (document: ProjectDocument) => void;
}

export function DocumentItemRow({ document, onSelect, canEdit, onQuickGenerate }: DocumentItemRowProps) {
  const getStatusIcon = () => {
    switch (document.status) {
      case 'approved':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'uploaded':
        return <FileText className="h-5 w-5 text-blue-600" />;
      case 'under_review':
        return <Clock className="h-5 w-5 text-amber-600" />;
      case 'rejected':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'expired':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Circle className="h-5 w-5 text-slate-400" />;
    }
  };

  const getStatusColor = () => {
    switch (document.status) {
      case 'approved':
        return 'bg-green-50 border-green-200 hover:border-green-300';
      case 'uploaded':
        return 'bg-blue-50 border-blue-200 hover:border-blue-300';
      case 'under_review':
        return 'bg-amber-50 border-amber-200 hover:border-amber-300';
      case 'rejected':
        return 'bg-red-50 border-red-200 hover:border-red-300';
      case 'expired':
        return 'bg-red-50 border-red-200 hover:border-red-300';
      default:
        return 'bg-white border-slate-200 hover:border-blue-300';
    }
  };

  const getStatusBadge = () => {
    const statusConfig = {
      approved: { label: 'Approved', className: 'bg-green-100 text-green-800 border-green-200' },
      uploaded: { label: 'Uploaded', className: 'bg-blue-100 text-blue-800 border-blue-200' },
      under_review: { label: 'Under Review', className: 'bg-amber-100 text-amber-800 border-amber-200' },
      rejected: { label: 'Rejected', className: 'bg-red-100 text-red-800 border-red-200' },
      expired: { label: 'Expired', className: 'bg-red-100 text-red-800 border-red-200' },
      pending: { label: 'Pending', className: 'bg-slate-100 text-slate-800 border-slate-200' },
    };

    const config = statusConfig[document.status];
    return (
      <Badge variant="outline" className={config.className}>
        {config.label}
      </Badge>
    );
  };

  const isOverdue = document.deadline && isPast(new Date(document.deadline)) && document.status === 'pending';
  const isExpiringSoon = document.expiration_date && !isPast(new Date(document.expiration_date)) &&
    new Date(document.expiration_date).getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000;

  // Check if document can be quick-generated
  const isGenerating = document.generation_status === 'generating';
  const hasGeneratedContent = document.generation_status === 'generated';
  const canQuickGenerate = canEdit && document.status === 'pending' && !isGenerating && onQuickGenerate;

  const handleQuickGenerate = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click
    if (onQuickGenerate) {
      onQuickGenerate(document);
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-4 p-4 rounded-lg border-2 transition-all cursor-pointer group',
        getStatusColor()
      )}
      onClick={() => onSelect(document)}
    >
      <div className="flex-shrink-0">
        {getStatusIcon()}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-semibold text-slate-900">
                {document.document_name}
                {document.is_required && (
                  <span className="text-red-600 ml-1">*</span>
                )}
              </h4>
              {document.requires_approval && (
                <Badge variant="outline" className="text-xs">Requires Approval</Badge>
              )}
              {document.pending_approvals && document.pending_approvals > 0 && (
                <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                  {document.pending_approvals} Pending Approval{document.pending_approvals > 1 ? 's' : ''}
                </Badge>
              )}
            </div>
            {document.description && (
              <p className="text-sm text-slate-600 line-clamp-1">{document.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {getStatusBadge()}
            <Badge variant="outline" className="text-xs">{document.category}</Badge>
          </div>
        </div>

        <div className="flex items-center gap-4 mt-2 text-xs">
          {document.phase && (
            <div className="flex items-center gap-1 text-slate-600">
              <FileText className="h-3 w-3" />
              <span className="capitalize">{document.phase.replace('_', ' ')}</span>
            </div>
          )}

          {document.assigned_user && (
            <div className="flex items-center gap-1 text-slate-600">
              <User className="h-3 w-3" />
              <span>{document.assigned_user.name}</span>
            </div>
          )}

          {document.deadline && (
            <div className={cn(
              'flex items-center gap-1',
              isOverdue ? 'text-red-600 font-medium' : 'text-slate-600'
            )}>
              <Calendar className="h-3 w-3" />
              <span>Due {format(new Date(document.deadline), 'MMM d, yyyy')}</span>
              {isOverdue && <span className="font-semibold">(Overdue)</span>}
            </div>
          )}

          {document.expiration_date && document.status === 'approved' && (
            <div className={cn(
              'flex items-center gap-1',
              isExpiringSoon ? 'text-amber-600 font-medium' : 'text-slate-600'
            )}>
              <AlertCircle className="h-3 w-3" />
              <span>Expires {format(new Date(document.expiration_date), 'MMM d, yyyy')}</span>
            </div>
          )}

          {document.latest_upload && (
            <div className="flex items-center gap-1 text-green-600">
              <CheckCircle2 className="h-3 w-3" />
              <span>Uploaded by {document.latest_upload.uploader?.name || 'Unknown'}</span>
            </div>
          )}

          {/* AI Generation Status */}
          {isGenerating && (
            <div className="flex items-center gap-1 text-blue-600">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Generating...</span>
            </div>
          )}
          {hasGeneratedContent && !isGenerating && (
            <div className="flex items-center gap-1 text-purple-600">
              <Sparkles className="h-3 w-3" />
              <span>AI Generated</span>
              {document.ai_quality_score && (
                <span className="text-purple-500">({document.ai_quality_score}%)</span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Quick Generate Button */}
        {canQuickGenerate && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleQuickGenerate}
            className="opacity-0 group-hover:opacity-100 transition-opacity gap-1 text-purple-600 border-purple-200 hover:bg-purple-50"
          >
            <Sparkles className="h-3 w-3" />
            Generate
          </Button>
        )}
        
        {/* Generating Indicator */}
        {isGenerating && (
          <Badge variant="outline" className="animate-pulse bg-blue-50 text-blue-700 border-blue-200">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Generating...
          </Badge>
        )}

        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
        <Button size="sm" variant="ghost">
          <ChevronRight className="h-4 w-4" />
        </Button>
        </div>
      </div>
    </div>
  );
}
