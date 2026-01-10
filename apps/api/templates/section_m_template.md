# SECTION M - EVALUATION FACTORS FOR AWARD

**Solicitation Number:** {{solicitation_number}}
**Contract Title:** {{program_name}}
**Issued By:** {{organization}}
**Date Issued:** {{date_issued}}

---

## M.1 GENERAL INFORMATION

### M.1.1 Evaluation Process

This section describes the evaluation methodology that will be used to evaluate proposals submitted in response to this Request for Proposal (RFP). The Government will evaluate proposals in accordance with Federal Acquisition Regulation (FAR) Part 15, Subpart 15.3.

### M.1.2 Source Selection Authority

The Source Selection Authority (SSA) for this acquisition is:
**{{source_selection_authority}}**

The SSA has the ultimate responsibility for source selection and award decision.

### M.1.3 Evaluation Team

A Source Selection Evaluation Board (SSEB) will be established to evaluate proposals. The SSEB will consist of qualified Government personnel with expertise in:
- Technical evaluation
- Management evaluation
- Past performance assessment
- Cost/price analysis

---

## M.2 EVALUATION METHODOLOGY

### M.2.1 Source Selection Approach

**This acquisition will use: {{evaluation_approach}}**

{{#if_best_value}}
**BEST VALUE TRADE-OFF PROCESS**

Award will be made to the offeror whose proposal provides the best value to the Government, considering technical merit, past performance, and cost/price. The Government may make trade-offs among cost/price and non-cost factors and may award to other than the lowest priced offeror or other than the highest technically rated offeror.
{{/if_best_value}}

{{#if_lpta}}
**LOWEST PRICE TECHNICALLY ACCEPTABLE (LPTA)**

Award will be made to the offeror whose proposal is determined to be technically acceptable and offers the lowest evaluated price. All non-cost factors will be evaluated on an acceptable/unacceptable basis. Proposals that are acceptable for all non-cost factors will be evaluated for price, and award will be made to the lowest priced, technically acceptable offeror.
{{/if_lpta}}

### M.2.2 Evaluation Phases

Proposals will be evaluated in the following phases:

**Phase I: Compliance Review**
- Verification of proposal completeness
- Verification of SAM.gov registration
- Review for compliance with Section L instructions
- Non-compliant proposals may be rejected without further evaluation

**Phase II: Factor Evaluation**
- Evaluation of Technical Factor
- Evaluation of Management Factor
- Evaluation of Past Performance Factor
- Evaluation of Cost/Price Factor

**Phase III: Competitive Range Determination** (if applicable)
- Determination of competitive range based on Phase II evaluations
- Offerors not in competitive range will be notified

**Phase IV: Discussions** (if conducted)
- Clarifications or discussions with competitive range offerors
- Request for Final Proposal Revisions (if applicable)

**Phase V: Source Selection Decision**
- Final evaluation of proposals
- Trade-off analysis (if Best Value approach)
- Award recommendation to SSA
- Award decision

---

## M.3 EVALUATION FACTORS

### M.3.1 Evaluation Factor Summary

Proposals will be evaluated based on the following factors:

{{evaluation_factors_summary_table}}

### M.3.2 Relative Importance of Evaluation Factors

**{{relative_importance_statement}}**

{{#if_best_value}}
**Example: Best Value Trade-Off**

**Non-Cost Factors (Technical + Management + Past Performance)** are **{{non_cost_importance}}** to **Cost/Price** when making the source selection decision.

**Within Non-Cost Factors:**
- **Technical Factor** is **{{technical_importance}}** to **Management Factor**
- **Technical Factor** is **{{technical_vs_past_performance}}** to **Past Performance Factor**
- **Management Factor** is **{{management_vs_past_performance}}** to **Past Performance Factor**
{{/if_best_value}}

{{#if_lpta}}
**LPTA Note:** All non-cost factors are evaluated on an acceptable/unacceptable basis. There is no relative importance among non-cost factors. Cost/Price is the determining factor for technically acceptable proposals.
{{/if_lpta}}

---

## M.4 FACTOR 1: TECHNICAL APPROACH

**Weight:** {{technical_weight}}%

### M.4.1 Description

The Technical Factor evaluates the offeror's understanding of the requirements and the proposed technical solution's ability to meet the Performance Work Statement (PWS) objectives.

### M.4.2 Technical Subfactors

The Technical Factor consists of the following subfactors:

{{technical_subfactors_table}}

### M.4.3 Technical Subfactor Descriptions

**M.4.3.1 Subfactor 1: Understanding of Requirements**

**Weight:** {{subfactor_1_weight}}% of Technical Factor

The Government will evaluate the offeror's demonstrated understanding of:
- PWS requirements and performance objectives
- Technical challenges and complexity
- Government's mission and operational environment
- Critical success factors

**Evaluation Considerations:**
- Depth and accuracy of requirements understanding
- Identification of technical challenges and constraints
- Understanding of interdependencies and integration points
- Demonstration of domain knowledge

**M.4.3.2 Subfactor 2: Technical Solution**

**Weight:** {{subfactor_2_weight}}% of Technical Factor

The Government will evaluate the proposed technical solution's ability to meet or exceed PWS requirements.

**Evaluation Considerations:**
- Technical approach soundness and feasibility
- Compliance with PWS performance standards
- Innovation and use of best practices/industry standards
- Technical risk identification and mitigation
- Scalability and flexibility of solution
- Security approach and compliance (if applicable)
- Technology choices and justification

**Specific Technical Areas to be Evaluated:**

{{technical_evaluation_areas}}

**M.4.3.3 Subfactor 3: Quality Assurance Approach**

**Weight:** {{subfactor_3_weight}}% of Technical Factor

The Government will evaluate the offeror's proposed quality assurance and quality control approach.

**Evaluation Considerations:**
- Quality control processes and procedures
- Testing and validation methodology
- Defect identification and resolution process
- Continuous improvement approach
- Compliance with quality standards
- Metrics and measurement approach

### M.4.4 Technical Rating Scale

{{#if_best_value}}
Technical proposals will be rated using the following adjectival ratings:

| Rating | Definition | Criteria |
|--------|------------|----------|
| **Outstanding** | Proposal meets requirements and exceeds in ways that provide exceptional benefit | - Exceeds all requirements<br>- Exceptional approach with significant benefits<br>- No weaknesses or deficiencies<br>- Minimal risk |
| **Good** | Proposal meets requirements and exceeds in ways that provide benefit | - Exceeds some requirements<br>- Sound approach with some benefits<br>- Minor weaknesses easily correctable<br>- Low risk |
| **Acceptable** | Proposal meets requirements | - Meets all requirements<br>- Adequate approach<br>- Weaknesses are correctable<br>- Moderate risk |
| **Marginal** | Proposal does not clearly meet requirements | - Does not clearly meet all requirements<br>- Questionable approach<br>- Significant weaknesses<br>- High risk |
| **Unacceptable** | Proposal does not meet requirements | - Fails to meet one or more requirements<br>- Unacceptable approach<br>- Major deficiencies<br>- Unacceptable risk |

**Award Threshold:** Proposals rated **Unacceptable** will not be eligible for award.
{{/if_best_value}}

{{#if_lpta}}
Technical proposals will be rated as:
- **Acceptable:** Meets all PWS requirements
- **Unacceptable:** Fails to meet one or more PWS requirements

**Award Threshold:** Only proposals rated **Acceptable** will be considered for award.
{{/if_lpta}}

---

## M.5 FACTOR 2: MANAGEMENT APPROACH

**Weight:** {{management_weight}}%

### M.5.1 Description

The Management Factor evaluates the offeror's ability to successfully manage and execute the contract.

### M.5.2 Management Subfactors

The Management Factor consists of the following subfactors:

{{management_subfactors_table}}

### M.5.3 Management Subfactor Descriptions

**M.5.3.1 Subfactor 1: Project Management Plan**

**Weight:** {{mgmt_subfactor_1_weight}}% of Management Factor

The Government will evaluate the offeror's project management approach.

**Evaluation Considerations:**
- Organizational structure and staffing plan
- Project execution plan and work breakdown structure
- Milestone schedule and critical path
- Resource allocation and management
- Risk management approach
- Issue escalation and resolution procedures
- Change management process

**M.5.3.2 Subfactor 2: Performance Management**

**Weight:** {{mgmt_subfactor_2_weight}}% of Management Factor

The Government will evaluate the offeror's approach to monitoring and managing performance.

**Evaluation Considerations:**
- Performance monitoring and measurement approach
- Metrics and key performance indicators (KPIs)
- Quality control processes
- Corrective action procedures
- Continuous improvement methodology
- Responsiveness to Government feedback

**M.5.3.3 Subfactor 3: Communication Plan**

**Weight:** {{mgmt_subfactor_3_weight}}% of Management Factor

The Government will evaluate the offeror's communication and reporting plan.

**Evaluation Considerations:**
- Government interface and communication protocols
- Status reporting approach and frequency
- Meeting schedules and formats
- Issue notification and escalation process
- Documentation and knowledge management
- Stakeholder engagement approach

**M.5.3.4 Subfactor 4: Key Personnel**

**Weight:** {{mgmt_subfactor_4_weight}}% of Management Factor

The Government will evaluate the qualifications and relevant experience of proposed key personnel.

**Evaluation Considerations:**
- Education, certifications, and qualifications
- Relevant experience in similar roles
- Experience with similar technical solutions
- Experience with Government/DoD contracts
- Availability and commitment to this effort
- Team composition and balance of skills

**Key Personnel Positions:**
{{key_personnel_positions}}

### M.5.4 Management Rating Scale

{{#if_best_value}}
Management proposals will be rated using the same adjectival rating scale as Technical (Outstanding, Good, Acceptable, Marginal, Unacceptable).
{{/if_best_value}}

{{#if_lpta}}
Management proposals will be rated as Acceptable or Unacceptable.
{{/if_lpta}}

---

## M.6 FACTOR 3: PAST PERFORMANCE

**Weight:** {{past_performance_weight}}%

### M.6.1 Description

The Past Performance Factor evaluates the offeror's record of performance on contracts of similar size, scope, and complexity.

### M.6.2 Past Performance Evaluation Approach

The Government will evaluate past performance based on:
1. **Offeror-Provided References:** References submitted with proposal
2. **Government Sources:** Past Performance Information Retrieval System (PPIRS), Contractor Performance Assessment Reporting System (CPARS), and other Government databases
3. **Other Sources:** Information obtained from other sources as appropriate

**Minimum References Required:** {{required_references}}

**Reference Relevancy Period:** Contracts performed within the past **{{reference_timeframe}}** years

### M.6.3 Relevancy Criteria

Past performance will be evaluated for relevancy based on:

**Contract Similarity:**
- Similar technical scope and complexity
- Similar contract type and value
- Similar performance period
- Similar customer environment (Government, DoD, Federal)

**Performance Areas:**
- {{relevance_criteria}}

**Relevancy Ratings:**
- **Very Relevant:** Highly similar in scope, complexity, and environment
- **Relevant:** Similar in scope, complexity, and environment
- **Somewhat Relevant:** Some similarities but significant differences
- **Not Relevant:** Minimal similarities

### M.6.4 Past Performance Assessment Criteria

For each relevant contract, past performance will be assessed in the following areas:

| Performance Area | Assessment Criteria |
|------------------|-------------------|
| **Quality of Service/Product** | - Met technical requirements<br>- Quality of deliverables<br>- Defect rates and resolution<br>- Customer satisfaction |
| **Schedule Performance** | - Met milestone and delivery schedules<br>- Responsiveness to requirements<br>- Timeliness of issue resolution |
| **Cost Control** | - Stayed within budget<br>- Accurate cost estimating<br>- Cost growth (if any) and justification<br>- Billing accuracy |
| **Management** | - Effectiveness of management<br>- Communication and reporting<br>- Problem identification and resolution<br>- Staffing stability |
| **Regulatory Compliance** | - Compliance with contract terms<br>- Compliance with applicable regulations<br>- Security compliance<br>- Ethics and business conduct |

### M.6.5 Past Performance Rating Scale

{{#if_best_value}}
Past performance will be assigned a confidence rating based on relevancy and quality:

| Rating | Definition |
|--------|------------|
| **Substantial Confidence** | Based on offeror's recent/relevant performance record, Government has high expectation offeror will successfully perform |
| **Satisfactory Confidence** | Based on offeror's recent/relevant performance record, Government has reasonable expectation offeror will successfully perform |
| **Limited Confidence** | Based on offeror's performance record, Government has uncertainty about offeror's ability to successfully perform |
| **No Confidence** | Based on offeror's performance record, Government has no expectation offeror will successfully perform |
| **Unknown Confidence** | No past performance record available or insufficient information to make reasonable assessment |

**Note:** Offerors without relevant past performance will receive an **Unknown Confidence** rating. An Unknown Confidence rating will not be evaluated favorably or unfavorably.
{{/if_best_value}}

{{#if_lpta}}
Past performance will be rated as:
- **Acceptable:** Satisfactory performance record on relevant contracts
- **Unacceptable:** Record of unsatisfactory performance on relevant contracts

**Note:** Offerors without past performance history will be rated Acceptable for this factor.
{{/if_lpta}}

---

## M.7 FACTOR 4: COST/PRICE

**Weight:** {{cost_weight}}%

### M.7.1 Description

The Cost/Price Factor evaluates the offeror's proposed cost/price for realism, reasonableness, and completeness.

### M.7.2 Cost/Price Evaluation Approach

{{#if_best_value}}
**Best Value Evaluation:**

The Government will evaluate proposed costs/prices for:

**M.7.2.1 Cost/Price Realism**
- Are proposed costs realistic for the technical approach proposed?
- Are labor hours and mix appropriate?
- Are material costs realistic?
- Are indirect rates reasonable and supported?
- Overall risk that proposed costs are insufficient to perform

**M.7.2.2 Cost/Price Reasonableness**
- Are proposed costs fair and reasonable?
- Comparison to Government estimate
- Comparison to other proposals
- Comparison to historical pricing data
- Market research and price analysis

**M.7.2.3 Cost/Price Completeness**
- Are all required cost elements included?
- Is cost proposal complete and well-documented?
- Is basis of estimate clear and supportable?

**M.7.2.4 Total Evaluated Price**

The Government will calculate Total Evaluated Price (TEP) as follows:

```
Total Evaluated Price = Base Year + Option Year 1 + Option Year 2
```

**Note:** The Government will evaluate the total price for the entire period of performance including all option periods.
{{/if_best_value}}

{{#if_lpta}}
**LPTA Evaluation:**

The Government will evaluate proposed prices for reasonableness only.

**Price Reasonableness:** Price will be compared to:
- Government estimate
- Other proposals
- Market research
- Historical pricing data

The offeror with the **lowest evaluated price** among technically acceptable proposals will be selected for award.

**Total Evaluated Price:**
```
Total Evaluated Price = Base Year + Option Year 1 + Option Year 2
```
{{/if_lpta}}

### M.7.3 Cost/Price Adjustments

The Government may make adjustments to proposed costs/prices for evaluation purposes:

**Potential Adjustments:**
- Correction of computational errors
- Normalization for comparison purposes
- Adjustment for unbalanced pricing
- Adjustment for unrealistic or unsupported costs

### M.7.4 Cost/Price Rating

{{#if_best_value}}
Cost/Price proposals will be rated as:
- **Low Risk:** Costs are realistic and reasonable with low risk of cost growth
- **Moderate Risk:** Costs are generally realistic and reasonable with some risk areas
- **High Risk:** Costs are questionable with significant risk of cost growth
- **Unacceptable:** Costs are unrealistic or unreasonable

**Note:** Cost/Price rating will be considered along with non-cost factors in the best value determination.
{{/if_best_value}}

{{#if_lpta}}
Cost/Price will be ranked from lowest to highest among technically acceptable proposals.
{{/if_lpta}}

---

## M.8 EVALUATION PROCESS DETAILS

### M.8.1 Compliance Review

All proposals will be reviewed for:
- Timely submission
- Compliance with Section L instructions
- Completeness of required sections
- SAM.gov registration status
- Required certifications and representations

**Non-compliant proposals may be rejected without further evaluation.**

### M.8.2 Factor Evaluation

Each proposal will be evaluated against the factors and subfactors described in this Section M.

**Evaluation Approach:**
- Each factor will be evaluated independently
- Subfactors will be evaluated and rolled up to factor ratings
- Strengths, weaknesses, and risks will be documented
- Evaluation scores/ratings will be assigned

### M.8.3 Competitive Range Determination

{{#if_best_value}}
If necessary, the Government will establish a competitive range comprising the most highly rated proposals based on initial evaluation.

**Competitive Range Basis:**
- Initial ratings for all evaluation factors
- Determination of which proposals have a reasonable chance of award
- Offerors not in competitive range will be notified and may request debriefing

**Note:** The Government may determine that the number of proposals warranting discussion is so large that establishing a competitive range is not practical.
{{/if_best_value}}

{{#if_lpta}}
All technically acceptable proposals will proceed to price evaluation.
{{/if_lpta}}

### M.8.4 Clarifications and Discussions

The Government intends to award **without discussions**; however, the Government reserves the right to conduct clarifications or discussions if determined necessary.

**If Discussions are Conducted:**
- Only competitive range offerors will participate
- Discussions will address weaknesses, deficiencies, and other aspects of proposals
- Offerors will be given opportunity to revise proposals
- Government may establish deadline for Final Proposal Revisions (FPRs)

### M.8.5 Final Evaluation

Following receipt of FPRs (if applicable), the Government will conduct final evaluation of proposals based on the evaluation factors and subfactors.

---

## M.9 SOURCE SELECTION DECISION

### M.9.1 Trade-Off Analysis (Best Value)

{{#if_best_value}}
The Source Selection Authority will make award decision based on best value to the Government.

**Trade-Off Considerations:**
- Relative strengths and weaknesses of each proposal
- Performance risk associated with each proposal
- Cost/price and likelihood of successful performance
- Relative importance of evaluation factors
- Overall best value determination

**The Government may:**
- Award to other than lowest priced offeror if proposal provides best value
- Award to other than highest technically rated offeror
- Make trade-offs among cost and non-cost factors

**Award Rationale:**
The SSA will document the award decision rationale including:
- Basis for award decision
- Significant factors and trade-offs considered
- Why selected proposal provides best value
{{/if_best_value}}

### M.9.2 Award Decision (LPTA)

{{#if_lpta}}
Award will be made to the lowest priced, technically acceptable offeror.

**Selection Process:**
1. All proposals rated Unacceptable for any non-cost factor are eliminated
2. Remaining technically acceptable proposals are ranked by price
3. Award is made to lowest priced, technically acceptable offeror

**No trade-offs** will be made between cost and non-cost factors.
{{/if_lpta}}

### M.9.3 Award Notification

Upon completion of source selection:
- Successful offeror will be notified of award
- Unsuccessful offerors will be notified
- Unsuccessful offerors may request debriefing per FAR 15.505/15.506

---

## M.10 EVALUATION STANDARDS AND SCORING

### M.10.1 Evaluation Team Qualifications

Evaluators will be qualified Government personnel with:
- Relevant technical expertise
- Contracting/acquisition experience
- Past performance assessment training
- Cost/price analysis expertise
- No conflicts of interest

### M.10.2 Evaluation Consistency

To ensure fair and consistent evaluation:
- All evaluators will use standardized evaluation criteria
- Calibration sessions will be conducted
- Evaluation documentation will be maintained
- Independent evaluations will be performed before team discussions

### M.10.3 Evaluation Documentation

All evaluations will be documented including:
- Individual evaluator assessments
- Team consensus ratings
- Identification of strengths, weaknesses, deficiencies, and risks
- Rationale for ratings assigned
- Final evaluation scores/ratings

---

## M.11 PROPOSAL RISK ASSESSMENT

Throughout the evaluation, the Government will assess risk associated with each proposal.

**Risk Categories:**
- **Technical Risk:** Risk that proposed solution will not perform as required
- **Management Risk:** Risk that offeror cannot successfully manage the effort
- **Performance Risk:** Risk based on past performance record
- **Cost Risk:** Risk of cost growth or insufficient resources

**Risk Levels:**
- **Low Risk:** Minimal concern about successful performance
- **Moderate Risk:** Some concern, but manageable with oversight
- **High Risk:** Significant concern about successful performance

Risk assessment will be integrated into the overall evaluation and source selection decision.

---

## M.12 ADDITIONAL EVALUATION INFORMATION

### M.12.1 Assumptions and Constraints

**Evaluation Assumptions:**
- Offerors will perform as proposed
- Information provided in proposals is accurate
- Key personnel committed will be available
- Subcontractors will perform as stated

**Evaluation Constraints:**
- Evaluation schedule may be adjusted
- Government may request additional information
- External factors may impact timeline

### M.12.2 Evaluation Questions

If questions arise during evaluation:
- Government may request clarifications
- Offerors must respond within specified timeframe
- Responses will be incorporated into evaluation

### M.12.3 Confidentiality

All proposal information will be protected:
- Evaluated only by authorized personnel
- Maintained in secure environment
- Not disclosed to other offerors
- Protected per FAR 15.207 and 3.104

---

**END OF SECTION M - EVALUATION FACTORS FOR AWARD**

**Questions regarding evaluation should be directed to:**
**{{contracting_officer}} - {{ko_email}}**

---

**Solicitation Number:** {{solicitation_number}}
**Page:** ___ of ___
