/**
 * NavigationContext
 * 
 * Manages application-wide navigation state for the ACES application.
 * Allows screens to trigger navigation without prop drilling.
 * 
 * Features:
 * - Centralized route state management
 * - Project selection tracking
 * - Navigation callbacks for screens
 * 
 * Dependencies:
 * - React Context API for global state management
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// ACES Route types - matches screens in the application
export type RouteType =
  | 'OVERVIEW'         // Dashboard/Overview screen
  | 'QUICK_GENERATE'   // Quick Generate wizard
  | 'EDITOR'           // Document editor
  | 'DOCUMENTS'        // Documents grid/list view
  | 'TRACKER'          // Procurement tracker
  | 'APPROVALS'        // Pending approvals
  | 'SOURCES'          // Knowledge sources/RAG
  | 'EXPORT'           // Export view
  | 'SETTINGS'         // Admin settings
  | 'ADMIN_ANALYTICS'  // Admin analytics dashboard
  | 'ADMIN_AUDIT_LOGS' // Admin audit logs view
  | 'ADMIN_ORGS'       // Organization management
  | 'GENERATE_DOCUMENT' // Standalone generation wizard
  | 'MY_DOCUMENTS'     // Standalone documents list
  | 'GENERATING';      // Generation progress view

// Context type definition
interface NavigationContextType {
  // Current route
  currentRoute: RouteType;
  
  // Selected project (used by Tracker, Documents, Sources, etc.)
  selectedProjectId: string | null;
  
  // Navigation methods
  navigate: (route: RouteType) => void;
  setSelectedProjectId: (id: string | null) => void;
  
  // Navigate to project (sets project and goes to Tracker)
  navigateToProject: (projectId: string) => void;
  
  // Navigate to editor with content
  navigateToEditor: (content?: Record<string, string>) => void;
  
  // Editor content (passed from generation screens)
  editorContent: Record<string, string> | null;
  setEditorContent: (content: Record<string, string> | null) => void;
  
  // Previous route for back navigation
  previousRoute: RouteType | null;
  goBack: () => void;
}

// Create context with undefined default
const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

// Provider props
interface NavigationProviderProps {
  children: ReactNode;
  initialRoute?: RouteType;
}

/**
 * NavigationProvider
 * 
 * Provides navigation state to the entire application.
 * Wrap this around the main app component, inside AuthProvider.
 */
export function NavigationProvider({ 
  children, 
  initialRoute = 'OVERVIEW' 
}: NavigationProviderProps) {
  const [currentRoute, setCurrentRoute] = useState<RouteType>(initialRoute);
  const [previousRoute, setPreviousRoute] = useState<RouteType | null>(null);
  const [selectedProjectId, setSelectedProjectIdState] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState<Record<string, string> | null>(null);
  
  // Navigate to a route, storing the previous route
  const navigate = useCallback((route: RouteType) => {
    setPreviousRoute(currentRoute);
    setCurrentRoute(route);
  }, [currentRoute]);
  
  // Set selected project ID
  const setSelectedProjectId = useCallback((id: string | null) => {
    setSelectedProjectIdState(id);
  }, []);
  
  // Navigate to a project (sets ID and navigates to Tracker)
  const navigateToProject = useCallback((projectId: string) => {
    setSelectedProjectIdState(projectId);
    setPreviousRoute(currentRoute);
    setCurrentRoute('TRACKER');
  }, [currentRoute]);
  
  // Navigate to editor, optionally with content
  const navigateToEditor = useCallback((content?: Record<string, string>) => {
    if (content) {
      setEditorContent(content);
    }
    setPreviousRoute(currentRoute);
    setCurrentRoute('EDITOR');
  }, [currentRoute]);
  
  // Go back to previous route
  const goBack = useCallback(() => {
    if (previousRoute) {
      setCurrentRoute(previousRoute);
      setPreviousRoute(null);
    } else {
      // Default to Overview if no previous route
      setCurrentRoute('OVERVIEW');
    }
  }, [previousRoute]);
  
  const value: NavigationContextType = {
    currentRoute,
    selectedProjectId,
    navigate,
    setSelectedProjectId,
    navigateToProject,
    navigateToEditor,
    editorContent,
    setEditorContent,
    previousRoute,
    goBack,
  };
  
  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
}

/**
 * useNavigation hook
 * 
 * Access navigation state and controls from any component.
 * Must be used within a NavigationProvider.
 */
export function useNavigation(): NavigationContextType {
  const context = useContext(NavigationContext);
  if (context === undefined) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
}

export default NavigationContext;
