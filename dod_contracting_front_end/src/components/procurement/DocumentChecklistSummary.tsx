import { useEffect, useState } from 'react';
import { CheckCircle2, FileText, Clock, AlertCircle } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useProjectDocuments } from '@/hooks/useProjectDocuments';

interface DocumentChecklistSummaryProps {
  projectId: string;
  compact?: boolean;
}

export function DocumentChecklistSummary({ projectId, compact = false }: DocumentChecklistSummaryProps) {
  const { documents, loading, getDocumentStats } = useProjectDocuments(projectId);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    completionPercentage: 0,
    underReview: 0,
    required: 0,
    requiredComplete: 0,
  });

  useEffect(() => {
    if (!loading) {
      setStats(getDocumentStats());
    }
  }, [documents, loading]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
        <div className="h-2 bg-slate-200 rounded w-full"></div>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-600">Documents</span>
          <span className="font-semibold text-slate-900">{stats.completionPercentage}%</span>
        </div>
        <Progress value={stats.completionPercentage} className="h-1.5" />
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-green-600" />
            <span className="text-slate-600">{stats.approved}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-amber-600" />
            <span className="text-slate-600">{stats.pending}</span>
          </div>
          {stats.underReview > 0 && (
            <div className="flex items-center gap-1">
              <AlertCircle className="h-3 w-3 text-blue-600" />
              <span className="text-slate-600">{stats.underReview}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-slate-900 flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Document Checklist
        </h4>
        <Badge variant="outline" className={cn(
          stats.completionPercentage === 100 ? 'bg-green-100 text-green-800 border-green-200' :
          stats.completionPercentage >= 50 ? 'bg-blue-100 text-blue-800 border-blue-200' :
          'bg-amber-100 text-amber-800 border-amber-200'
        )}>
          {stats.completionPercentage}% Complete
        </Badge>
      </div>

      <Progress value={stats.completionPercentage} className="h-2" />

      <div className="grid grid-cols-3 gap-2 text-sm">
        <div className="text-center p-2 bg-green-50 rounded-lg">
          <div className="flex items-center justify-center gap-1 mb-1">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </div>
          <div className="font-semibold text-green-900">{stats.approved}</div>
          <div className="text-xs text-green-700">Approved</div>
        </div>

        <div className="text-center p-2 bg-amber-50 rounded-lg">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Clock className="h-4 w-4 text-amber-600" />
          </div>
          <div className="font-semibold text-amber-900">{stats.pending}</div>
          <div className="text-xs text-amber-700">Pending</div>
        </div>

        <div className="text-center p-2 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-center gap-1 mb-1">
            <AlertCircle className="h-4 w-4 text-blue-600" />
          </div>
          <div className="font-semibold text-blue-900">{stats.underReview}</div>
          <div className="text-xs text-blue-700">Review</div>
        </div>
      </div>

      <div className="text-xs text-slate-600 pt-2 border-t">
        {stats.requiredComplete} of {stats.required} required documents approved
      </div>
    </div>
  );
}
