/**
 * DependencyGraph Component
 *
 * Phase 4: Visualizes document dependencies and generation order
 * Shows how documents reference each other and batch processing info
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { GitBranch, Clock, FileText, ArrowRight, CheckCircle2 } from 'lucide-react';

interface CollaborationMetadata {
  enabled: boolean;
  generation_order: string[];
  batch_count: number;
  batches: Array<{
    batch_number: number;
    documents: string[];
    generation_time_seconds: number;
  }>;
  cross_references: Array<{
    from: string;
    to: string;
    reference: string;
    created_at: string;
  }>;
  context_pool_stats: {
    document_count: number;
    total_words: number;
    total_characters: number;
    cross_reference_count: number;
    documents: string[];
  };
}

interface DependencyGraphProps {
  collaborationMetadata: CollaborationMetadata | null | undefined;
}

export function DependencyGraph({ collaborationMetadata }: DependencyGraphProps) {
  if (!collaborationMetadata || !collaborationMetadata.enabled) {
    return (
      <Card className="bg-gray-50">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            Document Dependencies
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">
            Collaboration mode not enabled for this generation.
          </p>
        </CardContent>
      </Card>
    );
  }

  const totalTime = collaborationMetadata.batches.reduce(
    (sum, batch) => sum + batch.generation_time_seconds,
    0
  );

  return (
    <div className="space-y-4">
      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-600">
              {collaborationMetadata.batch_count}
            </div>
            <p className="text-xs text-gray-600 mt-1">Generation Batches</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">
              {collaborationMetadata.context_pool_stats.document_count}
            </div>
            <p className="text-xs text-gray-600 mt-1">Documents Generated</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-purple-600">
              {collaborationMetadata.context_pool_stats.cross_reference_count}
            </div>
            <p className="text-xs text-gray-600 mt-1">Cross-References</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-orange-600">
              {totalTime.toFixed(1)}s
            </div>
            <p className="text-xs text-gray-600 mt-1">Total Time</p>
          </CardContent>
        </Card>
      </div>

      {/* Generation Flow */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            Generation Flow
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {collaborationMetadata.batches.map((batch, idx) => (
              <div key={batch.batch_number} className="relative">
                {/* Batch Header */}
                <div className="flex items-center gap-3 mb-3">
                  <Badge variant="outline" className="bg-blue-50 border-blue-200 text-blue-700">
                    Batch {batch.batch_number}
                  </Badge>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Clock className="h-3 w-3" />
                    {batch.generation_time_seconds.toFixed(1)}s
                  </div>
                  {batch.documents.length > 1 && (
                    <Badge variant="outline" className="bg-green-50 border-green-200 text-green-700 text-xs">
                      Parallel
                    </Badge>
                  )}
                </div>

                {/* Documents in Batch */}
                <div className="flex flex-wrap gap-2 ml-6">
                  {batch.documents.map((doc, docIdx) => (
                    <div
                      key={doc}
                      className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-sm"
                    >
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{doc}</div>
                        <div className="text-xs text-gray-500">
                          Step {collaborationMetadata.generation_order.indexOf(doc) + 1}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Arrow to next batch */}
                {idx < collaborationMetadata.batches.length - 1 && (
                  <div className="flex justify-center my-3">
                    <ArrowRight className="h-5 w-5 text-gray-400" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cross-References */}
      {collaborationMetadata.cross_references.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Cross-References ({collaborationMetadata.cross_references.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {collaborationMetadata.cross_references.map((ref, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <ArrowRight className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm">
                      <span className="font-medium text-gray-900">{ref.from}</span>
                      <span className="text-gray-500"> references </span>
                      <span className="font-medium text-gray-900">{ref.to}</span>
                    </div>
                    <div className="text-xs text-gray-600 mt-1">{ref.reference}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Context Pool Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Shared Context Pool
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {collaborationMetadata.context_pool_stats.total_words.toLocaleString()}
              </div>
              <p className="text-xs text-gray-600 mt-1">Total Words Shared</p>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {(collaborationMetadata.context_pool_stats.total_characters / 1024).toFixed(1)}KB
              </div>
              <p className="text-xs text-gray-600 mt-1">Total Content Size</p>
            </div>
          </div>

          <div className="mt-4">
            <p className="text-xs font-medium text-gray-700 mb-2">Documents in Context Pool:</p>
            <div className="flex flex-wrap gap-2">
              {collaborationMetadata.context_pool_stats.documents.map((doc) => (
                <Badge key={doc} variant="secondary" className="text-xs">
                  {doc}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
