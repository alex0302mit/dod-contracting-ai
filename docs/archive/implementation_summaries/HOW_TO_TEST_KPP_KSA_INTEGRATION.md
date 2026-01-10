# How to Test KPP/KSA Integration

This guide explains how to verify that the ALMS KPP/KSA document is properly integrated with the RAG system and that agents can successfully use this data during document generation.

---

## Quick Test (Run This)

**Single Command to Test Everything:**

```bash
python scripts/test_kpp_ksa_integration.py
```

This runs a comprehensive 3-part test suite that verifies:
1. **RAG Retrieval**: KPP/KSA data is accessible from the vector store
2. **PWS Generation**: Agents use KPP/KSA data when generating documents
3. **Cost Scaling**: IGCE can extract user scaling info from KPP/KSA

**Expected Output:**

```
======================================================================
FINAL TEST SUMMARY
======================================================================
✅ PASSED - RAG Retrieval
✅ PASSED - PWS Performance Requirements
✅ PASSED - IGCE Cost Scaling

======================================================================
OVERALL: 3/3 tests passed
======================================================================

✅ KPP/KSA integration is WORKING CORRECTLY
   Agents can retrieve and use KPP/KSA data during generation.
```

---

## What Each Test Does

### Test 1: RAG Retrieval (Direct Access)

**Purpose**: Verifies that KPP/KSA data can be retrieved from the vector store.

**What It Tests**:
- Query: "ALMS system availability performance requirement threshold objective"
  - Expected: KPP-1 data (99.5%, 99.9%, availability)
- Query: "ALMS inventory accuracy performance requirement threshold objective"
  - Expected: KPP-2 data (95%, 98%, inventory accuracy)
- Query: "ALMS transaction processing speed performance requirement"
  - Expected: KPP-3 data (5 seconds, 2 seconds, transaction)
- Query: "ALMS program timeline milestone IOC FOC June December 2026"
  - Expected: Timeline data (IOC, FOC, 2026)

**Success Criteria**: 4/4 queries retrieve KPP/KSA chunks with expected data

**Sample Output**:
```
1. System Availability (KPP-1)
   Query: ALMS system availability performance requirement threshold o...
   ✅ KPP/KSA document retrieved (3/5 chunks)
   ✅ Data points found: 4/4
      • 99.5%
      • 99.9%
      • availability
      • KPP-1
```

---

### Test 2: PWS Agent Generation (Real Usage)

**Purpose**: Verifies that agents can successfully use KPP/KSA data when generating documents.

**What It Tests**:
1. PWS agent retrieves RAG context including KPP/KSA chunks
2. Agent generates a complete PWS document
3. Generated document contains specific KPP/KSA data:
   - System availability metrics (99.5%, 99.9%)
   - Inventory accuracy metrics (95%, 98%)
   - Transaction performance requirements
   - Performance requirements section

**Success Criteria**: 4/4 checks find KPP/KSA data in generated PWS document

**Sample Output**:
```
======================================================================
VERIFICATION: Checking if KPP/KSA data appears in PWS
======================================================================
✅ System Availability Metric: Found (terms: 99.5%, 99.9%)
✅ Inventory Accuracy Metric: Found (terms: 95%, 98%)
✅ Transaction Performance: Found (terms: transaction, processing)
✅ Performance Requirements Section: Found (terms: performance, requirement)
```

**What This Proves**:
- The PWS agent successfully retrieved 4/10 KPP/KSA chunks in its RAG context
- The generated PWS includes actual performance metrics from the KPP/KSA document
- The integration is working end-to-end in production usage

---

### Test 3: IGCE Cost Scaling (User Data)

**Purpose**: Verifies that IGCE agent can extract user scaling information from KPP/KSA.

**What It Tests**:
- IOC user count: 500 users
- FOC user count: 2,800 users
- IOC timeline: June 2026
- FOC timeline: December 2026

**Success Criteria**: 4/4 data points found in KPP/KSA chunks

**Sample Output**:
```
✅ IOC User Count (500): Found in KPP/KSA data
✅ FOC User Count (2,800): Found in KPP/KSA data
✅ Timeline (June 2026): Found in KPP/KSA data
✅ Timeline (December 2026): Found in KPP/KSA data
```

**What This Proves**:
- IGCE agent can retrieve user scaling information
- Cost estimates can be scaled based on actual IOC/FOC user counts
- Timeline data is accessible for phased cost breakdowns

---

## Understanding the Results

### ✅ All Tests Passed

**Meaning**: The KPP/KSA integration is working correctly. Agents can:
- Retrieve KPP/KSA data from RAG
- Use KPP/KSA data during document generation
- Generate documents with actual performance requirements from approved KPP/KSA

**Next Steps**: You can now generate production documents. The agents will automatically include KPP/KSA data when relevant.

### ⚠️ Some Tests Failed

**Possible Issues**:

1. **RAG Retrieval Failed** (Test 1):
   - Issue: KPP/KSA document not in vector store
   - Fix: Run `python scripts/add_documents_to_rag.py data/documents/alms-kpp-ksa-complete.md`

2. **PWS Generation Failed** (Test 2):
   - Issue: Agent can't access or use KPP/KSA data
   - Check: Look at test output to see if KPP/KSA chunks were retrieved
   - Fix: If chunks retrieved but not in document, check PWS template and prompts

3. **IGCE Cost Scaling Failed** (Test 3):
   - Issue: User count or timeline data not in KPP/KSA document
   - Check: Verify `alms-kpp-ksa-complete.md` contains IOC/FOC information
   - Fix: Update KPP/KSA document with missing data

---

## Manual Testing (Alternative)

If you want to test individual components manually:

### 1. Test RAG Retrieval Directly

```python
from rag.vector_store import VectorStore
from rag.retriever import Retriever
import os

api_key = os.environ.get('ANTHROPIC_API_KEY')
vector_store = VectorStore(api_key)
vector_store.load()
retriever = Retriever(vector_store, top_k=5)

# Query for KPP data
results = retriever.retrieve("ALMS Key Performance Parameters system availability", k=5)

# Check if KPP/KSA document is in results
for result in results:
    source = result.get('metadata', {}).get('source', '')
    if 'kpp-ksa' in source.lower():
        print(f"✅ Found KPP/KSA: {result.get('content', '')[:200]}...")
```

### 2. Test PWS Generation Manually

```python
from agents.pws_writer_agent import PWSWriterAgent
from rag.vector_store import VectorStore
from rag.retriever import Retriever
import os

api_key = os.environ.get('ANTHROPIC_API_KEY')
vector_store = VectorStore(api_key)
vector_store.load()
retriever = Retriever(vector_store, top_k=10)

agent = PWSWriterAgent(api_key, retriever)

task = {
    'project_info': {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'contract_type': 'Firm Fixed Price (FFP)',
        'period_of_performance': '36 months',
        'organization': 'U.S. Army'
    }
}

result = agent.execute(task)
content = result.get('content', '')

# Check for KPP data
if '99.5%' in content or '99.9%' in content:
    print("✅ System availability KPP found in PWS")
if '95%' in content or '98%' in content:
    print("✅ Inventory accuracy KPP found in PWS")
```

### 3. Test IGCE User Scaling Manually

```python
from rag.retriever import Retriever
from rag.vector_store import VectorStore
import os

api_key = os.environ.get('ANTHROPIC_API_KEY')
vector_store = VectorStore(api_key)
vector_store.load()
retriever = Retriever(vector_store, top_k=10)

# Query for user scaling
results = retriever.retrieve("ALMS users IOC FOC 500 2800", k=10)

# Check for user counts
combined_content = ' '.join([r.get('content', '') for r in results])
if '500 users' in combined_content:
    print("✅ IOC user count (500) found")
if '2,800 users' in combined_content or '2800 users' in combined_content:
    print("✅ FOC user count (2,800) found")
```

---

## Verifying Document Quality

After confirming integration works, verify that generated documents use KPP/KSA data appropriately:

### Check PWS Performance Requirements

**Generate a PWS:**
```bash
python scripts/test_pws_agent.py
```

**Verify Section 3 (Performance Requirements) includes**:
- [ ] System availability requirement: ≥99.5% (threshold), ≥99.9% (objective)
- [ ] Inventory accuracy requirement: ≥95% (threshold), ≥98% (objective)
- [ ] Transaction speed requirement: ≤5 seconds (threshold), ≤2 seconds (objective)
- [ ] References to KPP document or "Key Performance Parameters"

### Check IGCE Cost Scaling

**Generate an IGCE:**
```bash
python scripts/test_igce_agent.py
```

**Verify cost estimates are scaled for**:
- [ ] Base year (IOC): 500 users
- [ ] Option year 1: 2,800 users (FOC)
- [ ] Hardware/software quantities scaled appropriately
- [ ] Timeline matches June 2026 (IOC) and December 2026 (FOC)

---

## Troubleshooting

### "KPP/KSA document NOT retrieved"

**Cause**: Document not in vector store or query doesn't match embeddings

**Fix**:
1. Verify document is in vector store:
   ```bash
   python -c "from rag.vector_store import VectorStore; import os; vs = VectorStore(os.environ.get('ANTHROPIC_API_KEY')); vs.load(); print(f'Total chunks: {len(vs.chunks)}')"
   ```
   Should show 12,923 chunks

2. Re-add document if needed:
   ```bash
   python scripts/add_documents_to_rag.py data/documents/alms-kpp-ksa-complete.md
   ```

### "PWS generation failed" or "ERROR during generation"

**Cause**: Agent error or missing dependencies

**Fix**:
1. Check error message in test output
2. Verify ANTHROPIC_API_KEY is set:
   ```bash
   echo $ANTHROPIC_API_KEY
   ```
3. Check agent logs in test output for specific errors

### "KPP/KSA data NOT found in generated content"

**Cause**: Agent retrieved KPP/KSA but didn't use it in generation

**Fix**:
1. Check if KPP/KSA chunks were in RAG context (test shows "✅ KPP/KSA chunks in RAG context: X/10")
2. If chunks retrieved but not used, the LLM chose not to include that specific data
3. This may be acceptable if other relevant information was included instead

---

## Results Archive

Test results are saved to:
- **Full output**: `output/kpp_ksa_integration_test_results.txt`
- **Integration report**: `KPP_KSA_RAG_INTEGRATION_REPORT.md`

---

## Summary

**To verify KPP/KSA integration is working:**

```bash
python scripts/test_kpp_ksa_integration.py
```

**Expected result:** 3/3 tests passed

**What this proves:**
1. ✅ KPP/KSA data is in vector store and retrievable
2. ✅ Agents retrieve KPP/KSA chunks during generation
3. ✅ Generated documents contain KPP/KSA performance requirements
4. ✅ User scaling data (500→2,800 users) is accessible for cost estimates

**Production ready**: Yes, agents will automatically use KPP/KSA data when generating ALMS documents.

---

**Last Updated**: 2025-10-16
**Test Suite Version**: 1.0
**Status**: ✅ All tests passing
