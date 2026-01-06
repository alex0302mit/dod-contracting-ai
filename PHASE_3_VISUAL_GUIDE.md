# Phase 3: Visual Changes Guide

## What Changed in the UI

### 1. Generation Plan Screen

#### BEFORE Phase 3:
```
┌─────────────────────────────────────────────────────┐
│ 📋 Generation Plan                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Select Documents to Generate:                       │
│                                                     │
│ [✓] Section L - Instructions to Offerors           │
│ [✓] Section M - Evaluation Factors                 │
│ [ ] Section B - Supplies/Services                  │
│ [ ] Section H - Special Contract Requirements      │
│                                                     │
│ [Generate Documents Button]                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### AFTER Phase 3:
```
┌─────────────────────────────────────────────────────┐
│ 📋 Generation Plan                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🎯 Solicitation Phase                           ││
│ │ Confidence: 100%                                ││
│ │                                                 ││
│ │ Completeness:                                   ││
│ │ ████████░░░░░░░░░░░░ 33% Complete              ││
│ │                                                 ││
│ │ 💡 Recommendations:                             ││
│ │ • Consider adding Section B (required)          ││
│ │ • Consider adding Section H (required)          ││
│ │                                                 ││
│ │ 📋 Missing Required Documents:                  ││
│ │ [Section B] [Section H] [Section I] [Section K]││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Select Documents to Generate:                       │
│                                                     │
│ [✓] Section L - Instructions to Offerors           │
│ [✓] Section M - Evaluation Factors                 │
│ [ ] Section B - Supplies/Services                  │
│ [ ] Section H - Special Contract Requirements      │
│                                                     │
│ [Generate Documents Button]                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Key Addition**: PhaseInfo card appears above document selection, showing:
- Phase name with color coding
- Confidence score
- Completeness progress bar
- Recommendations for missing documents
- Missing required documents as badges

---

### 2. Live Editor - Section List (Sidebar)

#### BEFORE Phase 3:
```
┌──────────────────────┐
│ Document Sections    │
│ 4 sections          │
├──────────────────────┤
│                      │
│ ┌──────────────────┐ │
│ │ Section L        │ │
│ │ 245 words     [85]│ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Section M        │ │
│ │ 312 words     [92]│ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Section B        │ │
│ │ 189 words     [78]│ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Section H        │ │
│ │ 276 words     [88]│ │
│ └──────────────────┘ │
│                      │
└──────────────────────┘
```

#### AFTER Phase 3:
```
┌──────────────────────┐
│ Document Sections    │
│ 4 sections          │
├──────────────────────┤
│                      │
│ ┌──────────────────┐ │
│ │ Section L    ✨  │ │
│ │ 245 words     [85]│ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Section M    ✨  │ │
│ │ 312 words     [92]│ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Section B    🤖  │ │
│ │ 189 words     [78]│ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Section H    ✨  │ │
│ │ 276 words     [88]│ │
│ └──────────────────┘ │
│                      │
└──────────────────────┘

✨ = Specialized Agent
🤖 = Generic Claude

(Hover for details)
```

**Key Addition**: Icons next to each section name:
- ✨ Sparkles (blue) = Generated by specialized agent
- 🤖 Bot (gray) = Generated by generic Claude
- Tooltip on hover shows agent name

---

### 3. Live Editor - Header

#### BEFORE Phase 3:
```
┌──────────────────────────────────────────────────────┐
│ [Edit] [Compare] [History]          [Commit]  [Auto] │
│                                             [Q: 87]   │
│                                    [Compliance] [Export]│
└──────────────────────────────────────────────────────┘
```

#### AFTER Phase 3:
```
┌──────────────────────────────────────────────────────┐
│ [Edit] [Compare] [History]          [Commit]  [Auto] │
│                     [Q: 87]  ┌───────────────────┐   │
│                              │ ✨ Agent Coverage │   │
│                              │ 3/4 special (75%) │   │
│                              └───────────────────┘   │
│                                    [Compliance] [Export]│
└──────────────────────────────────────────────────────┘
```

**Key Addition**: AgentStats card in header showing:
- ✨ Sparkles icon
- Count of specialized vs. total documents
- Percentage specialized

---

## Icon Legend

### Agent Type Indicators

| Icon | Meaning | Color | Use Case |
|------|---------|-------|----------|
| ✨ | Specialized Agent | Blue | Document generated by a specialized agent (e.g., SectionLGeneratorAgent) |
| 🤖 | Generic Claude | Gray | Document generated by fallback generic Claude |

### Phase Indicators

| Phase | Color | Icon | Example Documents |
|-------|-------|------|-------------------|
| Pre-Solicitation | 🟣 Purple | 🎯 | Market Research, Acquisition Plan, PWS |
| Solicitation | 🔵 Blue | 🎯 | Section L, Section M, Section B |
| Post-Solicitation | 🟢 Green | 🎯 | Evaluation Reports, Source Selection |
| Award | 🟠 Amber | 🎯 | Award Notice, Contract |

---

## Tooltip Examples

### Agent Badge Tooltip (Compact Mode)
```
┌────────────────────────────────┐
│ Generated by                   │
│ Section L Generator Agent      │
│                                │
│ Type: Specialized Agent        │
└────────────────────────────────┘
```

### Agent Badge Tooltip (Generic)
```
┌────────────────────────────────┐
│ Generated by                   │
│ Claude (Generic)               │
│                                │
│ Type: Generic Generation       │
└────────────────────────────────┘
```

---

## Phase Detection Examples

### Single Phase (100% Confidence)
```
┌─────────────────────────────────────────────┐
│ 🎯 Solicitation Phase                       │
│ Confidence: 100%                            │
│ ████████████████████ 50% Complete          │
└─────────────────────────────────────────────┘
```

### Mixed Phases (Lower Confidence)
```
┌─────────────────────────────────────────────┐
│ ⚠️ Mixed Phases Detected                    │
│                                             │
│ 🎯 Primary: Solicitation Phase              │
│ Confidence: 67%                             │
│                                             │
│ Phase Breakdown:                            │
│ • Pre-Solicitation: 1 document              │
│ • Solicitation: 2 documents                 │
│                                             │
│ ⚠️ Warning: Mixing phases may create        │
│    inconsistencies in your package          │
└─────────────────────────────────────────────┘
```

### Complete Phase
```
┌─────────────────────────────────────────────┐
│ 🎯 Pre-Solicitation Phase                   │
│ Confidence: 100%                            │
│ ████████████████████████████ 100% Complete │
│                                             │
│ ✅ All required documents selected!         │
└─────────────────────────────────────────────┘
```

### Incomplete Phase with Recommendations
```
┌─────────────────────────────────────────────┐
│ 🎯 Solicitation Phase                       │
│ Confidence: 100%                            │
│ ████████░░░░░░░░░░░░ 33% Complete          │
│                                             │
│ 💡 Recommendations:                         │
│ • Consider adding Section B (required)      │
│ • Consider adding Section H (required)      │
│ • Consider adding Section I (required)      │
│ • Consider adding Section K (required)      │
│                                             │
│ 📋 Missing Required Documents:              │
│ [Section B] [Section H] [Section I]        │
│ [Section K]                                 │
└─────────────────────────────────────────────┘
```

---

## Real-World User Flow

### Scenario: Creating a Solicitation Package

**Step 1**: User navigates to Generation Plan
```
[User sees empty document grid]
```

**Step 2**: User selects first document (Section L)
```
[After 500ms, PhaseInfo appears]
🎯 Solicitation Phase
Confidence: 100%
█░░░░░░░░░░░░░░░ 12% Complete

💡 Recommendations:
• Consider adding Section M (required)
• Consider adding Section B (required)
...
```

**Step 3**: User adds Section M
```
[PhaseInfo updates automatically]
🎯 Solicitation Phase
Confidence: 100%
███░░░░░░░░░░░░░ 25% Complete

💡 Recommendations:
• Consider adding Section B (required)
• Consider adding Section H (required)
...
```

**Step 4**: User adds Sections B and H
```
[PhaseInfo updates]
🎯 Solicitation Phase
Confidence: 100%
██████░░░░░░░░░░ 50% Complete

💡 Recommendations:
• Consider adding Section I (required)
• Consider adding Section K (required)
...
```

**Step 5**: User clicks "Generate Documents"
```
[Generation progress screen appears]
🎯 Generating Documents...
Progress: 45%
```

**Step 6**: User sees Live Editor
```
Document Sections:
┌──────────────────┐
│ Section L    ✨  │  ← Specialized
│ 245 words   [85] │
└──────────────────┘
┌──────────────────┐
│ Section M    ✨  │  ← Specialized
│ 312 words   [92] │
└──────────────────┘
┌──────────────────┐
│ Section B    🤖  │  ← Generic (no specialized agent yet)
│ 189 words   [78] │
└──────────────────┘
┌──────────────────┐
│ Section H    ✨  │  ← Specialized
│ 276 words   [88] │
└──────────────────┘

Header shows:
┌───────────────────┐
│ ✨ Agent Coverage │
│ 3/4 special (75%) │
└───────────────────┘
```

**Step 7**: User hovers over ✨ icon next to "Section L"
```
[Tooltip appears]
┌────────────────────────────────┐
│ Generated by                   │
│ Section L Generator Agent      │
│                                │
│ Type: Specialized Agent        │
└────────────────────────────────┘
```

---

## Design Principles

### 1. Non-Intrusive
- Phase info only appears when documents are selected
- Agent badges are small and don't clutter the UI
- Statistics are compact and optional

### 2. Progressive Disclosure
- Compact icons by default
- Details on hover (tooltips)
- Full information available when needed

### 3. Real-Time Feedback
- Phase analysis updates as user selects
- 500ms debounce prevents flickering
- Immediate visual feedback

### 4. Color Coding
- Consistent colors across phases
- Blue = specialized, Gray = generic
- Progress bars use gradient for visual appeal

### 5. Accessibility
- Icons have text alternatives
- Tooltips are keyboard accessible
- Color is not the only indicator

---

## Component Hierarchy

```
AIContractingUI (main app)
├── GenerationPlan
│   ├── PhaseInfo (NEW in Phase 3)
│   │   ├── Phase card with completeness
│   │   ├── Warnings section
│   │   ├── Recommendations section
│   │   └── Missing documents section
│   └── Document selection grid
│
└── LiveEditor
    ├── Header
    │   └── AgentStats (NEW in Phase 3)
    │       └── Shows X/Y specialized (Z%)
    │
    └── Section List (sidebar)
        └── Each section
            └── AgentBadge compact (NEW in Phase 3)
                └── ✨ or 🤖 icon with tooltip
```

---

## Future Enhancements (Phase 4+)

### Potential Visual Additions:

1. **Agent Details Modal**
   - Click agent badge to see full agent information
   - Show agent capabilities and specializations
   - Display agent generation history

2. **Phase Timeline**
   - Visual timeline showing all phases
   - Current phase highlighted
   - Click to see required docs for each phase

3. **Agent Comparison**
   - Side-by-side comparison of specialized vs. generic
   - Quality metrics per agent type
   - Performance statistics

4. **Interactive Recommendations**
   - Click recommendation to auto-select document
   - Smart suggestions based on past selections
   - Package templates (e.g., "Complete Solicitation")

5. **Agent Collaboration Indicators**
   - Show when agents referenced each other
   - Display dependency chains
   - Highlight cross-referenced sections

---

## Summary

Phase 3 UI changes are designed to be:
- ✅ **Informative**: Show phase and agent information
- ✅ **Non-intrusive**: Don't overwhelm the user
- ✅ **Progressive**: Details on demand via tooltips
- ✅ **Real-time**: Updates as user interacts
- ✅ **Accessible**: Works for all users

The result is a more transparent, helpful, and trustworthy document generation experience.
