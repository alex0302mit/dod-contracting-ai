/**
 * GroupedIssuesPanel - Issues organized by type with collapsible sections
 *
 * Groups issues by kind (TBD, Hallucination, Compliance, Vague, Other)
 * Each group has:
 * - Collapsible header with count
 * - Per-group "Fix All" button
 * - Individual issue cards with Fix and Dismiss buttons
 */

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { DocumentIssue } from "@/lib/editorUtils";
import { getIssueColors, IssueKind } from "@/lib/issueHighlightUtils";

interface GroupedIssuesPanelProps {
  issues: DocumentIssue[];
  onIssueClick: (issue: DocumentIssue) => void;
  onFixWithAI: (issue: DocumentIssue) => void;
  onFixGroup: (issueIds: string[]) => void;
  onDismiss: (issueId: string) => void;
  selectedIssueId?: string;
}

interface IssueGroup {
  id: string;
  label: string;
  color: string;
  issues: DocumentIssue[];
}

/**
 * Categorize issues into groups
 */
function groupIssues(issues: DocumentIssue[]): IssueGroup[] {
  const groups: Record<string, DocumentIssue[]> = {
    tbd: [],
    hallucination: [],
    compliance: [],
    vague: [],
    other: [],
  };

  issues.forEach((issue) => {
    if (issue.pattern?.toLowerCase().includes('tbd')) {
      groups.tbd.push(issue);
    } else if (issue.kind === 'hallucination') {
      groups.hallucination.push(issue);
    } else if (issue.kind === 'compliance') {
      groups.compliance.push(issue);
    } else if (issue.id.startsWith('vague')) {
      groups.vague.push(issue);
    } else {
      groups.other.push(issue);
    }
  });

  const result: IssueGroup[] = [];

  if (groups.tbd.length > 0) {
    result.push({
      id: 'tbd',
      label: 'TBD Placeholders',
      color: 'bg-red-500',
      issues: groups.tbd,
    });
  }

  if (groups.hallucination.length > 0) {
    result.push({
      id: 'hallucination',
      label: 'Hallucinations',
      color: 'bg-orange-500',
      issues: groups.hallucination,
    });
  }

  if (groups.compliance.length > 0) {
    result.push({
      id: 'compliance',
      label: 'Compliance',
      color: 'bg-purple-500',
      issues: groups.compliance,
    });
  }

  if (groups.vague.length > 0) {
    result.push({
      id: 'vague',
      label: 'Vague Language',
      color: 'bg-amber-500',
      issues: groups.vague,
    });
  }

  if (groups.other.length > 0) {
    result.push({
      id: 'other',
      label: 'Other Issues',
      color: 'bg-slate-500',
      issues: groups.other,
    });
  }

  return result;
}

export function GroupedIssuesPanel({
  issues,
  onIssueClick,
  onFixWithAI,
  onFixGroup,
  onDismiss,
  selectedIssueId,
}: GroupedIssuesPanelProps) {
  // Track which groups are expanded
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set(['tbd', 'hallucination', 'compliance', 'vague', 'other'])
  );

  const groups = useMemo(() => groupIssues(issues), [issues]);

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  if (issues.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {groups.map((group) => (
        <Collapsible
          key={group.id}
          open={expandedGroups.has(group.id)}
          onOpenChange={() => toggleGroup(group.id)}
        >
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors">
            <CollapsibleTrigger className="flex items-center gap-2 flex-1">
              {expandedGroups.has(group.id) ? (
                <ChevronDown className="h-4 w-4 text-slate-500" />
              ) : (
                <ChevronRight className="h-4 w-4 text-slate-500" />
              )}
              <div className={`w-2 h-2 rounded-full ${group.color}`} />
              <span className="text-sm font-medium text-slate-700">
                {group.label}
              </span>
              <span className="text-xs text-slate-500">({group.issues.length})</span>
            </CollapsibleTrigger>

            {group.issues.filter((i) => i.fix?.requiresAI).length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs gap-1 text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                onClick={(e) => {
                  e.stopPropagation();
                  onFixGroup(group.issues.map((i) => i.id));
                }}
              >
                <Sparkles className="h-3 w-3" />
                Fix All
              </Button>
            )}
          </div>

          <CollapsibleContent className="space-y-1 pt-1 pl-4">
            {group.issues.map((issue) => {
              const colors = getIssueColors(issue.kind as IssueKind);
              const isSelected = selectedIssueId === issue.id;

              return (
                <div
                  key={issue.id}
                  className={`
                    group relative p-2 rounded-lg cursor-pointer transition-all
                    ${isSelected
                      ? `ring-2 ring-offset-1 ${colors.ring} ${colors.bgLight}`
                      : `hover:bg-slate-50 border border-transparent hover:border-slate-200`
                    }
                  `}
                  onClick={() => onIssueClick(issue)}
                >
                  {/* Dismiss button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-1 right-1 h-5 w-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDismiss(issue.id);
                    }}
                    title="Dismiss"
                  >
                    <X className="h-3 w-3 text-slate-400" />
                  </Button>

                  <p className="text-xs text-slate-600 line-clamp-2 pr-6">
                    {issue.label}
                  </p>

                  {issue.fix && (
                    <Button
                      size="sm"
                      className="h-6 text-[10px] mt-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white gap-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        onFixWithAI(issue);
                      }}
                    >
                      <Sparkles className="h-2.5 w-2.5" />
                      Fix
                    </Button>
                  )}
                </div>
              );
            })}
          </CollapsibleContent>
        </Collapsible>
      ))}
    </div>
  );
}
