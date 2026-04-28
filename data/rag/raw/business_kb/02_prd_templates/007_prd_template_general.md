# PRD Template — General Standard

**Category**: prd_template
**Source**: ProductPlan, Roadmunk, Aha!
**Use Case**: Product Agent uses this template structure when writing PRDs from project briefs.

---

## 1. Overview

A Product Requirements Document (PRD) is the canonical artifact that defines what a product should do, for whom, and why—but deliberately not how it should be built. The PRD sits between strategy and execution: upstream of it lie the company vision, market research, and roadmap; downstream of it lie engineering design documents, UX specifications, and test plans. Its purpose is to align cross-functional stakeholders—product, engineering, design, marketing, sales, support, and leadership—around a single shared understanding of the problem being solved and the criteria for success.

A good PRD does three things at once. It articulates a user problem grounded in evidence. It defines measurable outcomes that determine whether the work succeeded. And it bounds the scope explicitly, both by listing what will be built and by listing what will not. The implementation details—architecture, technology choices, data models, algorithms—belong in engineering design documents that follow the PRD, not in the PRD itself.

This document presents the standard 8-section PRD structure that has converged across modern product organizations, identifies common optional sections, illustrates the structure with a realistic mini-PRD for an educational coding app, and contrasts the standard format with Amazon's Working Backwards alternative.

---

## 2. Why a PRD Matters

Without a PRD, product development tends to drift. Engineers build to imagined requirements, designers solve for unstated users, and stakeholders discover misalignment late, when changes are expensive. A written PRD forces the implicit to become explicit and creates a durable reference point for decisions throughout the build cycle.

The benefits compound across the organization. Product gets a checkable definition of done. Engineering gets a stable target against which to estimate effort and identify dependencies. Design gets clarity about which user problems matter and which user moments must be excellent. Marketing and sales get the basis for positioning, messaging, and customer education. Leadership gets a document that ties the work to business goals.

The PRD also serves as institutional memory. Six months after launch, when teams ask why a particular decision was made, the PRD is where the answer should live. For this reason, a PRD should be written as if it will be read by someone joining the project mid-flight, with no prior context.

---

## 3. Standard 8-Section Structure

The standard PRD comprises eight core sections. Each addresses a distinct question and contributes to a coherent argument from problem to solution.

**1. Overview / Summary**
The opening section establishes context. It briefly states the product or feature being defined, the background that motivates it, and the business goal it serves. A reader should be able to read this section alone and understand the broad strokes of the project. Include a one-sentence statement of what is being built, two to three sentences of background (market context, prior product state, strategic rationale), and an explicit link to the broader business goal—revenue, retention, expansion, or strategic positioning.

**2. Problem Statement**
The problem statement defines the user problem being solved. This is the most important section to get right, because everything downstream depends on it. The problem must be described in terms of the user's situation and unmet need, not in terms of the proposed solution. A common failure mode is solution-first thinking, where the problem statement reduces to "users do not have feature X." A correct problem statement describes friction, frustration, or unmet progress in the user's life independent of any specific product response. Cite evidence: support tickets, user research, analytics signals, market data.

**3. Target Users / Personas**
This section identifies who the work is for. List the primary persona and any secondary personas, and for each describe the relevant characteristics: context of use, goals, constraints, technical sophistication, and key behaviors. If the product has distinct buyer and user roles (such as a parent purchasing a children's app), both must be described, because their jobs differ. Avoid demographic-only personas; characteristics should be those that affect product decisions.

**4. Goals & Success Metrics**
Define what success looks like in measurable terms. State the goals at two levels: the business outcomes the work is meant to produce (tied to the company's North Star Metric or KPIs) and the product outcomes that will indicate the feature is working as intended. Each goal should have a specific metric, a current baseline if available, and a target. Vague goals ("improve engagement") should be replaced with measurable ones ("increase weekly active learners completing at least one lesson by 25% within 90 days of launch").

**5. User Stories / Use Cases**
Translate the problem and goals into narrative scenarios written in the user's voice. The standard form is "As a [persona], I want to [action], so that [outcome]." Cover the primary happy path, the most important edge cases, and any error or recovery flows that materially affect the user experience. User stories should be solution-flavored but not solution-prescriptive; they describe what the user wants to accomplish, leaving implementation latitude to engineering and design.

**6. Functional Requirements**
The functional requirements section enumerates the features and behaviors that must be built. Each requirement should be specific, testable, and prioritized. The standard prioritization scheme uses three tiers:

- **P0** — must-have for launch; the release cannot ship without it.
- **P1** — important but not blocking; ships shortly after launch if not at launch.
- **P2** — nice-to-have; deferred to a later release if effort is constrained.

Functional requirements describe behavior, not implementation. "The system must allow a user to reset their password via email" is a functional requirement; "the system must use SHA-256 with a 16-byte salt" is an engineering design decision.

**7. Non-functional Requirements**
Non-functional requirements describe how well the system must perform, not what it must do. Standard categories include performance (latency, throughput), reliability (uptime, error rates), security (authentication, authorization, data protection), scalability (peak load, growth headroom), compliance (legal and regulatory requirements such as GDPR, COPPA, HIPAA), and accessibility (WCAG conformance). Each non-functional requirement should be expressed as a measurable target wherever possible: "p95 page load under 2 seconds on 3G" rather than "fast."

**8. Out of Scope**
The Out of Scope section explicitly enumerates what will not be built in this release. Its purpose is to prevent scope creep and to short-circuit recurring debates. If a stakeholder repeatedly asks whether feature X is included, putting X in Out of Scope ends the conversation. This section is short and bullet-pointed, but it is one of the most strategically valuable parts of the document.

---

## 4. Optional Sections

Beyond the eight core sections, mature PRDs frequently include several optional sections depending on project complexity:

- **Dependencies** — upstream and downstream systems, teams, or external partners whose readiness affects the timeline.
- **Risks & Mitigation** — known technical, market, regulatory, or operational risks, with planned mitigations and contingency triggers.
- **Timeline / Milestones** — major checkpoints (design lock, code complete, beta, GA), without prescribing engineering schedules.
- **Open Questions** — explicit list of unresolved decisions, with named owners and target resolution dates.
- **Stakeholders** — RACI-style listing of who is responsible, accountable, consulted, and informed.
- **Rollout Plan** — phasing, feature flags, geographic or segment-based ramps, and rollback criteria.
- **Glossary** — definitions of domain-specific terms, especially for cross-functional or external readers.

These sections are optional, but their absence sometimes signals undermanaged risk. For complex multi-team projects, dependencies and risks are typically required rather than optional.

---

## 5. Example PRD Skeleton — Educational Coding App for Kids

Below is a realistic mini-PRD for a Python-based educational coding app targeting children aged 6–12, with each section condensed to two to three sentences for illustration.

**1. Overview / Summary**
We are launching CodeCub, a mobile and tablet app that teaches Python programming to children aged 6–12 through gamified, age-appropriate lessons. The kids' learning app market has matured for math and reading but remains fragmented for coding, and existing offerings lean either too playful (no real code) or too academic (intimidating). CodeCub aims to capture the underserved middle, supporting the company's strategic goal of expanding into the children's education vertical.

**2. Problem Statement**
Parents of children aged 6–12 want to redirect screen time toward skill-building activities, particularly coding, but existing options either teach drag-and-drop pseudo-code that does not transfer to real programming, or expose real code in a form too dense for young learners. As a result, children either lose interest within days or never get past setup, and parents end up feeling that their investment was wasted. User research with 38 parents confirmed both halves of this pattern.

**3. Target Users / Personas**
The primary user is the child aged 6–12 with no prior programming experience and limited reading fluency at the younger end of the range. The primary buyer is the parent, typically aged 30–45, technology-comfortable but not a developer, who wants visible evidence of learning progress. Secondary users include classroom teachers running after-school coding clubs, who need lightweight progress reporting and offline mode.

**4. Goals & Success Metrics**
The North Star Metric is Weekly Active Learners completing at least one lesson (WAL-Lessons), with a launch target of 25,000 WAL-Lessons within 90 days of GA. Supporting metrics: Day-30 retention of 35% or higher, parent satisfaction (CSAT) of 4.4/5 or higher, and an average of 3 lesson completions per active week per child. These metrics ladder up to the company-level KPI of expanding the children's education segment from 8% to 15% of revenue within the fiscal year.

**5. User Stories / Use Cases**
- As a 7-year-old learner, I want to complete a short lesson and see my code make a character move, so I feel proud of what I built.
- As a 11-year-old learner, I want to remix a published mini-game, so I can show my friends something I made.
- As a parent, I want a weekly summary of my child's progress, so I can confirm that screen time is being well spent.
- As a teacher, I want to assign a specific lesson sequence to my class, so I can use CodeCub in an after-school club without per-student setup.

**6. Functional Requirements**

| ID | Requirement | Priority |
|---|---|---|
| F1 | Onboarding flow that adapts to the child's age band (6–8, 9–10, 11–12). | P0 |
| F2 | Library of at least 40 lessons covering Python fundamentals through simple game logic. | P0 |
| F3 | In-app code editor with age-appropriate syntax highlighting, tap-friendly tokens, and a one-tap run button. | P0 |
| F4 | Mistake-tolerant runner with friendly, plain-language error messages and contextual hints. | P0 |
| F5 | Parent dashboard with weekly progress summary delivered via email and in-app. | P0 |
| F6 | Sharable mini-games: child-built artifacts can be exported as a link or short video. | P1 |
| F7 | Teacher mode with class roster, assignment sequencing, and offline lesson cache. | P1 |
| F8 | Animated mascot with milestone celebrations. | P1 |
| F9 | Code editor theme customization (fonts, color schemes). | P2 |

**7. Non-functional Requirements**
- **Performance**: lesson load time under 2 seconds on a 4-year-old tablet over a 5 Mbps connection; code execution feedback under 500 ms.
- **Reliability**: 99.5% monthly uptime for cloud-backed features; lessons fully usable offline once cached.
- **Security & Privacy**: full COPPA compliance; no third-party advertising to minors; parental consent required for any data collection beyond local progress.
- **Accessibility**: WCAG 2.1 AA conformance; full screen reader support for parent-facing screens; high-contrast mode and adjustable text size for child-facing screens.
- **Scalability**: support 500,000 concurrent active learners at peak with no degradation of in-app run times.

**8. Out of Scope**
- Multiplayer real-time coding sessions between children.
- Languages other than Python (e.g., JavaScript, Scratch import).
- Live human tutoring or chat support for children.
- Integration with school information systems (SIS) such as Clever or ClassLink.
- Android TV and smart-TV form factors.

---

## 6. Amazon Working Backwards Alternative

The Working Backwards format, popularized by Amazon, is a stylistic and conceptual alternative to the traditional PRD. Instead of opening with context and requirements, the team writes two artifacts as if the product had already shipped:

- **A future press release** — a one-page announcement aimed at customers, describing the product, the customer problem it solves, the headline benefit, and a representative customer quote. The constraint is that the press release must sound genuinely exciting; if it does not, the product probably is not worth building.
- **A frequently asked questions document (FAQ)** — both a customer-facing FAQ (pricing, availability, how to get started) and an internal FAQ (technical risks, business model, edge cases, dependencies).

Once the press release and FAQ are accepted, the team reverse-engineers the requirements that would be needed to make those documents true. The benefits are clarity of customer benefit (because the press release forces the team to articulate it concretely), early discovery of weak ideas (because an unconvincing press release exposes a thin value proposition), and forced customer-centricity throughout planning.

The trade-off is that Working Backwards documents are less directly executable than a standard PRD; they typically need to be supplemented with conventional functional and non-functional requirements before engineering can build. Many teams use a hybrid: open with a short Working Backwards press release at the top of the PRD, followed by the standard 8-section structure for execution detail.

---

## 7. Best Practices and Pitfalls

**Best practices**

- **Start with the problem, not the solution** — write and pressure-test the problem statement before drafting requirements; the rest of the document should follow from it.
- **Use the user's voice for stories** — written in the first person, anchored to a specific persona and situation.
- **Make everything measurable** — replace adjectives ("fast," "intuitive," "robust") with specific targets.
- **Be explicit about Out of Scope** — every recurring scope debate should resolve into either an in-scope requirement or an out-of-scope bullet.
- **Prioritize ruthlessly** — P0/P1/P2 must reflect real trade-offs; if everything is P0, nothing is.
- **Write for a reader joining mid-project** — assume no shared context.
- **Keep the PRD living** — date it, version it, and update it as decisions are made; treat it as a contract, not a draft.

**Common pitfalls**

- **Solution-first writing** — describing what to build before establishing the user problem.
- **Vague success metrics** — goals like "improve engagement" with no baseline or target.
- **Mixing in implementation detail** — architectural decisions, library choices, and data schemas that belong in engineering design docs.
- **Missing Out of Scope** — leaving boundaries implicit invites endless rescoping.
- **Personas without behavior** — demographic descriptions that do not affect product decisions.
- **Over-formatting** — heavy templating with empty sections; content matters more than format. Most effective PRDs run 4–10 pages.
- **Stale PRDs** — failing to update the document as decisions evolve, causing teams to lose trust in it as the source of truth.

---

## 8. References

- ProductPlan — Product Requirements Document: https://www.productplan.com/learn/product-requirements-document/
- Roadmunk — Product Requirements Document Template: https://roadmunk.com/guides/product-requirements-document-template-prd/
- Aha! — Product Requirements Templates: https://www.aha.io/roadmapping/guide/templates/create/product-requirements