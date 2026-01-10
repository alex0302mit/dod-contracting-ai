/**
 * DocumentCard Component
 * 
 * Card/tile for displaying document information in grid/list views.
 * Shows document name, status, generation status, and actions.
 * 
 * Used in Documents screen for batch selection and export.
 * 
 * Dependencies:
 * - StatusChip for status display
 * - Card from shadcn/ui
 * - Checkbox for selection
 */

import { FileText, Download, Eye, MoreHorizontal, Sparkles, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { StatusChip, normalizeStatus } from './StatusChip';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

// Document type matching useProjectDocuments
export interface DocumentData {
  id: string;
  document_name: string;
  description?: string | null;
  status: string;
  category?: string;
  phase?: string | null;
  generation_status?: 'not_generated' | 'generating' | 'generated' | 'failed';
  generated_at?: string | null;
  ai_quality_score?: number | null;
  updated_at?: string;
  created_at?: string;
}

interface DocumentCardProps {
  /** Document data */
  document: DocumentData;
  /** Whether card is selected */
  isSelected?: boolean;
  /** Selection change handler */
  onSelect?: (selected: boolean) => void;
  /** View document handler */
  onView?: () => void;
  /** Export handler */
  onExport?: (format: 'pdf' | 'docx' | 'markdown') => void;
  /** Generate/regenerate handler */
  onGenerate?: () => void;
  /** Additional className */
  className?: string;
  /** Card variant */
  variant?: 'default' | 'compact';
}

/**
 * DocumentCard displays document info with actions
 */
export function DocumentCard({
  document,
  isSelected = false,
  onSelect,
  onView,
  onExport,
  onGenerate,
  className,
  variant = 'default',
}: DocumentCardProps) {
  const status = normalizeStatus(document.status);
  const hasAIContent = document.generation_status === 'generated';
  const isGenerating = document.generation_status === 'generating';
  const lastUpdated = document.updated_at || document.created_at;
  
  // Compact variant
  if (variant === 'compact') {
    return (
      <div
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors",
          isSelected && "ring-2 ring-primary",
          className
        )}
      >
        {onSelect && (
          <Checkbox
            checked={isSelected}
            onCheckedChange={onSelect}
            className="flex-shrink-0"
          />
        )}
        
        <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{document.document_name}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <StatusChip status={status} size="sm" showIcon={false} />
            {hasAIContent && (
              <Badge variant="secondary" className="text-xs bg-ai/10 text-ai">
                <Sparkles className="h-3 w-3 mr-1" />
                AI
              </Badge>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          {onView && (
            <Button variant="ghost" size="sm" onClick={onView} className="h-8 w-8 p-0">
              <Eye className="h-4 w-4" />
            </Button>
          )}
          {onExport && hasAIContent && (
            <Button variant="ghost" size="sm" onClick={() => onExport('pdf')} className="h-8 w-8 p-0">
              <Download className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    );
  }
  
  // Default card variant
  return (
    <Card className={cn(
      "group transition-all hover:shadow-md",
      isSelected && "ring-2 ring-primary",
      className
    )}>
      <CardHeader className="pb-2">
        <div className="flex items-start gap-3">
          {/* Selection checkbox */}
          {onSelect && (
            <Checkbox
              checked={isSelected}
              onCheckedChange={onSelect}
              className="mt-1"
            />
          )}
          
          {/* Document icon */}
          <div className={cn(
            "h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0",
            hasAIContent ? "bg-ai/10" : "bg-muted"
          )}>
            {hasAIContent ? (
              <Sparkles className="h-5 w-5 text-ai" />
            ) : (
              <FileText className="h-5 w-5 text-muted-foreground" />
            )}
          </div>
          
          {/* Document info */}
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-sm truncate">
              {document.document_name}
            </h3>
            {document.description && (
              <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                {document.description}
              </p>
            )}
          </div>
          
          {/* Actions menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onView && (
                <DropdownMenuItem onClick={onView}>
                  <Eye className="h-4 w-4 mr-2" />
                  View
                </DropdownMenuItem>
              )}
              {onGenerate && (
                <DropdownMenuItem onClick={onGenerate}>
                  <Sparkles className="h-4 w-4 mr-2" />
                  {hasAIContent ? 'Regenerate' : 'Generate'}
                </DropdownMenuItem>
              )}
              {onExport && hasAIContent && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => onExport('pdf')}>
                    <Download className="h-4 w-4 mr-2" />
                    Export PDF
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onExport('docx')}>
                    <Download className="h-4 w-4 mr-2" />
                    Export DOCX
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onExport('markdown')}>
                    <Download className="h-4 w-4 mr-2" />
                    Export Markdown
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Status badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <StatusChip status={status} size="sm" />
          
          {isGenerating && (
            <Badge variant="secondary" className="text-xs bg-info/10 text-info">
              <Clock className="h-3 w-3 mr-1 animate-spin" />
              Generating...
            </Badge>
          )}
          
          {hasAIContent && document.ai_quality_score && (
            <Badge variant="secondary" className="text-xs">
              Quality: {Math.round(document.ai_quality_score)}%
            </Badge>
          )}
          
          {document.category && (
            <Badge variant="outline" className="text-xs">
              {document.category}
            </Badge>
          )}
        </div>
        
        {/* Last updated */}
        {lastUpdated && (
          <p className="text-xs text-muted-foreground mt-3">
            Updated {formatDistanceToNow(new Date(lastUpdated), { addSuffix: true })}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * DocumentCardGrid - Grid layout for document cards
 */
interface DocumentCardGridProps {
  children: React.ReactNode;
  className?: string;
}

export function DocumentCardGrid({ children, className }: DocumentCardGridProps) {
  return (
    <div className={cn(
      "grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
      className
    )}>
      {children}
    </div>
  );
}

export default DocumentCard;
