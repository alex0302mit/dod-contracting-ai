/**
 * Comparison Viewer Component
 *
 * Side-by-side view of multiple agent-generated variants
 * Part of Phase 6: Advanced Agent Comparison & Selection
 */

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Trophy,
  Zap,
  FileText,
  Quote,
  Clock,
} from 'lucide-react';

interface AgentVariant {
  variant_id: string;
  variant_name: string;
  model: string;
  content: string;
  quality_score: number;
  generation_time: number;
  word_count: number;
  citations_count: number;
  metadata: Record<string, any>;
  generated_at: string;
}

interface ComparisonData {
  task_id: string;
  document_name: string;
  status: string;
  results: AgentVariant[];
  created_at: string;
  completed_at?: string;
}

interface ComparisonViewerProps {
  comparisonData: ComparisonData;
  onSelectWinner: (variantId: string) => void;
}

export function ComparisonViewer({ comparisonData, onSelectWinner }: ComparisonViewerProps) {
  const [sortBy, setSortBy] = useState<'quality' | 'speed' | 'length' | 'citations'>('quality');
  const [viewMode, setViewMode] = useState<'sidebyside' | 'stacked' | 'metrics'>('sidebyside');
  const [selectedVariants, setSelectedVariants] = useState<string[]>([]);

  // Sort variants based on selected criteria
  const sortedVariants = useMemo(() => {
    const sorted = [...comparisonData.results];

    switch (sortBy) {
      case 'quality':
        sorted.sort((a, b) => b.quality_score - a.quality_score);
        break;
      case 'speed':
        sorted.sort((a, b) => a.generation_time - b.generation_time);
        break;
      case 'length':
        sorted.sort((a, b) => b.word_count - a.word_count);
        break;
      case 'citations':
        sorted.sort((a, b) => b.citations_count - a.citations_count);
        break;
    }

    return sorted;
  }, [comparisonData.results, sortBy]);

  // Get winner for each criterion
  const winners = useMemo(() => {
    const results = comparisonData.results;
    return {
      quality: results.reduce((max, v) => v.quality_score > max.quality_score ? v : max),
      speed: results.reduce((min, v) => v.generation_time < min.generation_time ? v : min),
      length: results.reduce((max, v) => v.word_count > max.word_count ? v : max),
      citations: results.reduce((max, v) => v.citations_count > max.citations_count ? v : max),
    };
  }, [comparisonData.results]);

  const toggleVariantSelection = (variantId: string) => {
    if (selectedVariants.includes(variantId)) {
      setSelectedVariants(selectedVariants.filter(id => id !== variantId));
    } else {
      setSelectedVariants([...selectedVariants, variantId]);
    }
  };

  const getModelBadgeColor = (model: string) => {
    if (model.includes('opus')) return 'bg-purple-600';
    if (model.includes('sonnet')) return 'bg-blue-600';
    if (model.includes('haiku')) return 'bg-green-600';
    return 'bg-gray-600';
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-600" />
                Agent Comparison: {comparisonData.document_name}
              </CardTitle>
              <CardDescription>
                Compare {comparisonData.results.length} variant{comparisonData.results.length !== 1 ? 's' : ''} generated with different agents/models
              </CardDescription>
            </div>
            <Badge variant={comparisonData.status === 'completed' ? 'default' : 'secondary'}>
              {comparisonData.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 flex-wrap">
            {/* Sort Criteria */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Sort by:</span>
              <Select value={sortBy} onValueChange={(v: any) => setSortBy(v)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="quality">Quality Score</SelectItem>
                  <SelectItem value="speed">Generation Speed</SelectItem>
                  <SelectItem value="length">Word Count</SelectItem>
                  <SelectItem value="citations">Citations</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* View Mode */}
            <Tabs value={viewMode} onValueChange={(v: any) => setViewMode(v)} className="ml-auto">
              <TabsList>
                <TabsTrigger value="sidebyside" className="gap-1">
                  <FileText className="h-4 w-4" />
                  Side-by-Side
                </TabsTrigger>
                <TabsTrigger value="stacked" className="gap-1">
                  Stacked
                </TabsTrigger>
                <TabsTrigger value="metrics" className="gap-1">
                  Metrics Only
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardContent>
      </Card>

      {/* Winners Dashboard */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">{Math.round(winners.quality.quality_score)}</div>
                <div className="text-xs text-muted-foreground">Best Quality</div>
              </div>
              <Trophy className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="mt-2 text-xs font-medium truncate">{winners.quality.variant_name}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">{winners.speed.generation_time.toFixed(1)}s</div>
                <div className="text-xs text-muted-foreground">Fastest</div>
              </div>
              <Zap className="h-8 w-8 text-green-600" />
            </div>
            <div className="mt-2 text-xs font-medium truncate">{winners.speed.variant_name}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">{winners.length.word_count}</div>
                <div className="text-xs text-muted-foreground">Most Detailed</div>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
            <div className="mt-2 text-xs font-medium truncate">{winners.length.variant_name}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">{winners.citations.citations_count}</div>
                <div className="text-xs text-muted-foreground">Best Citations</div>
              </div>
              <Quote className="h-8 w-8 text-purple-600" />
            </div>
            <div className="mt-2 text-xs font-medium truncate">{winners.citations.variant_name}</div>
          </CardContent>
        </Card>
      </div>

      {/* Variant Comparison */}
      {viewMode === 'metrics' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Metrics Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sortedVariants.map((variant, index) => (
                <div
                  key={variant.variant_id}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition cursor-pointer"
                  onClick={() => toggleVariantSelection(variant.variant_id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {index === 0 && (
                        <Trophy className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                      )}
                      <div>
                        <div className="font-semibold">{variant.variant_name}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          <Badge className={getModelBadgeColor(variant.model)}>
                            {variant.model}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectWinner(variant.variant_id);
                      }}
                    >
                      Select Winner
                    </Button>
                  </div>

                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Quality</div>
                      <div className="flex items-center gap-2">
                        <Progress value={variant.quality_score} className="h-2 flex-1" />
                        <span className="text-sm font-medium w-10 text-right">
                          {Math.round(variant.quality_score)}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Speed</div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">
                          {variant.generation_time.toFixed(2)}s
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Words</div>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">{variant.word_count}</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Citations</div>
                      <div className="flex items-center gap-2">
                        <Quote className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">{variant.citations_count}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {viewMode === 'sidebyside' && (
        <div className="grid grid-cols-2 gap-4">
          {sortedVariants.slice(0, 2).map((variant, index) => (
            <VariantCard
              key={variant.variant_id}
              variant={variant}
              rank={index + 1}
              isWinner={index === 0}
              onSelect={() => onSelectWinner(variant.variant_id)}
              getModelBadgeColor={getModelBadgeColor}
            />
          ))}
        </div>
      )}

      {viewMode === 'stacked' && (
        <div className="space-y-4">
          {sortedVariants.map((variant, index) => (
            <VariantCard
              key={variant.variant_id}
              variant={variant}
              rank={index + 1}
              isWinner={index === 0}
              onSelect={() => onSelectWinner(variant.variant_id)}
              getModelBadgeColor={getModelBadgeColor}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function VariantCard({
  variant,
  rank,
  isWinner,
  onSelect,
  getModelBadgeColor,
}: {
  variant: AgentVariant;
  rank: number;
  isWinner: boolean;
  onSelect: () => void;
  getModelBadgeColor: (model: string) => string;
}) {
  return (
    <Card className={isWinner ? 'border-yellow-500 border-2' : ''}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isWinner && <Trophy className="h-5 w-5 text-yellow-600" />}
            <div>
              <CardTitle className="text-base">{variant.variant_name}</CardTitle>
              <CardDescription className="mt-1">
                <Badge className={getModelBadgeColor(variant.model)}>
                  {variant.model}
                </Badge>
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">Rank #{rank}</Badge>
            <Button size="sm" onClick={onSelect}>
              {isWinner ? 'Use Winner' : 'Select'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Metrics */}
          <div className="grid grid-cols-2 gap-4 pb-4 border-b">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Quality Score</div>
              <div className="text-2xl font-bold">{Math.round(variant.quality_score)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Generation Time</div>
              <div className="text-2xl font-bold">{variant.generation_time.toFixed(2)}s</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Word Count</div>
              <div className="text-lg font-semibold">{variant.word_count}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Citations</div>
              <div className="text-lg font-semibold">{variant.citations_count}</div>
            </div>
          </div>

          {/* Content Preview */}
          <div>
            <div className="text-sm font-medium mb-2">Content Preview</div>
            <ScrollArea className="h-64 border rounded-lg p-3 bg-muted/30">
              <div className="prose prose-sm max-w-none">
                <div dangerouslySetInnerHTML={{ __html: variant.content.slice(0, 2000) }} />
                {variant.content.length > 2000 && (
                  <div className="text-muted-foreground italic">... (truncated)</div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
