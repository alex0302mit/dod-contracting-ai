# Tavily Web Search Setup Guide

## Overview

The Market Research Report Generator uses [Tavily](https://tavily.com) for real-time web search capabilities. This enables the system to gather actual vendor information, pricing data, and recent contract awards instead of relying solely on LLM knowledge.

## Why Tavily is Important

**Without Tavily** (Web Search Disabled):
- Quality Score: 65/100 (D grade)
- Hallucination Risk: HIGH (30/100)
- Citations: Missing for 25+ factual claims
- Vendor data: Generic/fabricated
- Pricing data: Estimates/TBDs

**With Tavily** (Web Search Enabled):
- Expected Quality Score: 80-85+ (B/A grade)
- Hallucination Risk: LOW/MEDIUM
- Citations: All factual claims cited with sources
- Vendor data: Real SAM.gov vendors
- Pricing data: Actual GSA Schedule/FPDS pricing

## Step 1: Get Free Tavily API Key

1. **Visit Tavily website**: Go to [https://tavily.com](https://tavily.com)

2. **Sign up for free account**:
   - Click "Get Started" or "Sign Up"
   - Provide email address
   - Verify email

3. **Get API key**:
   - Log in to Tavily dashboard
   - Navigate to API Keys section
   - Copy your API key (starts with `tvly-`)
   - Free tier includes: 1,000 searches/month (sufficient for most use cases)

## Step 2: Set Environment Variable

### On macOS/Linux:

**Temporary** (current terminal session only):
```bash
export TAVILY_API_KEY='tvly-your-actual-key-here'
```

**Permanent** (add to shell profile):
```bash
# For bash (~/.bashrc or ~/.bash_profile):
echo "export TAVILY_API_KEY='tvly-your-actual-key-here'" >> ~/.bashrc
source ~/.bashrc

# For zsh (~/.zshrc):
echo "export TAVILY_API_KEY='tvly-your-actual-key-here'" >> ~/.zshrc
source ~/.zshrc
```

### On Windows:

**Command Prompt** (temporary):
```cmd
set TAVILY_API_KEY=tvly-your-actual-key-here
```

**PowerShell** (temporary):
```powershell
$env:TAVILY_API_KEY = "tvly-your-actual-key-here"
```

**Permanent** (System Environment Variables):
1. Search for "Environment Variables" in Windows search
2. Click "Edit the system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Variable name: `TAVILY_API_KEY`
6. Variable value: `tvly-your-actual-key-here`
7. Click OK

## Step 3: Verify Installation

### Check if Tavily Python package is installed:

```bash
pip show tavily-python
```

**Expected output**:
```
Name: tavily-python
Version: 0.3.x
Summary: Python wrapper for Tavily API
```

**If not installed**:
```bash
pip install tavily-python
```

### Verify API key is set:

```bash
# macOS/Linux:
echo $TAVILY_API_KEY

# Windows Command Prompt:
echo %TAVILY_API_KEY%

# Windows PowerShell:
echo $env:TAVILY_API_KEY
```

**Expected output**: Your API key starting with `tvly-`

## Step 4: Test Web Search Functionality

### Generate Market Research Report:

```bash
cd "/Users/alejandromaldonado/Desktop/AI_Phantom_Fellow_Course/Basic use case market research LLM automation"
python scripts/generate_market_research_report.py
```

### Expected Output Indicators:

**Web Search Enabled**:
```
✅ Tavily API Key found - Web search enabled

🔍 Conducting web-based market research...
  ✅ Vendor landscape: 23 vendors found
  ✅ Pricing data: 6 contracts analyzed
  ✅ Recent awards: 8 contracts (last 6 months)
  ✅ FedRAMP vendors: 12 vendors identified
  ✅ Labor rates: 15 rate ranges extracted
```

**Web Search Disabled**:
```
⚠️  Tavily API Key not found - Web search disabled
   Set TAVILY_API_KEY to enable real-time market research
   Get free API key at: https://tavily.com

⚠️  Proceeding with LLM-only generation (may result in TBDs)
```

### Verify Quality Improvements:

Check the evaluation report:
```bash
cat output/market_research_report_*/market_research_report_evaluation.md
```

**Look for**:
- Overall Quality Score: 80+ (was 65)
- Hallucination Risk: LOW or MEDIUM (was HIGH)
- Citations: Minimal missing citations (was 25+)
- Issues: Fewer vague language instances (was 10+)

## Step 5: Understand Web Search Features

The Market Research Agent uses 5 specialized search methods:

### 1. Vendor Landscape Search
```python
search_vendor_information(
    company_name="logistics management system",
    naics_code="541512"
)
```
**Sources**: SAM.gov, FPDS.gov, SBA.gov, Bloomberg.gov

**Data Collected**:
- Registered vendor names
- NAICS code alignments
- Small business certifications
- Past performance records

### 2. Market Pricing Search
```python
search_market_pricing(
    service_type="cloud logistics system",
    naics_code="541512",
    year=2025
)
```
**Sources**: GSA Schedule 70, FPDS pricing data

**Data Collected**:
- Labor category rates
- Hourly/annual pricing
- Contract pricing ranges
- Commercial pricing benchmarks

### 3. Recent Contract Awards
```python
search_recent_awards(
    service_type="logistics management system",
    agency="DOD",
    days_back=180
)
```
**Sources**: Defense.gov, Army.mil, FPDS.gov

**Data Collected**:
- Contract numbers and amounts
- Award dates and agencies
- Vendor names
- Contract types

### 4. FedRAMP Vendor Search
**Sources**: FedRAMP marketplace, authorized cloud vendors

**Data Collected**:
- FedRAMP authorized vendors
- Authorization levels (Low/Moderate/High)
- Cloud service offerings

### 5. Labor Rate Analysis
**Sources**: GSA Schedule 70, FPDS historical contracts

**Data Collected**:
- Labor category definitions
- Rate ranges by category
- Geographic adjustments
- Time period trends

## Troubleshooting

### Issue 1: "ImportError: No module named 'tavily'"

**Cause**: Tavily Python package not installed

**Solution**:
```bash
pip install tavily-python
```

### Issue 2: "ValueError: Tavily API key required"

**Cause**: TAVILY_API_KEY environment variable not set

**Solution**:
```bash
export TAVILY_API_KEY='tvly-your-actual-key-here'
```

### Issue 3: "Web search disabled" message appears

**Cause**: API key not found or invalid

**Verification Steps**:
1. Check if environment variable is set: `echo $TAVILY_API_KEY`
2. Verify key starts with `tvly-`
3. Check if you're in the same terminal session where you set the variable
4. For permanent setup, restart terminal after adding to shell profile

### Issue 4: "Search failed: API key invalid"

**Cause**: API key is incorrect or expired

**Solution**:
1. Log in to [https://tavily.com](https://tavily.com)
2. Navigate to API Keys section
3. Verify your key is active
4. Generate new key if needed
5. Update environment variable with new key

### Issue 5: Low search result counts

**Example**: "Vendor landscape: 0 vendors found"

**Possible Causes**:
1. Overly restrictive search parameters
2. NAICS code mismatch
3. Domain filters too narrow
4. API rate limit exceeded

**Solution**:
1. Check Tavily dashboard for API usage
2. Verify NAICS code is correct (541512 for IT services)
3. Review domain filters in `agents/tools/web_search_tool.py`
4. Wait if rate limit exceeded (resets monthly)

### Issue 6: Quality score still low after enabling Tavily

**Possible Causes**:
1. Search results not being incorporated into report
2. Citations not being added properly
3. Vague language still present

**Debugging Steps**:
1. Check console output for search success messages
2. Verify APPENDIX A section exists in generated report
3. Search report for inline citations: `(Ref: `
4. Check for vague words: "numerous", "several", "many"

**If problems persist**:
- Review `agents/market_research_report_generator_agent.py` lines 221-347 for web search integration
- Check logs for search errors
- Verify source documents are accessible

## Expected Quality Improvements

### Before Tavily (Web Search Disabled):

```markdown
## Market Analysis Summary

The market for advanced logistics management systems is **robust**, with **numerous** qualified vendors.
Industry analysis suggests **significant** competition, with **several** small businesses capable of
meeting requirements. Pricing analysis indicates costs ranging from **approximately** $500K to $2M.

**Issues**:
- 10 instances of vague language
- 25 factual claims without citations
- HIGH hallucination risk
- Quality Score: 65/100
```

### After Tavily (Web Search Enabled):

```markdown
## Market Analysis Summary

The market for advanced logistics management systems demonstrates strong competition, with 23 qualified
vendors identified through SAM.gov search for NAICS 541512 (Ref: SAM.gov, 2025-10-18). Analysis of
FPDS data reveals 6 comparable contracts awarded in 2024-2025 totaling $8.2M (Ref: FPDS database search,
2024-01 to 2025-10). Small business participation is viable, with 12 of 23 vendors (52%) holding 8(a),
HUBZone, or SDVOSB certifications (Ref: SAM.gov entity records, 2025-10-18). Historical pricing from
GSA Schedule 70 indicates systems architect labor rates of $115-$175/hour (Ref: GSA Schedule 70,
Contract GS-35F-0119Y, 2024-09) and senior developer rates of $95-$145/hour (Ref: FPDS Contract
W56KGU-24-C-0042, 2024-06).

**Improvements**:
- 0 instances of vague language
- All factual claims cited
- LOW hallucination risk
- Quality Score: 82/100
```

## Best Practices

### 1. Set API Key Before Each Session
If using temporary environment variable, set it before running scripts:
```bash
export TAVILY_API_KEY='tvly-your-key-here'
python scripts/generate_market_research_report.py
```

### 2. Monitor API Usage
- Free tier: 1,000 searches/month
- Each market research report: ~15-25 searches
- Approximately 40-60 reports per month on free tier
- Check usage at [https://tavily.com/dashboard](https://tavily.com/dashboard)

### 3. Review Search Results
Check console output to verify searches succeeded:
```
✅ Vendor landscape: 23 vendors found
✅ Pricing data: 6 contracts analyzed
```

If you see "0 results", investigate search parameters.

### 4. Verify Citations in Output
After generation, spot-check the report for:
- Inline citations: `(Ref: SAM.gov, 2025-10-18)`
- APPENDIX A section with complete source list
- No vague language ("numerous", "several")

### 5. Compare Quality Scores
Run evaluation reports with and without Tavily to measure impact:
- Without: Expected 60-70/100
- With: Expected 80-90/100

## Additional Resources

- **Tavily Documentation**: [https://docs.tavily.com](https://docs.tavily.com)
- **Tavily Python SDK**: [https://github.com/tavily-ai/tavily-python](https://github.com/tavily-ai/tavily-python)
- **FAR 10.001**: Market Research requirements for federal acquisitions
- **SAM.gov**: [https://sam.gov](https://sam.gov) - Vendor registration database
- **FPDS**: [https://fpds.gov](https://fpds.gov) - Contract award database

## Support

If you encounter issues not covered in this guide:

1. **Check system logs**: Review console output for error messages
2. **Verify requirements**: `pip install -r requirements.txt`
3. **Test Tavily directly**: Use Tavily Python SDK to test API key
4. **Review source code**: `agents/tools/web_search_tool.py` for implementation details

## Summary Checklist

- [ ] Created Tavily account at [https://tavily.com](https://tavily.com)
- [ ] Copied API key (starts with `tvly-`)
- [ ] Set `TAVILY_API_KEY` environment variable
- [ ] Installed `tavily-python` package
- [ ] Ran market research report generator
- [ ] Verified "Web search enabled" message appears
- [ ] Checked quality score improved to 80+
- [ ] Reviewed report for inline citations
- [ ] Confirmed APPENDIX A section exists
- [ ] No vague language detected in report

**Status**: If all boxes checked, Tavily integration is working correctly!
