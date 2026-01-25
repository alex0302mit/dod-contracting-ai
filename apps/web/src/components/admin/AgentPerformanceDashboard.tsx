/**
 * AgentPerformanceDashboard Component
 *
 * Admin-only dashboard displaying agent performance based on user feedback.
 * Shows aggregated thumbs up/down ratings for each AI agent.
 *
 * Features:
 * - Time period filter (7, 30, 90 days)
 * - Performance table with ratings and percentages
 * - Trend indicators for agent performance
 * - Expandable comments view for each agent
 * - Loading and error states
 *
 * Dependencies:
 * - feedbackApi for data fetching
 * - useAuth for admin access check
 */

import { useState, useEffect, useCallback } from 'react';
import {
  ThumbsUp,
  ThumbsDown,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Bot,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { feedbackApi, AgentPerformanceStats, FeedbackEntry } from '@/services/api';
import { toast } from 'sonner';

// Date range options for the filter
const DATE_RANGE_OPTIONS = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
];

/**
 * Format agent name for display by removing "Agent" suffix
 * and adding spaces before capital letters
 */
function formatAgentName(name: string): string {
  return name
    .replace(/Agent$/, '')
    .replace(/([A-Z])/g, ' $1')
    .trim();
}

/**
 * Get trend icon and color based on rating percentage
 */
function getTrendIndicator(percentage: number) {
  if (percentage >= 85) {
    return {
      icon: <TrendingUp className="h-4 w-4" />,
      color: 'text-green-600',
      label: 'Excellent',
    };
  }
  if (percentage >= 70) {
    return {
      icon: <Minus className="h-4 w-4" />,
      color: 'text-slate-500',
      label: 'Average',
    };
  }
  return {
    icon: <TrendingDown className="h-4 w-4" />,
    color: 'text-red-600',
    label: 'Needs improvement',
  };
}

/**
 * Get badge variant based on rating percentage
 */
function getRatingBadgeVariant(percentage: number): 'default' | 'secondary' | 'destructive' {
  if (percentage >= 85) return 'default';
  if (percentage >= 70) return 'secondary';
  return 'destructive';
}

interface AgentCommentsProps {
  agentName: string;
  isOpen: boolean;
}

/**
 * Expandable section showing feedback comments for an agent
 */
function AgentComments({ agentName, isOpen }: AgentCommentsProps) {
  const [comments, setComments] = useState<FeedbackEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    if (isOpen) {
      loadComments(1);
    }
  }, [isOpen, agentName]);

  const loadComments = async (pageNum: number) => {
    setLoading(true);
    try {
      const result = await feedbackApi.getAgentComments(agentName, pageNum);
      if (pageNum === 1) {
        setComments(result.comments);
      } else {
        setComments((prev) => [...prev, ...result.comments]);
      }
      setTotal(result.total);
      setHasMore(pageNum < result.pages);
      setPage(pageNum);
    } catch (error) {
      console.error('Failed to load comments:', error);
      toast.error('Failed to load feedback comments');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="bg-slate-50 p-4 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">
          Feedback Comments ({total})
        </span>
      </div>

      {loading && comments.length === 0 ? (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
        </div>
      ) : comments.length === 0 ? (
        <p className="text-sm text-slate-500 text-center py-4">
          No comments yet for this agent.
        </p>
      ) : (
        <div className="space-y-2">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="bg-white rounded-md p-3 border border-slate-200"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-slate-700 flex-1">"{comment.comment}"</p>
                <Badge
                  variant={comment.rating === 'positive' ? 'default' : 'destructive'}
                  className="shrink-0"
                >
                  {comment.rating === 'positive' ? (
                    <ThumbsUp className="h-3 w-3" />
                  ) : (
                    <ThumbsDown className="h-3 w-3" />
                  )}
                </Badge>
              </div>
              <div className="mt-2 text-xs text-slate-500">
                {comment.section_name && (
                  <span className="mr-2">Section: {comment.section_name}</span>
                )}
                <span>
                  {new Date(comment.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}

          {hasMore && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => loadComments(page + 1)}
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              Load More
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Main AgentPerformanceDashboard component
 */
export function AgentPerformanceDashboard() {
  const [days, setDays] = useState('30');
  const [agents, setAgents] = useState<AgentPerformanceStats[]>([]);
  const [totalFeedback, setTotalFeedback] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await feedbackApi.getAgentPerformance(parseInt(days));
      setAgents(result.agents);
      setTotalFeedback(result.total_feedback);
    } catch (err) {
      console.error('Failed to load agent performance:', err);
      setError('Failed to load agent performance data');
      toast.error('Failed to load agent performance');
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleAgentExpand = (agentName: string) => {
    setExpandedAgent(expandedAgent === agentName ? null : agentName);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Agent Performance
          </CardTitle>
          <CardDescription>
            User feedback ratings for AI-generated content
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Select value={days} onValueChange={setDays}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DATE_RANGE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-center py-8">
            <p className="text-red-600">{error}</p>
            <Button variant="outline" className="mt-4" onClick={loadData}>
              Try Again
            </Button>
          </div>
        ) : loading && agents.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          </div>
        ) : agents.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <MessageSquare className="h-12 w-12 mx-auto mb-4 text-slate-300" />
            <p className="text-lg font-medium">No feedback data yet</p>
            <p className="text-sm mt-1">
              Feedback will appear here once users rate generated content.
            </p>
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead className="text-center w-20">
                    <div className="flex items-center justify-center gap-1">
                      <ThumbsUp className="h-3.5 w-3.5 text-green-600" />
                    </div>
                  </TableHead>
                  <TableHead className="text-center w-20">
                    <div className="flex items-center justify-center gap-1">
                      <ThumbsDown className="h-3.5 w-3.5 text-red-600" />
                    </div>
                  </TableHead>
                  <TableHead className="text-center w-24">Rating</TableHead>
                  <TableHead className="text-center w-24">Trend</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.map((agent) => {
                  const trend = getTrendIndicator(agent.rating_percentage);
                  const isExpanded = expandedAgent === agent.name;

                  return (
                    <Collapsible
                      key={agent.name}
                      open={isExpanded}
                      onOpenChange={() => toggleAgentExpand(agent.name)}
                      asChild
                    >
                      <>
                        <TableRow className="group">
                          <TableCell className="font-medium">
                            {formatAgentName(agent.name)}
                          </TableCell>
                          <TableCell className="text-center text-green-600 font-medium">
                            {agent.positive_count}
                          </TableCell>
                          <TableCell className="text-center text-red-600 font-medium">
                            {agent.negative_count}
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge variant={getRatingBadgeVariant(agent.rating_percentage)}>
                              {agent.rating_percentage}%
                            </Badge>
                          </TableCell>
                          <TableCell className="text-center">
                            <div
                              className={`flex items-center justify-center gap-1 ${trend.color}`}
                              title={trend.label}
                            >
                              {trend.icon}
                            </div>
                          </TableCell>
                          <TableCell>
                            <CollapsibleTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                              >
                                {isExpanded ? (
                                  <ChevronUp className="h-4 w-4" />
                                ) : (
                                  <ChevronDown className="h-4 w-4" />
                                )}
                              </Button>
                            </CollapsibleTrigger>
                          </TableCell>
                        </TableRow>
                        <CollapsibleContent asChild>
                          <tr>
                            <td colSpan={6} className="p-0">
                              <div className="px-4 pb-4">
                                <AgentComments
                                  agentName={agent.name}
                                  isOpen={isExpanded}
                                />
                              </div>
                            </td>
                          </tr>
                        </CollapsibleContent>
                      </>
                    </Collapsible>
                  );
                })}
              </TableBody>
            </Table>

            <div className="mt-4 pt-4 border-t text-sm text-slate-500 text-right">
              Total feedback: {totalFeedback} ratings
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
