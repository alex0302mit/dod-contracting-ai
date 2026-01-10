/**
 * Guided Assistant Panel
 *
 * AI-powered field suggestions panel.
 * Fetches suggestions from backend and allows user to accept/reject.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Sparkles,
  Check,
  X,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { useGuidedFlow } from '@/contexts/GuidedFlowContext';
import type { AISuggestion } from '@/types/guidedFlow';

interface GuidedAssistantPanelProps {
  fieldId: string;
}

export function GuidedAssistantPanel({ fieldId }: GuidedAssistantPanelProps) {
  const { requestAISuggestion, updateFieldValue, getFieldValue } = useGuidedFlow();

  const [suggestion, setSuggestion] = useState<AISuggestion | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRequested, setHasRequested] = useState(false);

  // ========================================================================
  // Request Suggestion
  // ========================================================================

  const handleRequestSuggestion = async () => {
    setIsLoading(true);
    setError(null);
    setHasRequested(true);

    try {
      const result = await requestAISuggestion(fieldId);

      if (result) {
        setSuggestion(result);
      } else {
        setError('No suggestion available');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get suggestion');
    } finally {
      setIsLoading(false);
    }
  };

  // ========================================================================
  // Accept Suggestion
  // ========================================================================

  const handleAcceptSuggestion = async () => {
    if (!suggestion) return;

    await updateFieldValue(fieldId, suggestion.value);
    setSuggestion(null); // Clear suggestion after accepting
  };

  // ========================================================================
  // Reject Suggestion
  // ========================================================================

  const handleRejectSuggestion = () => {
    setSuggestion(null);
  };

  // ========================================================================
  // Get Confidence Badge Color
  // ========================================================================

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) {
      return { variant: 'default' as const, label: 'High Confidence', color: 'bg-green-500' };
    } else if (confidence >= 0.5) {
      return { variant: 'secondary' as const, label: 'Medium Confidence', color: 'bg-yellow-500' };
    } else {
      return { variant: 'outline' as const, label: 'Low Confidence', color: 'bg-orange-500' };
    }
  };

  // ========================================================================
  // Render
  // ========================================================================

  // Don't show if user already has a value
  const currentValue = getFieldValue(fieldId);
  if (currentValue && !suggestion) {
    return null;
  }

  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2 text-purple-900">
          <Sparkles className="h-4 w-4 text-purple-600" />
          AI Assistant
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* No Suggestion State */}
        {!suggestion && !isLoading && !hasRequested && (
          <div className="text-center py-4">
            <p className="text-sm text-slate-600 mb-3">
              Get a smart suggestion based on your previous contracts
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRequestSuggestion}
              className="w-full border-purple-300 hover:bg-purple-50"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Get AI Suggestion
            </Button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-6 ai-thinking-pulse">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-purple-600 mb-2" />
            <p className="text-sm text-slate-600">Analyzing your data...</p>
          </div>
        )}

        {/* Error State */}
        {error && !suggestion && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-red-900 font-medium">Unable to get suggestion</p>
                <p className="text-xs text-red-700 mt-1">{error}</p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRequestSuggestion}
              className="w-full mt-2 border-red-300 hover:bg-red-50"
            >
              Try Again
            </Button>
          </div>
        )}

        {/* Suggestion Available */}
        {suggestion && (
          <div className="ai-suggestion-appear">
            {/* Confidence Badge */}
            <div className="flex items-center justify-between mb-2">
              <Badge
                variant={getConfidenceBadge(suggestion.confidence).variant}
                className="text-xs"
              >
                <div
                  className={`h-2 w-2 rounded-full mr-1 ${getConfidenceBadge(suggestion.confidence).color}`}
                />
                {getConfidenceBadge(suggestion.confidence).label}
              </Badge>
              {suggestion.source && (
                <span className="text-xs text-slate-500">
                  {suggestion.source === 'previous_contract' && 'From previous contract'}
                  {suggestion.source === 'rag_knowledge' && 'From knowledge base'}
                  {suggestion.source === 'ai_generated' && 'AI generated'}
                </span>
              )}
            </div>

            {/* Suggested Value */}
            <div className="p-3 bg-white border-2 border-purple-300 rounded-lg mb-2">
              <p className="text-sm font-medium text-slate-900 mb-1">Suggested Value:</p>
              <p className="text-sm text-slate-700 font-mono bg-slate-50 p-2 rounded">
                {String(suggestion.value)}
              </p>
            </div>

            {/* Explanation */}
            {suggestion.explanation && (
              <p className="text-xs text-slate-600 mb-3 italic">
                {suggestion.explanation}
              </p>
            )}

            {/* Contract Reference */}
            {suggestion.contractId && (
              <p className="text-xs text-slate-500 mb-3">
                Used in contract: <span className="font-mono">{suggestion.contractId}</span>
              </p>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={handleAcceptSuggestion}
                className="flex-1 bg-purple-600 hover:bg-purple-700"
              >
                <Check className="h-4 w-4 mr-1" />
                Use This
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleRejectSuggestion}
                className="flex-1"
              >
                <X className="h-4 w-4 mr-1" />
                Dismiss
              </Button>
            </div>

            {/* Re-request Option */}
            <Button
              size="sm"
              variant="ghost"
              onClick={handleRequestSuggestion}
              className="w-full mt-2 text-xs"
            >
              <Sparkles className="h-3 w-3 mr-1" />
              Get Another Suggestion
            </Button>
          </div>
        )}

        {/* Already Requested but No Result */}
        {hasRequested && !isLoading && !suggestion && !error && (
          <div className="text-center py-4">
            <p className="text-sm text-slate-500 mb-2">
              No previous data found for this field
            </p>
            <p className="text-xs text-slate-400">
              You can fill it manually or try again later
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
