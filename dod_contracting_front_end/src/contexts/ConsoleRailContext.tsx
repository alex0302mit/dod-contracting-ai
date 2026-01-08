/**
 * ConsoleRailContext
 * 
 * Manages the state of the collapsible right verification console rail.
 * The ConsoleRail contains 5 tabs for quality metrics, issues, citations, fields, and audit.
 * 
 * Features:
 * - Route-aware defaults (open on Editor/Approvals, closed elsewhere)
 * - Persists user preference to localStorage
 * - Provides methods to open, close, toggle, and switch tabs
 * 
 * Dependencies:
 * - React Context API for global state management
 * - localStorage for persistence
 */

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

// Available tabs in the ConsoleRail
export type ConsoleRailTab = 'quality' | 'issues' | 'citations' | 'fields' | 'audit';

// Quality data that can be passed to the ConsoleRail from screens
export interface ConsoleRailQualityData {
  score?: number;
  grade?: string;
  breakdown?: {
    hallucination?: { score: number; risk_level: string; issues: string[] };
    vague_language?: { score: number; count: number; issues: string[] };
    citations?: { score: number; valid: number; invalid: number; issues: string[] };
    compliance?: { score: number; level: string; issues: string[] };
    completeness?: { score: number; word_count: number; issues: string[] };
  };
  issues?: string[];
  suggestions?: string[];
}

// Citation data for the Citations tab
export interface ConsoleRailCitation {
  id: number;
  source: string;
  text: string;
  page?: number;
  sourceType?: 'regulation' | 'template' | 'past_contract';
}

// Audit event for the Audit tab
export interface ConsoleRailAuditEvent {
  id: string;
  action: string;
  performed_by: string;
  timestamp: string;
  details?: string;
  performed_by_user?: {
    name: string;
    email?: string;
    role?: string;
  };
}

// Context type definition
interface ConsoleRailContextType {
  // Rail state
  isOpen: boolean;
  activeTab: ConsoleRailTab;
  
  // Rail controls
  toggleRail: () => void;
  openRail: (tab?: ConsoleRailTab) => void;
  closeRail: () => void;
  setActiveTab: (tab: ConsoleRailTab) => void;
  
  // Data for tabs
  qualityData: ConsoleRailQualityData | null;
  setQualityData: (data: ConsoleRailQualityData | null) => void;
  citations: ConsoleRailCitation[];
  setCitations: (citations: ConsoleRailCitation[]) => void;
  auditEvents: ConsoleRailAuditEvent[];
  setAuditEvents: (events: ConsoleRailAuditEvent[]) => void;
  
  // Loading states
  isLoadingQuality: boolean;
  setIsLoadingQuality: (loading: boolean) => void;
}

// Create context with undefined default
const ConsoleRailContext = createContext<ConsoleRailContextType | undefined>(undefined);

// localStorage key for persisting rail state
const STORAGE_KEY = 'aces-console-rail-state';

// Provider props
interface ConsoleRailProviderProps {
  children: ReactNode;
  // Default open state based on current route
  defaultOpen?: boolean;
}

/**
 * ConsoleRailProvider
 * 
 * Provides ConsoleRail state to the entire application.
 * Wrap this around the main app component.
 */
export function ConsoleRailProvider({ children, defaultOpen = false }: ConsoleRailProviderProps) {
  // Initialize state from localStorage or default
  const [isOpen, setIsOpen] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return parsed.isOpen ?? defaultOpen;
      }
    } catch {
      // Ignore localStorage errors
    }
    return defaultOpen;
  });
  
  const [activeTab, setActiveTabState] = useState<ConsoleRailTab>('quality');
  
  // Data states for tabs
  const [qualityData, setQualityData] = useState<ConsoleRailQualityData | null>(null);
  const [citations, setCitations] = useState<ConsoleRailCitation[]>([]);
  const [auditEvents, setAuditEvents] = useState<ConsoleRailAuditEvent[]>([]);
  const [isLoadingQuality, setIsLoadingQuality] = useState(false);
  
  // Persist state to localStorage when it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ isOpen }));
    } catch {
      // Ignore localStorage errors
    }
  }, [isOpen]);
  
  // Toggle rail open/closed
  const toggleRail = useCallback(() => {
    setIsOpen(prev => !prev);
  }, []);
  
  // Open rail, optionally switching to a specific tab
  const openRail = useCallback((tab?: ConsoleRailTab) => {
    setIsOpen(true);
    if (tab) {
      setActiveTabState(tab);
    }
  }, []);
  
  // Close rail
  const closeRail = useCallback(() => {
    setIsOpen(false);
  }, []);
  
  // Set active tab
  const setActiveTab = useCallback((tab: ConsoleRailTab) => {
    setActiveTabState(tab);
  }, []);
  
  const value: ConsoleRailContextType = {
    isOpen,
    activeTab,
    toggleRail,
    openRail,
    closeRail,
    setActiveTab,
    qualityData,
    setQualityData,
    citations,
    setCitations,
    auditEvents,
    setAuditEvents,
    isLoadingQuality,
    setIsLoadingQuality,
  };
  
  return (
    <ConsoleRailContext.Provider value={value}>
      {children}
    </ConsoleRailContext.Provider>
  );
}

/**
 * useConsoleRail hook
 * 
 * Access ConsoleRail state and controls from any component.
 * Must be used within a ConsoleRailProvider.
 */
export function useConsoleRail(): ConsoleRailContextType {
  const context = useContext(ConsoleRailContext);
  if (context === undefined) {
    throw new Error('useConsoleRail must be used within a ConsoleRailProvider');
  }
  return context;
}

export default ConsoleRailContext;
