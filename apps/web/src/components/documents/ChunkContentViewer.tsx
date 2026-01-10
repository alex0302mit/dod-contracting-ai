/**
 * ChunkContentViewer Component
 * 
 * A modal dialog for viewing RAG chunk content with full metadata.
 * Used for chunk-level traceability in the document lineage view,
 * allowing users to see exactly which content segments influenced
 * AI-generated documents.
 * 
 * Features:
 * - Display chunk text content with scroll area
 * - Show metadata (source doc, chunk index, relevance)
 * - Copy to clipboard functionality
 * - Navigation between chunks from same source
 * 
 * Dependencies:
 * - lineageApi.getChunkContent for fetching chunk data
 * - Shadcn UI components (Dialog, ScrollArea, Badge)
 * - React Query for data fetching
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  FileText,
  Copy,
  Check,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  Database,
  Hash,
  Layers,
} from 'lucide-react';
import { lineageApi, type ChunkContent } from '@/services/api';

// Props interface for ChunkContentViewer
interface ChunkContentViewerProps {
  // Array of chunk IDs to display (enables navigation between chunks)
  chunkIds: string[];
  // Initially selected chunk index
  initialIndex?: number;
  // Whether the dialog is open
  open: boolean;
  // Callback when dialog open state changes
  onOpenChange: (open: boolean) => void;
  // Optional source document name for context
  sourceDocumentName?: string;
}

/**
 * ChunkMetadataRow - Helper component for displaying a single metadata field
 */
function ChunkMetadataRow({ 
  label, 
  value, 
  icon: Icon 
}: { 
  label: string; 
  value: string | number | undefined; 
  icon?: React.ComponentType<{ className?: string }>;
}) {
  if (value === undefined || value === null) return null;
  
  return (
    <div className="flex items-center gap-2 text-sm">
      {Icon && <Icon className="h-3.5 w-3.5 text-muted-foreground" />}
      <span className="text-muted-foreground">{label}:</span>
      <span className="font-medium">{String(value)}</span>
    </div>
  );
}

export function ChunkContentViewer({
  chunkIds,
  initialIndex = 0,
  open,
  onOpenChange,
  sourceDocumentName,
}: ChunkContentViewerProps) {
  // State for current chunk index and copy feedback
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [copied, setCopied] = useState(false);

  // Fetch all chunks in one request for efficient navigation
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['chunks', chunkIds.join(',')],
    queryFn: () => lineageApi.getChunkContent(chunkIds),
    enabled: open && chunkIds.length > 0,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Get current chunk from fetched data
  const chunks = data?.chunks || [];
  const currentChunk = chunks[currentIndex];
  const totalChunks = chunks.length;
  const hasMultiple = totalChunks > 1;

  // Navigation handlers
  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : totalChunks - 1));
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev < totalChunks - 1 ? prev + 1 : 0));
  };

  // Copy chunk content to clipboard
  const copyToClipboard = async () => {
    if (!currentChunk?.content) return;
    
    try {
      await navigator.clipboard.writeText(currentChunk.content);
      setCopied(true);
      // Reset copied state after 2 seconds
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Reset index when dialog opens with new chunks
  const handleOpenChange = (newOpen: boolean) => {
    if (newOpen) {
      setCurrentIndex(initialIndex);
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-blue-600" />
            RAG Chunk Content
          </DialogTitle>
          <DialogDescription>
            {sourceDocumentName 
              ? `Content from: ${sourceDocumentName}`
              : 'View the exact content that influenced AI generation'
            }
          </DialogDescription>
        </DialogHeader>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="flex flex-col items-center justify-center py-12 text-red-600">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p className="text-sm">Failed to load chunk content</p>
            <p className="text-xs text-muted-foreground mt-1">
              {(error as Error)?.message || 'Unknown error'}
            </p>
          </div>
        )}

        {/* Content */}
        {currentChunk && (
          <div className="flex-1 flex flex-col min-h-0">
            {/* Chunk Metadata Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex flex-wrap items-center gap-3">
                {/* Source document badge */}
                <Badge variant="outline" className="gap-1">
                  <FileText className="h-3 w-3" />
                  {currentChunk.original_filename || currentChunk.source_document}
                </Badge>
                
                {/* Chunk position badge */}
                <Badge variant="secondary" className="gap-1">
                  <Hash className="h-3 w-3" />
                  Chunk {(currentChunk.chunk_index || 0) + 1} of {currentChunk.total_chunks || '?'}
                </Badge>
                
                {/* Phase badge if available */}
                {currentChunk.phase && (
                  <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                    {currentChunk.phase.replace('_', ' ')}
                  </Badge>
                )}
                
                {/* Purpose badge if available */}
                {currentChunk.purpose && (
                  <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                    {currentChunk.purpose.replace('_', ' ')}
                  </Badge>
                )}
              </div>

              {/* Copy button */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={copyToClipboard}
                      className="gap-1.5"
                    >
                      {copied ? (
                        <>
                          <Check className="h-4 w-4 text-green-600" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4" />
                          Copy
                        </>
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Copy chunk content to clipboard</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            <Separator className="mb-3" />

            {/* Chunk Content Area */}
            <ScrollArea className="flex-1 rounded-md border bg-slate-50/50 p-4">
              <pre className="text-sm whitespace-pre-wrap font-mono text-slate-700 leading-relaxed">
                {currentChunk.content}
              </pre>
            </ScrollArea>

            {/* Additional Metadata */}
            <div className="mt-3 pt-3 border-t">
              <div className="grid grid-cols-2 gap-2">
                <ChunkMetadataRow
                  label="Chunk ID"
                  value={currentChunk.chunk_id?.slice(0, 40) + '...'}
                  icon={Layers}
                />
                {currentChunk.project_id && (
                  <ChunkMetadataRow
                    label="Project"
                    value={currentChunk.project_id.slice(0, 8) + '...'}
                  />
                )}
              </div>
            </div>

            {/* Navigation Controls (if multiple chunks) */}
            {hasMultiple && (
              <div className="flex items-center justify-between mt-4 pt-3 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToPrevious}
                  className="gap-1"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                
                <span className="text-sm text-muted-foreground">
                  {currentIndex + 1} of {totalChunks} chunks
                </span>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToNext}
                  className="gap-1"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !isError && chunks.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Database className="h-12 w-12 mb-3 opacity-50" />
            <p className="text-sm">No chunk content found</p>
            <p className="text-xs mt-1">The requested chunks may have been deleted</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
