/**
 * DocumentPreviewCard Component
 * 
 * Individual card for displaying a generated document in the AI Documents gallery.
 * Shows document preview, quality score, and provides quick action buttons.
 * 
 * Features:
 * - Content preview (first 250 characters with fade-out gradient)
 * - Quality score as a circular progress indicator with color coding
 * - Generation timestamp (relative time: "2 hours ago")
 * - Quick action buttons: Open in Editor, Download, Re-generate
 * - "Clear Generation" action: resets required docs back to pending (keeps checklist slot)
 * - "Delete Document" action: hard-deletes custom (non-required) documents only
 * 
 * Dependencies:
 * - Uses EditorNavigationContext for "Open in Editor" functionality
 * - Uses documentGenerationApi for re-generation, clear, and delete
 * - Uses date-fns for relative time formatting
 */

import { useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import {
  FileText,
  Sparkles,
  ExternalLink,
  Download,
  RefreshCw,
  MoreVertical,
  CheckCircle2,
  Loader2,
  Trash2,
  // Undo2 icon for "Clear Generation" action (reset to pending)
  Undo2,
} from 'lucide-react';
import { ProjectDocument } from '@/hooks/useProjectDocuments';
import { useEditorNavigation } from '@/contexts/EditorNavigationContext';
import { documentGenerationApi } from '@/services/api';
import { markdownToHtml } from '@/lib/markdownToHtml';

interface DocumentPreviewCardProps {
  document: ProjectDocument;
  selected?: boolean;
  onSelect?: (documentId: string, selected: boolean) => void;
  onUpdate: () => void;
}

export function DocumentPreviewCard({
  document,
  selected = false,
  onSelect,
  onUpdate,
}: DocumentPreviewCardProps) {
  const { navigateToEditor } = useEditorNavigation();
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  // "Clear Generation" state - resets doc to pending without removing from checklist
  const [isClearing, setIsClearing] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Get quality score color based on score value
  const getQualityColor = (score: number | null | undefined) => {
    if (!score) return 'text-slate-400';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  // Get quality score background color for the circular indicator
  const getQualityBgColor = (score: number | null | undefined) => {
    if (!score) return 'bg-slate-100';
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-amber-100';
    return 'bg-red-100';
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

  // Format phase name for display
  const formatPhaseName = (phase: string | null) => {
    if (!phase) return 'General';
    return phase.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  // Handle opening document in editor
  // Passes document.project_id to enable project-aware mode (all generated docs loaded as sections)
  const handleOpenInEditor = () => {
    if (document.generated_content) {
      navigateToEditor(document.generated_content, document.document_name, document.id, document.project_id);
      toast.success(`Opened "${document.document_name}" in editor`);
    } else {
      toast.error('No generated content available');
    }
  };

  // Handle downloading document as markdown
  const handleDownload = () => {
    if (!document.generated_content) {
      toast.error('No generated content available');
      return;
    }

    // Create markdown blob and download
    const blob = new Blob([document.generated_content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = `${document.document_name.replace(/\s+/g, '_')}.md`;
    window.document.body.appendChild(a);
    a.click();
    window.document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${document.document_name}.md`);
  };

  // Handle regenerating document
  const handleRegenerate = async () => {
    setShowRegenerateConfirm(false);
    setIsRegenerating(true);

    try {
      const assumptions = [
        { id: 'doc_type', text: `Document Type: ${document.document_name}`, source: 'AI Documents Gallery' },
      ];
      
      await documentGenerationApi.generate(document.id, assumptions);
      toast.info(`Started regenerating ${document.document_name}...`);
      
      // Refresh after a delay to show status
      setTimeout(() => {
        onUpdate();
        setIsRegenerating(false);
      }, 2000);
    } catch (error: any) {
      toast.error(`Failed to regenerate: ${error.message}`);
      setIsRegenerating(false);
    }
  };

  // Handle deleting document (hard delete - only for non-required custom docs)
  const handleDelete = async () => {
    setShowDeleteConfirm(false);
    setIsDeleting(true);
    try {
      await documentGenerationApi.deleteDocument(document.id);
      toast.success(`Deleted "${document.document_name}"`);
      onUpdate();
    } catch (error: any) {
      toast.error(`Failed to delete: ${error.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle clearing generation - resets document to pending, keeps checklist slot
  // This is the primary removal action for required/template-based documents
  const handleClearGeneration = async () => {
    setShowClearConfirm(false);
    setIsClearing(true);
    try {
      await documentGenerationApi.clearGeneration(document.id);
      toast.success(`Cleared generation for "${document.document_name}". Document reset to pending.`);
      onUpdate();
    } catch (error: any) {
      toast.error(`Failed to clear generation: ${error.message}`);
    } finally {
      setIsClearing(false);
    }
  };

  // Preview content: first 250 characters, converted to HTML for proper rendering
  const rawPreview = document.generated_content
    ? document.generated_content.substring(0, 250).trim()
    : 'No content available';
  const contentPreview = document.generated_content
    ? markdownToHtml(rawPreview)
    : rawPreview;
  const hasMoreContent = (document.generated_content?.length || 0) > 250;

  // Format generation date
  const generatedTimeAgo = document.generated_at
    ? formatDistanceToNow(new Date(document.generated_at), { addSuffix: true })
    : 'Unknown';

  return (
    <>
      <Card className="group relative hover:shadow-lg transition-shadow duration-200 overflow-hidden">
        {/* Selection checkbox */}
        {onSelect && (
          <div className="absolute top-3 left-3 z-10">
            <Checkbox
              checked={selected}
              onCheckedChange={(checked) => onSelect(document.id, checked as boolean)}
              className="bg-white shadow-sm"
            />
          </div>
        )}

        {/* Quality score indicator - top right */}
        <div className="absolute top-3 right-3 z-10">
          <div
            className={`flex items-center justify-center w-12 h-12 rounded-full ${getQualityBgColor(document.ai_quality_score)} shadow-sm`}
            title={`Quality Score: ${document.ai_quality_score || 'N/A'}%`}
          >
            <span className={`text-sm font-bold ${getQualityColor(document.ai_quality_score)}`}>
              {document.ai_quality_score || '—'}
            </span>
          </div>
        </div>

        <CardHeader className="pb-2 pt-12">
          <div className="flex items-start gap-2">
            <div className="h-8 w-8 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
              <Sparkles className="h-4 w-4 text-purple-600" />
            </div>
            <div className="flex-1 min-w-0 pr-8">
              <h3 className="font-semibold text-slate-900 line-clamp-2">
                {document.document_name}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className={`text-xs ${getPhaseBadgeColor(document.phase)}`}>
                  {formatPhaseName(document.phase)}
                </Badge>
                <span className="text-xs text-slate-500">
                  {generatedTimeAgo}
                </span>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="py-3">
          {/* Content preview with fade-out gradient - rendered as HTML */}
          <div className="relative">
            <div
              className="text-sm text-slate-600 prose prose-sm prose-slate max-w-none [&>h1]:text-base [&>h1]:font-semibold [&>h2]:text-sm [&>h2]:font-semibold [&>h3]:text-sm [&>p]:my-1"
              dangerouslySetInnerHTML={{ __html: contentPreview }}
            />
            {hasMoreContent && (
              <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-white to-transparent" />
            )}
          </div>
        </CardContent>

        <CardFooter className="pt-2 pb-4 flex items-center justify-between gap-2 border-t">
          {/* Primary action - Open in Editor */}
          <Button
            size="sm"
            onClick={handleOpenInEditor}
            className="gap-1 flex-1"
            disabled={!document.generated_content || isRegenerating}
          >
            <ExternalLink className="h-3 w-3" />
            Open in Editor
          </Button>

          {/* Secondary actions dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" variant="outline" className="px-2">
                {isRegenerating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <MoreVertical className="h-4 w-4" />
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleDownload} disabled={!document.generated_content}>
                <Download className="h-4 w-4 mr-2" />
                Download Markdown
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => setShowRegenerateConfirm(true)}
                disabled={isRegenerating}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Re-generate
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {/* "Clear Generation" - resets to pending, keeps checklist slot.
                  Always available (primary removal action for required docs). */}
              <DropdownMenuItem
                onClick={() => setShowClearConfirm(true)}
                disabled={isClearing || isDeleting || isRegenerating || document.generation_status === 'generating'}
                className="text-amber-600 focus:text-amber-600 focus:bg-amber-50"
              >
                <Undo2 className="h-4 w-4 mr-2" />
                Clear Generation
              </DropdownMenuItem>
              {/* "Delete Document" - hard delete, only for non-required custom docs.
                  Required/template docs are protected from accidental removal. */}
              {!document.is_required && (
                <DropdownMenuItem
                  onClick={() => setShowDeleteConfirm(true)}
                  disabled={isDeleting || isRegenerating || document.generation_status === 'generating'}
                  className="text-red-600 focus:text-red-600 focus:bg-red-50"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Document
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </CardFooter>

        {/* Generating / Deleting / Clearing overlay */}
        {(isRegenerating || isDeleting || isClearing || document.generation_status === 'generating') && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-20">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600 mx-auto mb-2" />
              <span className="text-sm font-medium text-slate-700">
                {isClearing ? 'Clearing...' : isDeleting ? 'Deleting...' : 'Regenerating...'}
              </span>
            </div>
          </div>
        )}
      </Card>

      {/* Regenerate confirmation dialog */}
      <AlertDialog open={showRegenerateConfirm} onOpenChange={setShowRegenerateConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Regenerate Document?</AlertDialogTitle>
            <AlertDialogDescription>
              This will replace the existing generated content for "{document.document_name}" 
              with newly generated content. The previous content will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRegenerate} className="bg-purple-600 hover:bg-purple-700">
              <RefreshCw className="h-4 w-4 mr-2" />
              Regenerate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Clear Generation confirmation dialog */}
      <AlertDialog open={showClearConfirm} onOpenChange={setShowClearConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Clear Generated Content?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the generated content for &quot;{document.document_name}&quot; and reset it
              back to pending. The document will stay in your Document Checklist and can be
              regenerated at any time. All version history, lineage, and feedback will also be cleared.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleClearGeneration} className="bg-amber-600 hover:bg-amber-700">
              <Undo2 className="h-4 w-4 mr-2" />
              Clear Generation
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Document confirmation dialog (only reachable for non-required docs) */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Document?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove &quot;{document.document_name}&quot; from both the AI Documents
              gallery and the Document Checklist, including all generated content, versions,
              lineage history, and feedback. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
