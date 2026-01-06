/**
 * Phase Info Component
 *
 * Displays procurement phase detection results, recommendations, and completeness
 */

import { CheckCircle2, AlertTriangle, Info, TrendingUp, Target } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";

interface PhaseAnalysis {
  phase_detection_enabled: boolean;
  primary_phase?: string;
  confidence?: number;
  mixed_phases?: boolean;
  phase_breakdown?: Record<string, number>;
  warnings?: string[];
  recommendations?: string[];
  phase_info?: {
    name: string;
    description: string;
    required_documents: string[];
  };
  validation?: {
    is_complete: boolean;
    completeness_percentage: number;
    missing_required: string[];
    missing_recommended: string[];
  };
}

interface PhaseInfoProps {
  analysis: PhaseAnalysis | null;
  loading?: boolean;
}

const phaseColors: Record<string, { bg: string; border: string; text: string }> = {
  pre_solicitation: {
    bg: "bg-purple-50",
    border: "border-purple-200",
    text: "text-purple-700"
  },
  solicitation: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-700"
  },
  post_solicitation: {
    bg: "bg-green-50",
    border: "border-green-200",
    text: "text-green-700"
  },
  award: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-700"
  }
};

const phaseDisplayNames: Record<string, string> = {
  pre_solicitation: "Pre-Solicitation",
  solicitation: "Solicitation",
  post_solicitation: "Post-Solicitation",
  award: "Award"
};

export function PhaseInfo({ analysis, loading }: PhaseInfoProps) {
  if (loading) {
    return (
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 animate-pulse" />
            Analyzing Phase...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-200 rounded w-3/4"></div>
            <div className="h-4 bg-slate-200 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analysis || !analysis.phase_detection_enabled) {
    return null;
  }

  const { primary_phase, confidence, mixed_phases, warnings, recommendations, phase_info, validation } = analysis;

  if (!primary_phase) {
    return null;
  }

  const phaseStyle = phaseColors[primary_phase] || phaseColors.solicitation;
  const phaseName = phaseDisplayNames[primary_phase] || primary_phase;

  return (
    <div className="space-y-4">
      {/* Primary Phase Card */}
      <Card className={`${phaseStyle.border} ${phaseStyle.bg} border-2`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Detected Phase: {phaseName}
              </CardTitle>
              <CardDescription className="mt-1">
                {phase_info?.description}
              </CardDescription>
            </div>
            <Badge variant={confidence && confidence >= 0.8 ? "default" : "secondary"} className="ml-2">
              {confidence ? `${Math.round(confidence * 100)}% confidence` : 'Detected'}
            </Badge>
          </div>
        </CardHeader>

        {/* Completeness Indicator */}
        {validation && (
          <CardContent className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Package Completeness</span>
                <span className={`text-sm font-bold ${
                  validation.is_complete ? 'text-green-600' : 'text-amber-600'
                }`}>
                  {Math.round(validation.completeness_percentage)}%
                </span>
              </div>
              <Progress
                value={validation.completeness_percentage}
                className="h-2"
              />

              {validation.is_complete ? (
                <div className="flex items-center gap-2 mt-3 text-sm text-green-600">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Complete {phaseName} package selected</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 mt-3 text-sm text-amber-600">
                  <Info className="h-4 w-4" />
                  <span>
                    {validation.missing_required.length} required document{validation.missing_required.length !== 1 ? 's' : ''} missing
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <Alert variant="destructive" className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-900">Warnings</AlertTitle>
          <AlertDescription className="text-amber-800">
            <ul className="list-disc list-inside space-y-1 mt-2">
              {warnings.map((warning, idx) => (
                <li key={idx}>{warning}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {recommendations.slice(0, 5).map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
            {recommendations.length > 5 && (
              <p className="text-xs text-muted-foreground mt-3">
                + {recommendations.length - 5} more recommendation{recommendations.length - 5 !== 1 ? 's' : ''}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Missing Documents (if incomplete) */}
      {validation && !validation.is_complete && validation.missing_required.length > 0 && (
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-base">Missing Required Documents</CardTitle>
            <CardDescription>
              These documents are required for a complete {phaseName} package
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {validation.missing_required.slice(0, 8).map((doc, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {doc}
                </Badge>
              ))}
              {validation.missing_required.length > 8 && (
                <Badge variant="outline" className="text-xs">
                  +{validation.missing_required.length - 8} more
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
