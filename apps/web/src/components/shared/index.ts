/**
 * Shared Components Barrel Export
 * 
 * Exports all ACES shared/reusable components:
 * - StatusChip: Semantic status badges
 * - EvidenceChip: Inline citation chips
 * - InstrumentCard: Metrics display cards
 * - ActionStrip: Page-level action bar
 * - AuditTimeline: Audit event timeline
 * - DependencyCallout: Dependency warning callout
 * - DocumentCard: Document tile component
 */

export { StatusChip, normalizeStatus, type StatusType } from './StatusChip';
export { EvidenceChip, EvidenceChipInline, type SourceType } from './EvidenceChip';
export { InstrumentCard, InstrumentCardGrid, type RiskLevel } from './InstrumentCard';
export { ActionStrip, ActionStripSeparator } from './ActionStrip';
export { AuditTimeline, AuditTimelineCompact, type AuditEvent } from './AuditTimeline';
export { DependencyCallout } from './DependencyCallout';
export { DocumentCard, DocumentCardGrid, type DocumentData } from './DocumentCard';
