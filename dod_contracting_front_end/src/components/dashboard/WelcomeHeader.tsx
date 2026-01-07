/**
 * WelcomeHeader Component
 *
 * Displays a personalized greeting with:
 * - Time-based greeting (Good morning/afternoon/evening)
 * - User name
 * - User role badge
 * - Welcoming subtitle
 */

import { useAuth } from '@/contexts/AuthContext';
import { Badge } from '@/components/ui/badge';
import { Shield } from 'lucide-react';

// Role display configuration
const ROLE_CONFIG: Record<string, { label: string; color: string }> = {
  admin: { label: 'Administrator', color: 'bg-purple-100 text-purple-700' },
  contracting_officer: { label: 'Contracting Officer', color: 'bg-blue-100 text-blue-700' },
  program_manager: { label: 'Program Manager', color: 'bg-emerald-100 text-emerald-700' },
  approver: { label: 'Approver', color: 'bg-amber-100 text-amber-700' },
  viewer: { label: 'Viewer', color: 'bg-slate-100 text-slate-700' },
};

function getTimeBasedGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export function WelcomeHeader() {
  const { user } = useAuth();
  const greeting = getTimeBasedGreeting();
  const roleConfig = ROLE_CONFIG[user?.role || 'viewer'];

  return (
    <div className="flex items-start justify-between">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl font-bold text-slate-900">
            {greeting}, {user?.name?.split(' ')[0] || 'there'}!
          </h1>
          <Badge className={`${roleConfig.color} border-0 font-medium`}>
            {roleConfig.label}
          </Badge>
        </div>
        <p className="text-slate-600">
          Welcome to DoD Acquisition AI - Your intelligent procurement assistant
        </p>
      </div>
      <div className="hidden md:flex items-center gap-2 text-slate-400">
        <Shield className="h-10 w-10" />
      </div>
    </div>
  );
}
