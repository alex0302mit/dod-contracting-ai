import { useState, useEffect, useCallback } from "react";
// Removed Map icon - Board tab removed from navigation
// Updated: Upload and Workflow icons removed - those tabs replaced by Quick Generate
import { FileText, Sparkles, Download, TrendingUp, UserCheck, Settings, LogOut, User, ChevronDown, Home, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { LiveEditor } from "./LiveEditor";
// StrategyBoard import removed - Board tab eliminated from UX
import { UploadCenter } from "./UploadCenter";
// AssumptionMap, TraceMatrix, GenerationPlan replaced by unified DocumentWorkflow
import { DocumentWorkflow } from "./DocumentWorkflow";
// QuickGenerateTab: One-time package generation wizard without project creation
import { QuickGenerateTab } from "./quick-generate/QuickGenerateTab";
// Compliance tab removed - compliance gate now appears in export dropdown
import { ExportView } from "./ExportView";
import { ProcurementHub } from "./procurement/ProcurementHub";
import { PendingApprovalsView } from "./procurement/PendingApprovalsView";
import { NotificationCenter } from "./procurement/NotificationCenter";
import { AdminUserManagement } from "./admin/AdminUserManagement";
import { DashboardView } from "./dashboard/DashboardView";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
// EditorNavigationProvider allows components to navigate to editor with pre-loaded content
import { EditorNavigationProvider, useEditorNavigation } from "@/contexts/EditorNavigationContext";
import { LoginPage } from "./LoginPage";
import { ragApi } from "@/services/api";
import { toast } from "sonner";
import { convertSectionsToHtml, convertMarkdownToHtml } from "@/lib/markdownToHtml";

// Route types for navigation - Dashboard is default, Consolidated workflow replaces ASSUMPTION_MAP, TRACE_MATRIX, GEN_PLAN
// QUICK_GENERATE: New one-time package generation wizard that doesn't require project creation
type RouteType = "DASHBOARD" | "QUICK_GENERATE" | "UPLOAD_CENTER" | "DOCUMENT_WORKFLOW" | "GENERATING" | "EDITOR" | "EXPORT" | "PROCUREMENT_TRACKER" | "PENDING_APPROVALS" | "ADMIN";

function MainApp() {
  const { user, signOut } = useAuth();
  // Get editor navigation context to handle "Open in Editor" from procurement tracker
  const { setNavigationCallback } = useEditorNavigation();
  const [route, setRoute] = useState<RouteType>("DASHBOARD");
  // State for project selection from Dashboard (to pass to ProcurementHub)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [uploads, setUploads] = useState({ strategy: [] as string[], reqs: [] as string[], market_research: [] as string[], templates: [] as string[] });
  const [parsed, setParsed] = useState({
    assumptions: [] as Array<{ id: string; text: string; source: string }>,
    reqSnippets: [] as string[],
    pdfPreview: null,
    citations: [
      { id: 1, source: "FAR 15.304", page: 12, text: "Evaluation factors must be stated in the solicitation", bbox: { x: 30, y: 40, w: 200, h: 16 } },
      { id: 2, source: "Acq Strategy §3.2", page: 8, text: "Best Value Tradeoff evaluation approach", bbox: { x: 30, y: 80, w: 180, h: 16 } },
      { id: 3, source: "DFARS 252.204-7012", page: 1, text: "Safeguarding covered defense information and cyber incident reporting", bbox: { x: 30, y: 120, w: 220, h: 16 } },
    ],
  });
  const [lockedAssumptions, setLockedAssumptions] = useState([
    { id: "a1", text: "BVTO evaluation with weighted factors", source: "Acq Strategy §3.2" },
    { id: "a2", text: "IDIQ base + 4 option years", source: "Acq Strategy §2.1" },
    { id: "a3", text: "CUI handling required for vendor data", source: "Reqs §5" },
  ]);
  const [planLocked, setPlanLocked] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [editorSections, setEditorSections] = useState<Record<string, string>>({
    Overview: "This notice intends to synopsize the acquisition action and describes evaluation factors [1]. Vendors must follow the instructions provided in Section L.",
    "Evaluation Approach": "The Government will conduct a Best Value Tradeoff evaluation [2] considering Technical, Past Performance, and Price. The SSA retains tradeoff authority.",
    Schedule: "The Government anticipates award in Q2 FY25. Timeline TBD subject to approvals.",
    "Security Requirements": "Contractors must comply with CUI handling requirements [3] and implement appropriate safeguarding measures.",
  });
  const [agentMetadata, setAgentMetadata] = useState<Record<string, any>>({});
  const [collaborationMetadata, setCollaborationMetadata] = useState<any>(null);
  // Precomputed quality scores from generation (for instant display in editor)
  const [qualityAnalysis, setQualityAnalysis] = useState<Record<string, any>>({});

  // Navigation callback for opening content in the editor from Procurement Tracker
  // This converts markdown content to HTML and navigates to the editor view
  const handleNavigateToEditor = useCallback((content: string, documentName: string) => {
    // Convert markdown to HTML for the editor
    const htmlContent = convertMarkdownToHtml(content);
    
    // Add as a new section with the document name
    setEditorSections(prev => ({
      ...prev,
      [documentName]: htmlContent
    }));
    
    // Navigate to editor
    setRoute("EDITOR");
    toast.success(`Opened "${documentName}" in editor`);
  }, []);

  // Register the navigation callback when the component mounts
  useEffect(() => {
    setNavigationCallback(handleNavigateToEditor);
  }, [setNavigationCallback, handleNavigateToEditor]);

  // Handle document generation
  const handleGenerateDocuments = async (selectedDocs: any[]) => {
    try {
      setRoute("GENERATING");
      setGenerationProgress(0);

      // Start generation
      const response = await ragApi.generateDocuments({
        assumptions: lockedAssumptions,
        documents: selectedDocs.map(doc => ({
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
            // Convert markdown sections to HTML for the editor
            const htmlSections = convertSectionsToHtml(status.result.sections);
            setEditorSections(htmlSections);

            // Store agent metadata if available
            if (status.result.agent_metadata) {
              setAgentMetadata(status.result.agent_metadata);
            }

            // Store collaboration metadata if available (Phase 4)
            if (status.result.collaboration_metadata) {
              setCollaborationMetadata(status.result.collaboration_metadata);
              console.log('Phase 4: Collaboration metadata received', status.result.collaboration_metadata);
            }

            // Store precomputed quality analysis if available
            if (status.result.quality_analysis) {
              setQualityAnalysis(status.result.quality_analysis);
              console.log('Quality analysis precomputed:', status.result.quality_analysis);
            }

            // Add bbox to citations for compatibility
            const citationsWithBbox = status.result.citations.map(c => ({
              ...c,
              bbox: { x: 30, y: 40 + (c.id * 20), w: 200, h: 16 }
            }));
            setParsed({ ...parsed, citations: citationsWithBbox });

            setRoute("EDITOR");
            toast.success("Documents generated successfully!");
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setRoute("DOCUMENT_WORKFLOW");
            toast.error(status.message || "Document generation failed");
          }
        } catch (error: any) {
          clearInterval(pollInterval);
          setRoute("DOCUMENT_WORKFLOW");
          toast.error(`Generation error: ${error.message}`);
        }
      }, 2000); // Poll every 2 seconds

    } catch (error: any) {
      console.error('Generation error:', error);
      toast.error(`Failed to start generation: ${error.message}`);
      setRoute("DOCUMENT_WORKFLOW");
    }
  };

  return (
      <div className="h-screen w-screen flex flex-col bg-gradient-to-br from-slate-50 via-white to-slate-50">
        <header className="border-b bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-50">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center shadow-md">
                <FileText className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                DoD Acquisition AI
              </h1>
              <p className="text-xs text-slate-500">Live Document Editor</p>
            </div>
          </div>

          <nav className="hidden lg:flex items-center gap-2">
            <NavButton
              icon={<Home className="h-4 w-4" />}
              label="Dashboard"
              active={route === "DASHBOARD"}
              onClick={() => setRoute("DASHBOARD")}
              highlight
            />
            {/* Quick Generate: One-time package generation without project creation */}
            <NavButton
              icon={<Sparkles className="h-4 w-4" />}
              label="Quick Generate"
              active={route === "QUICK_GENERATE"}
              onClick={() => setRoute("QUICK_GENERATE")}
              highlight
            />
            <NavButton
              icon={<TrendingUp className="h-4 w-4" />}
              label="Tracker"
              active={route === "PROCUREMENT_TRACKER"}
              onClick={() => setRoute("PROCUREMENT_TRACKER")}
              highlight
            />
            <NavButton
              icon={<UserCheck className="h-4 w-4" />}
              label="Approvals"
              active={route === "PENDING_APPROVALS"}
              onClick={() => setRoute("PENDING_APPROVALS")}
              highlight
            />
            {/* Uploads and Workflow tabs removed - replaced by Quick Generate wizard */}
            <NavButton
              icon={<FileText className="h-4 w-4" />}
              label="Editor"
              active={route === "EDITOR"}
              onClick={() => setRoute("EDITOR")}
            />
            <NavButton
              icon={<Download className="h-4 w-4" />}
              label="Export"
              active={route === "EXPORT"}
              onClick={() => setRoute("EXPORT")}
            />
            {/* Admin panel - only visible to admin users */}
            {user?.role === 'admin' && (
              <NavButton
                icon={<Settings className="h-4 w-4" />}
                label="Admin"
                active={route === "ADMIN"}
                onClick={() => setRoute("ADMIN")}
                highlight
              />
            )}
            <NotificationCenter />
            
            {/* User Menu */}
            {user && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="gap-2 ml-2">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <User className="h-4 w-4 text-blue-600" />
                    </div>
                    <span className="hidden md:inline text-sm font-medium">{user.name}</span>
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col">
                      <span className="font-medium">{user.name}</span>
                      <span className="text-xs text-slate-500 capitalize">
                        {user.role.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-slate-400 mt-1">{user.email}</span>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={() => signOut()} 
                    className="text-red-600 cursor-pointer focus:text-red-600 focus:bg-red-50"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1 overflow-auto">
        {route === "DASHBOARD" && (
          <DashboardView
            onNavigate={(newRoute) => setRoute(newRoute)}
            onSelectProject={(projectId) => {
              setSelectedProjectId(projectId);
              setRoute("PROCUREMENT_TRACKER");
            }}
          />
        )}
        {/* Quick Generate: One-time package generation wizard */}
        {route === "QUICK_GENERATE" && (
          <QuickGenerateTab
            onOpenEditor={(sections) => {
              // Transfer generated sections to the main editor
              setEditorSections(sections);
              setRoute("EDITOR");
            }}
            onComplete={(sections) => {
              // Optional: Handle completion (e.g., for analytics)
              setEditorSections(sections);
              setRoute("EDITOR");
            }}
          />
        )}
        {route === "PROCUREMENT_TRACKER" && (
          <ProcurementHub
            initialProjectId={selectedProjectId}
            onProjectChange={setSelectedProjectId}
          />
        )}
        {route === "PENDING_APPROVALS" && <PendingApprovalsView />}
        {route === "ADMIN" && <AdminUserManagement />}
        {/* StrategyBoard route removed - Board tab eliminated from UX */}
        {route === "UPLOAD_CENTER" && (
          <UploadCenter
            uploads={uploads}
            setUploads={setUploads}
            parsed={parsed}
            setParsed={setParsed}
            onExtract={(assumptions) => {
              // After extraction, go to the unified Document Workflow
              setLockedAssumptions(assumptions);
              setRoute("DOCUMENT_WORKFLOW");
            }}
            onBack={() => setRoute("EDITOR")}
          />
        )}
        {/* Unified Document Workflow - Assumptions, Traceability, and Generation Plan in one place */}
        {route === "DOCUMENT_WORKFLOW" && (
          <DocumentWorkflow
            assumptions={lockedAssumptions}
            setAssumptions={setLockedAssumptions}
            locked={planLocked}
            onLock={() => setPlanLocked(true)}
            onUnlock={() => setPlanLocked(false)}
            onGenerate={handleGenerateDocuments}
            onBack={() => setRoute("EDITOR")}
          />
        )}
        {route === "GENERATING" && (
          <GeneratingView progress={generationProgress} />
        )}
        {route === "EDITOR" && (
          <LiveEditor
            lockedAssumptions={lockedAssumptions}
            sections={editorSections}
            setSections={setEditorSections}
            citations={parsed.citations}
            agentMetadata={agentMetadata}
            collaborationMetadata={collaborationMetadata}
            initialQualityScores={qualityAnalysis}
            onExport={() => setRoute("EXPORT")}
            onBack={() => setRoute("DOCUMENT_WORKFLOW")}
          />
        )}
        {route === "EXPORT" && (
          <ExportView
            sections={editorSections}
            citations={parsed.citations}
            metadata={{
              project_name: parsed.project_name,
              assumptions: parsed.assumptions,
            }}
            agentMetadata={agentMetadata}
            collaborationMetadata={collaborationMetadata}
            onBack={() => setRoute("EDITOR")}
          />
        )}
      </main>
    </div>
  );
}

function AuthenticatedApp() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  // Wrap MainApp with EditorNavigationProvider to enable "Open in Editor" from Procurement Tracker
  return (
    <EditorNavigationProvider>
      <MainApp />
    </EditorNavigationProvider>
  );
}

export default function AIContractingUI() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}

interface NavButtonProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  highlight?: boolean;
}

function NavButton({ icon, label, active, onClick, highlight }: NavButtonProps) {
  return (
    <Button
      variant={active ? "default" : "ghost"}
      size="sm"
      onClick={onClick}
      className={`gap-2 ${highlight && !active ? 'border-blue-200 hover:border-blue-300 hover:bg-blue-50' : ''}`}
    >
      {icon}
      <span className="hidden md:inline">{label}</span>
    </Button>
  );
}

interface GeneratingViewProps {
  progress: number;
}

// Fun rotating messages to keep users engaged while waiting
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

function GeneratingView({ progress }: GeneratingViewProps) {
  // State for rotating through fun loading messages
  const [messageIndex, setMessageIndex] = useState(0);
  // State for animated dots (cycles through "", ".", "..", "...")
  const [dots, setDots] = useState("");

  // Rotate through messages every 3 seconds
  useEffect(() => {
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);

    return () => clearInterval(messageInterval);
  }, []);

  // Animate dots every 500ms for a smooth loading effect
  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots((prev) => {
        if (prev === "...") return "";
        return prev + ".";
      });
    }, 500);

    return () => clearInterval(dotsInterval);
  }, []);

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <div className="flex flex-col items-center justify-center min-h-[600px]">
        <div className="text-center space-y-8">
          {/* DotLottie Animation */}
          <div className="relative mx-auto">
            <div className="w-64 h-64 mx-auto">
              <DotLottieReact
                src="https://lottie.host/599a9594-2bc0-4177-b1f3-b4939ad8516e/0orfoYqcjG.lottie"
                loop
                autoplay
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>

          <div className="space-y-3">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">
              Generating Documents
            </h1>
            <p className="text-lg text-muted-foreground">
              AI agents are analyzing assumptions and creating your acquisition documents...
            </p>
          </div>

          {/* Animated rotating messages - more engaging than static percentage */}
          <div className="w-full max-w-md mx-auto">
            <div className="text-center space-y-3">
              {/* Rotating message with animated dots */}
              <div className="flex items-center justify-center">
                <span className="text-xl font-medium text-slate-700 transition-opacity duration-300">
                  {LOADING_MESSAGES[messageIndex]}
                </span>
                <span className="text-xl font-medium text-blue-600 w-8 text-left">{dots}</span>
              </div>
              {/* Helpful time estimate */}
              <p className="text-sm text-muted-foreground">
                This usually takes 30-60 seconds
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-12">
            <div className="p-4 rounded-lg border bg-white shadow-sm">
              <FileText className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <div className="text-sm font-medium">Extracting Context</div>
              <div className="text-xs text-muted-foreground mt-1">From RAG documents</div>
            </div>
            <div className="p-4 rounded-lg border bg-white shadow-sm">
              <Sparkles className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
              <div className="text-sm font-medium">Generating Content</div>
              <div className="text-xs text-muted-foreground mt-1">Using AI agents</div>
            </div>
            <div className="p-4 rounded-lg border bg-white shadow-sm">
              <Shield className="h-8 w-8 text-purple-600 mx-auto mb-2" />
              <div className="text-sm font-medium">Validating Quality</div>
              <div className="text-xs text-muted-foreground mt-1">Ensuring compliance</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
