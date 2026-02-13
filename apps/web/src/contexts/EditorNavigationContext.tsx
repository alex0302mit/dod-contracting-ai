/**
 * Editor Navigation Context
 * 
 * Provides navigation functionality to open content in the main Live Editor
 * from anywhere in the app (e.g., Procurement Tracker's document dialogs).
 * 
 * Features:
 * - Store pending content to be loaded in the editor
 * - Navigate to the Editor view with pre-loaded content
 * - Used by DocumentDetailDialog to implement "Open in Editor" functionality
 * 
 * Dependencies:
 * - Consumed by AIContractingUI to handle actual navigation
 * - Used by procurement components to trigger editor navigation
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// Interface for pending editor content
interface PendingEditorContent {
  content: string;        // The markdown/HTML content to load
  documentName: string;   // Name of the document (used as section title)
  documentId?: string;    // Optional database ID for reasoning/lineage tracking
  projectId?: string;     // Optional project ID -- when present, EditorScreen loads ALL generated docs for the project
}

// Context type definition
interface EditorNavigationContextType {
  // Pending content to be loaded when navigating to editor
  pendingEditorContent: PendingEditorContent | null;
  // Function to navigate to editor with specific content
  // projectId (4th arg) triggers project-aware mode: editor loads all generated docs as sections
  navigateToEditor: (content: string, documentName: string, documentId?: string, projectId?: string) => void;
  // Clear pending content after it has been loaded
  clearPendingContent: () => void;
  // Callback setter for the actual navigation (set by AIContractingUI)
  setNavigationCallback: (callback: (content: string, documentName: string, documentId?: string, projectId?: string) => void) => void;
}

// Create the context with undefined default
const EditorNavigationContext = createContext<EditorNavigationContextType | undefined>(undefined);

/**
 * EditorNavigationProvider
 * 
 * Wrap this around components that need to navigate to the editor.
 * The AIContractingUI component should register its navigation callback
 * using setNavigationCallback.
 */
export function EditorNavigationProvider({ children }: { children: ReactNode }) {
  // State for pending content
  const [pendingEditorContent, setPendingEditorContent] = useState<PendingEditorContent | null>(null);
  
  // Navigation callback - set by AIContractingUI to handle actual navigation
  const [navigationCallback, setNavigationCallbackState] = useState<
    ((content: string, documentName: string, documentId?: string, projectId?: string) => void) | null
  >(null);

  // Navigate to editor with content
  // When projectId is provided, EditorScreen will fetch ALL generated docs for that project
  const navigateToEditor = useCallback((content: string, documentName: string, documentId?: string, projectId?: string) => {
    // Store the pending content (including projectId for project-aware mode)
    setPendingEditorContent({ content, documentName, documentId, projectId });

    // If a navigation callback is registered, call it
    if (navigationCallback) {
      navigationCallback(content, documentName, documentId, projectId);
    }
  }, [navigationCallback]);

  // Clear pending content after loading
  const clearPendingContent = useCallback(() => {
    setPendingEditorContent(null);
  }, []);

  // Setter for the navigation callback (used by AIContractingUI)
  const setNavigationCallback = useCallback((callback: (content: string, documentName: string, documentId?: string, projectId?: string) => void) => {
    setNavigationCallbackState(() => callback);
  }, []);

  return (
    <EditorNavigationContext.Provider
      value={{
        pendingEditorContent,
        navigateToEditor,
        clearPendingContent,
        setNavigationCallback,
      }}
    >
      {children}
    </EditorNavigationContext.Provider>
  );
}

/**
 * useEditorNavigation hook
 * 
 * Use this hook to access editor navigation functionality from any component.
 * Must be used within an EditorNavigationProvider.
 * 
 * Example usage:
 * ```tsx
 * const { navigateToEditor } = useEditorNavigation();
 *
 * // Navigate to editor with content, documentId, and projectId for project-aware mode
 * navigateToEditor(documentContent, "Market Research Report", document.id, document.project_id);
 * ```
 */
export function useEditorNavigation() {
  const context = useContext(EditorNavigationContext);
  if (context === undefined) {
    throw new Error('useEditorNavigation must be used within an EditorNavigationProvider');
  }
  return context;
}
