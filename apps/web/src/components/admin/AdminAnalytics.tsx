/**
 * AdminAnalytics Component
 *
 * Admin-only dashboard displaying organization-wide analytics including:
 * - Summary KPI cards (documents, success rate, hours saved, avg phase days)
 * - Documents generated trend chart (daily bar chart)
 * - Documents by type breakdown (horizontal bar chart)
 * - Top contributors leaderboard table
 *
 * Features:
 * - Date range filter (7, 30, 90 days)
 * - CSV export of summary data
 * - Responsive layout
 * - Loading and error states
 *
 * Dependencies:
 * - useAdminAnalytics hook for data fetching
 * - Recharts for charts (BarChart)
 * - useAuth for admin access check
 */

import { useState } from 'react';
import {
  BarChart3,
  FileText,
  CheckCircle2,
  Clock,
  Calendar,
  TrendingUp,
  TrendingDown,
  Download,
  RefreshCw,
  Loader2,
  AlertTriangle,
  Users,
  Trophy,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { useAdminAnalytics } from '@/hooks/useAdminAnalytics';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { AgentPerformanceDashboard } from './AgentPerformanceDashboard';

// Date range options for the filter
const DATE_RANGE_OPTIONS = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
];

// Chart colors
const CHART_COLORS = {
  primary: 'hsl(var(--primary))',
  success: '#22c55e',
  muted: 'hsl(var(--muted-foreground))',
};

/**
 * KPI Card component for summary statistics
 */
interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    label: string;
  };
}

function KPICard({ title, value, subtitle, icon, trend }: KPICardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
            {trend && (
              <div className="flex items-center gap-1 mt-1">
                {trend.direction === 'up' && (
                  <TrendingUp className="h-3 w-3 text-green-500" />
                )}
                {trend.direction === 'down' && (
                  <TrendingDown className="h-3 w-3 text-red-500" />
                )}
                <span
                  className={`text-xs ${
                    trend.direction === 'up'
                      ? 'text-green-600'
                      : trend.direction === 'down'
                      ? 'text-red-600'
                      : 'text-muted-foreground'
                  }`}
                >
                  {trend.label}
                </span>
              </div>
            )}
          </div>
          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Custom tooltip for the trend chart
 */
function TrendChartTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-popover border rounded-lg shadow-lg p-3">
      <p className="text-sm font-medium mb-1">{label}</p>
      {payload.map((entry, index) => (
        <p key={index} className="text-xs text-muted-foreground">
          {entry.dataKey === 'generated' && `Generated: ${entry.value}`}
          {entry.dataKey === 'failed' && `Failed: ${entry.value}`}
        </p>
      ))}
    </div>
  );
}

/**
 * Main AdminAnalytics component
 */
export function AdminAnalytics() {
  const { user: currentUser } = useAuth();
  const [days, setDays] = useState(30);
  
  // Fetch analytics data
  const { data, loading, fetching, error, refetch } = useAdminAnalytics({ days });

  // Handle CSV export
  const handleExport = () => {
    if (!data) return;

    // Build CSV content
    const lines: string[] = [];
    
    // Summary section
    lines.push('ACES Analytics Report');
    lines.push(`Period: ${data.period.start} to ${data.period.end} (${data.period.days} days)`);
    lines.push('');
    lines.push('Summary Statistics');
    lines.push(`Total Documents Generated,${data.summary.total_documents_generated}`);
    lines.push(`Success Rate,${data.summary.success_rate}%`);
    lines.push(`Failed Generations,${data.summary.failed_generations}`);
    lines.push(`Total Hours Saved,${data.summary.total_hours_saved}`);
    lines.push(`Active Projects,${data.summary.projects_active}`);
    lines.push(`Average Phase Duration,${data.summary.avg_phase_days} days`);
    lines.push('');
    
    // Documents by type
    lines.push('Documents by Type');
    lines.push('Type,Count,Hours Saved');
    data.documents_by_type.forEach((doc) => {
      lines.push(`${doc.type},${doc.count},${doc.hours_saved}`);
    });
    lines.push('');
    
    // Top contributors
    lines.push('Top Contributors');
    lines.push('Name,Documents,Hours Saved');
    data.top_contributors.forEach((user) => {
      lines.push(`${user.name},${user.documents},${user.hours_saved}`);
    });

    // Create and download file
    const csvContent = lines.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `aces-analytics-${data.period.start}-to-${data.period.end}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    toast.success('Analytics exported successfully');
  };

  // Check if current user is admin
  if (currentUser?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Access Denied</h3>
              <p className="text-muted-foreground">
                You don't have permission to access the analytics dashboard.
                Contact an administrator if you need elevated access.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="mt-4 text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error Loading Analytics</h3>
              <p className="text-muted-foreground mb-4">{error}</p>
              <Button onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No data state
  if (!data) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
              <p className="text-muted-foreground">
                No analytics data is available for the selected period.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Prepare chart data - show last 14 days max for readability
  const trendData = data.daily_trend.slice(-14).map((d) => ({
    ...d,
    // Format date for display (Jan 15)
    displayDate: new Date(d.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
  }));

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <BarChart3 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Analytics Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Organization-wide performance metrics
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Date range selector */}
            <Select
              value={String(days)}
              onValueChange={(value) => setDays(Number(value))}
            >
              <SelectTrigger className="w-[150px]">
                <Calendar className="h-4 w-4 mr-2 text-muted-foreground" />
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
            
            {/* Refresh button */}
            <Button
              variant="outline"
              size="icon"
              onClick={() => refetch()}
              disabled={fetching}
            >
              <RefreshCw className={`h-4 w-4 ${fetching ? 'animate-spin' : ''}`} />
            </Button>
            
            {/* Export button */}
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="space-y-6 max-w-7xl mx-auto">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              title="Documents Generated"
              value={data.summary.total_documents_generated}
              subtitle={`${data.summary.failed_generations} failed`}
              icon={<FileText className="h-5 w-5 text-primary" />}
            />
            <KPICard
              title="Success Rate"
              value={`${data.summary.success_rate}%`}
              icon={<CheckCircle2 className="h-5 w-5 text-primary" />}
              trend={
                data.summary.success_rate >= 90
                  ? { direction: 'up', label: 'Excellent' }
                  : data.summary.success_rate >= 80
                  ? { direction: 'neutral', label: 'Good' }
                  : { direction: 'down', label: 'Needs attention' }
              }
            />
            <KPICard
              title="Hours Saved"
              value={`${data.summary.total_hours_saved}`}
              subtitle="Estimated time savings"
              icon={<Clock className="h-5 w-5 text-primary" />}
            />
            <KPICard
              title="Avg Phase Duration"
              value={`${data.summary.avg_phase_days} days`}
              subtitle={`${data.summary.projects_active} active projects`}
              icon={<TrendingUp className="h-5 w-5 text-primary" />}
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Documents Trend Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Documents Generated</CardTitle>
                <CardDescription>
                  Daily generation activity (last 14 days shown)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[250px]">
                  {trendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={trendData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                          dataKey="displayDate"
                          tick={{ fontSize: 11 }}
                          className="text-muted-foreground"
                        />
                        <YAxis
                          tick={{ fontSize: 11 }}
                          className="text-muted-foreground"
                          allowDecimals={false}
                        />
                        <Tooltip content={<TrendChartTooltip />} />
                        <Bar
                          dataKey="generated"
                          fill={CHART_COLORS.primary}
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                      No data for this period
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Documents by Type Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Documents by Type</CardTitle>
                <CardDescription>
                  Breakdown of generated document types
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[250px]">
                  {data.documents_by_type.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={data.documents_by_type.slice(0, 6)}
                        layout="vertical"
                        margin={{ left: 20, right: 20 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                        <YAxis
                          type="category"
                          dataKey="type"
                          tick={{ fontSize: 11 }}
                          width={120}
                          tickFormatter={(value) =>
                            value.length > 18 ? `${value.slice(0, 18)}...` : value
                          }
                        />
                        <Tooltip
                          formatter={(value: number, name: string) => [
                            value,
                            name === 'count' ? 'Documents' : 'Hours Saved',
                          ]}
                        />
                        <Bar
                          dataKey="count"
                          fill={CHART_COLORS.success}
                          radius={[0, 4, 4, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                      No documents generated
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Phase Velocity & Top Contributors Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Phase Velocity Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Phase Velocity</CardTitle>
                <CardDescription>
                  Average days per procurement phase
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(data.phase_velocity).map(([phase, stats]) => (
                    <div key={phase} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-primary" />
                        <span className="text-sm capitalize">
                          {phase.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="font-medium">
                          {stats.avg_days > 0 ? `${stats.avg_days} days` : 'N/A'}
                        </span>
                        <span className="text-xs text-muted-foreground ml-2">
                          ({stats.count} completed)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Contributors Table */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Trophy className="h-4 w-4 text-amber-500" />
                      Top Contributors
                    </CardTitle>
                    <CardDescription>
                      Users with most generated documents
                    </CardDescription>
                  </div>
                  <Users className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent>
                {data.top_contributors.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">Rank</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead className="text-right">Documents</TableHead>
                        <TableHead className="text-right">Hours Saved</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.top_contributors.slice(0, 5).map((user, index) => (
                        <TableRow key={user.user_id}>
                          <TableCell className="font-medium">
                            {index === 0 && '🥇'}
                            {index === 1 && '🥈'}
                            {index === 2 && '🥉'}
                            {index > 2 && `#${index + 1}`}
                          </TableCell>
                          <TableCell>{user.name || 'Unknown User'}</TableCell>
                          <TableCell className="text-right font-medium">
                            {user.documents}
                          </TableCell>
                          <TableCell className="text-right text-muted-foreground">
                            {user.hours_saved} hrs
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="py-8 text-center text-muted-foreground">
                    No contributor data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Agent Performance Dashboard */}
          <div className="mt-6">
            <AgentPerformanceDashboard />
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminAnalytics;
