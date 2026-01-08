/**
 * DocumentsScreen Component
 * 
 * Grid/list view of project documents with batch selection and export.
 * 
 * Features:
 * - Grid/List view toggle
 * - Batch selection with checkboxes
 * - Export dropdown (PDF/DOCX/JSON)
 * - Filter by status, phase, generation status
 * 
 * Dependencies:
 * - useProjectDocuments for document data
 * - DocumentCard for display
 * - ActionStrip for actions
 * - documentGenerationApi for batch export
 */

import { useState, useMemo } from 'react';
import { 
  LayoutGrid, 
  List, 
  Download, 
  FileJson,
  Filter,
  Loader2,
  FolderOpen
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { useProjectDocuments } from '@/hooks/useProjectDocuments';
import { useNavigation } from '@/contexts/NavigationContext';
import { documentGenerationApi } from '@/services/api';
import { DocumentCard, DocumentCardGrid, ActionStrip } from '@/components/shared';
import { toast } from 'sonner';

type ViewMode = 'grid' | 'list';
type StatusFilter = 'all' | 'pending' | 'generated' | 'approved';

/**
 * DocumentsScreen displays project documents with batch operations
 */
export function DocumentsScreen() {
  const { selectedProjectId, navigate } = useNavigation();
  const { documents, loading, getDocumentStats } = useProjectDocuments(selectedProjectId);
  
  // View and filter state
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isExporting, setIsExporting] = useState(false);
  
  // Filter documents based on status filter
  const filteredDocuments = useMemo(() => {
    if (statusFilter === 'all') return documents;
    
    return documents.filter(doc => {
      switch (statusFilter) {
        case 'pending': return doc.status === 'pending';
        case 'generated': return doc.generation_status === 'generated';
        case 'approved': return doc.status === 'approved';
        default: return true;
      }
    });
  }, [documents, statusFilter]);
  
  // Get document stats
  const stats = getDocumentStats();
  
  // Toggle document selection
  const toggleSelection = (docId: string, selected: boolean) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(docId);
      } else {
        newSet.delete(docId);
      }
      return newSet;
    });
  };
  
  // Select all filtered documents
  const selectAll = () => {
    setSelectedIds(new Set(filteredDocuments.map(d => d.id)));
  };
  
  // Clear selection
  const clearSelection = () => {
    setSelectedIds(new Set());
  };
  
  // Handle batch export
  const handleBatchExport = async (format: 'pdf' | 'docx' | 'markdown') => {
    if (!selectedProjectId || selectedIds.size === 0) {
      toast.error('Please select documents to export');
      return;
    }
    
    setIsExporting(true);
    try {
      await documentGenerationApi.exportBatch(
        selectedProjectId,
        Array.from(selectedIds),
        format
      );
      toast.success(`Exporting ${selectedIds.size} documents as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error(`Export failed: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };
  
  // Handle document view
  const handleViewDocument = (docId: string) => {
    // Navigate to editor with document
    const doc = documents.find(d => d.id === docId);
    if (doc?.generated_content) {
      navigate('EDITOR');
    }
  };
  
  // No project selected
  if (!selectedProjectId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <FolderOpen className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
          <h2 className="text-lg font-medium mb-2">No Project Selected</h2>
          <p className="text-muted-foreground mb-4">
            Select a project from the header or go to the Tracker
          </p>
          <Button onClick={() => navigate('TRACKER')}>
            Go to Tracker
          </Button>
        </div>
      </div>
    );
  }
  
  // Loading state
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="mt-4 text-muted-foreground">Loading documents...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* Action Strip */}
      <ActionStrip
        primaryAction={{
          label: 'Download Batch',
          icon: <Download className="h-4 w-4" />,
          onClick: () => handleBatchExport('pdf'),
          loading: isExporting,
          disabled: selectedIds.size === 0,
        }}
        secondaryActions={[
          {
            label: 'Export JSON',
            icon: <FileJson className="h-4 w-4" />,
            onClick: () => handleBatchExport('markdown'),
            disabled: selectedIds.size === 0,
          },
        ]}
      >
        {/* View toggle */}
        <div className="flex items-center gap-1 border rounded-lg p-1">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('grid')}
            className="h-7 w-7 p-0"
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('list')}
            className="h-7 w-7 p-0"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Status filter */}
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as StatusFilter)}>
          <SelectTrigger className="w-[150px] h-8">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Documents</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="generated">Generated</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
          </SelectContent>
        </Select>
        
        {/* Selection controls */}
        <div className="flex items-center gap-2">
          <Checkbox
            checked={selectedIds.size === filteredDocuments.length && filteredDocuments.length > 0}
            onCheckedChange={(checked) => checked ? selectAll() : clearSelection()}
          />
          <span className="text-sm text-muted-foreground">
            {selectedIds.size > 0 
              ? `${selectedIds.size} selected` 
              : `${filteredDocuments.length} documents`
            }
          </span>
        </div>
      </ActionStrip>
      
      {/* Stats badges */}
      <div className="px-4 py-2 border-b flex items-center gap-2 flex-wrap">
        <Badge variant="outline">Total: {stats.total}</Badge>
        <Badge variant="outline" className="text-info">Uploaded: {stats.uploaded}</Badge>
        <Badge variant="outline" className="text-success">Approved: {stats.approved}</Badge>
        <Badge variant="outline" className="text-warning">Under Review: {stats.underReview}</Badge>
      </div>
      
      {/* Documents display */}
      <div className="flex-1 overflow-auto p-4">
        {filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <FolderOpen className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
            <p className="text-muted-foreground">No documents match your filter</p>
          </div>
        ) : viewMode === 'grid' ? (
          <DocumentCardGrid>
            {filteredDocuments.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                isSelected={selectedIds.has(doc.id)}
                onSelect={(selected) => toggleSelection(doc.id, selected)}
                onView={() => handleViewDocument(doc.id)}
                onExport={(format) => handleBatchExport(format)}
                variant="default"
              />
            ))}
          </DocumentCardGrid>
        ) : (
          <div className="space-y-2">
            {filteredDocuments.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                isSelected={selectedIds.has(doc.id)}
                onSelect={(selected) => toggleSelection(doc.id, selected)}
                onView={() => handleViewDocument(doc.id)}
                onExport={(format) => handleBatchExport(format)}
                variant="compact"
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default DocumentsScreen;
