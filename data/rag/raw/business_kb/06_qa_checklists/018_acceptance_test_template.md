# Acceptance Test Case Template

**Category**: qa_checklist
**Source**: Atlassian, PractiTest
**Use Case**: QA Agent uses this template when generating and recording test cases.

---

## 1. Overview

An **acceptance test case** is a structured specification of how to verify that a piece of functionality satisfies its acceptance criteria. Where acceptance criteria describe the conditions a story must meet, test cases describe the procedures by which those conditions are checked: which preconditions must hold, which steps to execute, what to observe, and what verdict to record.

Test cases serve four purposes simultaneously. They **document** how the team verifies that work is done, in a form that survives across team members and across releases. They **drive execution**, providing manual testers and automation engineers with a repeatable script. They **support regression**, by accumulating into a suite that is re-run against future releases to catch unintended breakage. And they **communicate scope**, by exposing the cases the team has actually planned to verify and, by implication, the cases it has not.

A well-written test case has three properties: it is **complete** (every field filled, no implicit assumptions), it is **deterministic** (running the same steps produces the same outcome), and it is **independent** (the result does not depend on the success of prior test cases). This document defines the standard test case structure, describes the major test types, articulates best practices, distinguishes severity from priority, and provides a complete six-case example for a login feature in an educational coding app.

---

## 2. Standard Test Case Structure

Every test case includes the following fields. Examples are drawn from a hypothetical login test for the educational coding app.

- **Test ID** — A unique identifier, typically of the form `TC-NNN` or scoped by feature (`LOGIN-TC-001`). The ID is used to reference the test case from defect reports, traceability matrices, and automation scripts. *Example: `LOGIN-TC-001`.*
- **Title / Description** — A one-line summary of what the test verifies. *Example: "Valid credentials successfully log in a parent and route to the dashboard."*
- **Preconditions** — The environment and data state required before the test can run. Preconditions name the test environment, any required test accounts, and any system state that must be set up. *Example: "Test environment: staging. Test account: parent_test_001@example.com with password set to ValidPass123! and email verified."*
- **Test Steps** — A numbered sequence of actions to perform. Steps must be specific enough that any tester can execute them without interpretation. *Example: "1. Navigate to /login. 2. Enter parent_test_001@example.com in the email field. 3. Enter ValidPass123! in the password field. 4. Tap the Sign In button."*
- **Expected Result** — What the system should do at the end of the steps. The expected result must be observable and binary (passed or failed); subjective expectations ("the page should look nice") fail this test. *Example: "User is redirected to /dashboard within 2 seconds; dashboard displays parent_test_001's child profile cards."*
- **Actual Result** — Filled in during execution. Captures what actually happened, including screenshots, error messages, or response codes when relevant. Left blank in the template; populated during a test run.
- **Pass / Fail** — The verdict for the test run. A test passes only when the actual result matches the expected result exactly; partial matches are failures.
- **Severity** — For failed tests, the impact of the failure: Critical, Major, Minor, or Trivial. Severity is a property of the defect, not the test case in the abstract. (Discussed in Section 5.)
- **Priority** — The order in which the test should be executed in a test run: P0 (must run before any release), P1 (should run before release), P2 (run when time permits). Priority is a property of the test case itself and remains stable across runs.

Optional but commonly included fields: **Author**, **Date Created**, **Linked Story / Requirement**, **Test Type** (see Section 3), **Automation Status** (manual, automated, planned).

---

## 3. Test Types

Different categories of test verify different aspects of the system. A complete test suite includes cases from multiple types.

| Type | When to use | Example |
|---|---|---|
| **Functional** | To verify that the feature behaves as specified for happy-path inputs. | Valid credentials log a user in and route them to the dashboard. |
| **Boundary** | To verify behavior at the extremes of allowed input ranges (minimum, maximum, just-inside, just-outside). | Username of exactly 50 characters (the maximum allowed) is accepted; 51 characters is rejected. |
| **Negative** | To verify the system handles invalid input and error conditions gracefully. | Wrong password shows a clear error and does not lock the account on a single attempt. |
| **Performance** | To verify the system meets latency, throughput, or load requirements. | Login completes within 2 seconds at p95 under a simulated load of 500 concurrent users. |
| **Security** | To verify the system resists unauthorized access, injection, leakage, and abuse. | SQL injection in the password field is sanitized; failed-login messages do not disclose whether the email exists. |
| **Compatibility** | To verify the feature works across the supported matrix of browsers, OSes, devices, and screen sizes. | Login works on iOS Safari, Android Chrome, Windows Edge, and macOS Firefox at the latest two major versions of each. |

A complete acceptance suite for a feature like login typically includes several functional cases, a few boundary cases, several negative and security cases, at least one performance case, and a sampled compatibility matrix.

---

## 4. Best Practices

- **One test, one assertion.** Each test case verifies a single behavior with a single expected outcome. Cases that bundle multiple assertions become hard to interpret on failure (which assertion broke?) and hard to automate.
- **Independence.** A test case must not depend on the success of a previous test case. Each test should set up its own preconditions and tear down its own state. Tests that depend on chained outcomes are brittle and produce cascading failures.
- **Determinism.** Running the same case with the same preconditions should always produce the same result. Tests that depend on timing, randomness, or external services should explicitly handle those dependencies (mocks, fixed seeds, retry logic with bounded retries).
- **Clear, unambiguous expected results.** "Login works" is not an expected result. "User is redirected to /dashboard within 2 seconds and the dashboard displays the parent's child profile cards" is.
- **Automatable when possible.** Manual test cases are valuable for exploratory and visual checks; automated test cases are essential for regression at scale. Write cases in a form that an engineer could mechanically translate into automation.
- **Cover the happy path, the edge cases, and the failure modes.** A suite of only happy-path cases produces false confidence; a suite of only failure cases misses what the feature is actually supposed to do.
- **Maintain traceability.** Each test case should reference the user story or acceptance criterion it verifies, so that test coverage of requirements is auditable.

---

## 5. Severity vs Priority

Severity and priority are often confused but represent different dimensions.

- **Severity** is a property of a *defect*. It describes the impact on the user or business when the test fails. Severity scales typically run: **Critical** (the feature is unusable or data is corrupted), **Major** (a significant function is impaired but workarounds exist), **Minor** (a small function is degraded), **Trivial** (cosmetic or wording issue with no functional impact).
- **Priority** is a property of a *test case* (or, for defect triage, of a defect's required fix urgency). It describes the order in which work should be addressed. Priority typically runs P0 (immediately), P1 (next), P2 (when time permits).

The two are independent. A typo in marketing copy is high priority (visible to every user) but low severity (no functional impact). A complex bug in an edge case affecting 0.1% of users is low priority (small population) but high severity (affected users cannot complete the workflow). Test runs are organized by priority; defect remediation is organized by both severity and priority.

---

## 6. Example: Login Feature Test Suite

The following six test cases illustrate a complete acceptance suite for a login feature in the educational coding app. Each case is filled in with all standard fields.

**Test Case 1**
| Field | Value |
|---|---|
| Test ID | LOGIN-TC-001 |
| Title | Valid credentials successfully log in a parent and route to the dashboard. |
| Test Type | Functional |
| Preconditions | Test environment: staging. Test account `parent_test_001@example.com` exists with password `ValidPass123!` and email is verified. No existing session in the test browser. |
| Test Steps | 1. Navigate to `/login`. 2. Enter `parent_test_001@example.com` in the email field. 3. Enter `ValidPass123!` in the password field. 4. Tap the Sign In button. |
| Expected Result | User is redirected to `/dashboard` within 2 seconds. Dashboard displays the child profile cards associated with `parent_test_001`. Session cookie is set with a 30-day expiration. |
| Actual Result | _(filled during execution)_ |
| Pass / Fail | _(filled during execution)_ |
| Severity (if fails) | Critical |
| Priority | P0 |

**Test Case 2**
| Field | Value |
|---|---|
| Test ID | LOGIN-TC-002 |
| Title | Invalid password shows a generic error and does not log the user in. |
| Test Type | Negative |
| Preconditions | Test account `parent_test_001@example.com` exists with password `ValidPass123!`. No existing session. Account is not currently locked. |
| Test Steps | 1. Navigate to `/login`. 2. Enter `parent_test_001@example.com` in the email field. 3. Enter `WrongPassword!` in the password field. 4. Tap the Sign In button. |
| Expected Result | Page remains on `/login`. Error message "Email or password is incorrect" is displayed. The error does not disclose which field was wrong. The password field is cleared; the email field is preserved. No session cookie is set. |
| Actual Result | _(filled during execution)_ |
| Pass / Fail | _(filled during execution)_ |
| Severity (if fails) | Critical |
| Priority | P0 |

**Test Case 3**
| Field | Value |
|---|---|
| Test ID | LOGIN-TC-003 |
| Title | Account is locked for 15 minutes after 5 consecutive failed login attempts within 15 minutes. |
| Test Type | Boundary (security-adjacent) |
| Preconditions | Test account `parent_test_002@example.com` exists with password `ValidPass456!`. Account is not currently locked. Failed-attempt counter is at 0. |
| Test Steps | 1. Navigate to `/login`. 2. Submit incorrect password 5 times consecutively, with no more than 1 minute between attempts. 3. On the 6th attempt, submit either the correct or an incorrect password. |
| Expected Result | Attempts 1–5 each show the standard "Email or password is incorrect" error. On the 6th attempt, the system displays "Account temporarily locked. Try again in 15 minutes." regardless of whether the password is correct. An account-lockout email is sent to `parent_test_002@example.com` containing a password-reset link. |
| Actual Result | _(filled during execution)_ |
| Pass / Fail | _(filled during execution)_ |
| Severity (if fails) | Critical |
| Priority | P0 |

**Test Case 4**
| Field | Value |
|---|---|
| Test ID | LOGIN-TC-004 |
| Title | Email field accepts a valid email address at the maximum allowed length (254 characters). |
| Test Type | Boundary |
| Preconditions | A test account exists with an email address of exactly 254 characters in the form `<243-char-local-part>@example.com`, and with password `BoundaryPass789!`. |
| Test Steps | 1. Navigate to `/login`. 2. Enter the 254-character email address in the email field. 3. Enter `BoundaryPass789!` in the password field. 4. Tap the Sign In button. |
| Expected Result | The email field accepts all 254 characters with no truncation or rejection. Login succeeds and the user is redirected to `/dashboard`. A complementary case (LOGIN-TC-004b, not shown) verifies that 255 characters is rejected with a validation error. |
| Actual Result | _(filled during execution)_ |
| Pass / Fail | _(filled during execution)_ |
| Severity (if fails) | Major |
| Priority | P1 |

**Test Case 5**
| Field | Value |
|---|---|
| Test ID | LOGIN-TC-005 |
| Title | SQL injection payload in the password field is rejected and does not affect the database. |
| Test Type | Security |
| Preconditions | Test account `parent_test_003@example.com` exists with password `ValidPass789!`. Database has been snapshotted before the test. |
| Test Steps | 1. Navigate to `/login`. 2. Enter `parent_test_003@example.com` in the email field. 3. Enter `' OR '1'='1` in the password field. 4. Tap the Sign In button. |
| Expected Result | The login attempt fails with the standard "Email or password is incorrect" error message. No session is created. Application logs record the failed attempt. Database state is identical to the pre-test snapshot. The system does not return any database error to the client. A complementary case (LOGIN-TC-005b, not shown) repeats with a payload in the email field. |
| Actual Result | _(filled during execution)_ |
| Pass / Fail | _(filled during execution)_ |
| Severity (if fails) | Critical |
| Priority | P0 |

**Test Case 6**
| Field | Value |
|---|---|
| Test ID | LOGIN-TC-006 |
| Title | Password input is masked by default and toggles to plain text when the visibility toggle is activated. |
| Test Type | Security (UI) |
| Preconditions | No existing session. User is on the login page. |
| Test Steps | 1. Navigate to `/login`. 2. Enter `VisibleText123!` in the password field. 3. Observe the rendered field. 4. Tap the password visibility toggle (eye icon). 5. Observe the rendered field. 6. Tap the toggle again. 7. Observe the rendered field. |
| Expected Result | After step 3, the password field renders as masked dots (or platform-equivalent masking characters); the underlying value is `VisibleText123!`. After step 5, the field renders as plain text showing `VisibleText123!`. After step 7, the field returns to masked rendering. The visibility state does not persist across page reloads. |
| Actual Result | _(filled during execution)_ |
| Pass / Fail | _(filled during execution)_ |
| Severity (if fails) | Major |
| Priority | P1 |

The six cases together cover the functional happy path, a negative path, a boundary-and-security case (account lockout), a pure boundary case (email length), a pure security case (SQL injection), and a UI-security case (password masking). A complete suite would extend this with performance cases (login latency under load), additional negative cases (malformed email, empty fields), and compatibility cases across the supported browser/OS matrix.

---

## 7. References

- Atlassian — Test Cases in Scrum: https://www.atlassian.com/agile/scrum/test-cases
- PractiTest — Test Case Template Best Practices: https://www.practitest.com/qa-learningcenter/best-practices/test-case-template/