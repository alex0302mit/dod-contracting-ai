import React, { useMemo, useState } from "react";

/**
 * AI Contracting UI — Enhanced Prototype (Assumption‑Driven Flow)
 * v9 — Complete Live Editor with:
 *  • Before/After split view with Accept/Reject redlines
 *  • Real-time editing with quality scoring
 *  • Version History (commit/restore/compare)
 *  • Inline clickable citation chips + PDF preview
 *  • Section Quality Score meter with breakdown
 *  • Auto‑Improve to 85+ (proposes targeted changes)
 *  • Upload parsing + Assumptions Diff + Generation Plan
 */

const R = {
  STRATEGY_BOARD: "strategy_board",
  UPLOAD_CENTER: "upload_center",
  ASSUMPTION_MAP: "assumption_map",
  DIFF: "assumption_diff",
  TRACE_MATRIX: "trace_matrix",
  GEN_PLAN: "gen_plan",
  EDITOR: "editor",
  COMPLIANCE: "compliance",
  EXPORT: "export",
};

export default function App() {
  const [route, setRoute] = useState(R.EDITOR); // Start at editor for demo
  const [uploads, setUploads] = useState({ strategy: [], reqs: [] });
  const [parsed, setParsed] = useState({ 
    assumptions: [], 
    reqSnippets: [], 
    pdfPreview: null,
    citations: [
      { id: 1, source: "FAR 15.304", page: 12, text: "Evaluation factors must be stated in the solicitation", bbox: {x:30,y:40,w:200,h:16} },
      { id: 2, source: "Acq Strategy §3.2", page: 8, text: "Best Value Tradeoff evaluation approach", bbox: {x:30,y:80,w:180,h:16} },
      { id: 3, source: "DFARS 252.204-7012", page: 1, text: "Safeguarding covered defense information and cyber incident reporting", bbox: {x:30,y:120,w:220,h:16} },
    ]
  });
  const [lockedAssumptions, setLockedAssumptions] = useState([
    { id: "a1", text: "BVTO evaluation with weighted factors", source: "Acq Strategy §3.2" },
    { id: "a2", text: "IDIQ base + 4 option years", source: "Acq Strategy §2.1" },
    { id: "a3", text: "CUI handling required for vendor data", source: "Reqs §5" },
  ]);
  const [planLocked, setPlanLocked] = useState(false);

  // Editor sections with initial content
  const [editorSections, setEditorSections] = useState({
    Overview: "This notice intends to synopsize the acquisition action and describes evaluation factors [1]. Vendors must follow the instructions provided in Section L.",
    "Evaluation Approach": "The Government will conduct a Best Value Tradeoff evaluation [2] considering Technical, Past Performance, and Price. The SSA retains tradeoff authority.",
    Schedule: "The Government anticipates award in Q2 FY25. Timeline TBD subject to approvals.",
    "Security Requirements": "Contractors must comply with CUI handling requirements [3] and implement appropriate safeguarding measures.",
  });

  return (
    <div className="h-screen w-screen bg-neutral-50 text-neutral-900">
      <Top onNav={setRoute} route={route} />
      <div className="h-[calc(100vh-56px)] overflow-auto">
        {route === R.STRATEGY_BOARD && (
          <StrategyBoard
            onStart={()=>setRoute(R.UPLOAD_CENTER)}
            onAssumptions={()=>setRoute(R.ASSUMPTION_MAP)}
            onTrace={()=>setRoute(R.TRACE_MATRIX)}
            onPlan={()=>setRoute(R.GEN_PLAN)}
          />
        )}
        {route === R.UPLOAD_CENTER && (
          <UploadCenter
            uploads={uploads}
            setUploads={setUploads}
            parsed={parsed}
            setParsed={setParsed}
            onExtract={()=>setRoute(R.ASSUMPTION_MAP)}
            onDiff={()=>setRoute(R.DIFF)}
            onBack={()=>setRoute(R.STRATEGY_BOARD)}
          />
        )}
        {route === R.ASSUMPTION_MAP && (
          <AssumptionMap
            assumptions={lockedAssumptions}
            setAssumptions={setLockedAssumptions}
            onTrace={()=>setRoute(R.TRACE_MATRIX)}
            onBack={()=>setRoute(R.UPLOAD_CENTER)}
          />
        )}
        {route === R.DIFF && (
          <AssumptionDiff
            previous={lockedAssumptions}
            next={parsed.assumptions}
            onAccept={(merged)=>{ setLockedAssumptions(merged); setRoute(R.ASSUMPTION_MAP); }}
            onBack={()=>setRoute(R.UPLOAD_CENTER)}
          />
        )}
        {route === R.TRACE_MATRIX && (
          <TraceMatrix onBack={()=>setRoute(R.ASSUMPTION_MAP)} onPlan={()=>setRoute(R.GEN_PLAN)} />
        )}
        {route === R.GEN_PLAN && (
          <GenerationPlan 
            locked={planLocked} 
            onLock={()=>setPlanLocked(true)} 
            onEdit={()=>setPlanLocked(false)} 
            onGenerate={()=>setRoute(R.EDITOR)} 
            onBack={()=>setRoute(R.TRACE_MATRIX)} 
          />
        )}
        {route === R.EDITOR && (
          <LiveEditor
            lockedAssumptions={lockedAssumptions}
            sections={editorSections}
            setSections={setEditorSections}
            citations={parsed.citations}
            onCompliance={()=>setRoute(R.COMPLIANCE)}
            onExport={()=>setRoute(R.EXPORT)}
            onBack={()=>setRoute(R.GEN_PLAN)}
          />
        )}
        {route === R.COMPLIANCE && <Compliance onBack={()=>setRoute(R.EDITOR)} onExport={()=>setRoute(R.EXPORT)} />}
        {route === R.EXPORT && <Export onBack={()=>setRoute(R.EDITOR)} />}
      </div>
    </div>
  );
}

function Top({ onNav, route }) {
  const btn = (id, label) => (
    <button
      onClick={()=>onNav(id)}
      className={`px-3 py-1 rounded border text-xs ${route===id?"bg-neutral-900 text-white":"bg-white hover:bg-neutral-100"}`}
    >{label}</button>
  );
  return (
    <div className="h-14 border-b bg-white flex items-center gap-2 px-4 text-sm shadow-sm">
      <div className="font-bold text-base">🎯 DoD Acquisition AI — Live Editor</div>
      <div className="ml-auto flex gap-2">
        {btn(R.STRATEGY_BOARD, "Board")}
        {btn(R.UPLOAD_CENTER, "Uploads")}
        {btn(R.ASSUMPTION_MAP, "Assumptions")}
        {btn(R.TRACE_MATRIX, "Traceability")}
        {btn(R.GEN_PLAN, "Gen Plan")}
        {btn(R.EDITOR, "✨ Editor")}
        {btn(R.COMPLIANCE, "Compliance")}
        {btn(R.EXPORT, "Export")}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// LIVE EDITOR — The main attraction
// ═══════════════════════════════════════════════════════════════════════════════

function LiveEditor({ lockedAssumptions, sections, setSections, citations, onCompliance, onExport, onBack }) {
  const sectionNames = Object.keys(sections);
  const [activeSection, setActiveSection] = useState(sectionNames[0]);
  const [viewMode, setViewMode] = useState("edit"); // "edit" | "compare" | "history"
  const [showCitationPreview, setShowCitationPreview] = useState(null);
  
  // Version history management
  const [versionHistory, setVersionHistory] = useState([
    { 
      id: "v0", 
      timestamp: new Date(Date.now() - 3600000).toISOString(), 
      message: "Initial generation", 
      sections: { ...sections },
      author: "AI Agent"
    }
  ]);
  const [compareVersion, setCompareVersion] = useState(null);
  
  // Proposed changes (redlines) for accept/reject
  const [proposedChanges, setProposedChanges] = useState(null);
  const [showAutoImprove, setShowAutoImprove] = useState(false);

  const currentText = sections[activeSection] || "";
  const quality = computeQualityScore(currentText, citations);
  const issues = computeIssues(currentText);

  // Handle text editing
  const handleTextChange = (newText) => {
    setSections({ ...sections, [activeSection]: newText });
  };

  // Commit current state to version history
  const commitVersion = () => {
    const message = prompt("Version commit message:", "Manual edit");
    if (!message) return;
    
    const newVersion = {
      id: `v${versionHistory.length}`,
      timestamp: new Date().toISOString(),
      message,
      sections: { ...sections },
      author: "User"
    };
    setVersionHistory([...versionHistory, newVersion]);
  };

  // Restore a specific version
  const restoreVersion = (version) => {
    if (confirm(`Restore version "${version.message}"? Current changes will be lost.`)) {
      setSections({ ...version.sections });
      setViewMode("edit");
      setCompareVersion(null);
    }
  };

  // Generate auto-improvement suggestions
  const generateAutoImprove = () => {
    // Simulate AI-generated improvements
    const improvements = {
      before: currentText,
      after: autoImproveText(currentText, quality, issues),
      changes: [
        { type: "fix", text: "Replaced 'TBD' with concrete date", line: 2 },
        { type: "enhance", text: "Clarified evaluation factor references", line: 1 },
        { type: "compliance", text: "Added FAR citation for timeline", line: 2 },
      ]
    };
    setProposedChanges(improvements);
    setShowAutoImprove(true);
  };

  // Accept proposed changes
  const acceptChanges = () => {
    if (proposedChanges) {
      handleTextChange(proposedChanges.after);
      setProposedChanges(null);
      setShowAutoImprove(false);
    }
  };

  // Reject proposed changes
  const rejectChanges = () => {
    setProposedChanges(null);
    setShowAutoImprove(false);
  };

  return (
    <div className="h-full flex flex-col bg-neutral-50">
      {/* Top Toolbar */}
      <div className="border-b bg-white px-4 py-3 flex items-center gap-3 shadow-sm">
        <button onClick={onBack} className="px-3 py-1.5 border rounded text-sm hover:bg-neutral-50">
          ← Back
        </button>
        
        <div className="h-6 w-px bg-neutral-300" />
        
        {/* View Mode Tabs */}
        <div className="flex gap-1 border rounded p-1 bg-neutral-100">
          <TabButton active={viewMode === "edit"} onClick={() => setViewMode("edit")}>
            ✏️ Edit
          </TabButton>
          <TabButton active={viewMode === "compare"} onClick={() => setViewMode("compare")}>
            🔍 Compare
          </TabButton>
          <TabButton active={viewMode === "history"} onClick={() => setViewMode("history")}>
            📜 History
          </TabButton>
        </div>

        <div className="h-6 w-px bg-neutral-300" />

        {/* Actions */}
        <button 
          onClick={commitVersion}
          className="px-3 py-1.5 border rounded text-sm bg-blue-50 border-blue-300 hover:bg-blue-100"
        >
          💾 Commit
        </button>
        
        <button 
          onClick={generateAutoImprove}
          disabled={quality.total >= 85}
          className="px-3 py-1.5 border rounded text-sm bg-purple-50 border-purple-300 hover:bg-purple-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ✨ Auto-Improve to 85+
        </button>

        <div className="ml-auto flex items-center gap-3">
          {/* Quality Score Badge */}
          <QualityBadge score={quality.total} />
          
          <button 
            onClick={onCompliance}
            className="px-3 py-1.5 border rounded text-sm hover:bg-neutral-50"
          >
            Compliance →
          </button>
          <button 
            onClick={onExport}
            className="px-3 py-1.5 border rounded text-sm bg-neutral-900 text-white hover:bg-neutral-800"
          >
            Export →
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Section Navigator */}
        <div className="w-64 border-r bg-white flex flex-col">
          <div className="p-4 border-b bg-neutral-50">
            <h3 className="font-bold text-sm">Document Sections</h3>
            <p className="text-xs text-neutral-600 mt-1">{sectionNames.length} sections</p>
          </div>
          <div className="flex-1 overflow-auto">
            {sectionNames.map(name => {
              const sectionQuality = computeQualityScore(sections[name], citations);
              return (
                <button
                  key={name}
                  onClick={() => setActiveSection(name)}
                  className={`w-full text-left px-4 py-3 border-b hover:bg-neutral-50 transition-colors ${
                    activeSection === name ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{name}</div>
                      <div className="text-xs text-neutral-500 mt-1">
                        {sections[name].split(/\s+/).length} words
                      </div>
                    </div>
                    <div className={`text-xs font-bold px-2 py-0.5 rounded ${
                      sectionQuality.total >= 85 ? 'bg-green-100 text-green-800' :
                      sectionQuality.total >= 70 ? 'bg-amber-100 text-amber-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {Math.round(sectionQuality.total)}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Editor Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {viewMode === "edit" && (
            <EditView
              sectionName={activeSection}
              text={currentText}
              onTextChange={handleTextChange}
              quality={quality}
              issues={issues}
              citations={citations}
              onCitationClick={(id) => setShowCitationPreview(id)}
            />
          )}
          
          {viewMode === "compare" && (
            <CompareView
              sections={sections}
              versionHistory={versionHistory}
              compareVersion={compareVersion}
              setCompareVersion={setCompareVersion}
              activeSection={activeSection}
            />
          )}
          
          {viewMode === "history" && (
            <HistoryView
              versionHistory={versionHistory}
              onRestore={restoreVersion}
              onCompare={(v) => {
                setCompareVersion(v);
                setViewMode("compare");
              }}
            />
          )}
        </div>

        {/* Right Sidebar - Context & Citations */}
        <div className="w-80 border-l bg-white flex flex-col overflow-hidden">
          <div className="p-4 border-b bg-neutral-50">
            <h3 className="font-bold text-sm">Context & Citations</h3>
          </div>
          
          <div className="flex-1 overflow-auto p-4 space-y-4">
            {/* Quality Breakdown */}
            <Card title="Quality Breakdown" subtitle={`Overall: ${Math.round(quality.total)}/100`}>
              <div className="space-y-2 text-xs">
                <QualityBar label="Readability" score={quality.breakdown.readability} />
                <QualityBar label="Citations" score={quality.breakdown.citations} />
                <QualityBar label="Compliance" score={quality.breakdown.compliance} />
                <QualityBar label="Length" score={quality.breakdown.length} />
              </div>
            </Card>

            {/* Issues */}
            {issues.length > 0 && (
              <Card title="Issues" subtitle={`${issues.length} found`}>
                <div className="space-y-2">
                  {issues.map(issue => (
                    <div key={issue.id} className="text-xs border rounded p-2 bg-neutral-50">
                      <div className="flex items-start gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          issue.kind === 'error' ? 'bg-red-100 text-red-800' :
                          issue.kind === 'warning' ? 'bg-amber-100 text-amber-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {issue.kind.toUpperCase()}
                        </span>
                        <span className="flex-1">{issue.label}</span>
                      </div>
                      {issue.fix && (
                        <button
                          onClick={() => handleTextChange(issue.fix.apply(currentText))}
                          className="text-[10px] px-2 py-1 border rounded hover:bg-white mt-1"
                        >
                          {issue.fix.label}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Citations */}
            <Card title="Citations" subtitle={`${citations.length} available`}>
              <div className="space-y-2">
                {citations.map(cite => (
                  <button
                    key={cite.id}
                    onClick={() => setShowCitationPreview(cite.id)}
                    className={`w-full text-left border rounded p-2 text-xs hover:bg-neutral-50 transition-colors ${
                      showCitationPreview === cite.id ? 'bg-blue-50 border-blue-300' : 'bg-white'
                    }`}
                  >
                    <div className="font-bold mb-1">[{cite.id}] {cite.source}</div>
                    <div className="text-neutral-600 text-[11px]">
                      {cite.text.length > 80 ? cite.text.slice(0, 80) + '...' : cite.text}
                    </div>
                  </button>
                ))}
              </div>
            </Card>

            {/* Locked Assumptions */}
            <Card title="Locked Assumptions" subtitle={`${lockedAssumptions.length} active`}>
              <div className="space-y-1.5">
                {lockedAssumptions.map(a => (
                  <div key={a.id} className="text-xs border rounded p-2 bg-neutral-50">
                    <div className="font-medium mb-0.5">{a.text}</div>
                    <div className="text-neutral-500 text-[10px]">{a.source}</div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Citation Preview Modal */}
      {showCitationPreview && (
        <CitationPreviewModal
          citation={citations.find(c => c.id === showCitationPreview)}
          onClose={() => setShowCitationPreview(null)}
        />
      )}

      {/* Auto-Improve Modal */}
      {showAutoImprove && proposedChanges && (
        <AutoImproveModal
          before={proposedChanges.before}
          after={proposedChanges.after}
          changes={proposedChanges.changes}
          onAccept={acceptChanges}
          onReject={rejectChanges}
        />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// EDITOR VIEW COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

function EditView({ sectionName, text, onTextChange, quality, issues, citations, onCitationClick }) {
  const renderedText = renderInlineCitations(text, citations, onCitationClick);
  const highlightedText = highlightIssues(renderedText);

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">{sectionName}</h2>
          <div className="flex items-center gap-2 text-sm text-neutral-600">
            <span>{text.split(/\s+/).length} words</span>
            <span>•</span>
            <span>{text.length} chars</span>
            <span>•</span>
            <span>{issues.length} issues</span>
          </div>
        </div>

        {/* Live Preview */}
        <div className="bg-white border rounded-lg p-6 mb-4 shadow-sm">
          <div className="text-sm text-neutral-600 mb-2 font-medium">Preview:</div>
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: highlightedText }}
          />
        </div>

        {/* Editor Textarea */}
        <div className="bg-white border rounded-lg shadow-sm">
          <div className="border-b px-4 py-2 bg-neutral-50 flex items-center justify-between">
            <div className="text-sm font-medium">Edit Mode</div>
            <div className="text-xs text-neutral-500">
              Real-time quality scoring • Click [#] for citations
            </div>
          </div>
          <textarea
            value={text}
            onChange={(e) => onTextChange(e.target.value)}
            className="w-full p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-b-lg"
            rows={15}
            placeholder="Enter section content..."
          />
        </div>
      </div>
    </div>
  );
}

function CompareView({ sections, versionHistory, compareVersion, setCompareVersion, activeSection }) {
  const currentText = sections[activeSection] || "";
  const versionText = compareVersion ? compareVersion.sections[activeSection] || "" : currentText;

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold mb-2">Compare Versions</h2>
        <select
          value={compareVersion?.id || "current"}
          onChange={(e) => {
            const v = versionHistory.find(h => h.id === e.target.value);
            setCompareVersion(v || null);
          }}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="current">Current (unsaved)</option>
          {versionHistory.map(v => (
            <option key={v.id} value={v.id}>
              {v.message} — {new Date(v.timestamp).toLocaleString()}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Before */}
        <Card title="Before" subtitle={compareVersion ? compareVersion.message : "Current"}>
          <div className="bg-neutral-50 rounded p-4 font-mono text-xs whitespace-pre-wrap max-h-96 overflow-auto">
            {versionText || "(empty)"}
          </div>
        </Card>

        {/* After */}
        <Card title="After" subtitle="Current version">
          <div className="bg-neutral-50 rounded p-4 font-mono text-xs whitespace-pre-wrap max-h-96 overflow-auto">
            {currentText || "(empty)"}
          </div>
        </Card>
      </div>

      {/* Diff View */}
      <div className="mt-4">
        <Card title="Changes" subtitle="Line-by-line diff">
          <div className="bg-neutral-50 rounded p-4 font-mono text-xs max-h-64 overflow-auto">
            {generateDiff(versionText, currentText)}
          </div>
        </Card>
      </div>
    </div>
  );
}

function HistoryView({ versionHistory, onRestore, onCompare }) {
  return (
    <div className="flex-1 overflow-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Version History</h2>
      
      <div className="space-y-2">
        {versionHistory.slice().reverse().map((version, idx) => (
          <div key={version.id} className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="font-bold">{version.message}</div>
                <div className="text-xs text-neutral-500 mt-1">
                  {new Date(version.timestamp).toLocaleString()} • by {version.author}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => onCompare(version)}
                  className="px-3 py-1 border rounded text-xs hover:bg-neutral-50"
                >
                  Compare
                </button>
                {idx > 0 && (
                  <button
                    onClick={() => onRestore(version)}
                    className="px-3 py-1 border rounded text-xs bg-blue-50 border-blue-300 hover:bg-blue-100"
                  >
                    Restore
                  </button>
                )}
              </div>
            </div>
            
            <div className="text-xs text-neutral-600">
              {Object.keys(version.sections).length} sections • {
                Object.values(version.sections).reduce((sum, s) => sum + s.split(/\s+/).length, 0)
              } total words
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODALS
// ═══════════════════════════════════════════════════════════════════════════════

function CitationPreviewModal({ citation, onClose }) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
        <div className="border-b px-6 py-4 flex items-center justify-between bg-neutral-50">
          <h3 className="font-bold text-lg">Citation Preview — [{citation.id}]</h3>
          <button onClick={onClose} className="text-neutral-500 hover:text-neutral-900">✕</button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <div className="text-sm font-bold text-neutral-600 mb-1">Source</div>
            <div className="text-base">{citation.source}</div>
          </div>
          
          <div>
            <div className="text-sm font-bold text-neutral-600 mb-1">Referenced Text</div>
            <div className="bg-neutral-50 rounded p-4 text-sm border-l-4 border-blue-500">
              {citation.text}
            </div>
          </div>
          
          <div>
            <div className="text-sm font-bold text-neutral-600 mb-2">PDF Preview — Page {citation.page}</div>
            <PDFRenderer page={citation.page} bbox={citation.bbox} />
          </div>
        </div>
        
        <div className="border-t px-6 py-4 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 border rounded hover:bg-neutral-50">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function AutoImproveModal({ before, after, changes, onAccept, onReject }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-auto">
        <div className="border-b px-6 py-4 bg-purple-50">
          <h3 className="font-bold text-lg">✨ Auto-Improve Suggestions</h3>
          <p className="text-sm text-neutral-600 mt-1">Review proposed changes to improve quality score to 85+</p>
        </div>
        
        <div className="p-6">
          {/* Changes Summary */}
          <div className="mb-6">
            <h4 className="font-bold mb-3">Proposed Changes ({changes.length})</h4>
            <div className="space-y-2">
              {changes.map((change, idx) => (
                <div key={idx} className="flex items-start gap-3 text-sm border rounded p-3 bg-neutral-50">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    change.type === 'fix' ? 'bg-red-100 text-red-800' :
                    change.type === 'enhance' ? 'bg-blue-100 text-blue-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {change.type.toUpperCase()}
                  </span>
                  <span className="flex-1">{change.text}</span>
                  <span className="text-neutral-500 text-xs">Line {change.line}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Before/After Comparison */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <div className="font-bold mb-2 text-sm">Before</div>
              <div className="bg-red-50 border border-red-200 rounded p-4 font-mono text-xs whitespace-pre-wrap max-h-64 overflow-auto">
                {before}
              </div>
            </div>
            <div>
              <div className="font-bold mb-2 text-sm flex items-center gap-2">
                After
                <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-[10px] font-bold">
                  IMPROVED
                </span>
              </div>
              <div className="bg-green-50 border border-green-200 rounded p-4 font-mono text-xs whitespace-pre-wrap max-h-64 overflow-auto">
                {after}
              </div>
            </div>
          </div>
        </div>
        
        <div className="border-t px-6 py-4 flex justify-end gap-3 bg-neutral-50">
          <button 
            onClick={onReject}
            className="px-4 py-2 border rounded hover:bg-white"
          >
            Reject Changes
          </button>
          <button 
            onClick={onAccept}
            className="px-4 py-2 border rounded bg-green-600 text-white hover:bg-green-700"
          >
            ✓ Accept All Changes
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SUPPORTING ROUTE COMPONENTS (Simplified versions)
// ═══════════════════════════════════════════════════════════════════════════════

function UploadCenter({ uploads, setUploads, parsed, setParsed, onExtract, onBack, onDiff }) {
  const add = (k) => setUploads({ ...uploads, [k]: [...uploads[k], `${k}‑doc‑${uploads[k].length+1}.pdf`] });

  const parseFiles = () => {
    const newAssumptions = [
      { id: "a1", text: "BVTO evaluation with weighted factors (updated weights)", source: "Acq Strategy §3.2" },
      { id: "a2", text: "IDIQ base + 4 option years", source: "Acq Strategy §2.1" },
      { id: "a4", text: "Industry engagement includes virtual Industry Day", source: "Strategy Annex B" },
    ];
    setParsed({ ...parsed, assumptions: newAssumptions });
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Upload Center</h1>
      <div className="grid grid-cols-2 gap-4">
        <Card title="Acquisition Strategy" subtitle=".pdf/.docx">
          <button className="px-3 py-1.5 border rounded text-sm mb-2" onClick={()=>add("strategy")}>
            Add Strategy
          </button>
          <List items={uploads.strategy.length ? uploads.strategy : ["— none —"]} />
        </Card>
        <Card title="Requirements" subtitle="Reqs, CDRLs">
          <button className="px-3 py-1.5 border rounded text-sm mb-2" onClick={()=>add("reqs")}>
            Add Requirement
          </button>
          <List items={uploads.reqs.length ? uploads.reqs : ["— none —"]} />
        </Card>
      </div>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-3 py-2 border rounded">← Back</button>
        <button onClick={parseFiles} className="px-3 py-2 border rounded bg-blue-600 text-white">
          Parse Files
        </button>
        <button onClick={onExtract} className="ml-auto px-3 py-2 border rounded">
          Assumptions →
        </button>
      </div>
    </div>
  );
}

function AssumptionMap({ assumptions, setAssumptions, onTrace, onBack }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Assumption Map</h1>
      <div className="space-y-2">
        {assumptions.map(a => (
          <div key={a.id} className="bg-white border rounded p-4">
            <div className="font-bold">{a.text}</div>
            <div className="text-xs text-neutral-500 mt-1">{a.source}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-3 py-2 border rounded">← Back</button>
        <button onClick={onTrace} className="ml-auto px-3 py-2 border rounded">
          Traceability →
        </button>
      </div>
    </div>
  );
}

function AssumptionDiff({ previous, next, onAccept, onBack }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Assumption Diff</h1>
      <p className="text-sm mb-4">Compare previous vs. newly extracted assumptions</p>
      <div className="grid grid-cols-2 gap-4">
        <Card title="Previous" subtitle={`${previous.length} items`}>
          <List items={previous.map(a => a.text)} />
        </Card>
        <Card title="New" subtitle={`${next.length} items`}>
          <List items={next.map(a => a.text)} />
        </Card>
      </div>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-3 py-2 border rounded">← Back</button>
        <button onClick={() => onAccept([...previous, ...next])} className="ml-auto px-3 py-2 border rounded bg-green-600 text-white">
          Accept Merge →
        </button>
      </div>
    </div>
  );
}

function TraceMatrix({ onBack, onPlan }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Traceability Matrix</h1>
      <table className="w-full bg-white border rounded text-sm">
        <thead>
          <tr className="border-b bg-neutral-50">
            <th className="p-3 text-left">Assumption</th>
            <th className="p-3 text-left">Requirement</th>
            <th className="p-3 text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b">
            <td className="p-3">BVTO evaluation</td>
            <td className="p-3">Req §6: Eval Factors</td>
            <td className="p-3"><Pill ok>Traced</Pill></td>
          </tr>
          <tr className="border-b">
            <td className="p-3">IDIQ structure</td>
            <td className="p-3">Req §2: Contract Type</td>
            <td className="p-3"><Pill ok>Traced</Pill></td>
          </tr>
        </tbody>
      </table>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-3 py-2 border rounded">← Back</button>
        <button onClick={onPlan} className="ml-auto px-3 py-2 border rounded">
          Generation Plan →
        </button>
      </div>
    </div>
  );
}

function GenerationPlan({ locked, onLock, onEdit, onGenerate, onBack }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Generation Plan</h1>
      <Card title="Documents to Generate" subtitle="Day-One Artifacts">
        <List items={[
          "✓ Presolicitation Notice",
          "✓ Sources Sought Notice",
          "○ RFI (optional)",
          "○ Market Research Report"
        ]} />
      </Card>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-3 py-2 border rounded">← Back</button>
        {!locked ? (
          <button onClick={onLock} className="ml-auto px-3 py-2 border rounded bg-amber-600 text-white">
            🔒 Lock Plan
          </button>
        ) : (
          <>
            <button onClick={onEdit} className="ml-auto px-3 py-2 border rounded">
              Edit Plan
            </button>
            <button onClick={onGenerate} className="px-3 py-2 border rounded bg-green-600 text-white">
              Generate →
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function Compliance({ onBack, onExport }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Compliance Gate</h1>
      <table className="w-full bg-white border rounded text-sm">
        <thead>
          <tr className="border-b bg-neutral-50">
            <th className="p-3 text-left">Rule</th>
            <th className="p-3 text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b">
            <td className="p-3">Citations for eval factors</td>
            <td className="p-3"><Pill ok>Pass</Pill></td>
          </tr>
          <tr className="border-b">
            <td className="p-3">Timeline compliance (FAR 5.2)</td>
            <td className="p-3"><Pill warn>Review</Pill></td>
          </tr>
        </tbody>
      </table>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-3 py-2 border rounded">← Back</button>
        <button onClick={onExport} className="ml-auto px-3 py-2 border rounded bg-neutral-900 text-white">
          Export →
        </button>
      </div>
    </div>
  );
}

function Export({ onBack }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Export</h1>
      <Card title="Export Formats" subtitle="Ready for download">
        <List items={["PDF with citations", "DOCX editable", "JSON metadata"]} />
      </Card>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-3 py-2 border rounded">← Back</button>
        <button className="ml-auto px-3 py-2 border rounded bg-neutral-900 text-white">
          Download Bundle
        </button>
      </div>
    </div>
  );
}

function StrategyBoard({ onStart, onAssumptions, onTrace, onPlan }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-extrabold mb-4">Strategy Board</h1>
      <div className="grid grid-cols-4 gap-4">
        <Tile title="1. Uploads" subtitle="Strategy + Reqs" onClick={onStart} />
        <Tile title="2. Assumptions" subtitle="Extract & curate" onClick={onAssumptions} />
        <Tile title="3. Traceability" subtitle="Map requirements" onClick={onTrace} />
        <Tile title="4. Generate" subtitle="Draft documents" onClick={onPlan} />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

function computeQualityScore(text, citations) {
  const wordCount = text.split(/\s+/).filter(Boolean).length;
  
  // Length score
  let lengthScore = 100;
  if (wordCount < 50) lengthScore = 40;
  else if (wordCount < 100) lengthScore = 70;
  else if (wordCount > 500) lengthScore = 85;
  
  // Citation score
  const citationMatches = (text.match(/\[\d+\]/g) || []).length;
  let citationsScore = Math.min(100, (citationMatches / Math.max(wordCount / 100, 1)) * 50);
  
  // Compliance score (check for FAR references, proper structure)
  let complianceScore = 80;
  if (!text.includes("FAR") && !text.includes("DFARS")) complianceScore -= 20;
  if (/TBD/i.test(text)) complianceScore -= 15;
  
  // Readability
  const sentences = text.split(/[.!?]+/).filter(Boolean);
  const avgSentenceLength = wordCount / Math.max(sentences.length, 1);
  let readabilityScore = 100;
  if (avgSentenceLength > 30) readabilityScore -= (avgSentenceLength - 30) * 2;
  readabilityScore = Math.max(40, readabilityScore);
  
  const breakdown = {
    readability: Math.round(readabilityScore),
    citations: Math.round(citationsScore),
    compliance: Math.round(complianceScore),
    length: Math.round(lengthScore)
  };
  
  const total = (readabilityScore * 0.3) + (citationsScore * 0.2) + (complianceScore * 0.3) + (lengthScore * 0.2);
  
  return { total: Math.round(total), breakdown };
}

function computeIssues(text) {
  const issues = [];
  
  if (/TBD/i.test(text)) {
    issues.push({
      id: "i1",
      kind: "error",
      label: "Timeline contains TBD placeholder",
      fix: {
        label: "Replace with concrete date",
        apply: (t) => t.replace(/TBD/gi, "30 Mar 2025")
      }
    });
  }
  
  if (text.includes("instructions provided") && !text.includes("Section L")) {
    issues.push({
      id: "i2",
      kind: "suggestion",
      label: "Clarify which instructions (specify Section L)",
      fix: {
        label: "Add Section L reference",
        apply: (t) => t.replace("instructions provided", "instructions in Section L")
      }
    });
  }
  
  if (!text.match(/\[\d+\]/)) {
    issues.push({
      id: "i3",
      kind: "warning",
      label: "No citations found in this section"
    });
  }
  
  return issues;
}

function renderInlineCitations(text, citations, onClick) {
  return text.replace(/\[(\d+)\]/g, (match, num) => {
    const id = parseInt(num);
    const exists = citations.some(c => c.id === id);
    if (!exists) return match;
    return `<button onclick="window.citationClick(${id})" class="inline-flex items-center px-1.5 py-0.5 border border-blue-300 rounded text-[11px] bg-blue-50 hover:bg-blue-100 font-mono font-bold text-blue-700">[${id}]</button>`;
  });
}

function highlightIssues(html) {
  return html
    .replace(/TBD/gi, '<mark class="bg-amber-200 px-1 rounded">TBD</mark>')
    .replace(/instructions provided(?!\s+in\s+Section)/gi, '<mark class="bg-amber-200 px-1 rounded">instructions provided</mark>');
}

function autoImproveText(text, quality, issues) {
  let improved = text;
  
  // Apply all fixes
  issues.forEach(issue => {
    if (issue.fix) {
      improved = issue.fix.apply(improved);
    }
  });
  
  // Add more improvements
  if (quality.total < 85) {
    // Add citation if missing
    if (!improved.match(/\[\d+\]/)) {
      improved = improved.replace(/evaluation/i, "evaluation [1]");
    }
    
    // Improve vague language
    improved = improved.replace(/may/gi, "will");
    improved = improved.replace(/should/gi, "shall");
  }
  
  return improved;
}

function generateDiff(before, after) {
  const beforeLines = before.split('\n');
  const afterLines = after.split('\n');
  const maxLines = Math.max(beforeLines.length, afterLines.length);
  
  let diff = [];
  for (let i = 0; i < maxLines; i++) {
    const b = beforeLines[i] || '';
    const a = afterLines[i] || '';
    
    if (b === a) {
      diff.push(`  ${a}`);
    } else if (!b && a) {
      diff.push(`+ ${a}`);
    } else if (b && !a) {
      diff.push(`- ${b}`);
    } else {
      diff.push(`- ${b}`);
      diff.push(`+ ${a}`);
    }
  }
  
  return diff.join('\n');
}

function PDFRenderer({ page, bbox }) {
  return (
    <div className="relative border bg-white h-64 rounded overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-neutral-100 to-neutral-200 flex items-center justify-center text-neutral-400 text-sm">
        PDF Page {page} Preview
      </div>
      {bbox && (
        <div
          className="absolute border-2 border-amber-500 bg-amber-200/30 animate-pulse"
          style={{
            left: bbox.x,
            top: bbox.y,
            width: bbox.w,
            height: bbox.h
          }}
        />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// UI COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

const Card = ({ title, subtitle, children }) => (
  <div className="border rounded-lg p-4 bg-white shadow-sm">
    <div className="font-bold text-sm">{title}</div>
    {subtitle && <div className="text-xs text-neutral-500 mb-3">{subtitle}</div>}
    {children}
  </div>
);

const List = ({ items }) => (
  <ul className="space-y-1 text-sm">
    {items.map((item, i) => (
      <li key={i} className="flex items-start gap-2">
        <span className="text-neutral-400 mt-0.5">•</span>
        <span className="flex-1">{item}</span>
      </li>
    ))}
  </ul>
);

const Pill = ({ children, ok, warn }) => (
  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
    ok ? 'bg-green-100 text-green-800' :
    warn ? 'bg-amber-100 text-amber-800' :
    'bg-red-100 text-red-800'
  }`}>
    {children}
  </span>
);

const Tile = ({ title, subtitle, onClick }) => (
  <button 
    onClick={onClick}
    className="border rounded-lg p-6 bg-white hover:shadow-md transition-all text-left hover:border-blue-300"
  >
    <div className="font-bold text-lg mb-1">{title}</div>
    <div className="text-sm text-neutral-600">{subtitle}</div>
  </button>
);

const TabButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
      active 
        ? 'bg-white shadow-sm' 
        : 'text-neutral-600 hover:text-neutral-900'
    }`}
  >
    {children}
  </button>
);

const QualityBadge = ({ score }) => {
  const color = score >= 85 ? 'green' : score >= 70 ? 'amber' : 'red';
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded border ${
      color === 'green' ? 'bg-green-50 border-green-300 text-green-800' :
      color === 'amber' ? 'bg-amber-50 border-amber-300 text-amber-800' :
      'bg-red-50 border-red-300 text-red-800'
    }`}>
      <span className="text-xs font-medium">Quality Score:</span>
      <span className="text-lg font-bold">{Math.round(score)}</span>
      <span className="text-xs">/100</span>
    </div>
  );
};

const QualityBar = ({ label, score }) => {
  const percentage = Math.max(0, Math.min(100, score));
  const color = percentage >= 85 ? 'bg-green-500' : percentage >= 70 ? 'bg-amber-500' : 'bg-red-500';
  
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="font-medium">{label}</span>
        <span className="font-bold">{Math.round(percentage)}</span>
      </div>
      <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

// Make citation click available globally for inline buttons
if (typeof window !== 'undefined') {
  window.citationClick = (id) => {
    // This will be handled by the component's onClick handler
    console.log('Citation clicked:', id);
  };
}
