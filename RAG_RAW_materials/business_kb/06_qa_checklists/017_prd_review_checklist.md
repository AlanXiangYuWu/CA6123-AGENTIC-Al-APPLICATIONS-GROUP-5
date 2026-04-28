# PRD Review Checklist — 30 Items

**Category**: qa_checklist
**Source**: Synthesized from ProductPlan, Roadmunk, and product management best practices
**Use Case**: QA Agent uses this checklist to systematically review PRD completeness and quality.

---

## 1. Overview

A Product Requirements Document is only as useful as it is reviewable. Without a structured review process, PRDs tend to ship with predictable defects: missing success metrics, vague problem statements, implicit dependencies, and silent risks. Each defect costs the team some combination of build-time rework, cross-functional misalignment, and post-launch surprises. A checklist-based review catches the defects before they propagate.

This document presents a 30-item PRD review checklist organized into four categories: **Completeness** (does the PRD contain the required sections?), **Clarity & Logic** (is the content unambiguous and internally consistent?), **Feasibility** (can this realistically be built?), and **Risk Identification** (are risks called out?). Each item is phrased as a binary yes/no question, specific enough that a human reviewer or an AI agent can mechanically verify the answer by inspecting the document.

The checklist is intended to be used during PRD finalization, before engineering scoping begins. It is not a substitute for engineering design review, security review, or legal review—those produce their own checklists at later stages—but it ensures that the PRD itself is in a fit state to support those downstream activities.

---

## 2. How to Use This Checklist

Apply the 30 items to a complete PRD draft. For each item, answer yes or no based strictly on what the document contains; do not infer or fill in missing content from external knowledge. Track unchecked items along with a brief note on what is missing. After the full pass, apply the scoring guidance in Section 7 to determine whether the PRD is ready to ship to engineering, needs minor revisions, or needs major revisions.

The checklist works best when applied by someone other than the PRD author. Self-review tends to inherit the author's blind spots; cross-functional review (a peer product manager, an engineering lead, a designer, or a QA agent) catches more defects.

---

## 3. Completeness (8 items)

These items confirm that the PRD contains the required sections and that each section has substantive content rather than placeholder text.

- [ ] **C1.** Does the PRD include an Overview / Summary section that states what is being built, the background, and the business goal in three or fewer paragraphs?
- [ ] **C2.** Does the PRD include a Problem Statement that describes the user problem being solved, citing at least one piece of evidence (research, support data, analytics, or competitor analysis)?
- [ ] **C3.** Does the PRD identify at least one primary persona with described context, goals, and key behaviors—not just demographics?
- [ ] **C4.** Does the PRD include at least 3 quantifiable success metrics, each with a baseline (or "no baseline" stated explicitly), a target value, and a time horizon?
- [ ] **C5.** Does the PRD include at least 3 user stories in the standard "As a [role], I want to [action], so that [benefit]" format?
- [ ] **C6.** Does the PRD include a Functional Requirements section in which every requirement has an explicit priority label (P0, P1, or P2)?
- [ ] **C7.** Does the PRD include a Non-functional Requirements section covering at least three of: performance, reliability, security, scalability, compliance, accessibility?
- [ ] **C8.** Does the PRD include an explicit Out of Scope section listing at least 3 items that will not be built?

---

## 4. Clarity & Logic (7 items)

These items confirm that the content is internally consistent and unambiguous.

- [ ] **L1.** Is the problem statement free of solution language—does it describe the user's situation rather than the absence of a specific feature?
- [ ] **L2.** Do all success metrics use specific numbers (e.g., "increase by 25%") rather than vague language (e.g., "improve" or "boost")?
- [ ] **L3.** Does every user story include a "so that" clause that describes the user's underlying benefit, not just a restated action?
- [ ] **L4.** Does each functional requirement describe observable behavior rather than implementation detail (no references to specific endpoints, libraries, schemas, or algorithms)?
- [ ] **L5.** Do the success metrics logically follow from the problem statement—would improving each metric meaningfully indicate that the problem is being solved?
- [ ] **L6.** Are non-functional requirements expressed with measurable thresholds (e.g., "p95 under 2 seconds") rather than adjectives (e.g., "fast")?
- [ ] **L7.** Do the personas, user stories, and functional requirements all reference the same set of users—are there no orphan user stories targeting personas not described elsewhere?

---

## 5. Feasibility (7 items)

These items confirm that the work proposed in the PRD is realistic given the team's resources, dependencies, and constraints.

- [ ] **F1.** Has the PRD been reviewed by at least one engineering representative who has confirmed that the P0 requirements are buildable within the stated timeline?
- [ ] **F2.** Does every P0 functional requirement have at least one corresponding acceptance criterion that defines what "done" looks like?
- [ ] **F3.** Are external dependencies (third-party APIs, partner integrations, other internal teams) explicitly listed, with a status note for each (e.g., "confirmed," "pending," "blocked")?
- [ ] **F4.** Does the PRD identify the platforms (iOS, Android, web, specific browsers, specific OS versions) that are in scope for launch?
- [ ] **F5.** Are the proposed success metrics measurable with the team's current analytics and instrumentation, or is required new instrumentation listed as a dependency?
- [ ] **F6.** If the PRD names a target launch date or milestones, is the timeline consistent with the volume of P0 work (i.e., not obviously underestimated)?
- [ ] **F7.** Does the PRD avoid mixing implementation detail into requirements (e.g., specifying a database, framework, or architectural pattern) that would constrain engineering's design space without justification?

---

## 6. Risk Identification (8 items)

These items confirm that risks have been surfaced rather than left implicit.

- [ ] **R1.** Does the PRD include an explicit Risks or Risks & Mitigation section with at least 3 identified risks?
- [ ] **R2.** Is at least one of the identified risks a market or user-adoption risk (e.g., users may not value the proposed feature)?
- [ ] **R3.** Is at least one of the identified risks a technical or execution risk (e.g., new technology, scaling challenge, integration complexity)?
- [ ] **R4.** If the product collects, stores, or processes user data, does the PRD address compliance considerations (GDPR, COPPA, HIPAA, FERPA, or regional equivalents) explicitly?
- [ ] **R5.** Does the PRD address accessibility (WCAG conformance level or equivalent) explicitly rather than leaving it implicit?
- [ ] **R6.** Are open questions—decisions not yet made—listed explicitly with named owners and target resolution dates, rather than left buried in prose?
- [ ] **R7.** Does the PRD identify the rollout approach (e.g., feature flag, phased rollout, beta cohort) and rollback criteria for the launch?
- [ ] **R8.** Does the PRD identify how the team will know whether the launch succeeded or failed, including specific thresholds or telemetry that would trigger a rollback or post-launch revision?

---

## 7. Scoring Guidance

The 30 items collectively score the PRD's readiness. Use the following thresholds, applied to the percentage of items that are checked (yes):

- **≥ 90% checked (27 of 30 or more)**: The PRD is in good shape. Address the few unchecked items, then ship to engineering.
- **75–89% checked (23–26 of 30)**: Minor revisions required. Pay particular attention to whichever category is weakest; a PRD that is strong on Completeness but weak on Risk Identification, for example, is more dangerous than one with a few scattered gaps.
- **50–74% checked (15–22 of 30)**: Major revisions required. The PRD is not yet a reliable contract for engineering. Return to the author with the specific list of unchecked items.
- **< 50% checked (fewer than 15 of 30)**: The PRD is not ready for review. Return for substantial rework before re-review.

Two additional rules override the percentage thresholds:

- **Critical-item gating**: Items C2 (problem statement with evidence), C4 (quantifiable success metrics), C8 (out of scope), and L4 (no implementation in requirements) are critical. If any of these is unchecked, the PRD requires major revisions regardless of overall score.
- **Category balance**: A PRD scoring above 90% overall but below 60% in any single category requires targeted revision in that category before proceeding.

---

## 8. Example: Applying This Checklist

The following walks through three checklist items applied to a hypothetical PRD for an educational Python coding app for children aged 6–12, showing what passes and what fails.

**Item C4 — Quantifiable success metrics**

The PRD includes the following success-metrics paragraph:

> "We aim to drive strong engagement with the new lesson recommendation feature, improving overall completion rates and increasing time spent in the app. Success will be measured by retention and learning outcomes."

**Verdict: FAILS C4.**
The paragraph names categories of metrics but does not provide numbers. There are no baselines, no target values, and no time horizons. Compare with a passing version:

> "Within 90 days of launch: (1) Day-30 retention increases from 32% baseline to 38% (target). (2) Average lessons completed per active week per child increases from 2.4 to 3.2. (3) Parent-reported satisfaction (CSAT) increases from 4.1/5 to 4.4/5."

The passing version makes each metric specific, baselined, and time-bounded. A reviewer or QA agent can mechanically confirm that the criterion is satisfied.

**Item L4 — Functional requirements describe behavior, not implementation**

The PRD lists the following requirement:

> "F3. The lesson recommender must use the new vector-search service, calling the `/v2/recommend` endpoint with a 200ms timeout and falling back to the legacy keyword search if the latency budget is exceeded."

**Verdict: FAILS L4.**
The requirement names a specific service, a specific endpoint, a specific timeout, and a specific fallback strategy. These are engineering design decisions, not user-observable behavior. The PRD has constrained the engineering team's design space without justification, and if the engineering team later concludes that a different architecture is preferable, the PRD will be out of date. A passing version of the same requirement:

> "F3. When a learner finishes a lesson, the system recommends a next lesson. If the recommendation cannot be produced within the platform's standard interaction-latency budget (defined in non-functional requirements), the system shows a default next-lesson recommendation rather than blocking the user."

The passing version describes what the user observes and the latency expectation, without specifying which service or endpoint produces it.

**Item R4 — Compliance considerations**

The PRD's risks section reads:

> "Privacy and security will be handled per company standards."

**Verdict: FAILS R4.**
Because the product is directed at children under 13, COPPA applies in the United States, and equivalent regulations apply in other jurisdictions (UK Age-Appropriate Design Code, GDPR-K provisions in the EU). A blanket reference to "company standards" does not satisfy the criterion. A passing version:

> "Compliance: COPPA-compliant from launch (no behavioral advertising to under-13 users; verifiable parental consent for any data collection beyond local progress; data-deletion workflow for parental request). FERPA considerations apply to the school-channel tier and are addressed in the school-tier section. UK Age-Appropriate Design Code conformance reviewed and confirmed by legal team on [date]."

The passing version names the specific regulations, the specific obligations, and the review status.

**Aggregate result for this hypothetical PRD**

If the rest of the document is similarly under-specified, this PRD is likely scoring in the 50–74% range and requires major revisions—particularly given that two of the failed items (C4 and L4) are on the critical-items list, which gates approval regardless of overall score. The reviewer's output to the PRD author would specify the failing items, give one passing example for each, and request a revised draft.

---

## 9. References

- ProductPlan — Product Requirements Document: https://www.productplan.com/learn/product-requirements-document/
- Roadmunk — Product Requirements Document Template: https://roadmunk.com/guides/product-requirements-document-template-prd/