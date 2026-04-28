# Data Privacy: GDPR, PDPA, COPPA, CCPA

**Category**: security
**Source**: GDPR.eu, Singapore PDPC, FTC COPPA
**Use Case**: Architect Agent uses this for compliance review when target market includes EU/SG/US/CA.

> **Disclaimer**: This document provides general technical and architectural guidance on data privacy regulations. It is not legal advice. Privacy law varies by jurisdiction, evolves continually, and depends on facts specific to each business. Consult qualified legal counsel before relying on this guidance for compliance decisions.

---

## 1. Overview

Data privacy regulation has evolved into a defining constraint on modern application architecture. Where once "privacy" meant a privacy-policy page that few read and fewer enforced, today's regulations carry meaningful penalties—up to 4% of global revenue under the GDPR—and shape decisions about what data systems collect, where it is stored, who can access it, how long it is kept, and how users can exercise control over it. A team building any consumer-facing application that crosses jurisdictional borders, or that serves children, or that processes sensitive categories of data, must treat privacy compliance as an architectural concern, not a documentation task.

The regulatory landscape is not unified. Different jurisdictions impose different requirements with different enforcement regimes. The **General Data Protection Regulation (GDPR)** governs personal data in the European Union and is the most comprehensive and most strictly enforced. **Singapore's Personal Data Protection Act (PDPA)** is more pragmatic and business-friendly but applies to data of Singapore residents. The **Children's Online Privacy Protection Act (COPPA)** in the United States governs data of children under 13 and predates most modern privacy regulation by nearly two decades. The **California Consumer Privacy Act (CCPA)**, expanded by the California Privacy Rights Act (CPRA), covers California residents with a regime that resembles GDPR in spirit if not in detail.

This document covers all four, the principles common to modern privacy law (most clearly articulated in GDPR's seven core principles), the user rights that flow from them, the specific obligations COPPA imposes on children's applications, the architectural patterns that produce compliant systems, and a worked compliance plan for an educational coding app whose users include children and whose target markets cross all four jurisdictions.

---

## 2. The Major Regulations

| Regulation | Jurisdiction | Scope | Maximum penalty |
|---|---|---|---|
| **GDPR** | European Union and EEA (and applies to any organization processing data of EU residents, regardless of where the organization is located) | Comprehensive: all personal data of EU residents, plus extraterritorial reach | Up to €20 million or 4% of global annual revenue, whichever is higher |
| **PDPA** | Singapore (with extraterritorial reach for organizations processing Singapore residents' data) | Personal data of Singapore residents; includes a Do Not Call registry for marketing | Up to SGD $1 million or 10% of annual turnover in Singapore (raised in 2020 amendments), whichever is higher for organizations with annual turnover exceeding SGD $10 million |
| **COPPA** | United States | Personal information of children under 13 collected by online services | FTC civil penalties; per-violation fines that have totaled tens of millions in major cases |
| **CCPA / CPRA** | California (with reach to companies serving California residents that meet specific thresholds) | Personal information of California residents; rights to know, delete, correct, and opt out of "sale" | Up to $7,500 per intentional violation, plus statutory damages in private litigation for data breaches |

Several other regulations are worth naming briefly: **LGPD** (Brazil, GDPR-similar), **APPI** (Japan), **PIPEDA** (Canada), **POPIA** (South Africa), **PIPL** (China). The trend across jurisdictions is convergent on the principles GDPR articulates, even when the specific obligations and enforcement regimes differ. Building a system to GDPR standards typically produces something close to compliance with most other regimes; building to a less rigorous regime typically does not produce GDPR compliance.

---

## 3. GDPR Core Principles

GDPR's **Article 5** articulates seven principles that govern all processing of personal data. They are the conceptual foundation of the regulation and the lens through which specific provisions are interpreted.

1. **Lawfulness, fairness, and transparency.** Personal data must be processed on a lawful basis (one of six listed in GDPR Article 6: consent, contract, legal obligation, vital interests, public task, or legitimate interests), and individuals must be told clearly what is happening with their data.
2. **Purpose limitation.** Data is collected for specified, explicit, and legitimate purposes, and not further processed in ways incompatible with those purposes. Data collected for one reason cannot be quietly repurposed for another.
3. **Data minimization.** Only data that is adequate, relevant, and limited to what is necessary for the stated purpose may be collected. The instinct to "collect everything in case we need it later" violates this principle.
4. **Accuracy.** Data must be accurate and kept up to date. Inaccurate data must be corrected or erased without delay.
5. **Storage limitation.** Data must not be kept in identifiable form longer than necessary for the stated purpose. Indefinite retention is a violation; defined retention periods are required.
6. **Integrity and confidentiality (security).** Data must be processed with appropriate security: encryption, access controls, integrity protection, resilience against incidents.
7. **Accountability.** The data controller must be able to demonstrate compliance with the other six principles. Records of processing activities, documented assessments, and clear governance are how accountability is shown.

The principles produce a different mental model from the historical "collect everything, secure the database" approach. GDPR-compliant architectures are built around **deliberate, minimal, purpose-bound** data flows with documented governance.

---

## 4. GDPR User Rights

GDPR grants data subjects (individuals) a set of enumerated rights that organizations must support operationally. The technical implication is that systems must be designed to honor these rights, not just policies that promise to.

- **Right to access** (Article 15): the individual can request a copy of all personal data the organization holds about them, along with information about how it is used.
- **Right to rectification** (Article 16): the individual can require correction of inaccurate or incomplete data.
- **Right to erasure** ("right to be forgotten," Article 17): the individual can require deletion of their data in defined circumstances. This includes deletion from backups and from any third-party processors who received the data.
- **Right to restrict processing** (Article 18): the individual can require the organization to stop processing their data while disputes are resolved.
- **Right to data portability** (Article 20): the individual can require their data to be provided in a machine-readable format suitable for transferring to another service.
- **Right to object** (Article 21): the individual can object to processing based on legitimate interests, direct marketing, or research.
- **Right not to be subject to automated decisions** (Article 22): the individual can require human review of decisions made solely by automated processing that produce legal or similarly significant effects.

The technical implication: every system holding personal data must support **Data Subject Requests (DSRs)** as a first-class operation. The organization must be able to identify all data about a specific individual, export it, correct it, restrict it, or delete it within the regulation's response window (one month for most rights under GDPR). Systems where personal data is scattered across many tables, services, logs, backups, and third-party platforms—with no central inventory—cannot honor these rights reliably and are at compliance risk.

---

## 5. PDPA Specifics

Singapore's Personal Data Protection Act (PDPA) shares the conceptual foundation of GDPR but is more pragmatic and less prescriptive. The PDPA was originally enacted in 2012, came into force in 2014, and was substantially amended in 2020 to introduce data-portability rights, mandatory breach notification, and significantly increased penalties.

Key features:

- **Consent-based model**, with broader allowances for **deemed consent** and a list of permitted exceptions where consent is not required (e.g., processing necessary for legitimate interests, business asset transactions, certain research purposes).
- **Do Not Call (DNC) Registry** governing marketing calls and messages to Singapore phone numbers; organizations must check the registry before marketing outreach.
- **Mandatory data-breach notification** for breaches that result in significant harm or affect 500 or more individuals; notification must reach the PDPC and affected individuals within prescribed timelines.
- **Penalties** up to **SGD $1 million** or **10% of annual turnover in Singapore** (whichever is higher for organizations with annual turnover exceeding SGD $10 million)—raised substantially in the 2020 amendments.
- **Cross-border transfer requirements** ensure that data sent outside Singapore receives a comparable standard of protection.

Compared to GDPR, the PDPA is generally considered more business-friendly: more practical guidance, more flexibility in how consent is obtained, and a less prescriptive approach to processing. Compliance approaches that satisfy GDPR typically satisfy PDPA without additional work; the reverse is not always true.

---

## 6. COPPA for Children's Apps

The **Children's Online Privacy Protection Act (COPPA)** governs personal information collected from children under 13 by online services in the United States. It came into effect in 2000 and is enforced by the Federal Trade Commission. Children's-app developers operating in or marketing to the US must comply with COPPA regardless of company location.

COPPA's key obligations:

- **Verifiable parental consent** is required before collecting, using, or disclosing personal information from a child under 13. Acceptable consent methods include credit-card verification, signed consent forms, government-ID verification, video chat with a trained person, and several others outlined in the FTC's COPPA Rule. The standard is "verifiable"—a checkbox claiming "I am the parent" is not sufficient.
- **Limited data collection** from children: the operator may collect only personal information reasonably necessary for the activity. Persistent identifiers used for behavioral advertising are explicitly restricted.
- **No conditioning participation on disclosure**: a child cannot be required to disclose more information than reasonably necessary to participate in an activity.
- **Parental access rights**: parents must be able to review the personal information collected from their child, refuse further collection, and require deletion.
- **Data security**: operators must maintain reasonable security for collected personal information.
- **Direct-to-child notices and parent-facing privacy policies** must clearly describe practices.
- **No behavioral advertising** to children based on their personal information without verifiable parental consent.

COPPA penalties have reached substantial levels in major cases (tens to hundreds of millions of dollars), and the FTC has been increasingly active in enforcement. Children's-app companies that get COPPA wrong face both legal and reputational consequences that can be existential for a startup.

Several jurisdictions have parallel regulations for children's data: GDPR's **Article 8** addresses consent for children's data, with the age threshold varying by EU member state (16 by default, lowered to 13 in some); the UK's **Age-Appropriate Design Code** imposes additional design-level requirements; California's CCPA includes specific provisions for under-16 users.

---

## 7. Implementation Patterns (Privacy by Design)

**Privacy by Design** is the principle—originally articulated by Ann Cavoukian and now a GDPR requirement (Article 25)—that privacy considerations should be built into systems from the start, not retrofitted. The pattern produces architectures that satisfy regulations as a side effect of well-designed data flows, rather than as a separate compliance overlay.

Key implementation patterns:

- **Data inventory.** Maintain a registry of every category of personal data the system processes: what data, where it lives, who has access, what it is used for, where it is shared, and how long it is retained. The inventory is the foundation for satisfying access, deletion, and accountability requirements. Without it, data subject requests are best-effort guesses.
- **Data minimization in design.** When designing a feature, ask what data it strictly needs and collect only that. Optional fields should default to off; analytics events should not include identifiers that are not needed.
- **Purpose binding in code.** Tag data with the purpose for which it was collected. Processing for incompatible purposes (e.g., using customer-service data for marketing) violates purpose limitation.
- **Encryption at rest and in transit.** TLS 1.2 minimum for transit. AES-256 or equivalent for storage of sensitive fields. Database-level encryption is necessary but not sufficient—application-level encryption of particularly sensitive fields adds defense in depth.
- **PII redaction in logs.** Application logs and analytics events frequently leak personal data. Audit log output for redaction; use structured logging libraries with field-level redaction filters.
- **DSR automation.** Build APIs and internal tooling for Data Subject Requests: identify all data about a user, export it in machine-readable form, delete it across all stores including backups and third-party processors. Manual DSR processing does not scale and produces compliance gaps.
- **Defined retention policies.** Every category of data has a defined retention period beyond which it is deleted or anonymized. Implement retention as automated deletion jobs, not as policy documents.
- **Consent management.** A consent management platform records what each user has consented to, when, and on what basis. Consent must be specific, informed, freely given, and revocable; the system must reflect changes promptly.
- **Cookie consent for EU users.** GDPR (and the ePrivacy Directive) requires informed consent before non-essential cookies are set. Cookie consent banners are the standard implementation.
- **Data Processing Agreements (DPAs).** When a third-party processor handles personal data on the organization's behalf (cloud providers, analytics vendors, email providers), a DPA documents the obligations and is itself a compliance artifact.
- **Breach notification readiness.** Define and test the process for detecting breaches, assessing their scope, and notifying authorities and affected individuals within regulatory timelines (72 hours under GDPR for many cases).

The architectural shift these patterns produce: data flows are explicit, minimal, and traceable, with deletion and access as first-class operations rather than afterthoughts.

---

## 8. Example: Compliance Plan for Educational Coding App for Kids

Consider a compliance plan for **CodeCub**, a Python-based educational coding app for children aged 6–12, with a target market spanning the United States (COPPA), the European Union (GDPR), Singapore (PDPA), and California specifically (CCPA). The application is subject to all four regimes simultaneously.

**Identity and consent flow:**

- **No child-direct accounts.** Children access the app through a parent account. The parent registers, verifies their email, and creates child profiles within their account. Children do not provide email addresses, passwords, or contact information directly.
- **Verifiable parental consent for COPPA.** Before any data collection beyond what is strictly necessary for in-app function, the parent completes a verifiable-consent flow. The default at launch is **credit-card verification** (a small charge that is immediately refunded, sufficient to establish the consenting individual is an adult). For non-paying users, the alternative is a **signed consent form** workflow.
- **GDPR-aligned consent for EU users.** The same consent flow extends to GDPR Article 8 requirements. The age threshold for parental consent in each EU member state is checked against the parent's locale; where the threshold is 13 (some member states), COPPA-aligned consent suffices; where it is higher (up to 16), the same verifiable-parental-consent flow applies.
- **PDPA for Singapore users.** Consent is obtained at signup and documented. The PDPA's deemed-consent provisions are not relied upon for child data.
- **CCPA opt-outs.** California users see explicit notices about any data sharing that might constitute "sale" under CCPA, with opt-out controls. Children under 16 in California require opt-in consent for any such sharing (CCPA's heightened standard for minors).

**Data minimization:**

- **Child profiles store minimum data**: a parent-chosen display name, an age band (`6-8`, `9-10`, `11-12`), and progress data (lessons completed, attempts, achievements). No real names, addresses, phone numbers, or independent contact information for children.
- **No third-party advertising or behavioral tracking** of children. Analytics on child usage are first-party only and aggregated wherever possible.
- **Lesson telemetry** captures progress and learning outcomes but not voice recordings, video, or other rich biometric data.

**Storage and security:**

- **Encryption at rest** (database-level encryption on PostgreSQL, plus application-level encryption for particularly sensitive fields).
- **Encryption in transit** (TLS 1.3 throughout; HSTS enforced).
- **Access controls** via the RBAC scheme described in the auth document; access to child data is logged for audit.
- **Hosted in regions appropriate to user location**: EU data on EU-region infrastructure where required; Singapore data on Singapore-region infrastructure where required. Cross-border transfers governed by Standard Contractual Clauses or equivalent mechanisms.

**Data subject request (DSR) automation:**

- **Parent-facing self-service portal** for the rights that GDPR, PDPA, COPPA, and CCPA all support: review all data the system holds about their child, export it in JSON, correct it, and request deletion.
- **Deletion is implemented as a real deletion**, not a soft-delete or "anonymization in name only." The deletion API removes records from primary databases, replicas, search indexes, analytics warehouses, third-party processors (Stripe for billing, email service providers for transactional emails, AI providers for tutoring history), and backups (with backup deletion handled through a documented schedule).
- **Audit log** of every DSR request: who requested, what was returned or deleted, when. Logs are retained for the period required by applicable regulations and exempt from the deletion request itself (legal-obligation basis under GDPR).

**Retention policies:**

- **Active learner data**: retained for as long as the parent's account is active.
- **Account deletion**: parent-initiated deletion erases all data within 30 days, with a documented exception for legally required retention (financial records, fraud investigation evidence) for the periods specified by applicable law.
- **Inactive account auto-deletion**: parent accounts inactive for 24 months trigger an automated email warning; if no response, the account and all child data are deleted automatically.
- **Logs**: application logs containing any personal data are retained for 90 days; security and audit logs retained longer per legal requirements.
- **Backups**: rolling 30-day window; deletion requests against backups handled via the documented schedule.

**Third-party processors:**

- A maintained inventory of every third-party service that touches personal data: cloud provider (compute, storage), database provider, payment processor, email service, AI tutoring API provider, analytics platform.
- A signed Data Processing Agreement (DPA) with each.
- A documented assessment of each provider's certifications (SOC 2, ISO 27001) and data residency options.

**AI tutoring specifically:**

- The AI tutoring layer must not transmit identifiable child data to LLM providers. Prompts are constructed using non-identifying tokens (age band, lesson context, code submission) without names or stable IDs.
- AI conversation logs are stored in the application's own database (not solely on the provider's side) and are subject to the same retention and deletion policies as other child data.
- AI provider DPAs explicitly cover children's data processing.

**Breach response:**

- Documented incident-response runbook with breach-notification timelines aligned to each applicable regulation: 72 hours under GDPR for many cases; PDPC for breaches affecting 500+ individuals or producing significant harm; FTC for COPPA-related incidents involving children's data; California Attorney General for CCPA.
- Regular tabletop exercises to verify the runbook is operationally current.

**Documentation:**

- A clear, plain-language **privacy policy** explaining what data is collected, why, with whom it is shared, and how rights can be exercised.
- A separate **direct-to-child notice** appropriate to the youngest age bands, written for the child user.
- A **cookie-consent banner** for EU users, with granular controls for analytics and functional cookies.
- A **records of processing** document maintained internally as required by GDPR Article 30.

The cumulative effect: privacy compliance is built into the architecture, not bolted on. The team builds systems that minimize data, document its flow, encrypt it, enable user rights, delete it on schedule, and produce audit trails. Compliance is the natural output of these patterns, not a separate workstream.

---

## 9. Common Pitfalls

- **Logging PII in plaintext.** Application logs, debug output, and error traces routinely include emails, names, identifiers, and request bodies that contain personal data. Log infrastructure is rarely secured to the same standard as the primary database, and logs are often retained longer. Audit log output for PII; use redaction filters.
- **No data retention policy.** Indefinite retention is itself a violation of GDPR's storage-limitation principle. "We keep it forever just in case" is not a lawful basis. Define retention by data category and implement automated deletion.
- **Confusing consent with legitimate interest.** GDPR offers six lawful bases for processing; consent is one, legitimate interests is another. Each has its own requirements, and they are not interchangeable. Marketing communications usually require consent; security operations may rely on legitimate interest. Get this distinction wrong and the entire processing activity becomes unlawful.
- **Soft-deleting and calling it "deletion."** A `deleted_at` column is fine for application semantics but does not satisfy GDPR's right to erasure. Real deletion across all stores, with documented backup handling, is required.
- **Forgetting backups.** Deletion that does not propagate to backups leaves personal data in places the system claims it has erased. Document backup-retention windows and ensure deletion requests are honored within them.
- **Cookie banners that nudge consent.** Banners with prominent "Accept all" buttons and hidden "Reject all" options have been ruled non-compliant by EU regulators. Symmetric controls are required.
- **Skipping DPAs with processors.** Every third-party service that processes personal data on the organization's behalf requires a DPA. Operating without one is a violation regardless of how compliant the service itself may be.
- **Treating COPPA as an afterthought for kids' apps.** COPPA enforcement has accelerated, with substantial penalties in recent years. Children's-app companies that ship without robust verifiable-consent flows are exposed.
- **Cross-border transfers without legal basis.** Sending EU personal data to non-EU jurisdictions requires a transfer mechanism (Standard Contractual Clauses, adequacy decisions, Binding Corporate Rules). Default cloud configurations often do not provide one.
- **Not testing DSR flows.** A DSR pipeline that works in staging but fails on real production data—because some data lives in a system the team forgot about—produces compliance failures during real requests. Test it on real edge cases before relying on it.

---

## 10. References

- GDPR.eu: https://gdpr.eu/
- Singapore PDPC — Personal Data Protection Act overview: https://www.pdpc.gov.sg/Overview-of-PDPA/The-Legislation/Personal-Data-Protection-Act
- US FTC — Children's Online Privacy Protection Rule (COPPA): https://www.ftc.gov/enforcement/rules/rulemaking-regulatory-reform-proceedings/childrens-online-privacy-protection-rule