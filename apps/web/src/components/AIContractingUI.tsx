/**
 * AIContractingUI - ACES Main Application Component
 * 
 * The root component for ACES (Acquisition Contracting Enterprise System).
 * Provides the main application structure with:
 * - Authentication handling
 * - Navigation context
 * - ConsoleRail context
 * - AppShell layout with all screens
 * 
 * Dependencies:
 * - AuthProvider for authentication
 * - NavigationProvider for routing
 * - ConsoleRailProvider for verification panel
 * - AppShell for layout
 * - All screen components
 */

import { useState, useEffect, useCallback } from "react";
import { FileText, Sparkles, Shield, Loader2 } from "lucide-react";
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { NavigationProvider, useNavigation } from "@/contexts/NavigationContext";
import { ConsoleRailProvider, useConsoleRail } from "@/contexts/ConsoleRailContext";
import { EditorNavigationProvider, useEditorNavigation } from "@/contexts/EditorNavigationContext";
import { LoginPage } from "./LoginPage";
import { AppShell } from "./layout/AppShell";
import { AdminUserManagement } from "./admin/AdminUserManagement";
import { AdminAuditLogs } from "./admin/AdminAuditLogs";
import { AdminAnalytics } from "./admin/AdminAnalytics";
import { OrgManagement } from "./admin/OrgManagement";

// Import all screens
import {
  OverviewScreen,
  QuickGenerateScreen,
  EditorScreen,
  DocumentsScreen,
  TrackerScreen,
  ApprovalsScreen,
  SourcesScreen,
  ExportScreen,
  GenerateDocumentScreen,
  MyDocumentsScreen,
} from "./screens";

import { ragApi } from "@/services/api";
import { toast } from "sonner";
import { convertSectionsToHtml, convertMarkdownToHtml } from "@/lib/markdownToHtml";

/**
 * GeneratingView - Animated loading screen during document generation
 * @param _progress - Generation progress percentage (currently unused, shown via animation)
 */
function GeneratingView({ progress: _progress }: { progress: number }) {
  const [messageIndex, setMessageIndex] = useState(0);
  const [dots, setDots] = useState("");

  const LOADING_MESSAGES = [
    "Crunching the numbers",
    "Teaching AI about procurement",
    "Consulting the regulations",
    "Organizing the paperwork",
    "Double-checking everything",
    "Analyzing requirements",
    "Drafting compliance language",
    "Cross-referencing FAR clauses"
  ];

  // Rotate messages every 3 seconds
  useEffect(() => {
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);
    return () => clearInterval(messageInterval);
  }, []);

  // Animate dots every 500ms
  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots((prev) => (prev === "..." ? "" : prev + "."));
    }, 500);
    return () => clearInterval(dotsInterval);
  }, []);

  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center space-y-8 max-w-2xl px-4">
        {/* Lottie Animation */}
        <div className="w-48 h-48 mx-auto">
          <DotLottieReact
            src="https://lottie.host/599a9594-2bc0-4177-b1f3-b4939ad8516e/0orfoYqcjG.lottie"
            loop
            autoplay
            style={{ width: '100%', height: '100%' }}
          />
        </div>

        <div className="space-y-3">
          <h1 className="text-3xl font-bold text-primary">
            Generating Documents
          </h1>
          <p className="text-muted-foreground">
            AI agents are analyzing assumptions and creating your acquisition documents...
          </p>
        </div>

        {/* Animated message */}
        <div className="flex items-center justify-center">
          <span className="text-lg font-medium text-foreground">
            {LOADING_MESSAGES[messageIndex]}
          </span>
          <span className="text-lg font-medium text-primary w-8 text-left">{dots}</span>
        </div>
        <p className="text-sm text-muted-foreground">
          This usually takes 30-60 seconds
        </p>

        {/* Progress indicators */}
        <div className="grid grid-cols-3 gap-4 mt-8">
          <div className="p-4 rounded-lg border bg-card">
            <FileText className="h-8 w-8 text-info mx-auto mb-2" />
            <div className="text-sm font-medium">Extracting Context</div>
            <div className="text-xs text-muted-foreground mt-1">From RAG documents</div>
          </div>
          <div className="p-4 rounded-lg border bg-card">
            <Sparkles className="h-8 w-8 text-ai mx-auto mb-2" />
            <div className="text-sm font-medium">Generating Content</div>
            <div className="text-xs text-muted-foreground mt-1">Using AI agents</div>
          </div>
          <div className="p-4 rounded-lg border bg-card">
            <Shield className="h-8 w-8 text-success mx-auto mb-2" />
            <div className="text-sm font-medium">Validating Quality</div>
            <div className="text-xs text-muted-foreground mt-1">Ensuring compliance</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * MainApp - Main application content with routing
 */
function MainApp() {
  const { currentRoute, navigate, setEditorContent } = useNavigation();
  const { closeRail } = useConsoleRail();
  const { setNavigationCallback } = useEditorNavigation();
  
  // Generation state
  const [generationProgress, setGenerationProgress] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Editor content for generation flow
  const [lockedAssumptions] = useState<Array<{ id: string; text: string; source: string }>>([]);
  // Citations state for generation flow (passed to ConsoleRail context)
  const [, setCitations] = useState<Array<{ id: number; source: string; page: number; text: string; bbox: { x: number; y: number; w: number; h: number } }>>([]);

  // Keep ConsoleRail closed - screens have their own panels
  useEffect(() => {
    closeRail();
  }, [currentRoute, closeRail]);

  // Handle navigation to editor from procurement components
  // When projectId is provided, EditorScreen will fetch all generated docs for the project
  const handleNavigateToEditor = useCallback((content: string, documentName: string, documentId?: string, projectId?: string) => {
    const htmlContent = convertMarkdownToHtml(content);
    setEditorContent({ [documentName]: htmlContent });
    navigate('EDITOR');
    toast.success(`Opened "${documentName}" in editor`);
  }, [navigate, setEditorContent]);

  // Register navigation callback
  useEffect(() => {
    setNavigationCallback(handleNavigateToEditor);
  }, [setNavigationCallback, handleNavigateToEditor]);

  // Handle document generation (used by Quick Generate flow)
  const handleGenerateDocuments = useCallback(async (selectedDocs: any[]) => {
    try {
      setIsGenerating(true);
      setGenerationProgress(0);

      const response = await ragApi.generateDocuments({
        assumptions: lockedAssumptions,
        documents: selectedDocs.map((doc: any) => ({
          name: doc.name,
          section: doc.section,
          category: doc.category,
          linkedAssumptions: doc.linkedAssumptions,
        })),
      });

      toast.success(`Generating ${response.documents_requested} documents...`);

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await ragApi.getGenerationStatus(response.task_id);
          setGenerationProgress(status.progress);

          if (status.status === 'completed' && status.result) {
            clearInterval(pollInterval);
            const htmlSections = convertSectionsToHtml(status.result.sections);
            setEditorContent(htmlSections);

            // Update citations for ConsoleRail
            const citationsWithBbox = status.result.citations.map((c: any) => ({
              ...c,
              bbox: { x: 30, y: 40 + (c.id * 20), w: 200, h: 16 }
            }));
            setCitations(citationsWithBbox);

            setIsGenerating(false);
            navigate('EDITOR');
            toast.success("Documents generated successfully!");
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            toast.error(status.message || "Document generation failed");
          }
        } catch (error: any) {
          clearInterval(pollInterval);
          setIsGenerating(false);
          toast.error(`Generation error: ${error.message}`);
        }
      }, 2000);

    } catch (error: any) {
      console.error('Generation error:', error);
      toast.error(`Failed to start generation: ${error.message}`);
      setIsGenerating(false);
    }
  }, [lockedAssumptions, setEditorContent, navigate]);
  
  // Mark handleGenerateDocuments as used (available for legacy workflows)
  void handleGenerateDocuments;

  // Determine if ConsoleRail should be shown
  // Currently disabled for all routes - Editor has its own quality panel, Approvals has its own UI
  const showConsoleRail = false;

  // Render content based on current route
  const renderContent = () => {
    // Show generating view if in progress
    if (isGenerating) {
      return <GeneratingView progress={generationProgress} />;
    }

    switch (currentRoute) {
      case 'OVERVIEW':
        return <OverviewScreen />;
      
      case 'QUICK_GENERATE':
        return <QuickGenerateScreen />;
      
      case 'EDITOR':
        return <EditorScreen />;
      
      case 'DOCUMENTS':
        return <DocumentsScreen />;
      
      case 'TRACKER':
        return <TrackerScreen />;
      
      case 'APPROVALS':
        return <ApprovalsScreen />;
      
      case 'SOURCES':
        return <SourcesScreen />;
      
      case 'EXPORT':
        return <ExportScreen />;
      
      case 'SETTINGS':
        return <AdminUserManagement />;

      case 'ADMIN_ANALYTICS':
        return <AdminAnalytics />;

      case 'ADMIN_AUDIT_LOGS':
        return <AdminAuditLogs />;

      case 'ADMIN_ORGS':
        return <OrgManagement />;

      case 'GENERATE_DOCUMENT':
        return <GenerateDocumentScreen />;

      case 'MY_DOCUMENTS':
        return <MyDocumentsScreen />;

      // Legacy routes for backwards compatibility
      case 'GENERATING' as any:
        return <GeneratingView progress={generationProgress} />;
      
      default:
        return <OverviewScreen />;
    }
  };

  return (
    <AppShell showConsoleRail={showConsoleRail}>
      {renderContent()}
    </AppShell>
  );
}

/**
 * AuthenticatedApp - Handles auth state and renders app or login
 */
function AuthenticatedApp() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading ACES...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  // Wrap with all required providers
  return (
    <NavigationProvider initialRoute="OVERVIEW">
      <ConsoleRailProvider>
        <EditorNavigationProvider>
          <MainApp />
        </EditorNavigationProvider>
      </ConsoleRailProvider>
    </NavigationProvider>
  );
}

/**
 * AIContractingUI - Root export with AuthProvider
 */
export default function AIContractingUI() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}
