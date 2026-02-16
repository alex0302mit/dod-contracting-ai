/**
 * MyDocumentsScreen - Lists standalone documents owned by the current user.
 * Provides actions to open in editor or delete.
 */

import { useState } from 'react';
import {
  FileText,
  Trash2,
  Loader2,
  FilePlus2,
  Clock,
  Star,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
import { useNavigation } from '@/contexts/NavigationContext';
import { useStandaloneDocuments } from '@/hooks/useStandaloneDocuments';
import { convertMarkdownToHtml } from '@/lib/markdownToHtml';
import { toast } from 'sonner';

const STATUS_STYLES: Record<string, string> = {
  generated: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  generating: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  failed: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
  not_generated: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
};

export function MyDocumentsScreen() {
  const { navigate, navigateToEditor, setEditorContent } = useNavigation();
  const { documents, loading, error, deleteDocument } = useStandaloneDocuments();
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleOpenInEditor = (doc: typeof documents[0]) => {
    if (!doc.generated_content) {
      toast.error('No generated content available');
      return;
    }
    const html = convertMarkdownToHtml(doc.generated_content);
    setEditorContent({ [doc.document_name]: html });
    navigateToEditor({ [doc.document_name]: html });
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      setDeleting(true);
      await deleteDocument(deleteTarget);
      toast.success('Document deleted');
    } catch (err: any) {
      toast.error(`Failed to delete: ${err.message}`);
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Loading your documents...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-4xl mx-auto py-8 px-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">My Documents</h1>
            <p className="text-muted-foreground mt-1">
              Your standalone generated documents
            </p>
          </div>
          <Button onClick={() => navigate('GENERATE_DOCUMENT')}>
            <FilePlus2 className="h-4 w-4 mr-2" />
            Generate New
          </Button>
        </div>

        {documents.length === 0 ? (
          <Card className="p-12 text-center">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No documents yet</h3>
            <p className="text-muted-foreground mb-4">
              Generate your first standalone document to get started.
            </p>
            <Button onClick={() => navigate('GENERATE_DOCUMENT')}>
              <FilePlus2 className="h-4 w-4 mr-2" />
              Generate Document
            </Button>
          </Card>
        ) : (
          <div className="space-y-3">
            {documents.map(doc => (
              <Card
                key={doc.id}
                className="p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleOpenInEditor(doc)}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <FileText className="h-8 w-8 text-primary flex-shrink-0" />
                    <div className="min-w-0">
                      <h3 className="font-medium truncate">{doc.document_name}</h3>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-muted-foreground flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          {formatDate(doc.generated_at || doc.created_at)}
                        </span>
                        {doc.ai_quality_score !== null && (
                          <span className="text-xs text-muted-foreground flex items-center">
                            <Star className="h-3 w-3 mr-1" />
                            Quality: {doc.ai_quality_score}/100
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge className={`text-xs ${STATUS_STYLES[doc.generation_status] || STATUS_STYLES.not_generated}`}>
                      {doc.generation_status.replace('_', ' ')}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={e => {
                        e.stopPropagation();
                        setDeleteTarget(doc.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Document</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The document and its generated content will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default MyDocumentsScreen;
