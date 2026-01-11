import { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ImportPlacement } from '@/hooks/useDocumentImport';

export interface ImportedDocument {
  id: string;
  filename: string;
  fileType: 'pdf' | 'docx';
  importedAt: string;
  placement: ImportPlacement;
  sectionName: string;
  content: string;
}

interface ImportedDocumentsListProps {
  documents: ImportedDocument[];
  onDelete: (id: string) => void;
  onNavigate: (sectionName: string) => void;
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function ImportedDocumentsList({ documents, onDelete, onNavigate }: ImportedDocumentsListProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Don't render if no documents
  if (documents.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-slate-200 pt-3 mt-3">
      {/* Header - Collapsible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1.5 w-full px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        <span>Imported Documents</span>
        <span className="ml-auto text-slate-400">({documents.length})</span>
      </button>

      {/* List */}
      {isExpanded && (
        <div className="mt-2 space-y-1">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="group flex items-center gap-2 px-2 py-1.5 rounded-md bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer"
              onClick={() => onNavigate(doc.sectionName)}
            >
              {/* File icon */}
              <div className={cn(
                'flex-shrink-0 p-1 rounded',
                doc.fileType === 'pdf' ? 'bg-red-100' : 'bg-blue-100'
              )}>
                <FileText className={cn(
                  'h-3 w-3',
                  doc.fileType === 'pdf' ? 'text-red-600' : 'text-blue-600'
                )} />
              </div>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-700 truncate" title={doc.filename}>
                  {doc.filename}
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  <span className="text-slate-500">{doc.sectionName}</span>
                  <span className="mx-1">·</span>
                  {formatRelativeTime(doc.importedAt)}
                </p>
              </div>

              {/* Delete button */}
              <Button
                variant="ghost"
                size="icon"
                className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(doc.id);
                }}
              >
                <X className="h-3 w-3 text-slate-400 hover:text-slate-600" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
