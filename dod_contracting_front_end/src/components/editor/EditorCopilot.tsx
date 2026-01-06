/**
 * EditorCopilot Component
 * 
 * A draggable AI assistant popup that appears when text is selected in the editor.
 * Provides quick actions for document editing assistance.
 * 
 * Features:
 * - Centered on screen when opened (can be dragged to reposition)
 * - Draggable header for repositioning
 * - Quick action buttons for common operations
 * - Custom prompt input
 * - Loading states and response display
 * 
 * Dependencies:
 * - copilotApi from services/api
 * - TipTap Editor instance
 * - Shadcn UI components
 */

import { useState, useEffect, useRef, useCallback } from "react";
import {
  MessageCircle, Wand2, Expand, FileText, Quote, Shield,
  Sparkles, Loader2, X, ChevronDown, ChevronUp, Copy, Check,
  Send, RotateCcw, GripHorizontal, Globe
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { copilotApi, type CopilotAction, type WebSearchType } from "@/services/api";
import { toast } from "sonner";
import { Editor } from "@tiptap/react";

// Props for the EditorCopilot component
interface EditorCopilotProps {
  editor: Editor | null;
  sectionName: string;
  isVisible: boolean;
  position: { top: number; left: number };
  selectedText: string;
  onClose: () => void;
  onApplyText: (newText: string) => void;
}

// Quick action configuration
const QUICK_ACTIONS: Array<{
  action: CopilotAction;
  label: string;
  icon: React.ReactNode;
  description: string;
  color: string;
}> = [
  {
    action: "answer",
    label: "Ask",
    icon: <MessageCircle className="h-4 w-4" />,
    description: "Ask a question about this text",
    color: "bg-blue-500"
  },
  {
    action: "rewrite",
    label: "Rewrite",
    icon: <Wand2 className="h-4 w-4" />,
    description: "Improve and rewrite the text",
    color: "bg-purple-500"
  },
  {
    action: "expand",
    label: "Expand",
    icon: <Expand className="h-4 w-4" />,
    description: "Add more detail and elaboration",
    color: "bg-emerald-500"
  },
  {
    action: "summarize",
    label: "Summarize",
    icon: <FileText className="h-4 w-4" />,
    description: "Create a concise summary",
    color: "bg-amber-500"
  },
  {
    action: "citations",
    label: "Citations",
    icon: <Quote className="h-4 w-4" />,
    description: "Add FAR/DFARS citations",
    color: "bg-cyan-500"
  },
  {
    action: "compliance",
    label: "Compliance",
    icon: <Shield className="h-4 w-4" />,
    description: "Check for compliance issues",
    color: "bg-red-500"
  },
  {
    action: "web_search",
    label: "Web Search",
    icon: <Globe className="h-4 w-4" />,
    description: "Search the web for information",
    color: "bg-indigo-500"
  }
];

// Web search type options for dropdown
const WEB_SEARCH_TYPES: Array<{
  value: WebSearchType;
  label: string;
  description: string;
}> = [
  { value: "general", label: "General Search", description: "Search for general information" },
  { value: "vendor", label: "Vendor Info", description: "Search for vendor/company information" },
  { value: "pricing", label: "Market Pricing", description: "Search for market pricing data" },
  { value: "awards", label: "Recent Awards", description: "Search for recent contract awards" },
  { value: "small_business", label: "Small Business", description: "Search for small business certifications" }
];

export function EditorCopilot({
  editor,
  sectionName,
  isVisible,
  position: _position, // Unused - we now center the popup
  selectedText,
  onClose,
  onApplyText
}: EditorCopilotProps) {
  // State management
  const [activeAction, setActiveAction] = useState<CopilotAction | null>(null);
  const [customPrompt, setCustomPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showResponse, setShowResponse] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  // Web search specific state
  const [webSearchType, setWebSearchType] = useState<WebSearchType>("general");
  const [showSearchOptions, setShowSearchOptions] = useState(false);
  
  // Drag state for repositioning the popup
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const initialOffsetRef = useRef({ x: 0, y: 0 });
  
  // Ref for the popup container
  const popupRef = useRef<HTMLDivElement>(null);

  // Reset state when visibility changes
  useEffect(() => {
    if (!isVisible) {
      setActiveAction(null);
      setCustomPrompt("");
      setResponse("");
      setShowResponse(false);
      setIsExpanded(false);
      setShowSearchOptions(false);
      setWebSearchType("general");
      // Reset drag position when closed so it re-centers on next open
      setDragOffset({ x: 0, y: 0 });
    }
  }, [isVisible]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        // Don't close if clicking on editor selection
        const selection = window.getSelection();
        if (selection && selection.toString().trim()) {
          return;
        }
        onClose();
      }
    };

    if (isVisible) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isVisible, onClose]);

  // Handle escape key to close
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    if (isVisible) {
      document.addEventListener("keydown", handleEscape);
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isVisible, onClose]);

  // Handle drag start on header
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    initialOffsetRef.current = { ...dragOffset };
  }, [dragOffset]);

  // Handle drag move
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      const deltaX = e.clientX - dragStartRef.current.x;
      const deltaY = e.clientY - dragStartRef.current.y;
      
      setDragOffset({
        x: initialOffsetRef.current.x + deltaX,
        y: initialOffsetRef.current.y + deltaY
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  // Get surrounding context from editor
  const getContext = useCallback(() => {
    if (!editor) return "";
    
    // Get full document text for context
    const fullText = editor.getText();
    const maxContextLength = 500;
    
    // Find position of selected text and extract surrounding context
    const selectedPos = fullText.indexOf(selectedText);
    if (selectedPos === -1) return fullText.slice(0, maxContextLength);
    
    const start = Math.max(0, selectedPos - 200);
    const end = Math.min(fullText.length, selectedPos + selectedText.length + 200);
    
    return fullText.slice(start, end);
  }, [editor, selectedText]);

  // Handle quick action click
  const handleQuickAction = async (action: CopilotAction, searchType?: WebSearchType) => {
    // For web_search action, show search options first if not already selected
    if (action === "web_search" && !searchType && !showSearchOptions) {
      setShowSearchOptions(true);
      setActiveAction(action);
      return;
    }

    setActiveAction(action);
    setShowResponse(true);
    setIsLoading(true);
    setResponse("");
    setShowSearchOptions(false);

    try {
      const context = getContext();
      const result = await copilotApi.assist(
        action,
        selectedText,
        context,
        sectionName,
        action === "custom" ? customPrompt : undefined,
        action === "web_search" ? (searchType || webSearchType) : undefined
      );
      
      setResponse(result.result);
    } catch (error: any) {
      console.error("Copilot error:", error);
      toast.error(`Copilot error: ${error.message}`);
      setResponse("An error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle custom prompt submission
  const handleCustomSubmit = async () => {
    if (!customPrompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }

    setActiveAction("custom");
    setShowResponse(true);
    setIsLoading(true);
    setResponse("");

    try {
      const context = getContext();
      const result = await copilotApi.assist(
        "custom",
        selectedText,
        context,
        sectionName,
        customPrompt
      );
      
      setResponse(result.result);
    } catch (error: any) {
      console.error("Copilot error:", error);
      toast.error(`Copilot error: ${error.message}`);
      setResponse("An error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle apply to editor - works for rewrite, expand, citations, and custom actions
  const handleApply = () => {
    if (response && activeAction && ["rewrite", "expand", "citations", "custom"].includes(activeAction)) {
      onApplyText(response);
      toast.success("Text applied to editor");
      onClose();
    }
  };

  // Handle copy to clipboard
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Copied to clipboard");
    } catch {
      toast.error("Failed to copy");
    }
  };

  // Handle retry
  const handleRetry = () => {
    if (activeAction) {
      handleQuickAction(activeAction);
    }
  };

  if (!isVisible) return null;

  return (
    <div
      ref={popupRef}
      className="fixed z-50 animate-in fade-in-0 zoom-in-95 duration-200"
      style={{
        // Center on screen with drag offset applied
        top: `calc(50% + ${dragOffset.y}px)`,
        left: `calc(50% + ${dragOffset.x}px)`,
        transform: "translate(-50%, -50%)",
        maxWidth: "min(90vw, 500px)",
        width: "500px"
      }}
    >
      <Card className="shadow-2xl border-2 border-blue-200/50 bg-white/95 backdrop-blur-sm">
        {/* Draggable Header - grab this to move the popup */}
        <CardHeader 
          className={`p-3 pb-2 flex flex-row items-center justify-between ${
            isDragging ? "cursor-grabbing" : "cursor-grab"
          }`}
          onMouseDown={handleDragStart}
        >
          <div className="flex items-center gap-2">
            {/* Drag handle indicator */}
            <div 
              className="flex flex-col items-center justify-center text-slate-400 mr-1"
              title="Drag to move"
            >
              <GripHorizontal className="h-4 w-4" />
            </div>
            <div className="h-7 w-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <h4 className="text-sm font-semibold select-none">AI Copilot</h4>
              <p className="text-[10px] text-muted-foreground select-none">
                {selectedText.length} characters selected • Drag to move
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-[10px] gap-1"
              onClick={() => setIsExpanded(!isExpanded)}
              title={isExpanded ? "Hide selected text" : "Show selected text"}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3" />
                  Hide
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" />
                  Show
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-[10px] gap-1"
              onClick={onClose}
              title="Close Copilot"
            >
              <X className="h-3 w-3" />
              Close
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-3 pt-0 space-y-3">
          {/* Selected Text Preview */}
          {isExpanded && (
            <div className="bg-slate-50 rounded-lg p-2 border">
              <p className="text-[10px] font-medium text-slate-500 mb-1">SELECTED TEXT</p>
              <p className="text-xs text-slate-700 line-clamp-3">
                {selectedText}
              </p>
            </div>
          )}

          {/* Quick Actions */}
          <div className="flex flex-wrap gap-1.5">
            {QUICK_ACTIONS.map((qa) => (
              <Button
                key={qa.action}
                variant={activeAction === qa.action ? "default" : "outline"}
                size="sm"
                className={`h-8 text-xs gap-1.5 ${
                  activeAction === qa.action ? "" : "hover:bg-slate-100"
                } ${qa.action === "web_search" ? "bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200 hover:from-indigo-100 hover:to-purple-100" : ""}`}
                onClick={() => handleQuickAction(qa.action)}
                disabled={isLoading}
                title={qa.description}
              >
                {qa.icon}
                {qa.label}
              </Button>
            ))}
          </div>

          {/* Web Search Options - shown when web_search is selected */}
          {showSearchOptions && activeAction === "web_search" && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-3 border border-indigo-200 space-y-3">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-indigo-600" />
                <span className="text-sm font-medium text-indigo-900">Web Search Options</span>
              </div>
              
              <div className="space-y-2">
                <label className="text-xs text-indigo-700">Search Type:</label>
                <Select value={webSearchType} onValueChange={(v) => setWebSearchType(v as WebSearchType)}>
                  <SelectTrigger className="h-8 text-xs bg-white">
                    <SelectValue placeholder="Select search type" />
                  </SelectTrigger>
                  <SelectContent>
                    {WEB_SEARCH_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value} className="text-xs">
                        <div>
                          <span className="font-medium">{type.label}</span>
                          <span className="text-muted-foreground ml-2">- {type.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 h-8 text-xs"
                  onClick={() => setShowSearchOptions(false)}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="flex-1 h-8 text-xs bg-indigo-600 hover:bg-indigo-700"
                  onClick={() => handleQuickAction("web_search", webSearchType)}
                  disabled={isLoading}
                >
                  <Globe className="h-3 w-3 mr-1" />
                  Search Web
                </Button>
              </div>
            </div>
          )}

          {/* Custom Prompt Input */}
          <div className="flex gap-2">
            <Textarea
              placeholder="Or type a custom instruction..."
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              className="min-h-[36px] max-h-[80px] text-xs resize-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleCustomSubmit();
                }
              }}
            />
            <Button
              size="sm"
              className="h-9 px-3 shrink-0 text-xs gap-1.5"
              onClick={handleCustomSubmit}
              disabled={isLoading || !customPrompt.trim()}
              title="Send custom instruction"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              Send
            </Button>
          </div>

          {/* Response Area */}
          {showResponse && (
            <>
              <Separator />
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-[10px]">
                    {activeAction ? QUICK_ACTIONS.find(a => a.action === activeAction)?.label || "Custom" : "Response"}
                  </Badge>
                  
                  {!isLoading && response && (
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-[10px] gap-1"
                        onClick={handleRetry}
                        title="Retry request"
                      >
                        <RotateCcw className="h-3 w-3" />
                        Retry
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-[10px] gap-1"
                        onClick={handleCopy}
                        title="Copy to clipboard"
                      >
                        {copied ? (
                          <Check className="h-3 w-3 text-green-500" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                        {copied ? "Copied" : "Copy"}
                      </Button>
                    </div>
                  )}
                </div>

                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                      <p className="text-xs text-muted-foreground">Generating...</p>
                    </div>
                  </div>
                ) : (
                  <div className="max-h-[250px] overflow-y-auto rounded-lg border bg-slate-50">
                    <div className="text-sm whitespace-pre-wrap p-3">
                      {response}
                    </div>
                  </div>
                )}

                {/* Apply/Insert Buttons - shown for rewrite, expand, citations, and custom actions */}
                {!isLoading && response && activeAction && 
                 ["rewrite", "expand", "citations", "custom"].includes(activeAction) && (
                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      className="flex-1 h-8 text-xs bg-gradient-to-r from-blue-600 to-purple-600"
                      onClick={handleApply}
                      title="Replace selected text with AI suggestion"
                    >
                      <Wand2 className="h-3 w-3 mr-1.5" />
                      Apply to Editor
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs"
                      onClick={handleCopy}
                      title="Copy AI suggestion to clipboard"
                    >
                      <Copy className="h-3 w-3 mr-1.5" />
                      Copy
                    </Button>
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default EditorCopilot;

