/**
 * ReasoningPanel - Chain-of-Thought Display Component
 *
 * Displays AI reasoning metadata for document generation, including:
 * - Token usage and cost
 * - RAG sources used
 * - Step-by-step reasoning timeline
 * - Debug panel for admins (raw prompts/responses)
 *
 * This component provides transparency into how AI-generated content
 * was created and what sources influenced the generation.
 */
import { useState } from "react";
import {
  Brain,
  Clock,
  Database,
  DollarSign,
  ChevronDown,
  ChevronRight,
  Bug,
  RefreshCw,
  Zap,
  FileText,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { reasoningApi, ReasoningData, ReasoningStep } from "@/services/api";
import { useQuery } from "@tanstack/react-query";

interface ReasoningPanelProps {
  /** Document ID to fetch reasoning for */
  documentId?: string;
  /** Whether current user is an admin (shows debug panel) */
  isAdmin?: boolean;
  /** Optional callback when a source chunk is clicked */
  onSourceClick?: (chunkId: string) => void;
}

/**
 * Empty state component shown when no reasoning data is available
 */
function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <Brain className="h-10 w-10 text-muted-foreground/40 mb-3" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

/**
 * Loading skeleton for reasoning panel
 */
function LoadingSkeleton() {
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Skeleton className="h-5 w-5 rounded" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-5 w-20 ml-auto rounded-full" />
      </div>
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-20" />
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-2">
          <Skeleton className="h-16 w-full rounded" />
          <Skeleton className="h-16 w-full rounded" />
          <Skeleton className="h-16 w-full rounded" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-12 w-full rounded" />
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Format duration in ms to human-readable string
 */
function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

/**
 * Get icon for reasoning step type
 */
function getStepIcon(stepType: string) {
  switch (stepType) {
    case "context_retrieval":
      return <Database className="h-3 w-3" />;
    case "agent_selection":
      return <Zap className="h-3 w-3" />;
    case "llm_generation":
      return <Brain className="h-3 w-3" />;
    case "validation":
      return <FileText className="h-3 w-3" />;
    default:
      return <Clock className="h-3 w-3" />;
  }
}

/**
 * Get color for step type badge
 */
function getStepColor(stepType: string): string {
  switch (stepType) {
    case "context_retrieval":
      return "bg-blue-100 text-blue-700 border-blue-200";
    case "agent_selection":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "llm_generation":
      return "bg-purple-100 text-purple-700 border-purple-200";
    case "validation":
      return "bg-green-100 text-green-700 border-green-200";
    default:
      return "bg-slate-100 text-slate-700 border-slate-200";
  }
}

export function ReasoningPanel({
  documentId,
  isAdmin = false,
  onSourceClick,
}: ReasoningPanelProps) {
  const [showDebug, setShowDebug] = useState(false);
  const [showAllSteps, setShowAllSteps] = useState(false);

  const {
    data: reasoning,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["document-reasoning", documentId, isAdmin],
    queryFn: () => reasoningApi.get(documentId!, isAdmin),
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  if (!documentId) {
    return <EmptyState message="Save document to see AI reasoning" />;
  }

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-center py-4">
          <p className="text-sm text-red-600 mb-2">Failed to load reasoning data</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-3 w-3 mr-1" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!reasoning || reasoning.message) {
    return (
      <EmptyState message={reasoning?.message || "No reasoning data available. Generate content to see AI thought process."} />
    );
  }

  const stepsToShow = showAllSteps
    ? reasoning.reasoning_steps
    : reasoning.reasoning_steps.slice(0, 5);

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2 flex-wrap">
          <Brain className="h-5 w-5 text-purple-600 flex-shrink-0" />
          <span className="font-semibold text-sm">AI Reasoning</span>
          <Badge variant="outline" className="text-[10px] max-w-full truncate" title={reasoning.agent_name}>
            {reasoning.agent_name}
          </Badge>
        </div>

        {/* Token Usage Card */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-green-600" />
              Token Usage
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-1.5 text-center">
            <div className="p-1.5 bg-muted rounded-lg">
              <div className="text-base font-bold text-slate-900">
                {reasoning.input_tokens.toLocaleString()}
              </div>
              <div className="text-[9px] text-muted-foreground uppercase tracking-wide">
                Input
              </div>
            </div>
            <div className="p-1.5 bg-muted rounded-lg">
              <div className="text-base font-bold text-slate-900">
                {reasoning.output_tokens.toLocaleString()}
              </div>
              <div className="text-[9px] text-muted-foreground uppercase tracking-wide">
                Output
              </div>
            </div>
            <div className="p-1.5 bg-muted rounded-lg">
              <div className="text-sm font-bold text-green-600">
                ${reasoning.total_cost_usd.toFixed(3)}
              </div>
              <div className="text-[9px] text-muted-foreground uppercase tracking-wide">
                Cost
              </div>
            </div>
          </CardContent>
        </Card>

        {/* RAG Context Card */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-600" />
              Sources Used
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold text-slate-900">
                {reasoning.rag_chunks_retrieved}
              </span>
              <span className="text-sm text-muted-foreground">
                knowledge chunks
              </span>
            </div>
            {reasoning.rag_query && (
              <p className="text-xs text-muted-foreground mt-2 truncate">
                Query: &quot;{reasoning.rag_query}&quot;
              </p>
            )}
            {reasoning.rag_phase_filter && (
              <Badge variant="secondary" className="mt-2 text-xs">
                Phase: {reasoning.rag_phase_filter}
              </Badge>
            )}
            {/* Show chunk IDs if available and onSourceClick is provided */}
            {reasoning.rag_chunk_ids.length > 0 && onSourceClick && (
              <div className="mt-3 pt-3 border-t">
                <p className="text-xs font-medium mb-2">Chunk References:</p>
                <div className="flex flex-wrap gap-1">
                  {reasoning.rag_chunk_ids.slice(0, 5).map((chunkId, idx) => (
                    <Badge
                      key={idx}
                      variant="outline"
                      className="text-[10px] cursor-pointer hover:bg-slate-100"
                      onClick={() => onSourceClick(chunkId)}
                    >
                      {chunkId.slice(0, 8)}...
                    </Badge>
                  ))}
                  {reasoning.rag_chunk_ids.length > 5 && (
                    <Badge variant="secondary" className="text-[10px]">
                      +{reasoning.rag_chunk_ids.length - 5} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Reasoning Timeline */}
        {reasoning.reasoning_steps.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock className="h-4 w-4 text-slate-600" />
                Reasoning Steps
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {stepsToShow.map((step: ReasoningStep, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 pl-2 border-l-2 border-purple-200"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-1.5">
                        {getStepIcon(step.step_type)}
                        <span
                          className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${getStepColor(
                            step.step_type
                          )}`}
                        >
                          {step.step_type.replace(/_/g, " ")}
                        </span>
                      </div>
                      <p className="text-sm mt-1 text-slate-700">
                        {step.description}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDuration(step.duration_ms)}
                    </span>
                  </div>
                ))}
              </div>

              {reasoning.reasoning_steps.length > 5 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-2 text-xs"
                  onClick={() => setShowAllSteps(!showAllSteps)}
                >
                  {showAllSteps
                    ? "Show less"
                    : `Show ${reasoning.reasoning_steps.length - 5} more steps`}
                </Button>
              )}

              <div className="mt-3 pt-3 border-t text-sm text-muted-foreground flex justify-between items-center">
                <span>Total time:</span>
                <span className="font-medium text-slate-700">
                  {formatDuration(reasoning.generation_time_ms)}
                </span>
              </div>

              {reasoning.confidence_score !== null &&
                reasoning.confidence_score !== undefined && (
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-sm text-muted-foreground">
                      Confidence:
                    </span>
                    <span className="font-medium text-slate-700">
                      {(reasoning.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
            </CardContent>
          </Card>
        )}

        {/* Model Info */}
        <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
          <span>Model: {reasoning.model_used}</span>
          <span>
            {new Date(reasoning.created_at).toLocaleDateString()}
          </span>
        </div>

        {/* Debug Panel (Admin Only) */}
        {isAdmin && reasoning.full_prompt && (
          <Collapsible open={showDebug} onOpenChange={setShowDebug}>
            <CollapsibleTrigger className="flex items-center gap-2 w-full p-2 hover:bg-muted rounded transition-colors">
              {showDebug ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              <Bug className="h-4 w-4 text-orange-600" />
              <span className="font-medium text-sm">Debug (Admin)</span>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-2 space-y-3">
                <div>
                  <div className="text-xs font-medium mb-1 flex items-center gap-1">
                    <span>Full Prompt</span>
                    <Badge variant="secondary" className="text-[9px]">
                      {reasoning.input_tokens} tokens
                    </Badge>
                  </div>
                  <pre className="text-[10px] bg-muted p-2 rounded overflow-auto max-h-40 whitespace-pre-wrap font-mono">
                    {reasoning.full_prompt}
                  </pre>
                </div>
                {reasoning.full_response && (
                  <div>
                    <div className="text-xs font-medium mb-1 flex items-center gap-1">
                      <span>Full Response</span>
                      <Badge variant="secondary" className="text-[9px]">
                        {reasoning.output_tokens} tokens
                      </Badge>
                    </div>
                    <pre className="text-[10px] bg-muted p-2 rounded overflow-auto max-h-40 whitespace-pre-wrap font-mono">
                      {reasoning.full_response}
                    </pre>
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}
      </div>
    </ScrollArea>
  );
}
