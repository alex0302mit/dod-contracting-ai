# ALMS Acquisition Package Generation Guide

## 🎯 New: ALMS Document Generation Using Program Files

**You now have a specialized script that generates ALL acquisition documents using ACTUAL ALMS requirements from your program documents!**

---

## 🚀 Quick Start

```bash
# Generate complete ALMS acquisition package using program documents
python scripts/generate_all_phases_alms.py
```

**That's it!** The script will:
1. ✅ Load ALMS requirements from program document files
2. ✅ Generate ~21 documents using REAL ALMS data
3. ✅ Cross-reference all documents
4. ✅ Output complete acquisition package

**Runtime**: 10-15 minutes

---

## 📊 What Makes This Special?

### Uses ACTUAL ALMS Program Data:

**From Your Program Documents:**
- ✅ Key Performance Parameters (KPPs)
- ✅ System requirements and capabilities
- ✅ Security requirements (FedRAMP, NIST 800-171)
- ✅ Integration requirements (SAP, DLA)
- ✅ User base (2,800 users, 15 installations)
- ✅ Timeline (IOC June 2026, FOC Dec 2026)
- ✅ Budget ($2.5M dev, $6.4M lifecycle)

**Labor Categories** (from ALMS program):
- Program Manager (PMP)
- Cloud Solutions Architect
- Full Stack Developers (Senior/Mid)
- DevSecOps Engineer
- Security Engineer (CISSP)
- QA/Test Engineer
- Business Analyst
- Technical Writer
- Training Specialist

**Materials/ODCs** (ALMS-specific):
- AWS GovCloud hosting (FedRAMP Moderate)
- COTS platform licenses
- Mobile devices for warehouse personnel
- Barcode/RFID scanners
- SAP integration licenses
- Security tools
- Training materials

**Vendor Data** (based on acquisition strategy):
- 3 realistic vendors based on 12 RFI responses
- Small business set-aside
- Best value trade-off evaluation

---

## 📁 Generated Documents

### Phase 1: Pre-Solicitation (4 documents)
Uses ALMS requirements to generate:
1. **Sources Sought Notice** - Market research for ALMS capabilities
2. **Request for Information (RFI)** - Technical questions for ALMS vendors
3. **Pre-Solicitation Notice** - Advance notice of ALMS RFP
4. **Industry Day Materials** - Vendor engagement for ALMS

### Phase 2: Solicitation/RFP (11 documents)
Uses ALMS labor categories, costs, and requirements:
1. **IGCE** - Based on ALMS labor cats and $2.5M estimate
2. **Acquisition Plan** - ALMS strategy, IOC/FOC timeline
3. **PWS** - ALMS performance requirements (KPPs, integrations)
4. **QASP** - Quality metrics for ALMS (99.9% uptime, 95% accuracy)
5. **Section B** - ALMS CLINs and pricing
6. **Section H** - ALMS-specific contract requirements
7. **Section I** - Contract clauses for IT services
8. **Section K** - Representations for small business
9. **Section L** - Instructions tailored to ALMS evaluation
10. **Section M** - Evaluation factors for ALMS (tech/mgmt/price)
11. **SF-33** - Solicitation form with ALMS details

### Phase 3: Evaluation & Award (6+ documents)
Uses realistic ALMS vendor scenarios:
1. **Source Selection Plan** - Best value trade-off for ALMS
2. **Evaluation Scorecards** (3 vendors) - Scores for each ALMS proposal
3. **SSDD** - Source selection decision for ALMS contract
4. **SF-26** - Award form for winning ALMS vendor
5. **Award Notification** - Letter to ALMS winner
6. **Debriefings** (2 non-winners) - Feedback for unsuccessful offerors

**Total**: ~21 documents with ALMS-specific content

---

## 🔍 How RAG Enhancement Works

The script retrieves ALMS requirements using these queries:
1. "ALMS system requirements capabilities features"
2. "ALMS Key Performance Parameters KPP inventory accuracy availability"
3. "ALMS contract strategy acquisition approach"
4. "ALMS technical requirements integration SAP DLA"
5. "ALMS security requirements FedRAMP NIST"
6. "ALMS users installations deployment timeline"

**Result**: Top 15 relevant document chunks combined into comprehensive requirements text used by all agents.

---

## 🆚 Comparison: Generic vs ALMS-Specific

| Feature | `generate_all_phases.py` | `generate_all_phases_alms.py` |
|---------|--------------------------|-------------------------------|
| **Program** | Generic "Cloud Infrastructure Modernization" | Real "Advanced Logistics Management System" |
| **Requirements** | Generic cloud requirements | Actual ALMS KPPs, requirements from RAG |
| **Labor Categories** | Generic cloud roles | ALMS-specific roles (warehouse, SAP integration) |
| **Cost Estimate** | Generic $8M | Actual $2.5M dev / $6.4M lifecycle |
| **Users** | Generic 5,000 users | Actual 2,800 users at 15 installations |
| **Timeline** | Generic 60 months | Actual IOC Jun 2026, FOC Dec 2026 |
| **Vendors** | Generic cloud vendors | Realistic ALMS vendors (small business) |
| **Materials** | Generic cloud services | ALMS-specific (barcode scanners, SAP licenses) |
| **RAG Integration** | ❌ No | ✅ Yes - uses your ALMS documents |

---

## 💡 Usage Examples

### Example 1: Generate Complete ALMS Package

```bash
# Just run it!
python scripts/generate_all_phases_alms.py

# Output: output/alms_complete_acquisition_YYYYMMDD_HHMMSS/
```

### Example 2: Review ALMS Requirements Used

The script shows what it retrieves:
```
📚 Retrieving ALMS requirements from RAG system...
✅ Retrieved 30 relevant document chunks
   Combined length: 45823 characters
```

This confirms it's using YOUR actual ALMS documents!

### Example 3: Check Generated IGCE Matches ALMS

After generation, check the IGCE:
```bash
cat output/alms_complete_acquisition_*/phase2_solicitation/igce.md | grep -A 5 "Total Cost"
```

You'll see it uses ALMS labor categories and costs!

---

## 📖 ALMS Program Details (Automated in Script)

The script automatically configures:

**Program Information:**
- Name: Advanced Logistics Management System (ALMS)
- Solicitation: W56KGU-25-R-0042
- Command: PEO Combat Support & Combat Service Support
- ACAT Level: III

**Performance Requirements:**
- KPP-1: System Availability ≥99.9%
- KPP-2: Inventory Accuracy ≥95%
- KPP-3: Transaction Performance (95% in ≤1 second)

**Integration Requirements:**
- SAP S/4HANA (Army ERP)
- Defense Logistics Agency (DLA) systems
- Common Access Card (CAC) authentication

**Security Requirements:**
- FedRAMP Moderate authorization
- NIST 800-171 compliance
- CMMC Level 2

**Deployment:**
- Initial: 3 sites, 500 users (IOC June 2026)
- Full: 15 sites, 2,800 users (FOC December 2026)

---

## 🔧 Customization (Optional)

The script is pre-configured with ALMS data, but you can customize:

### Change Labor Rates
Edit lines ~310-320:
```python
labor_categories = [
    {'category': 'Program Manager (PMP)', 'hours': 2080, 'rate': 175},  # ← Change rate
    # ...
]
```

### Add/Remove Materials
Edit lines ~323-330:
```python
materials = [
    {'description': 'AWS GovCloud hosting', 'cost': 180000},  # ← Change cost
    # ...
]
```

### Modify Vendors
Edit lines ~470-520:
```python
vendors = [
    {
        'vendor_name': 'Your Vendor Name',
        'technical_score': 94,
        # ... customize
    }
]
```

---

## ✅ Verification Steps

### 1. Check RAG is Working
```bash
python -c "from rag.vector_store import VectorStore; from rag.retriever import Retriever; vs = VectorStore('data/vector_db/faiss_index'); r = Retriever(vs); results = r.retrieve('ALMS requirements', k=3); print(f'Retrieved {len(results)} chunks')"
```

Expected: "Retrieved 3 chunks"

### 2. Run the ALMS Generation
```bash
python scripts/generate_all_phases_alms.py
```

Expected: All phases complete with ALMS-specific content

### 3. Verify ALMS Content
```bash
# Check PWS mentions ALMS KPPs
grep -i "inventory accuracy" output/alms_complete_acquisition_*/phase2_solicitation/pws.md

# Check IGCE uses ALMS labor categories
grep -i "devops" output/alms_complete_acquisition_*/phase2_solicitation/igce.md
```

---

## 🎯 When to Use Which Script

| Scenario | Use This Script |
|----------|----------------|
| **Generate ALMS acquisition package** | `generate_all_phases_alms.py` ⭐ |
| **Generate generic/example package** | `generate_all_phases.py` |
| **Generate just Phase 1 for ALMS** | Modify `generate_phase1_presolicitation.py` |
| **Generate just Phase 2 for ALMS** | Modify `generate_phase2_solicitation.py` |

---

## 📚 Related Documentation

- **ALMS Documents**: `data/documents/README_ALMS_DOCUMENTS.md`
- **KPP/KSA Details**: `data/documents/alms-kpp-ksa-complete.md`
- **System Guide**: [NEW_SCRIPTS_GUIDE.md](NEW_SCRIPTS_GUIDE.md)
- **General Usage**: [HOW_TO_USE.md](HOW_TO_USE.md)

---

## 🎉 Summary

**You now have a script that generates a complete ALMS acquisition package using your actual program requirements!**

**Run it:**
```bash
python scripts/generate_all_phases_alms.py
```

**Get:**
- ✅ 21 ALMS-specific documents
- ✅ Based on actual requirements from RAG
- ✅ Realistic labor categories and costs
- ✅ Accurate vendor scenarios
- ✅ Full cross-referencing
- ✅ Ready for use!

**In 10-15 minutes, you'll have a complete, realistic ALMS acquisition package!** 🚀
