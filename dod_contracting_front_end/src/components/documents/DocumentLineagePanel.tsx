/**
 * DocumentLineagePanel Component
 * 
 * Displays the lineage/provenance of AI-generated documents, showing:
 * - Source documents that influenced the generation
 * - Relevance scores indicating importance of each source
 * - Chunk usage details for fine-grained traceability
 * 
 * This component provides explainability for AI decisions, which is critical
 * for DoD/FAR compliance and auditability requirements.
 * 
 * Dependencies:
 * - lineageApi from services/api for fetching lineage data
 * - Shadcn UI components for consistent styling
 * - React Query for data fetching and caching
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  GitBranch, 
  FileText, 
  ChevronDown, 
  ChevronRight,
  Database,
  ExternalLink,
  Info,
  Loader2,
  AlertCircle,
  FileStack,
  Scale,
  BookOpen
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { lineageApi, type DocumentLineage, type InfluenceType } from '@/services/api';

// Props interface for the DocumentLineagePanel
interface DocumentLineagePanelProps {
  documentId: string;
  documentName?: string;
  compact?: boolean;
  onSourceClick?: (sourceId: string) => void;
}

// Influence type display configuration
const INFLUENCE_CONFIG: Record<InfluenceType, {
  label: string;
  icon: React.ReactNode;
  color: string;
  description: string;
}> = {
  context: {
    label: 'Context',
    icon: <Database className="h-3 w-3" />,
    color: 'bg-blue-100 text-blue-700 border-blue-200',
    description: 'General context provided to the AI'
  },
  template: {
    label: 'Template',
    icon: <FileStack className="h-3 w-3" />,
    color: 'bg-amber-100 text-amber-700 border-amber-200',
    description: 'Used as a structural template'
  },
  regulation: {
    label: 'Regulation',
    icon: <Scale className="h-3 w-3" />,
    color: 'bg-violet-100 text-violet-700 border-violet-200',
    description: 'FAR/DFARS or policy reference'
  },
  data_source: {
    label: 'Data Source',
    icon: <FileText className="h-3 w-3" />,
    color: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    description: 'Primary data (market research, prior awards)'
  },
  reference: {
    label: 'Reference',
    icon: <BookOpen className="h-3 w-3" />,
    color: 'bg-slate-100 text-slate-700 border-slate-200',
    description: 'Cited in the generated content'
  }
};

// Single source item component
function SourceItem({ 
  source, 
  expanded,
  onToggle,
  onSourceClick 
}: { 
  source: DocumentLineage;
  expanded: boolean;
  onToggle: () => void;
  onSourceClick?: (sourceId: string) => void;
}) {
  const influenceConfig = INFLUENCE_CONFIG[source.influence_type] || INFLUENCE_CONFIG.data_source;
  
  // Calculate relevance as percentage
  const relevancePercent = Math.round((source.relevance_score || 0) * 100);
  
  // Get display name
  const displayName = source.source_document?.document_name || source.source_filename || 'Unknown Source';
  
  return (
    <Collapsible open={expanded} onOpenChange={onToggle}>
      <div className="border rounded-lg overflow-hidden mb-2 hover:border-blue-200 transition-colors">
        <CollapsibleTrigger asChild>
          <button className="w-full p-3 flex items-center gap-3 text-left hover:bg-slate-50">
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
            ) : (
              <ChevronRight className="h-4 w-4 text-slate-400 shrink-0" />
            )}
            
            {/* Source Icon & Name */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm truncate" title={displayName}>
                  {displayName}
                </span>
                {source.source_document?.category && (
                  <Badge variant="secondary" className="text-[10px]">
                    {source.source_document.category}
                  </Badge>
                )}
              </div>
              
              {/* Influence Type Badge */}
              <div className="flex items-center gap-2 mt-1">
                <Badge 
                  variant="outline" 
                  className={`text-[10px] gap-1 ${influenceConfig.color}`}
                >
                  {influenceConfig.icon}
                  {influenceConfig.label}
                </Badge>
                
                {/* Chunks Count */}
                {source.chunks_used_count > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {source.chunks_used_count} chunk{source.chunks_used_count !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
            
            {/* Relevance Score */}
            <div className="shrink-0 w-16 text-right">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div>
                      <div className="text-sm font-medium">{relevancePercent}%</div>
                      <Progress value={relevancePercent} className="h-1.5 mt-1" />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">Relevance score: {source.relevance_score?.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">
                      Higher = more influential in generation
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </button>
        </CollapsibleTrigger>
        
        <CollapsibleContent>
          <div className="px-3 pb-3 pt-0 border-t bg-slate-50/50">
            <div className="grid gap-2 mt-2 text-xs">
              {/* Influence Type Explanation */}
              <div className="flex items-start gap-2">
                <Info className="h-3 w-3 text-muted-foreground mt-0.5" />
                <span className="text-muted-foreground">{influenceConfig.description}</span>
              </div>
              
              {/* Context if available */}
              {source.context && (
                <div className="flex items-start gap-2">
                  <span className="text-muted-foreground shrink-0">Note:</span>
                  <span>{source.context}</span>
                </div>
              )}
              
              {/* Chunk IDs (collapsible for debugging) */}
              {source.chunk_ids_used && source.chunk_ids_used.length > 0 && (
                <details className="text-muted-foreground">
                  <summary className="cursor-pointer hover:text-slate-700">
                    View {source.chunk_ids_used.length} chunk IDs
                  </summary>
                  <div className="mt-1 p-2 bg-slate-100 rounded text-[10px] font-mono break-all">
                    {source.chunk_ids_used.slice(0, 5).join(', ')}
                    {source.chunk_ids_used.length > 5 && ` ... +${source.chunk_ids_used.length - 5} more`}
                  </div>
                </details>
              )}
              
              {/* View Source Button */}
              {source.source_document_id && onSourceClick && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="gap-1 h-7 text-xs mt-1"
                  onClick={() => onSourceClick(source.source_document_id!)}
                >
                  <ExternalLink className="h-3 w-3" />
                  View Source Document
                </Button>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

export function DocumentLineagePanel({ 
  documentId, 
  documentName,
  compact = false,
  onSourceClick 
}: DocumentLineagePanelProps) {
  // State for expanded items
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  
  // Fetch lineage data
  const { data: lineage, isLoading, isError, error } = useQuery({
    queryKey: ['document-lineage', documentId],
    queryFn: () => lineageApi.getLineage(documentId),
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  // Toggle expanded state for an item
  const toggleExpanded = (id: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };
  
  // Loading state
  if (isLoading) {
    return (
      <Card className={compact ? 'border-0 shadow-none' : ''}>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        </CardContent>
      </Card>
    );
  }
  
  // Error state
  if (isError) {
    return (
      <Card className={compact ? 'border-0 shadow-none' : ''}>
        <CardContent className="flex items-center justify-center py-8 text-red-600">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span className="text-sm">Failed to load lineage: {(error as Error)?.message}</span>
        </CardContent>
      </Card>
    );
  }
  
  // No lineage data
  if (!lineage || lineage.total_sources === 0) {
    return (
      <Card className={compact ? 'border-0 shadow-none' : ''}>
        {!compact && (
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              Document Sources
            </CardTitle>
          </CardHeader>
        )}
        <CardContent className={compact ? 'py-4' : ''}>
          <div className="text-center py-4 text-muted-foreground">
            <GitBranch className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No source lineage recorded</p>
            <p className="text-xs mt-1">
              Source tracking will appear after AI generation
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className={compact ? 'border-0 shadow-none' : ''}>
      {!compact && (
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-blue-600" />
            Document Sources
          </CardTitle>
          <CardDescription className="text-xs">
            {lineage.total_sources} source{lineage.total_sources !== 1 ? 's' : ''} influenced this document
          </CardDescription>
        </CardHeader>
      )}
      
      <CardContent className={compact ? 'py-2' : ''}>
        {compact && lineage.total_sources > 0 && (
          <div className="flex items-center gap-2 mb-3 text-sm text-muted-foreground">
            <GitBranch className="h-4 w-4" />
            <span>{lineage.total_sources} sources</span>
          </div>
        )}
        
        <ScrollArea className={compact ? 'h-[200px]' : 'h-[300px]'}>
          <div className="space-y-1">
            {lineage.sources.map((source) => (
              <SourceItem
                key={source.id}
                source={source}
                expanded={expandedItems.has(source.id)}
                onToggle={() => toggleExpanded(source.id)}
                onSourceClick={onSourceClick}
              />
            ))}
          </div>
        </ScrollArea>
        
        {/* Derived documents (if this document was a source) */}
        {lineage.derived_from_this.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="text-xs font-medium text-muted-foreground mb-2">
              Used as source for:
            </h4>
            <div className="space-y-1">
              {lineage.derived_from_this.map((derived) => (
                <div 
                  key={derived.id}
                  className="flex items-center gap-2 text-xs p-2 rounded bg-slate-50"
                >
                  <FileText className="h-3 w-3 text-slate-500" />
                  <span className="truncate">
                    Document {derived.derived_document_id.slice(0, 8)}...
                  </span>
                  <Badge variant="outline" className="ml-auto text-[10px]">
                    {Math.round((derived.relevance_score || 0) * 100)}% relevance
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
