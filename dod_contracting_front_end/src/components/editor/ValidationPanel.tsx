/**
 * Validation Panel Component
 *
 * Displays validation issues with severity indicators and auto-fix options
 */

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  Wrench,
  Filter,
  Zap,
  Shield,
  FileText,
  Layers,
  PenTool,
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ValidationResult, ValidationIssue, ValidationSeverity } from '@/lib/ValidationEngine';

interface ValidationPanelProps {
  validationResult: ValidationResult | null;
  onApplyFix?: (issue: ValidationIssue) => void;
  onApplyAllFixes?: () => void;
}

const SEVERITY_CONFIG = {
  error: {
    icon: AlertCircle,
    color: 'red',
    label: 'Error',
    variant: 'destructive' as const,
  },
  warning: {
    icon: AlertTriangle,
    color: 'orange',
    label: 'Warning',
    variant: 'secondary' as const,
  },
  info: {
    icon: Info,
    color: 'blue',
    label: 'Info',
    variant: 'default' as const,
  },
};

const CATEGORY_CONFIG = {
  compliance: { icon: Shield, label: 'Compliance', color: 'purple' },
  format: { icon: FileText, label: 'Format', color: 'blue' },
  content: { icon: PenTool, label: 'Content', color: 'green' },
  structure: { icon: Layers, label: 'Structure', color: 'orange' },
  style: { icon: Zap, label: 'Style', color: 'yellow' },
};

export function ValidationPanel({
  validationResult,
  onApplyFix,
  onApplyAllFixes,
}: ValidationPanelProps) {
  const [severityFilter, setSeverityFilter] = useState<ValidationSeverity | 'all'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  // Filter issues
  const filteredIssues = useMemo(() => {
    if (!validationResult) return [];

    let filtered = validationResult.issues;

    if (severityFilter !== 'all') {
      filtered = filtered.filter((issue) => issue.severity === severityFilter);
    }

    if (categoryFilter !== 'all') {
      filtered = filtered.filter((issue) => issue.category === categoryFilter);
    }

    return filtered;
  }, [validationResult, severityFilter, categoryFilter]);

  // Count fixable issues
  const fixableCount = useMemo(() => {
    return validationResult?.issues.filter((issue) => issue.autoFix !== undefined).length || 0;
  }, [validationResult]);

  if (!validationResult) {
    return (
      <div className="p-4 text-center text-muted-foreground text-sm">
        No validation results available
      </div>
    );
  }

  const { score, errorCount, warningCount, infoCount, isValid } = validationResult;

  return (
    <div className="space-y-4">
      {/* Validation Score */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm flex items-center gap-2">
                {isValid ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                )}
                Validation Score
              </CardTitle>
              <CardDescription className="text-xs mt-1">
                {isValid ? 'All checks passed' : 'Issues found'}
              </CardDescription>
            </div>
            <Badge
              variant={score >= 85 ? 'default' : score >= 70 ? 'secondary' : 'destructive'}
              className="text-lg font-bold px-3 py-1"
            >
              {Math.round(score)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <Progress value={score} className="h-2" />

          {/* Issue Counts */}
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center p-2 rounded-lg bg-red-50 border border-red-200">
              <div className="text-2xl font-bold text-red-700">{errorCount}</div>
              <div className="text-[10px] text-red-600 uppercase font-medium">Errors</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-orange-50 border border-orange-200">
              <div className="text-2xl font-bold text-orange-700">{warningCount}</div>
              <div className="text-[10px] text-orange-600 uppercase font-medium">Warnings</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-blue-50 border border-blue-200">
              <div className="text-2xl font-bold text-blue-700">{infoCount}</div>
              <div className="text-[10px] text-blue-600 uppercase font-medium">Info</div>
            </div>
          </div>

          {/* Auto-Fix All Button */}
          {fixableCount > 0 && onApplyAllFixes && (
            <>
              <Separator />
              <Button
                size="sm"
                className="w-full gap-2"
                variant="outline"
                onClick={onApplyAllFixes}
              >
                <Wrench className="h-4 w-4" />
                Auto-Fix {fixableCount} Issue{fixableCount > 1 ? 's' : ''}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Severity Filter */}
          <div className="space-y-2">
            <label className="text-xs font-medium">Severity</label>
            <Select value={severityFilter} onValueChange={(v) => setSeverityFilter(v as any)}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="error">Errors Only</SelectItem>
                <SelectItem value="warning">Warnings Only</SelectItem>
                <SelectItem value="info">Info Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Category Filter */}
          <div className="space-y-2">
            <label className="text-xs font-medium">Category</label>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="compliance">Compliance</SelectItem>
                <SelectItem value="format">Format</SelectItem>
                <SelectItem value="content">Content</SelectItem>
                <SelectItem value="structure">Structure</SelectItem>
                <SelectItem value="style">Style</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Issues List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            Issues ({filteredIssues.length})
          </CardTitle>
          <CardDescription className="text-xs">
            {filteredIssues.length === 0
              ? 'No issues match your filters'
              : 'Click to view details and apply fixes'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-2">
              {filteredIssues.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-xs">
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  No validation issues found
                </div>
              ) : (
                filteredIssues.map((issue) => (
                  <IssueCard
                    key={issue.id}
                    issue={issue}
                    onApplyFix={onApplyFix}
                  />
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

function IssueCard({
  issue,
  onApplyFix,
}: {
  issue: ValidationIssue;
  onApplyFix?: (issue: ValidationIssue) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const severityConfig = SEVERITY_CONFIG[issue.severity];
  const categoryConfig = CATEGORY_CONFIG[issue.category];

  const SeverityIcon = severityConfig.icon;
  const CategoryIcon = categoryConfig.icon;

  return (
    <div
      className={`border rounded-lg p-3 bg-${severityConfig.color}-50/50 border-${severityConfig.color}-200 hover:shadow-sm transition-all cursor-pointer`}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Issue Header */}
      <div className="flex items-start gap-2">
        <SeverityIcon className={`h-4 w-4 text-${severityConfig.color}-600 flex-shrink-0 mt-0.5`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="text-xs font-medium text-gray-900 flex-1">{issue.message}</p>
            <div className="flex gap-1 flex-shrink-0">
              <Badge variant={severityConfig.variant} className="text-[9px] h-4 px-1">
                {severityConfig.label}
              </Badge>
              <Badge variant="outline" className="text-[9px] h-4 px-1">
                <CategoryIcon className="h-2 w-2 mr-0.5" />
                {categoryConfig.label}
              </Badge>
            </div>
          </div>

          {/* Issue Location */}
          {issue.location && (
            <p className="text-[10px] text-muted-foreground font-mono mb-2 truncate">
              "{issue.location.text}"
            </p>
          )}

          {/* Expanded Content */}
          {expanded && issue.description && (
            <p className="text-xs text-gray-700 mb-2 mt-2 border-t pt-2">
              {issue.description}
            </p>
          )}

          {/* Auto-Fix Button */}
          {issue.autoFix && onApplyFix && (
            <Button
              size="sm"
              variant="outline"
              className={`h-6 text-[10px] w-full gap-1 bg-${severityConfig.color}-100 hover:bg-${severityConfig.color}-200 border-${severityConfig.color}-300`}
              onClick={(e) => {
                e.stopPropagation();
                onApplyFix(issue);
              }}
            >
              <Wrench className="h-3 w-3" />
              {issue.autoFix.label}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
