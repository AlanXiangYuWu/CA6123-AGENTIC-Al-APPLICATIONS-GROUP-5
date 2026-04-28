# Acceptance Criteria Writing Guide

**Category**: prd_template
**Source**: Atlassian, Mike Cohn, AltexSoft
**Use Case**: Product Agent and QA Agent use this format to specify and verify story completion.

---

## 1. Overview

Acceptance Criteria (AC) are the conditions a user story must satisfy to be considered complete. They translate the intent of a story into a set of observable, testable statements that the team uses to verify that the work is done. Where the user story expresses *what* the user wants and *why*, the acceptance criteria specify *under which conditions* the team will agree that the want has been met.

Mike Cohn refers to acceptance criteria as **Conditions of Satisfaction**: the conditions under which the customer or product owner will be satisfied that the story is delivered. The two terms are interchangeable in practice. Whichever name is used, the artifact serves the same role—closing the loop between the negotiable conversation that surrounds a user story and the binary judgment of whether that story has been completed.

This guide presents the two dominant AC formats (Given-When-Then and rule-oriented checklists), the properties that distinguish good acceptance criteria from poor ones, the boundary between AC and the team-wide Definition of Done, and concrete examples for a login feature in an educational coding app.

---

## 2. Why Acceptance Criteria Matter

Without explicit acceptance criteria, "done" becomes a matter of interpretation. Engineers may consider a story finished when the happy path works; QA may expect edge cases to be handled; product may discover at review that an obvious behavior was missed. Acceptance criteria pre-empt this drift by making the success conditions explicit and shared before implementation begins.

They serve four concrete functions. They **scope** the story by clarifying which behaviors are in scope and which are not. They **align** product, design, engineering, and QA on the same definition of done. They **drive testing** by providing the basis for test cases (manual, automated, or both). And they **resolve disputes** at review time, because a story either does or does not satisfy each criterion. Acceptance criteria written before code is written tend to surface ambiguity early, when it is cheap to resolve, rather than late, when it is expensive.

---

## 3. Format 1: Given-When-Then (BDD Style)

The Given-When-Then format originates in Behavior-Driven Development (BDD) and the Gherkin syntax used by tools such as Cucumber. Each criterion is a small scenario with three clauses:

- **Given** [precondition] — the state of the system and the user before the action.
- **When** [user action] — the trigger that initiates the behavior.
- **Then** [expected result] — the observable outcome that proves the behavior is correct.

Optional **And** clauses can be appended to any of the three sections to handle compound preconditions, multi-step actions, or multiple expected results.

**Example (educational coding app — lesson completion)**

> **Given** a learner is signed in and has started Lesson 5 but not completed it,
> **When** the learner submits a final solution that passes all built-in checks,
> **Then** Lesson 5 is marked as complete in the learner's progress,
> **And** the next lesson in the sequence is unlocked,
> **And** a celebratory animation plays for at least 1.5 seconds.

The Given-When-Then form is well-suited to flows with clear state changes—authentication, transactions, progression, error recovery—and it maps cleanly to automated test cases.

---

## 4. Format 2: Checklist (Rule-Oriented)

The checklist format expresses acceptance criteria as a flat bulleted list of conditions, without scenario structure. Each bullet is a discrete rule the implementation must satisfy. This format is well-suited to UI components, business rules, validation logic, and other contexts where multiple constraints apply but no single user flow dominates.

**Example (educational coding app — parent weekly email)**

- The email is sent every Sunday at 09:00 in the parent's local time zone.
- The email lists every lesson the child completed during the prior seven days.
- The email shows total time spent in the app for the prior week.
- If the child completed zero lessons, the email is still sent and includes a brief "no activity" note rather than being suppressed.
- The email contains an unsubscribe link in the footer.
- The email renders correctly on iOS Mail, Gmail web, and Gmail Android.

Checklist-format ACs are quicker to read and write but provide less structural guidance for testing than Given-When-Then. Many teams use both: Given-When-Then for behavioral flows and checklists for static rules and constraints, sometimes within the same story.

---

## 5. Properties of Good Acceptance Criteria

Regardless of format, good acceptance criteria share four properties.

- **Written from the user's perspective, not the implementation's.** "The page displays the lesson title within 2 seconds" is user-perspective. "The lesson title is fetched from the `/lessons/:id` endpoint with a 200 status" is implementation. The latter belongs in engineering design, not in AC.
- **Testable, with binary pass/fail outcomes.** A reviewer must be able to look at the running system and say yes or no. Criteria that require subjective judgment ("the animation should feel smooth") fail this test and must be rewritten with measurable thresholds.
- **Concrete and unambiguous.** Replace vague adjectives with specific numbers. "Fast" becomes "under 2 seconds at p95." "Easy to read" becomes "minimum 16px font size, contrast ratio of at least 4.5:1." If two reviewers could disagree about whether a criterion is met, it is not concrete enough.
- **Independent of implementation.** AC describe behavior, not how that behavior is achieved. The same criterion should remain valid if the team changes frameworks, databases, or architectures. This independence is what allows AC to function as a contract between product and engineering.

A useful heuristic: read each criterion aloud and ask, "Could a tester verify this without reading the source code?" If yes, the criterion is well-formed.

---

## 6. Acceptance Criteria vs Definition of Done

Acceptance Criteria and Definition of Done (DoD) are often confused but serve different purposes.

| Dimension | Acceptance Criteria | Definition of Done |
|---|---|---|
| Scope | Specific to one user story. | Applies to every story the team ships. |
| Owner | Authored by product, refined with the team during grooming. | Agreed upon by the team and stable across stories. |
| Content | Behavioral conditions for this story. | Quality and process gates (code reviewed, unit tests passing, deployed to staging, documentation updated, accessibility checked, telemetry instrumented). |
| Changes | New AC for every story. | Changes rarely, and deliberately, as team standards evolve. |

A story is considered complete only when both its AC and the team's DoD are satisfied. The AC ensures the right thing was built; the DoD ensures it was built to the team's quality standards. Neither replaces the other.

---

## 7. Example: Login Feature for Educational Coding App

Consider a login feature for the parent-facing portion of the app. The user story:

> *As a parent, I want to sign in to my account, so that I can view my child's progress.*

**Given-When-Then form**

1. **Given** a parent is on the login screen and has a valid registered email and password,
   **When** they enter both correctly and tap "Sign In,"
   **Then** they are redirected to the parent dashboard within 2 seconds,
   **And** their session remains valid for 30 days unless they sign out manually.

2. **Given** a parent is on the login screen,
   **When** they enter a registered email but an incorrect password,
   **Then** the system displays "Email or password is incorrect" without disclosing which field was wrong,
   **And** the password field is cleared while the email field is preserved.

3. **Given** a parent has entered an incorrect password 5 times consecutively within 15 minutes,
   **When** they attempt a 6th sign-in,
   **Then** the account is locked for 15 minutes,
   **And** the parent receives an email notifying them of the lockout and offering a password reset link.

**Checklist form**

- The login screen contains an email field, a password field, a "Sign In" button, and a "Forgot password?" link.
- The email field validates format on blur; invalid format displays "Please enter a valid email address" inline.
- The password field masks input by default and offers a visibility toggle.
- After 5 failed attempts within 15 minutes, the account is locked for 15 minutes; subsequent attempts during lockout display "Account temporarily locked. Try again in X minutes" with X computed from the lockout start time.
- All authentication requests use HTTPS and submit credentials only via POST body, never in URL parameters.
- The login screen meets WCAG 2.1 AA contrast and keyboard navigation requirements.

The two formats coexist comfortably: Given-When-Then captures the behavioral flows, checklist items capture static rules and security constraints.

---

## 8. Common Pitfalls

- **Implementation detail leaking into AC** — referencing endpoints, table names, or libraries instead of user-observable behavior.
- **Vague language** — "fast," "intuitive," "robust," "user-friendly" without measurable thresholds.
- **Missing edge cases** — happy-path-only criteria that ignore failure modes, empty states, and error recovery.
- **Confusing AC with DoD** — listing team-wide quality gates (code review, test coverage) as story-specific AC, or vice versa.
- **Ambiguous outcomes** — criteria that two reviewers could disagree about; rewrite until verification is binary.
- **Overlapping or contradictory criteria** — multiple bullets specifying the same behavior in different terms, or quietly conflicting on edge cases.
- **Writing AC after implementation** — undermines their purpose; AC written retroactively tend to describe what the code already does rather than what the user actually needs.
- **Too many criteria for one story** — a long AC list often signals that the story is too large and should be split.

---

## 9. References

- Atlassian — Acceptance Criteria: https://www.atlassian.com/work-management/project-management/acceptance-criteria
- Mike Cohn / Mountain Goat Software — Conditions of Satisfaction: https://www.mountaingoatsoftware.com/blog/conditions-of-satisfaction
- AltexSoft — Acceptance Criteria: Purposes, Formats, and Best Practices: https://www.altexsoft.com/blog/business/acceptance-criteria-purposes-formats-and-best-practices/