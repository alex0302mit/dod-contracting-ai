/**
 * GenerationTimeline Component
 * 
 * Timeline view showing chronological generation history for AI documents.
 * Displays entries for initial generation and any re-generations with
 * visual connector lines and expandable content previews.
 * 
 * Features:
 * - Chronological entries sorted by generation date
 * - Visual connector lines between entries
 * - Badges for document phase and quality score
 * - Quick action buttons (Open in Editor)
 * - Expandable content preview
 * 
 * Dependencies:
 * - Uses EditorNavigationContext for "Open in Editor" functionality
 * - Uses date-fns for date formatting
 */

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { toast } from 'sonner';
import { format, formatDistanceToNow } from 'date-fns';
import {
  Sparkles,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { ProjectDocument } from '@/hooks/useProjectDocuments';
import { useEditorNavigation } from '@/contexts/EditorNavigationContext';

interface GenerationTimelineProps {
  documents: ProjectDocument[];
  onUpdate: () => void;
}

// Timeline entry type
interface TimelineEntry {
  id: string;
  document: ProjectDocument;
  date: Date;
  isRegeneration: boolean;
}

export function GenerationTimeline({ documents, onUpdate }: GenerationTimelineProps) {
  const { navigateToEditor } = useEditorNavigation();
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // Sort documents by generation date (newest first)
  const sortedDocs = [...documents]
    .filter(doc => doc.generated_at)
    .sort((a, b) => new Date(b.generated_at!).getTime() - new Date(a.generated_at!).getTime());

  // Create timeline entries
  const timelineEntries: TimelineEntry[] = sortedDocs.map(doc => ({
    id: doc.id,
    document: doc,
    date: new Date(doc.generated_at!),
    // For now, we mark as regeneration if updated_at is significantly different from created_at
    // In a full implementation, we'd track generation history in a separate table
    isRegeneration: doc.updated_at && doc.created_at 
      ? new Date(doc.updated_at).getTime() > new Date(doc.created_at).getTime() + 60000
      : false,
  }));

  // Toggle entry expansion
  const toggleExpanded = (id: string) => {
    setExpandedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Handle opening in editor
  const handleOpenInEditor = (document: ProjectDocument) => {
    if (document.generated_content) {
      navigateToEditor(document.generated_content, document.document_name);
      toast.success(`Opened "${document.document_name}" in editor`);
    }
  };

  // Get phase badge color
  const getPhaseBadgeColor = (phase: string | null) => {
    switch (phase) {
      case 'pre_solicitation':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'solicitation':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'post_solicitation':
        return 'bg-green-100 text-green-700 border-green-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  // Format phase name
  const formatPhaseName = (phase: string | null) => {
    if (!phase) return 'General';
    return phase.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  // Get quality score badge
  const getQualityBadge = (score: number | null | undefined) => {
    if (!score) return null;
    
    let colorClass = 'bg-slate-100 text-slate-700';
    if (score >= 80) colorClass = 'bg-green-100 text-green-700';
    else if (score >= 60) colorClass = 'bg-amber-100 text-amber-700';
    else colorClass = 'bg-red-100 text-red-700';
    
    return (
      <Badge variant="outline" className={`${colorClass} border-0`}>
        Quality: {score}%
      </Badge>
    );
  };

  if (timelineEntries.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-12 text-center">
          <Clock className="h-12 w-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No Generation History</h3>
          <p className="text-slate-600">
            Generated documents will appear here in chronological order.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="relative">
      {/* Timeline vertical line */}
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200" />

      {/* Timeline entries */}
      <div className="space-y-4">
        {timelineEntries.map((entry, index) => {
          const isExpanded = expandedIds.has(entry.id);
          const contentPreview = entry.document.generated_content?.substring(0, 300) || '';
          
          return (
            <div key={entry.id} className="relative pl-14">
              {/* Timeline node */}
              <div className="absolute left-4 w-4 h-4 rounded-full border-2 border-white shadow-sm bg-purple-500 flex items-center justify-center">
                {entry.isRegeneration ? (
                  <RefreshCw className="h-2 w-2 text-white" />
                ) : (
                  <Sparkles className="h-2 w-2 text-white" />
                )}
              </div>

              <Collapsible open={isExpanded} onOpenChange={() => toggleExpanded(entry.id)}>
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="py-4">
                    {/* Header row */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-slate-900 truncate">
                            {entry.document.document_name}
                          </h4>
                          {entry.isRegeneration && (
                            <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                              Re-generated
                            </Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <span>{format(entry.date, 'MMM d, yyyy h:mm a')}</span>
                          <span className="text-slate-400">•</span>
                          <span>{formatDistanceToNow(entry.date, { addSuffix: true })}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Badge variant="outline" className={`text-xs ${getPhaseBadgeColor(entry.document.phase)}`}>
                          {formatPhaseName(entry.document.phase)}
                        </Badge>
                        {getQualityBadge(entry.document.ai_quality_score)}
                      </div>
                    </div>

                    {/* Actions row */}
                    <div className="flex items-center justify-between mt-3 pt-3 border-t">
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" size="sm" className="gap-1 text-slate-600">
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-4 w-4" />
                              Hide Preview
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-4 w-4" />
                              Show Preview
                            </>
                          )}
                        </Button>
                      </CollapsibleTrigger>

                      <Button
                        size="sm"
                        onClick={() => handleOpenInEditor(entry.document)}
                        className="gap-1"
                        disabled={!entry.document.generated_content}
                      >
                        <ExternalLink className="h-3 w-3" />
                        Open in Editor
                      </Button>
                    </div>

                    {/* Expandable content preview */}
                    <CollapsibleContent>
                      <div className="mt-4 pt-4 border-t">
                        <div className="bg-slate-50 rounded-lg p-4">
                          <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
                            {contentPreview}
                            {(entry.document.generated_content?.length || 0) > 300 && (
                              <span className="text-slate-400">...</span>
                            )}
                          </pre>
                        </div>
                      </div>
                    </CollapsibleContent>
                  </CardContent>
                </Card>
              </Collapsible>
            </div>
          );
        })}
      </div>
    </div>
  );
}
