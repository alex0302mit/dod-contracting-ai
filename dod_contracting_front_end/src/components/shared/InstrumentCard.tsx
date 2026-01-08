/**
 * InstrumentCard Component
 * 
 * Displays a metric in "instrument" style with:
 * - Label (e.g., "Confidence", "Compliance Risk")
 * - Numeric value (0-100)
 * - Optional progress bar
 * - Color based on value thresholds
 * 
 * Used for quality metrics in ConsoleRail and Overview screens.
 * 
 * Dependencies:
 * - Card from shadcn/ui
 * - Progress component
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

// Risk level type
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

interface InstrumentCardProps {
  /** Metric label */
  label: string;
  /** Value (0-100 for percentages, or any number for counts) */
  value: number;
  /** Optional risk level override */
  riskLevel?: RiskLevel;
  /** Whether to show progress bar */
  showProgress?: boolean;
  /** Whether to show % suffix (default: true for percentages, false for counts) */
  showPercent?: boolean;
  /** Subtitle text */
  subtitle?: string;
  /** Icon to display */
  icon?: React.ReactNode;
  /** Additional className */
  className?: string;
  /** Compact mode for smaller cards */
  compact?: boolean;
  /** Whether higher values are worse (inverted coloring) */
  inverted?: boolean;
}

/**
 * Get color class based on value and thresholds
 */
function getValueColor(value: number, inverted: boolean = false): string {
  const effectiveValue = inverted ? 100 - value : value;
  if (effectiveValue >= 70) return 'text-success';
  if (effectiveValue >= 40) return 'text-warning';
  return 'text-destructive';
}

/**
 * Get progress bar color based on value
 */
function getProgressColor(value: number, inverted: boolean = false): string {
  const effectiveValue = inverted ? 100 - value : value;
  if (effectiveValue >= 70) return '[&>div]:bg-success';
  if (effectiveValue >= 40) return '[&>div]:bg-warning';
  return '[&>div]:bg-destructive';
}

/**
 * Get color based on risk level
 */
function getRiskLevelColor(level: RiskLevel): string {
  switch (level) {
    case 'LOW': return 'text-success';
    case 'MEDIUM': return 'text-warning';
    case 'HIGH': return 'text-destructive';
    default: return 'text-muted-foreground';
  }
}

/**
 * InstrumentCard displays a metric with visual indicators
 */
export function InstrumentCard({ 
  label,
  value,
  riskLevel,
  showProgress = true,
  showPercent = true,
  subtitle,
  icon,
  className,
  compact = false,
  inverted = false,
}: InstrumentCardProps) {
  // For percentages, clamp between 0 and 100; for counts, just round
  const displayValue = showPercent 
    ? Math.max(0, Math.min(100, Math.round(value)))
    : Math.round(value);
  
  // For color calculation, use clamped percentage value
  const clampedValue = Math.max(0, Math.min(100, Math.round(value)));
  
  // Determine color based on risk level or value
  const valueColor = riskLevel 
    ? getRiskLevelColor(riskLevel) 
    : getValueColor(clampedValue, inverted);
  
  if (compact) {
    return (
      <div className={cn(
        "flex items-center justify-between p-3 rounded-lg bg-card border",
        className
      )}>
        <div className="flex items-center gap-2">
          {icon && <div className="text-muted-foreground">{icon}</div>}
          <div>
            <p className="text-sm font-medium">{label}</p>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          </div>
        </div>
        <div className="text-right">
          <span className={cn("text-lg font-semibold", valueColor)}>
            {displayValue}{showPercent && '%'}
          </span>
          {riskLevel && (
            <p className={cn("text-xs", valueColor)}>{riskLevel}</p>
          )}
        </div>
      </div>
    );
  }
  
  return (
    <Card className={cn("border shadow-sm", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            {icon}
            {label}
          </CardTitle>
          {riskLevel && (
            <span className={cn("text-xs font-medium", valueColor)}>
              {riskLevel}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className={cn("text-2xl font-bold", valueColor)}>
              {displayValue}{showPercent && '%'}
            </span>
            {subtitle && (
              <span className="text-xs text-muted-foreground">{subtitle}</span>
            )}
          </div>
          {showProgress && (
            <Progress 
              value={clampedValue} 
              className={cn("h-1.5", getProgressColor(clampedValue, inverted))}
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * InstrumentCardGrid - Grid layout for multiple instrument cards
 */
interface InstrumentCardGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4;
  className?: string;
}

export function InstrumentCardGrid({ 
  children, 
  columns = 4,
  className 
}: InstrumentCardGridProps) {
  const gridCols = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };
  
  return (
    <div className={cn("grid gap-4", gridCols[columns], className)}>
      {children}
    </div>
  );
}

export default InstrumentCard;
