/**
 * GeneratedDocumentsGallery Component
 * 
 * Main gallery component for displaying all AI-generated documents for a project.
 * Provides both grid and timeline views with batch export functionality.
 * 
 * Features:
 * - Stats bar with total count, average quality score, last generation time
 * - Grid view (default) - responsive card-based layout
 * - Timeline view - chronological list of generation events
 * - Batch export panel with checkbox selection
 * - Export to PDF, DOCX, or Markdown ZIP
 * 
 * Dependencies:
 * - DocumentPreviewCard for individual document cards
 * - GenerationTimeline for timeline view
 * - documentGenerationApi for batch export
 */

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { format, formatDistanceToNow } from 'date-fns';
import {
  Sparkles,
  Grid3X3,
  Clock,
  Download,
  FileText,
  CheckSquare,
  Square,
  Loader2,
  FileDown,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import { ProjectDocument } from '@/hooks/useProjectDocuments';
import { DocumentPreviewCard } from './DocumentPreviewCard';
import { GenerationTimeline } from './GenerationTimeline';
import { documentGenerationApi } from '@/services/api';

interface GeneratedDocumentsGalleryProps {
  projectId: string;
  documents: ProjectDocument[];
  onUpdate: () => void;
}

// View type for toggling between grid and timeline
type ViewType = 'grid' | 'timeline';

// Export format options
type ExportFormat = 'pdf' | 'docx' | 'markdown';

export function GeneratedDocumentsGallery({
  projectId,
  documents,
  onUpdate,
}: GeneratedDocumentsGalleryProps) {
  // State for view toggle
  const [viewType, setViewType] = useState<ViewType>('grid');
  
  // State for batch selection
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  
  // State for export
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('pdf');

  // Filter to only show generated documents
  const generatedDocs = useMemo(() => {
    return documents.filter(doc => doc.generation_status === 'generated');
  }, [documents]);

  // Calculate stats
  const stats = useMemo(() => {
    const totalGenerated = generatedDocs.length;
    
    // Calculate average quality score (only from docs with scores)
    const docsWithScores = generatedDocs.filter(doc => doc.ai_quality_score != null);
    const avgQuality = docsWithScores.length > 0
      ? Math.round(docsWithScores.reduce((sum, doc) => sum + (doc.ai_quality_score || 0), 0) / docsWithScores.length)
      : null;
    
    // Find most recent generation
    const sortedByDate = [...generatedDocs]
      .filter(doc => doc.generated_at)
      .sort((a, b) => new Date(b.generated_at!).getTime() - new Date(a.generated_at!).getTime());
    
    const lastGenerated = sortedByDate.length > 0 ? sortedByDate[0].generated_at : null;
    
    // Count by phase
    const byPhase = {
      pre_solicitation: generatedDocs.filter(d => d.phase === 'pre_solicitation').length,
      solicitation: generatedDocs.filter(d => d.phase === 'solicitation').length,
      post_solicitation: generatedDocs.filter(d => d.phase === 'post_solicitation').length,
      general: generatedDocs.filter(d => !d.phase).length,
    };

    return { totalGenerated, avgQuality, lastGenerated, byPhase };
  }, [generatedDocs]);

  // Handle individual document selection
  const handleDocSelect = (docId: string, selected: boolean) => {
    setSelectedDocIds(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(docId);
      } else {
        newSet.delete(docId);
      }
      return newSet;
    });
  };

  // Handle select all / deselect all
  const handleSelectAll = () => {
    if (selectedDocIds.size === generatedDocs.length) {
      // Deselect all
      setSelectedDocIds(new Set());
    } else {
      // Select all
      setSelectedDocIds(new Set(generatedDocs.map(d => d.id)));
    }
  };

  // Get quality color for stats display
  const getQualityColor = (score: number | null) => {
    if (!score) return 'text-slate-400';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  // Handle batch export
  const handleBatchExport = async (exportAll: boolean = false) => {
    const docIdsToExport = exportAll 
      ? generatedDocs.map(d => d.id)
      : Array.from(selectedDocIds);

    if (docIdsToExport.length === 0) {
      toast.error('No documents selected for export');
      return;
    }

    setIsExporting(true);

    try {
      // Call the batch export API
      await documentGenerationApi.exportBatch(projectId, docIdsToExport, exportFormat);
      toast.success(`Exported ${docIdsToExport.length} document(s) as ${exportFormat.toUpperCase()}`);
    } catch (error: any) {
      toast.error(`Export failed: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  // Empty state when no generated documents
  if (generatedDocs.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-purple-600" />
              AI Generated Documents
            </h3>
            <p className="text-sm text-slate-600 mt-1">
              View and manage AI-generated content for this project
            </p>
          </div>
        </div>

        <Card className="border-dashed">
          <CardContent className="py-16 text-center">
            <div className="h-16 w-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="h-8 w-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No Generated Documents Yet</h3>
            <p className="text-slate-600 max-w-md mx-auto">
              Use the "Generate with AI" feature in the Document Checklist to create AI-powered content 
              for your procurement documents.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-purple-600" />
            AI Generated Documents
          </h3>
          <p className="text-sm text-slate-600 mt-1">
            View and manage AI-generated content for this project
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-2">
          <Button
            variant={viewType === 'grid' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewType('grid')}
            className="gap-1"
          >
            <Grid3X3 className="h-4 w-4" />
            Grid
          </Button>
          <Button
            variant={viewType === 'timeline' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewType('timeline')}
            className="gap-1"
          >
            <Clock className="h-4 w-4" />
            Timeline
          </Button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Generated Documents</p>
                <p className="text-2xl font-bold text-slate-900">{stats.totalGenerated}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Avg. Quality Score</p>
                <p className={`text-2xl font-bold ${getQualityColor(stats.avgQuality)}`}>
                  {stats.avgQuality ?? '—'}%
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Last Generated</p>
                <p className="text-lg font-semibold text-slate-900">
                  {stats.lastGenerated 
                    ? formatDistanceToNow(new Date(stats.lastGenerated), { addSuffix: true })
                    : '—'
                  }
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Calendar className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">By Phase</p>
                <div className="flex gap-1 mt-1">
                  {stats.byPhase.pre_solicitation > 0 && (
                    <Badge variant="outline" className="text-xs bg-blue-50">
                      Pre: {stats.byPhase.pre_solicitation}
                    </Badge>
                  )}
                  {stats.byPhase.solicitation > 0 && (
                    <Badge variant="outline" className="text-xs bg-purple-50">
                      Sol: {stats.byPhase.solicitation}
                    </Badge>
                  )}
                  {stats.byPhase.post_solicitation > 0 && (
                    <Badge variant="outline" className="text-xs bg-green-50">
                      Post: {stats.byPhase.post_solicitation}
                    </Badge>
                  )}
                </div>
              </div>
              <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Batch Export Panel */}
      <Card className="bg-slate-50">
        <CardContent className="py-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSelectAll}
                className="gap-2"
              >
                {selectedDocIds.size === generatedDocs.length ? (
                  <>
                    <CheckSquare className="h-4 w-4" />
                    Deselect All
                  </>
                ) : (
                  <>
                    <Square className="h-4 w-4" />
                    Select All
                  </>
                )}
              </Button>
              <span className="text-sm text-slate-600">
                {selectedDocIds.size} of {generatedDocs.length} selected
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as ExportFormat)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="docx">DOCX</SelectItem>
                  <SelectItem value="markdown">Markdown</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBatchExport(false)}
                disabled={selectedDocIds.size === 0 || isExporting}
                className="gap-2"
              >
                {isExporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Export Selected
              </Button>

              <Button
                size="sm"
                onClick={() => handleBatchExport(true)}
                disabled={isExporting}
                className="gap-2 bg-purple-600 hover:bg-purple-700"
              >
                {isExporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileDown className="h-4 w-4" />
                )}
                Export All
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content Area - Grid or Timeline */}
      {viewType === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {generatedDocs.map(doc => (
            <DocumentPreviewCard
              key={doc.id}
              document={doc}
              selected={selectedDocIds.has(doc.id)}
              onSelect={handleDocSelect}
              onUpdate={onUpdate}
            />
          ))}
        </div>
      ) : (
        <GenerationTimeline
          documents={generatedDocs}
          onUpdate={onUpdate}
        />
      )}
    </div>
  );
}
