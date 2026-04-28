# Code Review Best Practices

**Category**: quality
**Source**: Google Engineering Practices, Thoughtbot
**Use Case**: QA Agent uses this checklist when reviewing Coder Agent's output.

---

## 1. Overview

**Code review** is the systematic examination of code by peers before it is merged into the main branch. The practice has become standard across modern software development, and for good reason: review catches defects before they reach production, distributes knowledge across the team, and produces a codebase that ages better than one shaped by individual developers working in isolation. A team that reviews thoughtfully produces better software with fewer surprises; a team that does not review accumulates technical debt and bugs at a steeper curve.

Two of the most influential public references on code review are **Google's Engineering Practices documentation**—a public version of internal guidance refined across decades of engineering at scale—and **Thoughtbot's code-review guide**, which captures the practical norms of a smaller, professional-services-oriented team. The two perspectives differ in emphasis but converge on the same underlying principles: small changes, clear descriptions, prompt and respectful review, and a focus on the change as a whole rather than a hunt for perfection.

This document covers the goals of code review, the responsibilities of authors and reviewers, the eight-point review checklist that covers what reviewers should examine, the "nit" convention that distinguishes blocking from non-blocking feedback, the recurring anti-patterns that erode review's value, and a worked example showing how review comments look in practice for a feature in an educational coding app.

---

## 2. Goals of Code Review

Google's engineering practices articulate a hierarchy of code-review goals, listed in order of importance:

1. **Maintain code health over time.** The most important goal. Each change either makes the codebase healthier or less healthy; reviewers should approve changes that improve overall code health, even when imperfect, and push back on changes that degrade it. The phrase "the code does not have to be perfect, but it does have to leave the codebase in a better state than before" captures the principle.
2. **Knowledge sharing.** Review is one of the few moments where engineers regularly read each other's code in detail. The reviewer learns about the parts of the system the author has touched; the author learns from the reviewer's questions and suggestions. Over time, this distributes knowledge across the team and reduces the "only one person understands this part" risk.
3. **Catch bugs.** Real, but secondary. Most bugs are caught by tests, type systems, and CI; review catches a meaningful additional fraction, particularly the kind that escape automated tools (subtle race conditions, incorrect assumptions, missed edge cases). Treating bug-catching as the primary goal—and pursuing it through nitpicking and exhaustive review—produces slow, hostile reviews that do not actually catch many more bugs.
4. **Mentorship.** Review is a natural channel for senior engineers to teach more-junior ones, and for engineers new to a part of the system to learn its conventions. Mentorship in review is gentle and incremental; it works through suggestions and explanations, not through enforcement.

The hierarchy matters because the goals occasionally conflict. A reviewer focused entirely on bug-catching will block a change for a marginal concern that does not affect overall code health; a reviewer focused on health will approve a change with minor issues and suggest improvements as follow-ups. The Google guidance is that **health-and-progress over perfection** is almost always the right call.

---

## 3. Author Responsibilities

The author of a change has the larger share of the work in making review go well. Several disciplines matter.

**Keep PRs small.** A change of fewer than 400 lines is reviewable in a single sitting; a change of 2,000 lines is not. Large PRs receive worse review (reviewers skim or rubber-stamp because thorough review is overwhelming), produce more bugs, and merge slowly. When a feature genuinely requires more code, split the work into a sequence of small, individually mergeable PRs that build on each other.

**Write a clear PR description that explains WHY.** The diff shows what changed; the description should explain why the change exists, what problem it solves, what alternatives were considered, and what risks remain. A good description lets a reviewer assess the change's appropriateness before reading any code. Linking to the issue or design document is essential, not optional.

**Self-review first.** Before requesting review, the author opens the PR view and reads the diff as if they were a reviewer. Self-review catches typos, leftover debugging code, missing tests, and weak structure—the kinds of issues that waste a reviewer's time when caught externally.

**Keep each PR focused on one logical change.** Mixing a refactor with a feature with a bug fix in a single PR forces the reviewer to evaluate three things at once and produces messy git history. Each PR should answer "what one thing does this do?"

**Respond to every comment.** Either accept the suggestion and apply it, push back with reasoning if disagreement, or explicitly mark non-blocking comments as acknowledged. Silent ignoring of comments breaks the conversation and makes future review harder.

**Keep ownership of the change through merge.** The reviewer is a collaborator, not a substitute for the author's judgment. The author retains responsibility for the change's design and quality.

---

## 4. Reviewer Responsibilities

Reviewers also have specific obligations.

**Respond promptly.** Google's internal guidance is to respond within one business day; the same target serves most teams well. Slow review is one of the largest sources of engineering frustration, because it blocks the author from moving on. If a thorough review will take longer, an acknowledgment ("looking, will respond by tomorrow") is itself helpful.

**Be respectful. Comment on code, not on the person.** "This function is hard to follow because the variable names overlap" is good. "You always write confusing code" is not. The pronoun discipline—"this code does X" instead of "you did X"—keeps the focus on the change rather than the author.

**Distinguish must-fix from suggestion.** Not every observation is blocking. The "nit:" convention (Section 6) is the standard way to signal that a comment is non-blocking. Reviewers who treat every comment as a blocker produce slow, frustrating review; reviewers who clearly mark severity allow the author to address blocking issues quickly and treat suggestions as opportunities.

**Approve when good enough, not when perfect.** The reviewer's job is not to bring the change to perfection; it is to confirm the change improves overall code health and is appropriate for its purpose. Approve and move on; reserve "request changes" for genuine blockers. Pursuing perfection produces stalled PRs and friction without proportional benefit.

**Ask questions instead of asserting when uncertain.** "I'm not sure why this branch is needed—can you explain?" invites collaboration. "This branch is wrong" without grounding produces defensiveness when the reviewer turns out to be the one who misunderstood.

**Praise good work.** Review is not only a venue for finding problems; it is also a venue for noticing what was done well. Brief positive comments on clean implementations or thoughtful test coverage cost nothing and reinforce the practices the team wants to see more of.

---

## 5. Review Checklist

A reviewer should examine a change against eight dimensions, in roughly decreasing order of importance.

1. **Design.** Is the change well-designed and appropriate for the system? Does it fit the existing architecture, or does it introduce a new pattern that is not justified? Is it solving the right problem? Design issues are the most expensive to fix later; catching them in review is high-value.

2. **Functionality.** Does the code do what it claims to do? Does the change behave correctly for the user? Does it handle the obvious edge cases? Reviewers should mentally execute the change against representative inputs, not just read the syntax.

3. **Tests.** Are there tests covering the change? Do the tests actually exercise the new behavior, or do they pass even when the new code is broken? Are the tests at the appropriate layer of the testing pyramid (unit for business logic, integration for boundaries, E2E for critical paths)? Untested changes raise the question of whether the author has verified the behavior at all.

4. **Naming.** Are variables, functions, classes, and modules named clearly? Names are the most enduring documentation a codebase has; sloppy names accumulate over years and produce confusion that no amount of comments can fix. Push back on names that obscure rather than clarify.

5. **Comments.** Where comments exist, do they explain **why** rather than **what**? Code that explains itself does not need a comment describing what it does; code with non-obvious motivation needs a comment explaining the reasoning. Comments that restate the obvious are noise; comments that document constraints, gotchas, or design decisions are valuable.

6. **Style.** Is the code consistent with the codebase's conventions? Style issues should mostly be caught by linters and formatters, not humans, but reviewers catch the cases that automated tools miss. Style discussions in review should be brief; codify the rule once in tooling rather than relitigating it on every PR.

7. **Documentation.** If the change affects the README, API documentation, configuration files, or runbooks, are those updated alongside the code? Documentation drift is a common source of operational confusion; catching it in review is much cheaper than discovering it during an incident.

8. **Security and Performance.** Are there obvious security issues (missing input validation, missing authorization checks, secrets in logs)? Are there obvious performance issues (N+1 queries, unbounded loops, blocking calls in async contexts)? These are not exhaustive—security and performance reviews go deeper than what general code review can cover—but obvious issues should be caught.

The order matters. Design issues found late are expensive; the reviewer should evaluate the high-level shape of the change before getting into line-by-line nits.

---

## 6. The "Nit" Convention and Comment Severity

A core practical convention in modern code review is the **"nit:"** prefix, which marks a comment as non-blocking—a suggestion the author can take or leave without affecting approval. The convention has spread because it solves a recurring tension: reviewers have legitimate observations that are not important enough to block on, and authors need to know which comments require action.

A useful three-level severity scheme:

- **Must-fix (blocking).** The comment must be addressed before merge. No prefix; the comment's severity is implicit. Examples: missing input validation, broken test, security issue, design flaw.
- **Suggestion (non-blocking but worth considering).** The author should evaluate; addressing is preferred but not required. Often unprefixed but written as a suggestion. Examples: "consider extracting this into a helper" or "this might be cleaner with a list comprehension."
- **Nit (taste-level, non-blocking).** Prefixed with `nit:`. The author can apply or skip. Examples: `nit: prefer 'learner_id' over 'userId' for consistency with the rest of the file`.

When the reviewer's intent is unclear, authors waste time guessing what is required. The prefix convention costs nothing and resolves the ambiguity.

A complementary discipline: when a reviewer has many nits and a few real issues, they should call out the real issues explicitly so they are not lost in the volume. "The blocking issue is the missing auth check on line 42; the rest are suggestions" is the kind of summary that makes review actionable.

---

## 7. Anti-Patterns

- **LGTM without reading.** "Looks good to me" rubber-stamping defeats the purpose of review. If the reviewer has not read the code, they should not approve. Sometimes a brief "I've skimmed and it looks reasonable; not deep-reviewing because it's a small refactor" is honest; silent approval of a complex change is not.
- **Bikeshedding.** Endless debate over trivial style choices when the substance is uncontroversial. The fix is to defer style decisions to tooling (formatters, linters with team-agreed configs) so they do not appear in human review at all.
- **Reviewer as gatekeeper.** Reviewers who treat their role as preventing changes from merging—rather than helping changes merge in good shape—produce slow, hostile review. The result is authors who avoid that reviewer and eventually a team that views review as obstacle rather than collaboration.
- **Author as defendant.** Reviewers phrase comments as accusations ("you broke this," "this is wrong"). Authors respond defensively. Both sides leave the interaction worse off. The fix is the language discipline above—comment on code, not on the person, and ask questions when uncertain.
- **Reviews that drag for days.** A PR that sits in review for three days for no good reason produces context-loss for the author. The fix is the prompt-response discipline; if review will take longer, communicate that.
- **Big PR + skimmed review.** When PRs are too large, reviewers skim. The fix is on the author side: keep PRs small enough to be reviewed thoroughly.
- **Approving with unaddressed comments.** A reviewer who leaves comments and then approves before they are addressed signals that the comments did not actually matter. Either the comments were unnecessary (do not leave them) or they did matter (do not approve until they are resolved).
- **Personal-taste enforcement disguised as standards.** "I prefer X" passed off as "the codebase does X" when it does not. The fix is to point at concrete examples or codified standards; if the convention is real, it can be cited.

---

## 8. Example: Code Review Comments for Educational Coding App for Kids

The following is a worked example of review comments on a fictional PR for **CodeCub**: a new endpoint that allows a parent to add a child profile to their account, with a corresponding schema change and a new validation function.

**Comment 1 — Design (must-fix)**

> The new `add_child_profile` endpoint accepts a `parent_id` directly from the request body. This bypasses the authorization model—any authenticated user could create a child profile under any parent's account. The `parent_id` should come from the authenticated session, not from the request body.
>
> *Context*: this is a fairly standard IDOR (Insecure Direct Object Reference) pattern. We've had this discussion before for the progress endpoint (PR #842) and landed on always deriving the parent identity from the session.

**Comment 2 — Functionality (must-fix)**

> `validate_age_band` accepts the literal strings `'6-8'`, `'9-10'`, `'11-12'`. The new endpoint passes a child's birth date and computes the band, but the computation rounds incorrectly for children whose birthday is today: a child turning 9 today is classified as `'6-8'` rather than `'9-10'`. Test case attached.

**Comment 3 — Tests (must-fix)**

> The endpoint has no test coverage. The PR description mentions the integration test in `test_parent_endpoints.py`, but the only test there exercises the existing endpoints, not this new one. We need at least one happy-path test (parent adds child, response is correct, database row exists) and one authorization test (parent A cannot create a child under parent B's account).

**Comment 4 — Naming (suggestion)**

> `def add_child_profile_v2` — what's the v2? If this is the second iteration of a previous design, the comment should explain. If not, the suffix is misleading. Suggest renaming to `add_child_profile`.

**Comment 5 — Comments (nit)**

> `nit:` The comment `# Compute age band from birth date` restates what the next line obviously does. Either delete the comment or replace it with one that explains the rounding rule the code is using (which is not obvious).

**Comment 6 — Style (nit)**

> `nit:` We use `snake_case` for column names elsewhere in the schema; this migration introduces `birthDate`. Recommend `birth_date` for consistency.

**Comment 7 — Security (suggestion)**

> Consider rate-limiting this endpoint. A scripted attack could create thousands of child profiles under a single parent account. Existing rate-limit middleware in `app/middleware/rate_limit.py` looks reusable.

**Comment 8 — Praise**

> The migration script's expand/contract sequence is exactly right—nullable column, backfill, then `NOT NULL` in a follow-up. Nice.

**Reviewer summary at the top of the review:**

> Approving in principle pending the three must-fix comments (design/auth, age-band rounding, missing tests). The nits and suggestions are optional; address whatever you have time for.

The example illustrates several disciplines:

- The reviewer summarizes severity at the top so the author can prioritize.
- Must-fix comments explain *why* they are blocking, not just that they are.
- The "nit:" prefix is used consistently.
- Suggestions point at concrete alternatives or existing patterns rather than vague preferences.
- Praise is included briefly where deserved.
- The language is about the code, not the author.

A PR review that follows this pattern is actionable, respectful, and produces a better outcome than either rubber-stamping or hostile gatekeeping.

---

## 9. References

- Google Engineering Practices — Code Review: https://google.github.io/eng-practices/review/
- Thoughtbot Guides — Code Review: https://github.com/thoughtbot/guides/tree/main/code-review