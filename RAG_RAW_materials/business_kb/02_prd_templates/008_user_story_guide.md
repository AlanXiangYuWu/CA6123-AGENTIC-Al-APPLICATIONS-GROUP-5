# User Story Writing Guide

**Category**: prd_template
**Source**: Atlassian, Mike Cohn (Mountain Goat Software)
**Use Case**: Product Agent uses this template when converting features into user-centric stories during PRD writing.

---

## 1. Overview

A user story is a short, plain-language description of a product capability told from the perspective of the person who will use it. Its purpose is to keep development centered on user outcomes rather than on technical artifacts. Where a traditional requirement might read "the system shall allow password reset via email," a user story reframes the same capability as a goal: "As a returning user who has forgotten my password, I want to reset it through my email, so that I can regain access without contacting support."

User stories originate in agile software development and are most strongly associated with Mike Cohn, whose formalization of the standard template and the Three C's (Card, Conversation, Confirmation) shaped how modern product teams write them. Stories are deliberately lightweight: they are not exhaustive specifications but invitations to a conversation. The acceptance criteria, edge cases, and design details emerge through that conversation and are confirmed before the story is considered complete.

A well-written story is small enough to be delivered within a single sprint, valuable enough to justify the work on its own, and testable enough that the team knows when it is done. This guide presents the standard template, the INVEST principle for evaluating story quality, the Three C's for working with stories in practice, the distinction between epics, stories, and tasks, and concrete examples grounded in an educational coding app for children aged 6–12.

---

## 2. The Standard Template

The canonical user story template is:

> **As a [role], I want to [action], so that [benefit].**

Each clause has a specific job. The **role** identifies who the story is for and grounds the story in a real persona. The **action** describes what that person wants to do. The **benefit** explains why—the underlying outcome that makes the action worth taking.

The "so that" clause is the most strategically important part of the template, because it captures the *why*. Without it, a story collapses into a feature request and loses the link to user value. A story that reads "As a parent, I want a weekly progress email" is incomplete; the same story written as "As a parent, I want a weekly progress email, so that I can confirm my child is actually learning and not just opening the app" is meaningfully different. The benefit clause exposes the underlying goal—reassurance about screen time investment—and that goal can be served in many ways. The team is now free to consider whether the email is the best solution or whether an in-app dashboard, a shareable certificate, or a parent-child review session would serve the same outcome better.

A good rule: if the "so that" clause could be removed without changing the meaning of the story, it is too generic and should be rewritten until it carries real information.

---

## 3. The INVEST Principle

INVEST, coined by Bill Wake and popularized by Mike Cohn, is a checklist for evaluating whether a user story is well-formed. Each letter represents one criterion.

| Letter | Criterion | What it means |
|---|---|---|
| I | **Independent** | The story can be delivered without requiring another story to be done first. Independent stories can be reordered, reprioritized, and shipped in any sequence. |
| N | **Negotiable** | The story is not a fixed contract; the details are open to discussion between product, design, and engineering until acceptance criteria are confirmed. |
| V | **Valuable** | Completing the story delivers tangible value to a user or to the business. Stories that produce no observable user-facing or business outcome on their own are usually technical tasks, not stories. |
| E | **Estimable** | The team can estimate the effort with reasonable confidence. If estimation is impossible, the story is either too large, too vague, or requires upstream research (a "spike"). |
| S | **Small** | The story is small enough to be completed within a single sprint, ideally a few days. Larger work is an epic and must be split. |
| T | **Testable** | Clear, objective acceptance criteria exist; the team can demonstrate when the story is done. Stories without testable criteria invite scope drift. |

Using INVEST as a checklist before committing to a story prevents the most common backlog pathologies: stories that cannot ship until others ship, stories that are so over-specified there is nothing left to discuss, stories that produce no user-visible outcome, stories that the team cannot size, stories that span entire quarters, and stories that no one knows how to verify.

---

## 4. The Three C's: Card, Conversation, Confirmation

Mike Cohn's Three C's describe how a user story exists in three connected forms across its lifecycle.

**Card**
The card is the brief written form of the story—originally an actual index card, today usually a ticket in Jira, Linear, or a similar tool. The card holds just enough text to identify the story and trigger memory: typically the one-sentence story template plus a short title. Crucially, the card is not the specification. It is a placeholder for a conversation.

**Conversation**
The conversation is the collaborative discussion that fleshes out the story. Product, engineering, design, and any other relevant participants explore the user's situation, edge cases, dependencies, and trade-offs. The conversation is where ambiguity is resolved and where the team aligns on what "done" actually looks like. This is also where the negotiable element of INVEST plays out—details that seemed fixed on the card may shift once the team understands the constraints.

**Confirmation**
Confirmation is the set of acceptance criteria that proves the story is done. These are written explicitly, typically in the "Given/When/Then" form or as a checklist of observable behaviors. Confirmation closes the loop opened by the card: the story is complete only when every acceptance criterion can be demonstrated. Acceptance criteria belong to the story itself and travel with it from grooming through review.

The Three C's discipline prevents the two most common failures of user-story practice: treating the card as a complete specification (skipping the conversation) and considering work done without explicit confirmation criteria (skipping the test).

---

## 5. Epic vs Story vs Task

User stories sit in a hierarchy of work items, and confusing the levels causes most planning friction.

| Level | Scope | Time horizon | Example (educational coding app) |
|---|---|---|---|
| **Epic** | A large body of user-facing work, broader than a single sprint and usually delivering a coherent capability. | Weeks to months. | "Teacher mode for classroom use." |
| **Story** | A single user-facing increment of value, deliverable within a sprint, written from the user's perspective. | A few days to one sprint. | "As a teacher, I want to assign a lesson sequence to my class, so that students can progress through a curriculum I have chosen." |
| **Task** | A technical step required to complete a story. Tasks are not user-facing and are not written in user-story form. | Hours to a couple of days. | "Add `class_id` foreign key to the `assignment` table; backfill existing rows." |

Epics are decomposed into stories; stories are decomposed into tasks. The decomposition rule is that every story must independently deliver value to a user, while tasks need only contribute to a story. A signal that something has been miscategorized: if a "story" reads naturally only to engineers and produces no observable user outcome, it is almost certainly a task. If a "story" cannot be completed in a single sprint, it is almost certainly an epic and should be split.

---

## 6. Examples and Anti-Patterns

The following examples are drawn from the educational coding app domain (Python lessons for children aged 6–12, with parent and teacher roles).

**Three well-written user stories**

1. *As an 11-year-old learner, I want to remix a mini-game that another child has published, so that I can show my friends a version I customized myself.*
   - The role is specific (age-banded learner), the action is concrete, and the "so that" clause exposes a real emotional and social outcome (pride, sharing). It is small, testable (acceptance criteria can describe remixing flow), and valuable on its own.

2. *As a parent of a child using the app, I want a weekly email summarizing which lessons my child completed, so that I can feel confident that screen time is producing real learning.*
   - The benefit clause carries genuine information about why the email matters; the team can now evaluate whether email is the best mechanism, or whether an in-app dashboard or a Sunday-morning recap might serve the same goal.

3. *As a classroom teacher running an after-school coding club, I want to cache assigned lessons for offline use, so that the club can run even when school Wi-Fi is unreliable.*
   - The role is grounded in a real situation, and the benefit reveals an environmental constraint (unreliable Wi-Fi) that engineering needs to know about. Acceptance criteria are obvious: assigned lessons must be available without a network connection.

**Three anti-patterns and why they fail**

1. *As a user, I want a button to share my code.*
   - **Missing the "why"** and the role is generic ("user"). What does sharing accomplish? With which audience? The story collapses to a feature request. Rewrite: *As a 9-year-old learner, I want to share a screenshot of my completed game with my parent, so that I can show them what I built today.*

2. *As a developer, I want to refactor the lesson loader to use the new caching layer, so that future lessons load faster.*
   - **Technical task disguised as a story.** The role is the wrong audience (developer, not user), and there is no observable user outcome on its own. This belongs as a task under a user-facing story (e.g., a story about reducing lesson load time), or as a tech-debt ticket outside the story format entirely.

3. *As a parent, I want a complete dashboard with progress, billing, parental controls, account management, content filters, multi-child support, and class integration.*
   - **Too large—this is an epic, not a story.** It cannot be completed in a sprint, it conflates many different user outcomes, and it cannot be estimated as written. Split into multiple stories, each delivering one coherent outcome (one for progress view, one for parental controls, one for multi-child support, and so on), grouped under a Parent Dashboard epic.

---

## 7. References

- Atlassian — User Stories: https://www.atlassian.com/agile/project-management/user-stories
- Mike Cohn / Mountain Goat Software — User Stories: https://www.mountaingoatsoftware.com/agile/user-stories
- Mike Cohn / Mountain Goat Software — The Three C's: Card, Conversation, Confirmation: https://www.mountaingoatsoftware.com/blog/the-three-cs-card-conversation-confirmation