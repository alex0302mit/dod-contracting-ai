# Cross-Reference System Design

**Date**: 2025-10-16
**Purpose**: Enable documents to reference and extract data from other generated documents
**Status**: 🔨 Design Phase

---

## 1. PROBLEM STATEMENT

### Current State
Documents are generated **independently** without knowledge of other documents:
- Acquisition Plan has `{{igce_summary}}` but doesn't know what the actual IGCE contains
- PWS references budget but doesn't pull from generated IGCE
- SOW/SOO might duplicate requirements already in PWS
- QA documents need metrics from PWS but generate them separately

### Desired State
Documents should **cross-reference** each other:
- Acquisition Plan extracts total cost from generated IGCE
- PWS references performance requirements from KPP/KSA
- QASP extracts performance metrics from PWS
- All documents maintain **consistency** through shared data

---

## 2. DOCUMENT DEPENDENCY MAP

### Pre-Solicitation Phase Dependencies

```
┌─────────────────────┐
│   KPP/KSA (Source)  │ ← External requirement document
└──────────┬──────────┘
           │
           ├──────────────────────────────────────┐
           ↓                                      ↓
┌─────────────────────┐              ┌─────────────────────┐
│ Acquisition Plan    │              │      IGCE           │
│ - Requirements      │←─────────────│ - Total Cost        │
│ - {{igce_summary}}  │ Needs Cost   │ - Cost Breakdown    │
│ - Timeline          │              │ - Labor Categories  │
└──────────┬──────────┘              └──────────┬──────────┘
           │                                    │
           │                         ┌──────────┘
           │                         │
           ↓                         ↓
┌─────────────────────────────────────────────┐
│              PWS/SOO/SOW                     │
│ - Performance Requirements (from KPP/KSA)   │
│ - Budget (from IGCE)                        │
│ - Timeline (from Acquisition Plan)          │
└──────────┬──────────────────────────────────┘
           │
           ↓
┌─────────────────────┐
│   RFP Package       │
│ - Includes PWS      │
│ - Includes IGCE     │
│ - References Acq    │
└─────────────────────┘
```

### Post-Solicitation Phase Dependencies

```
┌─────────────────────┐
│    PWS (Generated)  │
└──────────┬──────────┘
           │
           ├──────────────────────────────────────┐
           ↓                                      ↓
┌─────────────────────┐              ┌─────────────────────┐
│   QASP/QCP          │              │  Amendment          │
│ - Metrics from PWS  │              │ - Original PWS      │
│ - Standards         │              │ - Changes           │
└─────────────────────┘              └─────────────────────┘
```

---

## 3. CROSS-REFERENCE TYPES

### Type 1: **Data Extraction** (Most Common)
Extract specific values from another document

**Example**:
- Acquisition Plan needs: "Total Program Cost from IGCE"
- Extract: `$2,847,500` from IGCE Section 8 (Total Cost Summary)

### Type 2: **Summary Generation**
Summarize content from another document

**Example**:
- Acquisition Plan needs: "IGCE Summary"
- Generate: "The IGCE estimates total program cost at $2.8M over 36 months, including $1.2M for development, $800K for operations, and $847K for maintenance and support."

### Type 3: **Section Inclusion**
Include an entire section from another document

**Example**:
- RFP Package needs: "Attachment A: PWS"
- Include: Full PWS document as attachment

### Type 4: **Consistency Validation**
Verify values match across documents

**Example**:
- PWS says: "Budget: $2.5M"
- IGCE says: "Total Cost: $2,847,500"
- Flag: ⚠️ Inconsistency detected (PWS rounded, IGCE specific)

---

## 4. PROPOSED ARCHITECTURE

### Component 1: Document Metadata Store

**Purpose**: Track all generated documents and their key data

**Implementation**: JSON file or simple database

```python
# data/document_metadata.json
{
  "documents": {
    "igce_alms_2025-10-16": {
      "type": "igce",
      "program": "ALMS",
      "generated_date": "2025-10-16",
      "file_path": "output/igce_alms_20251016.md",
      "word_count": 2678,
      "extracted_data": {
        "total_cost": 2847500,
        "total_cost_formatted": "$2,847,500",
        "base_year_cost": 1245000,
        "option_year_1_cost": 801250,
        "option_year_2_cost": 801250,
        "period_of_performance": "36 months",
        "labor_categories": [
          {"category": "Senior Software Engineer", "rate": 165},
          {"category": "Project Manager", "rate": 175},
          ...
        ],
        "deliverables": [...],
        "assumptions": [...]
      }
    },
    "acquisition_plan_alms_2025-10-16": {
      "type": "acquisition_plan",
      "program": "ALMS",
      "generated_date": "2025-10-16",
      "file_path": "output/acquisition_plan_alms_20251016.md",
      "word_count": 4493,
      "extracted_data": {
        "total_cost": 2847500,  # ← References IGCE
        "contract_type": "FFP",
        "milestones": [...],
        "risks": [...]
      },
      "references": {
        "igce": "igce_alms_2025-10-16"  # ← Cross-reference
      }
    },
    "pws_alms_2025-10-16": {
      "type": "pws",
      "program": "ALMS",
      "generated_date": "2025-10-16",
      "file_path": "output/pws_alms_20251016.md",
      "word_count": 3066,
      "extracted_data": {
        "performance_requirements": [
          {"name": "System Availability", "threshold": "99.5%", "objective": "99.9%"},
          {"name": "Inventory Accuracy", "threshold": "95%", "objective": "98%"}
        ],
        "deliverables": [...],
        "period_of_performance": "36 months"
      },
      "references": {
        "kpp_ksa": "alms-kpp-ksa-complete.md",  # ← References KPP/KSA
        "acquisition_plan": "acquisition_plan_alms_2025-10-16"
      }
    }
  }
}
```

### Component 2: Document Data Extractor

**Purpose**: Extract key data from generated documents

**Implementation**: Utility class with document-type-specific extractors

```python
# utils/document_extractor.py

class DocumentDataExtractor:
    """Extract structured data from generated documents"""

    def extract_igce_data(self, igce_content: str) -> Dict:
        """Extract key data from IGCE document"""
        return {
            'total_cost': self._extract_total_cost(igce_content),
            'base_year_cost': self._extract_base_year_cost(igce_content),
            'option_year_costs': self._extract_option_year_costs(igce_content),
            'labor_categories': self._extract_labor_categories(igce_content),
            'period_of_performance': self._extract_period(igce_content),
            'cost_breakdown': self._extract_cost_breakdown(igce_content)
        }

    def extract_pws_data(self, pws_content: str) -> Dict:
        """Extract key data from PWS document"""
        return {
            'performance_requirements': self._extract_performance_reqs(pws_content),
            'deliverables': self._extract_deliverables(pws_content),
            'acceptance_criteria': self._extract_acceptance_criteria(pws_content),
            'period_of_performance': self._extract_period(pws_content)
        }

    def extract_acquisition_plan_data(self, acq_plan_content: str) -> Dict:
        """Extract key data from Acquisition Plan"""
        return {
            'total_cost': self._extract_total_cost(acq_plan_content),
            'contract_type': self._extract_contract_type(acq_plan_content),
            'milestones': self._extract_milestones(acq_plan_content),
            'risks': self._extract_risks(acq_plan_content),
            'acquisition_strategy': self._extract_strategy(acq_plan_content)
        }

    def _extract_total_cost(self, content: str) -> float:
        """Extract total cost using multiple patterns"""
        patterns = [
            r'Total.*Cost.*\$?([\d,]+(?:\.\d{2})?)',
            r'Grand Total.*\$?([\d,]+(?:\.\d{2})?)',
            r'\*\*Total\*\*.*\$?([\d,]+(?:\.\d{2})?)'
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return None
```

### Component 3: Cross-Reference Resolver

**Purpose**: Resolve cross-references when generating documents

**Implementation**: Middleware that injects referenced data into agent context

```python
# utils/cross_reference_resolver.py

class CrossReferenceResolver:
    """Resolve cross-references between documents"""

    def __init__(self, metadata_store_path: str):
        self.metadata_store = self._load_metadata(metadata_store_path)
        self.extractor = DocumentDataExtractor()

    def resolve_references(self, document_type: str, program: str,
                          project_info: Dict) -> Dict:
        """
        Resolve all references for a document type

        Returns dict with referenced data ready to inject into agent
        """
        resolved_data = {}

        if document_type == 'acquisition_plan':
            # Acquisition Plan needs IGCE data
            igce_doc = self._find_latest_document('igce', program)
            if igce_doc:
                resolved_data['igce'] = {
                    'total_cost': igce_doc['extracted_data']['total_cost'],
                    'total_cost_formatted': igce_doc['extracted_data']['total_cost_formatted'],
                    'summary': self._generate_igce_summary(igce_doc)
                }

        elif document_type == 'pws':
            # PWS needs Acquisition Plan and KPP/KSA data
            acq_plan = self._find_latest_document('acquisition_plan', program)
            if acq_plan:
                resolved_data['acquisition_plan'] = {
                    'contract_type': acq_plan['extracted_data']['contract_type'],
                    'period_of_performance': acq_plan['extracted_data']['period_of_performance']
                }

            # KPP/KSA from RAG (already handled)

        elif document_type == 'qasp':
            # QASP needs PWS data
            pws_doc = self._find_latest_document('pws', program)
            if pws_doc:
                resolved_data['pws'] = {
                    'performance_requirements': pws_doc['extracted_data']['performance_requirements'],
                    'acceptance_criteria': pws_doc['extracted_data']['acceptance_criteria']
                }

        return resolved_data

    def _generate_igce_summary(self, igce_doc: Dict) -> str:
        """Generate a summary of IGCE for inclusion in other documents"""
        data = igce_doc['extracted_data']
        return (
            f"The Independent Government Cost Estimate (IGCE) projects a total program cost of "
            f"{data['total_cost_formatted']} over {data['period_of_performance']}. "
            f"This includes a base year cost of ${data['base_year_cost']:,.2f} and "
            f"{len(data.get('option_year_costs', []))} option years. "
            f"The estimate is based on {len(data.get('labor_categories', []))} labor categories "
            f"and includes hardware, software, and operations costs."
        )

    def _find_latest_document(self, doc_type: str, program: str) -> Dict:
        """Find the most recent document of a given type for a program"""
        matching_docs = [
            doc for doc_id, doc in self.metadata_store['documents'].items()
            if doc['type'] == doc_type and doc['program'] == program
        ]
        if matching_docs:
            return sorted(matching_docs, key=lambda d: d['generated_date'], reverse=True)[0]
        return None
```

### Component 4: Agent Integration

**Purpose**: Inject cross-referenced data into agent generation process

**Implementation**: Modify agent execute() methods to use resolver

```python
# Modified agent execute() method

def execute(self, task: Dict) -> Dict:
    """Execute with cross-reference resolution"""
    project_info = task.get('project_info', {})
    config = task.get('config', {})

    # NEW: Resolve cross-references
    cross_ref_resolver = CrossReferenceResolver('data/document_metadata.json')
    referenced_data = cross_ref_resolver.resolve_references(
        document_type='acquisition_plan',  # this agent's type
        program=project_info.get('program_name', 'Unknown'),
        project_info=project_info
    )

    # Inject referenced data into RAG context
    if referenced_data.get('igce'):
        # Add IGCE summary to project_info for template population
        project_info['igce_summary'] = referenced_data['igce']['summary']
        project_info['total_cost'] = referenced_data['igce']['total_cost_formatted']

    # Continue with normal generation
    rag_extracted = self._extract_from_rag(project_info)
    llm_generated = self._generate_narrative_sections(project_info, rag_extracted)
    # ... rest of generation
```

---

## 5. IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1)
- [ ] Create `DocumentMetadataStore` class
- [ ] Create `DocumentDataExtractor` class with IGCE/PWS/Acquisition Plan extractors
- [ ] Create `data/document_metadata.json` schema
- [ ] Write unit tests for extractors

### Phase 2: Cross-Reference Resolution (Week 2)
- [ ] Create `CrossReferenceResolver` class
- [ ] Implement IGCE → Acquisition Plan cross-reference
- [ ] Implement PWS → QASP cross-reference
- [ ] Test resolution with sample documents

### Phase 3: Agent Integration (Week 3)
- [ ] Modify Acquisition Plan agent to use IGCE cross-reference
- [ ] Modify QASP agent to use PWS cross-reference
- [ ] Add cross-reference logging to agents
- [ ] Test end-to-end workflow

### Phase 4: Automation (Week 4)
- [ ] Auto-save metadata after document generation
- [ ] Auto-resolve references before generation
- [ ] Create cross-reference validation tool
- [ ] Create cross-reference visualization tool

---

## 6. DETAILED CROSS-REFERENCE MAPPINGS

### Acquisition Plan Cross-References

| Template Field | Source Document | Extraction Method | Fallback |
|----------------|----------------|-------------------|----------|
| `{{igce_summary}}` | IGCE | Summary generation | "TBD - IGCE not yet generated" |
| `{{total_cost}}` | IGCE | Extract from Section 8 | Project info budget |
| `{{dev_base}}` | IGCE | Extract Base Year Development | Calculate from budget |
| `{{om_base}}` | IGCE | Extract Base Year O&M | Smart default |

### PWS Cross-References

| Template Field | Source Document | Extraction Method | Fallback |
|----------------|----------------|-------------------|----------|
| `{{performance_requirements}}` | KPP/KSA | RAG retrieval | Generate from project scope |
| `{{budget}}` | IGCE or Acq Plan | Extract total cost | Project info budget |
| `{{period_of_performance}}` | Acquisition Plan | Extract timeline | Project info timeline |
| `{{deliverables}}` | SOW/SOO | Extract deliverables list | Generate from scope |

### QASP Cross-References

| Template Field | Source Document | Extraction Method | Fallback |
|----------------|----------------|-------------------|----------|
| `{{performance_metrics}}` | PWS | Extract from Section 3 | Generate from KPP/KSA |
| `{{acceptance_criteria}}` | PWS | Extract from Section 4 | Generate standards |
| `{{deliverables}}` | PWS | Extract deliverables | Generate from scope |
| `{{surveillance_methods}}` | PWS | Derive from metrics | Standard surveillance methods |

### Amendment Cross-References

| Template Field | Source Document | Extraction Method | Fallback |
|----------------|----------------|-------------------|----------|
| `{{original_pws}}` | PWS (original) | Load entire document | Error - original required |
| `{{original_budget}}` | Original RFP | Extract budget | Error - original required |
| `{{changes}}` | User input + Diff | Compute diff | User provides changes |

---

## 7. EXAMPLE WORKFLOW

### Scenario: Generate Pre-Solicitation Package

**Step 1: Generate IGCE**
```python
igce_agent = IGCEGeneratorAgent(api_key, retriever)
igce_result = igce_agent.execute(project_info)

# Save and extract metadata
metadata_store.save_document(
    doc_type='igce',
    program='ALMS',
    content=igce_result['content'],
    extracted_data=extractor.extract_igce_data(igce_result['content'])
)
```

**Metadata Saved**:
```json
{
  "igce_alms_2025-10-16": {
    "type": "igce",
    "program": "ALMS",
    "extracted_data": {
      "total_cost": 2847500,
      "total_cost_formatted": "$2,847,500"
    }
  }
}
```

**Step 2: Generate Acquisition Plan (with IGCE cross-reference)**
```python
acq_plan_agent = AcquisitionPlanGeneratorAgent(api_key, retriever)

# Resolver automatically finds IGCE and injects data
resolver = CrossReferenceResolver('data/document_metadata.json')
referenced_data = resolver.resolve_references('acquisition_plan', 'ALMS', project_info)

# Inject IGCE summary
project_info['igce_summary'] = referenced_data['igce']['summary']
project_info['total_cost'] = referenced_data['igce']['total_cost_formatted']

acq_plan_result = acq_plan_agent.execute({'project_info': project_info})
```

**Generated Acquisition Plan**:
```markdown
### 3.4 Independent Government Cost Estimate (IGCE)
The Independent Government Cost Estimate (IGCE) projects a total program cost of
$2,847,500 over 36 months. This includes a base year cost of $1,245,000 and 2
option years. The estimate is based on 8 labor categories and includes hardware,
software, and operations costs.

See Attachment A for complete IGCE documentation.
```

**Step 3: Generate PWS (with Acquisition Plan cross-reference)**
```python
pws_agent = PWSWriterAgent(api_key, retriever)

# Resolver finds Acquisition Plan and IGCE
referenced_data = resolver.resolve_references('pws', 'ALMS', project_info)

# Inject cross-referenced data
project_info['budget'] = referenced_data['acquisition_plan']['total_cost']
project_info['contract_type'] = referenced_data['acquisition_plan']['contract_type']

pws_result = pws_agent.execute({'project_info': project_info})
```

**Generated PWS**:
```markdown
## 1. Introduction
...
**Contract Type**: Firm Fixed Price (FFP)
**Total Estimated Value**: $2,847,500
**Period of Performance**: 36 months
```

---

## 8. BENEFITS

### Consistency
- ✅ Total cost is **identical** across IGCE, Acquisition Plan, and PWS
- ✅ Period of performance is **consistent** across all documents
- ✅ Performance requirements derived from **same source** (KPP/KSA)

### Efficiency
- ✅ No manual copy-paste of data between documents
- ✅ Update IGCE once, all documents automatically update
- ✅ Reduce generation time by reusing extracted data

### Quality
- ✅ Eliminate transcription errors
- ✅ Ensure regulatory compliance (FAR requires IGCE in Acquisition Plan)
- ✅ Provide audit trail of data sources

### Automation
- ✅ Enable "Generate Full Package" workflow
- ✅ Detect missing dependencies (warn if PWS generated before IGCE)
- ✅ Validate cross-document consistency automatically

---

## 9. TECHNICAL CHALLENGES

### Challenge 1: Document Not Yet Generated
**Problem**: Acquisition Plan needs IGCE, but IGCE hasn't been generated yet

**Solutions**:
1. **Generation Order Enforcement**: Require IGCE before Acquisition Plan
2. **Fallback Values**: Use project_info budget as fallback if IGCE not found
3. **Placeholder Warning**: Insert "⚠️ IGCE not yet generated" in document
4. **Dependency Graph**: Show required generation order to user

### Challenge 2: Multiple Versions
**Problem**: User generates IGCE v1, then IGCE v2. Which one does Acquisition Plan use?

**Solutions**:
1. **Latest Version**: Always use most recent (by timestamp)
2. **Explicit Version**: User specifies which IGCE to reference
3. **Version Tagging**: Tag documents with version numbers
4. **Diff Tool**: Show what changed between versions

### Challenge 3: Extraction Accuracy
**Problem**: Extractor fails to find total cost in IGCE (due to format variations)

**Solutions**:
1. **Multiple Patterns**: Use 5-10 regex patterns per field
2. **LLM Extraction**: Use Claude to extract if regex fails
3. **Manual Override**: Allow user to provide extracted values
4. **Validation**: Verify extracted values make sense (cost > 0, etc.)

### Challenge 4: Circular Dependencies
**Problem**: PWS needs budget from IGCE, but IGCE needs labor rates from PWS

**Solutions**:
1. **Dependency Graph**: Detect circular dependencies, error out
2. **Two-Pass Generation**: Generate IGCE with defaults, then PWS, then regenerate IGCE
3. **Independent Sources**: Ensure both documents pull from independent source (KPP/KSA, market research)

---

## 10. QUICK START IMPLEMENTATION

### Minimal Viable Product (MVP)

**Goal**: IGCE → Acquisition Plan cross-reference only

**Files to Create**:
1. `utils/document_metadata_store.py` (100 lines)
2. `utils/document_extractor.py` (200 lines)
3. `utils/cross_reference_resolver.py` (150 lines)
4. Modify `agents/acquisition_plan_generator_agent.py` (20 line change)

**Total Effort**: 2-3 hours

**Test**:
```python
# Generate IGCE
igce_result = igce_agent.execute(project_info)
metadata_store.save_document('igce', 'ALMS', igce_result['content'])

# Generate Acquisition Plan (should include IGCE summary automatically)
acq_plan_result = acq_plan_agent.execute({'project_info': project_info})

# Verify IGCE summary appears in acquisition plan
assert "2,847,500" in acq_plan_result['content']
assert "IGCE" in acq_plan_result['content']
```

---

## 11. NEXT STEPS

**Immediate**:
1. Review this design document
2. Prioritize which cross-references to implement first
3. Decide on implementation approach (MVP vs full system)

**Recommended Priority Order**:
1. **IGCE → Acquisition Plan** (most common, high value)
2. **PWS → QASP** (QA documents need metrics)
3. **Acquisition Plan → Amendment** (change tracking)
4. **Full Package Generation** (orchestrate all documents)

---

## 12. CONCLUSION

Cross-referencing will:
- ✅ Improve consistency across documents
- ✅ Reduce manual effort
- ✅ Enable automated package generation
- ✅ Ensure regulatory compliance

**Implementation Complexity**: Medium
**Value**: High
**Recommended**: Yes - Start with MVP (IGCE → Acquisition Plan)

---

**Document Prepared By**: Claude AI Assistant
**Date**: 2025-10-16
**Status**: Design Complete - Ready for Implementation Review
