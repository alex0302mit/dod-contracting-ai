/**
 * AdminAuditLogs Component
 *
 * Admin panel for viewing system audit logs.
 * Displays security events, login attempts, and system changes.
 * Only accessible to users with the 'admin' role.
 *
 * Features:
 * - Paginated table of audit log entries
 * - Filters by action type and entity type
 * - Export to CSV functionality
 * - Color-coded action badges
 */
import { useState, useEffect, useCallback } from 'react';
import {
  ScrollText,
  AlertTriangle,
  Loader2,
  Download,
  ChevronLeft,
  ChevronRight,
  Filter,
  RefreshCw,
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
import { auditLogsApi, type AuditLogEntry } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { format } from 'date-fns';

// Action type options for filtering
// Note: Using '__all__' instead of '' because Radix UI Select doesn't allow empty string values
const ACTION_TYPES = [
  { value: '__all__', label: 'All Actions' },
  { value: 'login_success', label: 'Login Success' },
  { value: 'login_failed', label: 'Login Failed' },
  { value: 'user_registered', label: 'User Registered' },
  { value: 'role_changed', label: 'Role Changed' },
  { value: 'user_deactivated', label: 'User Deactivated' },
  { value: 'user_created', label: 'User Created' },
  { value: 'password_changed', label: 'Password Changed' },
];

// Entity type options for filtering
// Note: Using '__all__' instead of '' because Radix UI Select doesn't allow empty string values
const ENTITY_TYPES = [
  { value: '__all__', label: 'All Entities' },
  { value: 'user', label: 'User' },
  { value: 'document', label: 'Document' },
  { value: 'project', label: 'Project' },
];

// Get badge styling based on action type
const getActionBadgeClass = (action: string) => {
  if (action.includes('failed') || action.includes('deactivated')) {
    return 'bg-red-100 text-red-800 border-red-200';
  }
  if (action.includes('success') || action.includes('created') || action.includes('registered')) {
    return 'bg-green-100 text-green-800 border-green-200';
  }
  if (action.includes('changed')) {
    return 'bg-blue-100 text-blue-800 border-blue-200';
  }
  return 'bg-slate-100 text-slate-800 border-slate-200';
};

// Format action for display
const formatAction = (action: string) => {
  return action.split('_').map((word) =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
};

const ITEMS_PER_PAGE = 25;

export function AdminAuditLogs() {
  const { user: currentUser } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);

  // Filter state - using '__all__' as the "no filter" value (Radix UI Select doesn't allow empty strings)
  const [actionFilter, setActionFilter] = useState('__all__');
  const [entityFilter, setEntityFilter] = useState('__all__');

  // Fetch logs with current filters
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      // Convert '__all__' to undefined for API call (no filter)
      const response = await auditLogsApi.getLogs(
        actionFilter === '__all__' ? undefined : actionFilter,
        entityFilter === '__all__' ? undefined : entityFilter,
        ITEMS_PER_PAGE,
        offset
      );
      setLogs(response.logs);
      setTotal(response.total);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [actionFilter, entityFilter, offset]);

  // Fetch on mount and when filters/pagination change
  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Reset pagination when filters change
  useEffect(() => {
    setOffset(0);
  }, [actionFilter, entityFilter]);

  // Handle export
  const handleExport = async () => {
    setExporting(true);
    try {
      // Convert '__all__' to undefined for API call (no filter)
      await auditLogsApi.exportCsv(
        actionFilter === '__all__' ? undefined : actionFilter,
        entityFilter === '__all__' ? undefined : entityFilter
      );
      toast.success('Audit logs exported successfully');
    } catch (error) {
      console.error('Error exporting audit logs:', error);
      toast.error('Failed to export audit logs');
    } finally {
      setExporting(false);
    }
  };

  // Pagination
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);
  const currentPage = Math.floor(offset / ITEMS_PER_PAGE) + 1;

  const goToPage = (page: number) => {
    setOffset((page - 1) * ITEMS_PER_PAGE);
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
              <p className="text-slate-600">
                You don't have permission to access the audit logs.
                Contact an administrator if you need elevated access.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <ScrollText className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Audit Logs</h2>
              <p className="text-sm text-slate-600">View system activity and security events</p>
            </div>
          </div>

          <Button onClick={handleExport} disabled={exporting} variant="outline" className="gap-2">
            {exporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 bg-slate-50 border-b">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <span className="text-sm font-medium text-slate-700">Filters:</span>
          </div>

          <Select value={actionFilter} onValueChange={setActionFilter}>
            <SelectTrigger className="w-48 bg-white">
              <SelectValue placeholder="Action Type" />
            </SelectTrigger>
            <SelectContent>
              {ACTION_TYPES.map((action) => (
                <SelectItem key={action.value} value={action.value}>
                  {action.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={entityFilter} onValueChange={setEntityFilter}>
            <SelectTrigger className="w-48 bg-white">
              <SelectValue placeholder="Entity Type" />
            </SelectTrigger>
            <SelectContent>
              {ENTITY_TYPES.map((entity) => (
                <SelectItem key={entity.value} value={entity.value}>
                  {entity.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="ghost" size="sm" onClick={fetchLogs} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>

          <div className="ml-auto text-sm text-slate-500">
            {total.toLocaleString()} total records
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Activity Log</CardTitle>
            <CardDescription>
              Showing {offset + 1}-{Math.min(offset + ITEMS_PER_PAGE, total)} of {total} entries
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                No audit logs found matching your filters
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-40">Timestamp</TableHead>
                    <TableHead className="w-48">User</TableHead>
                    <TableHead className="w-40">Action</TableHead>
                    <TableHead className="w-32">Entity</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="text-sm text-slate-600">
                        {log.created_at
                          ? format(new Date(log.created_at), 'MMM d, yyyy HH:mm:ss')
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {log.user_email || (
                            <span className="text-slate-400 italic">System</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={getActionBadgeClass(log.action)}
                          variant="outline"
                        >
                          {formatAction(log.action)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-slate-600">
                        {log.entity_type ? (
                          <span className="capitalize">{log.entity_type}</span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-slate-600 max-w-md truncate">
                        {log.details || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="text-sm text-slate-500">
                  Page {currentPage} of {totalPages}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage === 1 || loading}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage === totalPages || loading}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default AdminAuditLogs;
