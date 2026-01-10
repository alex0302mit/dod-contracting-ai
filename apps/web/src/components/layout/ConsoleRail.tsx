/**
 * ConsoleRail Component
 * 
 * Collapsible right verification console panel with 5 tabs:
 * - Quality: Document quality metrics (Confidence, Compliance Risk, etc.)
 * - Issues: List of quality issues with severity badges
 * - Citations: Document citations with preview
 * - Fields: Fillable fields from guided flow
 * - Audit: Audit timeline for approvals
 * 
 * Features:
 * - Collapsible via toggle button
 * - Tabs switch between different data views
 * - Data populated via ConsoleRailContext
 * 
 * Dependencies:
 * - ConsoleRailContext for state and data
 * - Tabs, ScrollArea, Progress from shadcn/ui
 */

import { 
  PanelRightClose, 
  PanelRight,
  Gauge,
  AlertTriangle,
  Quote,
  FormInput,
  History,
  Loader2,
  CheckCircle,
  AlertCircle,
  XCircle,
  Info
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { ResizablePanel } from '@/components/ui/resizable';
import { useConsoleRail, type ConsoleRailTab } from '@/contexts/ConsoleRailContext';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

// Tab configuration
const tabs: { id: ConsoleRailTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'quality', label: 'Quality', icon: Gauge },
  { id: 'issues', label: 'Issues', icon: AlertTriangle },
  { id: 'citations', label: 'Citations', icon: Quote },
  { id: 'fields', label: 'Fields', icon: FormInput },
  { id: 'audit', label: 'Audit', icon: History },
];

/**
 * QualityTab - Displays quality metrics as instrument cards
 */
function QualityTab() {
  const { qualityData, isLoadingQuality } = useConsoleRail();
  
  if (isLoadingQuality) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  
  if (!qualityData) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Gauge className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No quality data available</p>
        <p className="text-xs mt-1">Generate or analyze a document to see metrics</p>
      </div>
    );
  }
  
  // Helper to get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-success';
    if (score >= 40) return 'text-warning';
    return 'text-destructive';
  };
  
  return (
    <div className="space-y-4 p-4">
      {/* Overall Score */}
      <Card className="border-0 shadow-sm bg-muted/30">
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Overall Quality</span>
            <span className={cn("text-2xl font-bold", getScoreColor(qualityData.score || 0))}>
              {qualityData.score || 0}%
            </span>
          </div>
          <Progress 
            value={qualityData.score || 0} 
            className="h-2"
          />
        </CardContent>
      </Card>
      
      {/* Breakdown metrics */}
      {qualityData.breakdown && (
        <div className="grid gap-3">
          {qualityData.breakdown.hallucination && (
            <MetricCard
              label="Hallucination Risk"
              value={100 - (qualityData.breakdown.hallucination.score || 0)}
              riskLevel={qualityData.breakdown.hallucination.risk_level}
              inverted
            />
          )}
          {qualityData.breakdown.compliance && (
            <MetricCard
              label="Compliance"
              value={qualityData.breakdown.compliance.score || 0}
              riskLevel={qualityData.breakdown.compliance.level === 'COMPLIANT' ? 'LOW' : 
                        qualityData.breakdown.compliance.level === 'MINOR ISSUES' ? 'MEDIUM' : 'HIGH'}
            />
          )}
          {qualityData.breakdown.citations && (
            <MetricCard
              label="Citation Coverage"
              value={qualityData.breakdown.citations.score || 0}
              subtitle={`${qualityData.breakdown.citations.valid || 0} valid / ${qualityData.breakdown.citations.invalid || 0} invalid`}
            />
          )}
          {qualityData.breakdown.completeness && (
            <MetricCard
              label="Completeness"
              value={qualityData.breakdown.completeness.score || 0}
              subtitle={`${qualityData.breakdown.completeness.word_count || 0} words`}
            />
          )}
        </div>
      )}
    </div>
  );
}

/**
 * MetricCard - Individual metric display
 */
interface MetricCardProps {
  label: string;
  value: number;
  riskLevel?: string;
  subtitle?: string;
  inverted?: boolean;
}

function MetricCard({ label, value, riskLevel, subtitle, inverted }: MetricCardProps) {
  const displayValue = inverted ? 100 - value : value;
  
  const getColor = () => {
    if (riskLevel) {
      if (riskLevel === 'LOW') return 'text-success';
      if (riskLevel === 'MEDIUM') return 'text-warning';
      return 'text-destructive';
    }
    if (displayValue >= 70) return 'text-success';
    if (displayValue >= 40) return 'text-warning';
    return 'text-destructive';
  };
  
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-card border">
      <div>
        <p className="text-sm font-medium">{label}</p>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </div>
      <div className="text-right">
        <span className={cn("text-lg font-semibold", getColor())}>
          {Math.round(displayValue)}%
        </span>
        {riskLevel && (
          <Badge variant="outline" className={cn("ml-2 text-xs", getColor())}>
            {riskLevel}
          </Badge>
        )}
      </div>
    </div>
  );
}

/**
 * IssuesTab - Displays quality issues with severity
 */
function IssuesTab() {
  const { qualityData } = useConsoleRail();
  
  const allIssues: { text: string; severity: 'error' | 'warning' | 'info' }[] = [];
  
  // Collect issues from breakdown
  if (qualityData?.breakdown) {
    const b = qualityData.breakdown;
    b.hallucination?.issues?.forEach(i => allIssues.push({ text: i, severity: 'error' }));
    b.compliance?.issues?.forEach(i => allIssues.push({ text: i, severity: 'error' }));
    b.vague_language?.issues?.forEach(i => allIssues.push({ text: i, severity: 'warning' }));
    b.citations?.issues?.forEach(i => allIssues.push({ text: i, severity: 'warning' }));
    b.completeness?.issues?.forEach(i => allIssues.push({ text: i, severity: 'info' }));
  }
  
  // Add top-level issues
  qualityData?.issues?.forEach(i => allIssues.push({ text: i, severity: 'warning' }));
  
  if (allIssues.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <CheckCircle className="h-8 w-8 mx-auto mb-2 text-success opacity-70" />
        <p className="text-sm">No issues found</p>
        <p className="text-xs mt-1">Document looks good!</p>
      </div>
    );
  }
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error': return <XCircle className="h-4 w-4 text-destructive" />;
      case 'warning': return <AlertCircle className="h-4 w-4 text-warning" />;
      default: return <Info className="h-4 w-4 text-info" />;
    }
  };
  
  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-2">
        {allIssues.map((issue, idx) => (
          <div 
            key={idx}
            className="flex items-start gap-2 p-3 rounded-lg bg-card border text-sm"
          >
            {getSeverityIcon(issue.severity)}
            <span className="flex-1">{issue.text}</span>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}

/**
 * CitationsTab - Displays document citations
 */
function CitationsTab() {
  const { citations } = useConsoleRail();
  
  if (citations.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Quote className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No citations</p>
        <p className="text-xs mt-1">Citations will appear here when viewing documents</p>
      </div>
    );
  }
  
  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-2">
        {citations.map((citation) => (
          <div 
            key={citation.id}
            className="p-3 rounded-lg bg-card border"
          >
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className="text-xs">
                [{citation.id}]
              </Badge>
              <span className="font-medium text-sm truncate">{citation.source}</span>
            </div>
            <p className="text-xs text-muted-foreground line-clamp-2">
              {citation.text}
            </p>
            {citation.sourceType && (
              <Badge variant="secondary" className="mt-2 text-xs">
                {citation.sourceType.replace('_', ' ')}
              </Badge>
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}

/**
 * FieldsTab - Displays fillable fields
 */
function FieldsTab() {
  // Placeholder for guided flow fields
  return (
    <div className="text-center py-8 text-muted-foreground">
      <FormInput className="h-8 w-8 mx-auto mb-2 opacity-50" />
      <p className="text-sm">No fields to fill</p>
      <p className="text-xs mt-1">Fillable fields will appear when editing documents</p>
    </div>
  );
}

/**
 * AuditTab - Displays audit timeline
 */
function AuditTab() {
  const { auditEvents } = useConsoleRail();
  
  if (auditEvents.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No audit history</p>
        <p className="text-xs mt-1">Events will appear here for approvals</p>
      </div>
    );
  }
  
  return (
    <ScrollArea className="h-full">
      <div className="p-4">
        <div className="relative pl-4 border-l-2 border-border space-y-4">
          {auditEvents.map((event) => (
            <div key={event.id} className="relative">
              {/* Timeline dot */}
              <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-primary border-2 border-background" />
              
              <div className="pb-2">
                <p className="font-medium text-sm">{event.action}</p>
                <p className="text-xs text-muted-foreground">
                  {event.performed_by_user?.name || event.performed_by}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                </p>
                {event.details && (
                  <p className="text-xs mt-1 text-muted-foreground">{event.details}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </ScrollArea>
  );
}

/**
 * ConsoleRail component - collapsible right panel
 */
export function ConsoleRail() {
  const { isOpen, activeTab, setActiveTab, toggleRail } = useConsoleRail();
  
  // When collapsed, render just a toggle handle
  if (!isOpen) {
    return (
      <div className="w-10 bg-card border-l border-border flex flex-col items-center py-2">
        <TooltipProvider>
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleRail}
                className="h-8 w-8 p-0"
              >
                <PanelRight className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">
              Open Verification Console
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    );
  }
  
  return (
    <ResizablePanel defaultSize={30} minSize={20} maxSize={45}>
      <div className="h-full bg-card border-l border-border flex flex-col">
        {/* Header */}
        <div className="h-10 px-3 flex items-center justify-between border-b border-border">
          <span className="text-sm font-medium">Verification Console</span>
          <TooltipProvider>
            <Tooltip delayDuration={0}>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleRail}
                  className="h-7 w-7 p-0"
                >
                  <PanelRightClose className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left">
                Close Verification Console
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        
        {/* Tabs */}
        <Tabs 
          value={activeTab} 
          onValueChange={(v) => setActiveTab(v as ConsoleRailTab)}
          className="flex-1 flex flex-col overflow-hidden"
        >
          <TabsList className="h-9 w-full justify-start rounded-none border-b border-border bg-transparent p-0 px-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className="h-8 px-2 data-[state=active]:bg-muted data-[state=active]:shadow-none rounded-md text-xs"
                >
                  <Icon className="h-3.5 w-3.5 mr-1" />
                  <span className="hidden xl:inline">{tab.label}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>
          
          <div className="flex-1 overflow-hidden">
            <TabsContent value="quality" className="h-full m-0">
              <ScrollArea className="h-full">
                <QualityTab />
              </ScrollArea>
            </TabsContent>
            <TabsContent value="issues" className="h-full m-0">
              <IssuesTab />
            </TabsContent>
            <TabsContent value="citations" className="h-full m-0">
              <CitationsTab />
            </TabsContent>
            <TabsContent value="fields" className="h-full m-0">
              <FieldsTab />
            </TabsContent>
            <TabsContent value="audit" className="h-full m-0">
              <AuditTab />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </ResizablePanel>
  );
}

export default ConsoleRail;
