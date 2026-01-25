# Procurement Phase Document Checklist

## PRE-SOLICITATION PHASE
**Duration:** ~30 days | **Phase Order:** 1

### Required Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Market Research Report | Market conditions per FAR Part 10 | MarketResearchReportGeneratorAgent |
| Acquisition Plan | Acquisition strategy per FAR Part 7 | AcquisitionPlanGeneratorAgent |
| Performance Work Statement (PWS) | Performance-based work requirements | PWSWriterAgent |
| Independent Government Cost Estimate (IGCE) | Government cost estimate | IGCEGeneratorAgent |

### Recommended Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Sources Sought Notice | Industry capability assessment | SourcesSoughtGeneratorAgent |
| Quality Assurance Surveillance Plan (QASP) | Performance monitoring plan | QASPGeneratorAgent |

### Optional Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Pre-Solicitation Notice | Early market notification | PreSolicitationNoticeGeneratorAgent |
| Industry Day Materials | Vendor engagement materials | IndustryDayGeneratorAgent |
| Request for Information (RFI) | Market feedback tool | RFIGeneratorAgent |

---

## SOLICITATION PHASE
**Duration:** ~45 days | **Phase Order:** 2

### Required Documents
| Document | Description | Agent |
|----------|-------------|-------|
| SF33 - Solicitation, Offer and Award | Standard solicitation form | SF33GeneratorAgent |
| Section A - Solicitation/Contract Form | Foundation document | - |
| Section B - Supplies/Services and Prices | Pricing and procurement details | SectionBGeneratorAgent |
| Section C - Performance Work Statement | Work requirements (from pre-sol) | PWSWriterAgent |
| Section D - Packaging and Marking | Deliverable specifications | - |
| Section E - Inspection and Acceptance | Quality criteria | - |
| Section F - Delivery/Performance Schedule | Performance timeline | - |
| Section G - Contract Administration | Management procedures | - |
| Section H - Special Contract Requirements | Security and compliance | SectionHGeneratorAgent |
| Section I - Contract Clauses | FAR/DFARS provisions | SectionIGeneratorAgent |
| Section J - List of Attachments | Attachment listing | - |
| Section K - Representations and Certifications | Contractor certifications | SectionKGeneratorAgent |
| Section L - Instructions to Offerors | Proposal instructions | SectionLGeneratorAgent |
| Section M - Evaluation Factors | Evaluation criteria | SectionMGeneratorAgent |

### Recommended Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Quality Assurance Surveillance Plan (QASP) | Carried forward from pre-sol | QASPGeneratorAgent |
| Independent Government Cost Estimate (IGCE) | Carried forward from pre-sol | IGCEGeneratorAgent |

### Optional Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Draft RFP for Industry Review | Pre-release review | - |
| Q&A Document | Frequently asked questions | - |
| Site Visit Materials | Facility access for vendors | - |

---

## POST-SOLICITATION / EVALUATION PHASE
**Duration:** ~60 days | **Phase Order:** 3

### Required Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Source Selection Plan | Proposal evaluation plan | SourceSelectionPlanGeneratorAgent |
| Evaluation Scorecard | Proposal scoring sheet | EvaluationScorecardGeneratorAgent |
| Source Selection Decision Document (SSDD) | Award recommendation | SSDDGeneratorAgent |

### Recommended Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Past Performance Questionnaire (PPQ) | Vendor performance evaluation | PPQGeneratorAgent |
| Technical Evaluation Report | Technical assessment | - |
| Cost/Price Analysis Report | Cost evaluation details | - |

### Optional Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Competitive Range Determination Memo | Competitive range justification | - |
| Discussion Question Set | Contractor discussion questions | - |
| Clarification Requests | Proposal clarifications | - |

---

## AWARD PHASE
**Duration:** ~15 days | **Phase Order:** 4

### Required Documents
| Document | Description | Agent |
|----------|-------------|-------|
| SF26 - Award/Contract | Contract award form | SF26GeneratorAgent |
| Award Notification | Notification to awardee | AwardNotificationGeneratorAgent |

### Recommended Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Debriefing Letter | Response to debriefing requests | DebriefingGeneratorAgent |

### Optional Documents
| Document | Description | Agent |
|----------|-------------|-------|
| Public Award Announcement | Public notification | - |
| Post-Award Orientation Materials | Contractor orientation | - |

---

## Document Dependencies

### Pre-Solicitation Dependencies
```
Market Research Report
  ├── Acquisition Plan
  ├── Sources Sought Notice
  └── Industry Day Materials

Performance Work Statement (PWS)
  ├── Independent Government Cost Estimate (IGCE)
  └── Quality Assurance Surveillance Plan (QASP)
```

### Solicitation Dependencies
```
Section C (PWS) → Section L (Instructions) → Section M (Evaluation)
Section B (Pricing) → SF33 (Solicitation Form)
```

### Post-Solicitation Dependencies
```
Section M (Evaluation Factors)
  ├── Source Selection Plan
  └── Evaluation Scorecard → SSDD
```
