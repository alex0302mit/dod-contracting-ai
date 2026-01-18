# ACES Improvement Ideas

**Document Created:** 2026-01-17
**Application:** ACES - Acquisition Contracting Enterprise System
**Current Status:** Development Phase

---

## Overview

This document contains prioritized improvement ideas for the ACES application, organized by impact and effort level. Use this as a roadmap for future development sprints.

---

## High Impact, Lower Effort

### 1. Analytics Dashboard
**Current State:** Only basic counts (total, in-progress, completed, pending approvals)

**Improvements:**
- Time/cost savings tracker ("AI saved 47 hours this month")
- Document generation success rate charts
- Procurement velocity metrics (days per phase)
- Agent performance leaderboard
- Quality score trends over time
- User activity heatmaps

**Effort:** 3-5 days

---

### 2. Command Palette (Cmd+K)
**Description:** Power-user feature to quickly navigate, search, or execute actions without clicking through menus.

**Features:**
- Fuzzy search for projects, documents, users
- Quick actions (New Project, Generate Document, etc.)
- Recent items
- Keyboard-first navigation

**Effort:** 2-3 days

---

### 3. Dark Mode
**Current State:** Light mode only

**Implementation:**
- You have the shadcn/ui foundation - adding dark mode is straightforward
- Add theme toggle to settings/header
- Persist preference in localStorage
- System preference detection

**Effort:** 1-2 days

---

### 4. Full-Text Search
**Current State:** No search across documents

**Features:**
- Search across all documents, projects, and generated content
- Filters by phase, document type, quality score, date range
- Saved searches and search history
- Highlight matches in results

**Effort:** 3-5 days

---

### 5. Keyboard Shortcuts
**Current State:** Minimal keyboard support

**Shortcuts to Add:**
| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Command palette |
| `Cmd+S` | Save document |
| `Cmd+Shift+E` | Export |
| `Cmd+Enter` | Submit for approval |
| `Cmd+/` | Toggle comments |
| `?` | Show shortcuts help |

**Effort:** 1-2 days

---

## High Impact, Medium Effort

### 6. Real-Time Collaboration Presence
**Description:** Show who's viewing/editing a document

**Features:**
- Avatar indicators ("Sarah is viewing")
- Cursor positions for simultaneous editing
- "Currently editing" lock indicator
- Activity indicators in document list

**Effort:** 1-2 weeks

---

### 7. Document Version History
**Description:** Visual timeline of changes with diff view and rollback

**Features:**
- Version timeline sidebar
- Side-by-side diff comparison
- One-click rollback to previous version
- Auto-save with version snapshots
- Version labels/tags

**Effort:** 1-2 weeks

---

### 8. One-Click Quality Fixes
**Description:** When QualityAgent finds issues, offer inline "Fix with AI" buttons

**Features:**
- Inline issue highlighting with fix suggestions
- "Fix All" batch operation
- Preview before applying
- Undo capability
- Track fixes in audit log

**Effort:** 1 week

---

### 9. Bulk Operations
**Description:** Select multiple documents for batch actions

**Features:**
- Multi-select with checkboxes
- Bulk generate (queue multiple documents)
- Bulk export (ZIP download)
- Bulk submit for approval
- Bulk status update

**Effort:** 3-5 days

---

### 10. Smart Notifications
**Current State:** Basic toast notifications, preferences model exists but not wired up

**Improvements:**
- Email notifications for approvals/deadlines
- @mentions in comments
- Configurable notification preferences per event type
- Daily/weekly digest option
- Browser push notifications
- Slack/Teams integration (future)

**Effort:** 1-2 weeks

---

## Medium Impact, Lower Effort

### 11. Agent Insights Panel
**Description:** Show which agent generated each section

**Features:**
- Agent attribution per section
- Confidence scores
- Generation time/tokens used
- "Regenerate with different agent" option
- Agent reasoning/chain-of-thought display

**Effort:** 2-3 days

---

### 12. Favorites/Bookmarks
**Description:** Star frequently accessed projects or documents

**Features:**
- Star/unstar toggle
- Favorites section in sidebar
- Quick access from command palette
- Persist per user

**Effort:** 1 day

---

### 13. Recent Activity Feed
**Description:** Activity stream showing team actions

**Features:**
- "John approved Market Research Report 2 hours ago"
- Filterable by project, user, action type
- Real-time updates via WebSocket
- Click to navigate to item

**Effort:** 2-3 days

---

### 14. Export Presets
**Description:** Save export configurations for reuse

**Features:**
- Save format + sections + options as preset
- Quick-apply presets
- Share presets across team
- Default preset per document type

**Effort:** 1-2 days

---

### 15. Onboarding Wizard
**Description:** First-time user guide based on role

**Features:**
- Role-specific tours (CO vs PM vs Viewer)
- Interactive feature highlights
- Skip/resume capability
- "Show tips" toggle in settings
- Video tutorials (optional)

**Effort:** 2-3 days

---

## Feature Completions (Existing TODOs)

These are incomplete features identified in the codebase:

| Location | TODO | Priority | Effort |
|----------|------|----------|--------|
| `RichTextEditor.tsx` | Implement save functionality | High | 2-3 hrs |
| `DocumentUploads.tsx` | Implement actual file upload to backend | High | 4-6 hrs |
| `EditorStatusBar.tsx` | Calculate word count based on cursor position | Low | 1-2 hrs |
| `main.py:878` | Add proper permission filtering | Medium | 2-3 hrs |
| `main.py:2501` | Delete actual file from storage | Medium | 1-2 hrs |
| `main.py:3276` | Integrate with document generation code | Medium | 2-4 hrs |
| `Header.tsx` | Integrate with createWebSocket from api.ts | Medium | 2-3 hrs |

---

## Performance Improvements

### 16. Caching Layer
**Current State:** No caching

**Implementation:**
- Redis cache for RAG embeddings
- Cache frequently accessed documents
- Cache user sessions
- Cache agent responses for similar inputs
- Cache invalidation strategy

**Effort:** 3-5 days

---

### 17. Background Task Queue
**Current State:** Synchronous generation

**Implementation:**
- Celery or RQ for long-running tasks
- Progress tracking via WebSocket
- Task retry with exponential backoff
- Task priority queuing
- Dead letter queue for failures

**Effort:** 1 week

---

### 18. Incremental Generation
**Description:** Re-use unchanged sections when regenerating

**Features:**
- Hash-based change detection
- Only regenerate modified sections
- Significant time savings on iterations
- Cache previous generation results

**Effort:** 1 week

---

## AI Enhancements

### 19. Agent Feedback Loop
**Description:** User ratings improve future outputs

**Features:**
- Thumbs up/down on generated content
- Optional feedback comments
- Aggregate ratings per agent
- Use feedback to fine-tune prompts
- Quality trends dashboard

**Effort:** 3-5 days

---

### 20. Custom Agent Templates
**Description:** Let users create specialized agent variants

**Features:**
- Clone existing agent as template
- Customize system prompt
- Add domain-specific instructions
- Share templates across team
- Version control for templates

**Effort:** 1-2 weeks

---

### 21. Chain-of-Thought Display
**Description:** Show AI reasoning for complex generations

**Features:**
- Expandable reasoning panel
- Step-by-step thought process
- Source attribution (which RAG chunks used)
- Confidence indicators
- Debug mode for admins

**Effort:** 3-5 days

---

### 22. Similar Document Recommendations
**Description:** AI-powered suggestions based on context

**Features:**
- "Based on your assumptions, you might also need..."
- Similar past procurements
- Recommended next documents
- Gap analysis ("You're missing IGCE for this phase")

**Effort:** 3-5 days

---

## Quick Wins (< 1 day each)

| Feature | Description | Effort |
|---------|-------------|--------|
| Loading skeletons | Add skeleton loaders to tables and cards | 2-3 hrs |
| Empty states | Improve empty states with illustrations and CTAs | 2-3 hrs |
| Confirmation dialogs | Add confirmations for destructive actions | 1-2 hrs |
| Background completion toasts | Notify when background tasks complete | 1-2 hrs |
| Keyboard shortcut modal | Help modal showing all shortcuts (?) | 2-3 hrs |
| Breadcrumb navigation | Add breadcrumbs for deep navigation | 2-3 hrs |
| Copy to clipboard | One-click copy for document content | 1 hr |
| Print stylesheet | Optimized print layout for documents | 2-3 hrs |
| Error boundaries | Graceful error handling with retry | 2-3 hrs |
| Form autosave | Auto-save drafts to localStorage | 2-3 hrs |

---

## Top 5 Recommendations

Based on impact, user value, and alignment with DoD contracting needs:

### 1. Analytics Dashboard
**Why:** High visibility, demonstrates AI value, helps justify ROI
**Impact:** High
**Effort:** 3-5 days

### 2. Dark Mode
**Why:** User quality of life, modern expectation, easy with shadcn/ui
**Impact:** Medium-High
**Effort:** 1-2 days

### 3. One-Click Quality Fixes
**Why:** Differentiator, leverages existing QualityAgent, saves user time
**Impact:** High
**Effort:** 1 week

### 4. Command Palette
**Why:** Power user feature, modern UX pattern, improves efficiency
**Impact:** Medium-High
**Effort:** 2-3 days

### 5. Document Version History
**Why:** Critical for compliance/audit trail, reduces risk
**Impact:** High
**Effort:** 1-2 weeks

---

## Implementation Phases

### Phase 1: Quick Wins (Week 1)
- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Loading skeletons
- [ ] Empty states
- [ ] Fix existing TODOs

### Phase 2: Core Features (Week 2-3)
- [ ] Command palette
- [ ] Full-text search
- [ ] Favorites/bookmarks
- [ ] Recent activity feed

### Phase 3: AI Enhancements (Week 4-5)
- [ ] One-click quality fixes
- [ ] Agent insights panel
- [ ] Agent feedback loop
- [ ] Similar document recommendations

### Phase 4: Analytics & Collaboration (Week 6-8)
- [ ] Analytics dashboard
- [ ] Document version history
- [ ] Real-time collaboration presence
- [ ] Smart notifications

### Phase 5: Performance (Week 9-10)
- [ ] Caching layer
- [ ] Background task queue
- [ ] Incremental generation

---

## Current Feature Completeness

| Category | Status | Completeness |
|----------|--------|--------------|
| Core Document Generation | Complete | 95% |
| UI Components & Layout | Complete | 85% |
| Admin & Auth | Basic | 60% |
| Analytics & Insights | Minimal | 20% |
| Real-time Features | Implemented | 70% |
| Search & Discovery | Basic | 40% |
| Collaboration | Basic | 50% |
| Performance Optimization | Minimal | 30% |
| Testing | Partial | 50% |
| Documentation | Good | 75% |

---

## Notes

- Priorities should be adjusted based on user feedback
- Some features may require backend API additions
- Consider A/B testing new features before full rollout
- Track metrics before/after to measure impact

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Claude Code | Initial document |

---

*Review and update this document after each sprint to track progress and reprioritize as needed.*
