<!-- 0f3c2f0d-50bb-41f1-803c-5571ab6fa827 4d788705-c2a2-4670-a559-ea3ed98821e1 -->
# UX Enhancement Plan: Navigation, Upload Center, and Editor Copilot

## 1. Remove Board Tab from Navigation

**File:** `src/components/AIContractingUI.tsx`

- Remove the "STRATEGY_BOARD" from `RouteType` union (line 21)
- Delete NavButton for "Board" (lines 153-158)
- Remove StrategyBoard route rendering (lines 203-209)
- Update `onBack` in UploadCenter to navigate to "EDITOR" instead of "STRATEGY_BOARD"
- Remove unused import for StrategyBoard component

---

## 2. Redesign Upload Center

**File:** `src/components/UploadCenter.tsx`

### 2.1 Unified Document Library View

- Replace the dual-section layout (RAG section + category cards) with a single unified library
- Add tabbed interface for filtering by category (All, Strategy, Market Research, Requirements, Templates)
- Implement drag-and-drop upload zone with visual feedback

### 2.2 Document Card Redesign

- Create visually distinct cards showing: filename, category badge, file type icon, upload date, file size
- Add hover states with quick actions (view, delete)
- Group documents by category with collapsible sections

### 2.3 Delete Functionality

- Add delete button to each document card
- Create backend endpoint: `DELETE /api/rag/documents/{document_id}`
- Implement confirmation dialog before deletion
- Update `ragApi` in `src/services/api.ts` with delete method

### 2.4 Visual Improvements

- Modernize color scheme with gradient backgrounds per category
- Add empty state illustrations
- Implement smooth animations for upload/delete operations

---

## 3. Editor Copilot AI Assistant

### 3.1 Create Copilot Component

**New File:** `src/components/editor/EditorCopilot.tsx`

Features:

- Inline popup that appears on text selection
- Chat-style interface with user input and AI responses
- Quick action buttons: Ask, Rewrite, Expand, Summarize, Add Citations, Check Compliance
- Custom prompt input field
- Loading states and streaming response display

### 3.2 Backend Copilot Endpoint

**File:** `backend/main.py`

Add new endpoint: `POST /api/copilot/assist`

```python
{
  "action": "answer|rewrite|expand|summarize|citations|compliance|custom",
  "selected_text": "...",
  "context": "...",  # surrounding text
  "custom_prompt": "...",  # for custom action
  "section_name": "..."
}
```

### 3.3 Integrate with TipTap Editor

**File:** `src/components/editor/RichTextEditor.tsx`

- Add selection change listener to detect when text is highlighted
- Calculate popup position relative to selection
- Show/hide Copilot popup based on selection state
- Handle text replacement when user accepts Copilot suggestions

### 3.4 Update API Service

**File:** `src/services/api.ts`

Add `copilotApi` with methods:

- `assist(action, selectedText, context, sectionName, customPrompt?)`

---

## Key Files to Modify

| File | Changes |

|------|---------|

| `AIContractingUI.tsx` | Remove Board route and nav button |

| `UploadCenter.tsx` | Complete redesign with categories and delete |

| `RichTextEditor.tsx` | Add selection listener, Copilot integration |

| `api.ts` | Add delete document and copilot assist methods |

| `backend/main.py` | Add copilot endpoint and delete document endpoint |

---

## Implementation Order

1. **Phase 1:** Remove Board tab (quick win, ~10 min)
2. **Phase 2:** Backend endpoints (delete + copilot) (~30 min)
3. **Phase 3:** Upload Center redesign (~1-2 hours)
4. **Phase 4:** Copilot component + integration (~2-3 hours)

### To-dos

- [ ] Remove Board tab from navigation and clean up related code
- [ ] Add DELETE /api/rag/documents/{id} endpoint to backend
- [ ] Add POST /api/copilot/assist endpoint for AI assistance
- [ ] Update api.ts with deleteDocument and copilotApi methods
- [ ] Redesign UploadCenter with unified library, categories, and delete buttons
- [ ] Create EditorCopilot.tsx inline popup component
- [ ] Integrate Copilot with RichTextEditor selection handling