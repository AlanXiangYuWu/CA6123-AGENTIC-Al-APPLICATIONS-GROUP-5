# Jobs-to-be-Done Framework

**Category**: methodology
**Source**: Strategyn, Christensen Institute, GoPractice
**Use Case**: Product Agent uses this lens to reframe user needs from product features to underlying jobs during requirements analysis.

---

## 1. Overview

Jobs-to-be-Done (JTBD) is a theory of customer behavior and a methodology for innovation. Its core premise is that people do not buy products for their own sake; they hire products to accomplish a job in their lives. The often-cited Theodore Levitt formulation captures the idea: "People don't want to buy a quarter-inch drill. They want a quarter-inch hole." The product is a means; the job is the end.

The framework was invented by Tony Ulwick, who developed JTBD theory and the Outcome-Driven Innovation (ODI) process in 1990. Ulwick first demonstrated its commercial impact at Cordis Corporation in 1992, where applying the method helped lift market share from 1% to over 20%. In 1999, Ulwick introduced JTBD to Clayton Christensen, who later popularized the concept in his 2003 book *The Innovator's Solution*, citing Ulwick's work. Bob Moesta subsequently developed a distinct variation focused on Demand-Side Sales.

JTBD reframes innovation away from product features and demographic segments toward the underlying progress a customer is trying to make. By understanding the job, product teams can identify unmet needs, define meaningful success metrics, and design solutions that compete on the right dimension—the customer's desired outcome rather than feature parity.

---

## 2. Key Concepts

- **Job**: the progress a person is trying to make in a particular circumstance.
- **Hiring and firing**: customers hire a product to do a job and fire it when a better candidate appears.
- **Functional, emotional, and social dimensions**: every job has these three layers operating simultaneously.
- **Job Statement**: a structured articulation of a job, independent of any specific solution.
- **Outcome statement**: a measurable success criterion attached to a job step (central to Ulwick's ODI).
- **Forces of progress**: the push, pull, anxieties, and habits that drive or block a customer switch (central to Moesta's school).
- **Solution-agnostic framing**: jobs are described without reference to product features so that competing or future solutions can be evaluated on the same job.
- **Milkshake Study**: Christensen's well-known case where morning commuters were found to hire milkshakes for the job of making a long, boring drive more interesting while keeping them full until lunch.

---

## 3. The Three Schools of Thought

Although JTBD shares a common origin, three distinct schools have emerged, each with different emphases and methods.

**Christensen school — Jobs as functional + emotional + social**
Clayton Christensen and the Christensen Institute frame the job broadly. A job has a functional core but is always accompanied by emotional and social dimensions, and understanding all three is essential. The Milkshake Study is the canonical illustration: the functional job is "consume breakfast on the road," but the emotional and circumstantial layers (boredom, one free hand, satiety until lunch) are what actually explain the purchase. This school emphasizes qualitative interviews and narrative case studies.

**Moesta school — Demand-Side Sales and forces of progress**
Bob Moesta developed Demand-Side Sales as a variation focused on the moment of switching. The central question is what causes a customer to leave the old solution and adopt a new one. Moesta's lens analyzes four forces: the push of the current situation, the pull of the new solution, the anxiety about change, and the habit of the present. This school is particularly suited to sales, marketing, and onboarding design, because it focuses on the psychology of switching rather than feature design.

**Ulwick school — Outcome-Driven Innovation (ODI)**
Tony Ulwick's ODI is the most quantitative of the three. Jobs are decomposed into discrete steps, and each step produces a set of outcome statements expressed as measurable metrics (typically of the form "minimize the time it takes to..." or "increase the likelihood that..."). Customers rate each outcome on importance and current satisfaction, exposing under-served outcomes that represent innovation opportunities. Strategyn reports an 86% success rate for innovation projects using ODI, compared to roughly 17% for the industry average. This school is best suited to systematic product strategy, market sizing, and roadmap prioritization.

| School | Founder | Primary lens | Output |
|---|---|---|---|
| Christensen | Clayton Christensen | Functional + emotional + social job | Narrative job descriptions |
| Moesta (Demand-Side Sales) | Bob Moesta | Forces of progress around switching | Switching interviews and timelines |
| Ulwick (ODI) | Tony Ulwick | Job steps with measurable outcomes | Outcome statements and opportunity scores |

The three schools are complementary rather than contradictory. Many product teams use Christensen's framing to articulate the job, Moesta's lens to study switching behavior, and Ulwick's outcome statements to define measurable success.

---

## 4. Job Dimensions and Statement Template

A job has three dimensions that operate together:

- **Functional**: the practical task to be accomplished. What is the customer trying to do?
- **Emotional**: how the customer wants to feel, or avoid feeling, while doing the job. Includes self-perception.
- **Social**: how the customer wants to be perceived by others while doing the job.

A well-formed Job Statement is solution-agnostic—it could be satisfied by many different products—and uses the following template:

> **When [situation], I want to [motivation], so I can [expected outcome].**

For example: "When I am commuting alone in heavy morning traffic, I want something I can consume one-handed that will keep me occupied and full, so I can reach lunch without getting hungry." Note that this statement says nothing about milkshakes, breakfast bars, podcasts, or any specific product. That is intentional. The job exists independently of the solution, which means competing solutions can be evaluated against the same criteria.

A common diagnostic for whether a Job Statement is well-formed: if it would still make sense ten years from now, when today's solutions may be obsolete, it is correctly framed at the job level rather than the feature level.

---

## 5. Example: Educational Coding App for Kids

Consider parents evaluating a Python-based educational app for children aged 6–12. The buyer is the parent; the user is the child; both have jobs to be done.

**Parent's Job Statement**
> When my child has unstructured screen time after school, I want to redirect that time toward an activity that builds future-relevant skills, so I can feel that screen time is an investment rather than a waste.

**Three dimensions for the parent:**

| Dimension | Description |
|---|---|
| Functional | Replace passive entertainment with structured learning that teaches programming fundamentals appropriate to the child's age. |
| Emotional | Relieve guilt about screen time; feel like a responsible, engaged parent. |
| Social | Be able to tell other parents and family members that the child is learning to code; signal modern, forward-looking parenting. |

**Child's Job Statement**
> When I have free time and want to play, I want an activity that feels like a game and lets me create things I can show off, so I can have fun and feel proud of what I made.

**Three dimensions for the child:**

| Dimension | Description |
|---|---|
| Functional | Be entertained; build something tangible (a small game, an animation, a story). |
| Emotional | Feel competent, autonomous, and proud of personal creations. |
| Social | Show off creations to parents, siblings, and friends; appear capable and creative. |

**Implication for the product**
The product is hired by the parent and the child simultaneously, and the two jobs are different. A feature like sharable, kid-built mini-games serves both: it satisfies the child's social job (showing off) and the parent's social job (proof of progress to share with relatives). A feature like detailed parental progress reports serves only the parent's functional job. A feature that is purely entertainment without skill-building risks getting fired by the parent. A feature that is purely educational without playfulness risks getting fired by the child. This dual-job analysis directly informs prioritization.

---

## 6. Step-by-step Application

1. **Identify the customer and the moment of progress** — locate the situation in which the customer feels a need to change something. Avoid starting from a product idea.
2. **Conduct switch interviews** — interview customers who recently adopted (or abandoned) a solution. Reconstruct the timeline from first thought to first use, focusing on context and triggers rather than feature opinions.
3. **Articulate the job in solution-agnostic language** — write a Job Statement using the When/I want to/So I can template. Verify it does not name any specific product.
4. **Map the three dimensions** — describe the functional, emotional, and social layers of the job. Confirm that each layer is grounded in evidence from interviews.
5. **Decompose the job into steps (ODI)** — for quantitative work, break the job into sequential steps and generate outcome statements for each step in the form "minimize the time to..." or "increase the likelihood of..."
6. **Measure importance and satisfaction** — survey the target audience to rate each outcome on importance and current satisfaction. Outcomes with high importance and low satisfaction are the highest-value opportunities.
7. **Prioritize the roadmap by job, not by feature** — frame each PRD around the job it serves and the outcomes it improves, rather than the features it ships.
8. **Re-evaluate when context changes** — jobs are durable, but the circumstances around them shift. Re-run the analysis when entering a new segment or after major market changes.

---

## 7. Common Pitfalls

- **Confusing the product with the job** — describing the job in terms of the current solution ("the job is to use our app") collapses the framework's core insight.
- **Stopping at the functional layer** — ignoring emotional and social dimensions produces solutions that work technically but fail to get hired.
- **Treating personas as jobs** — demographic segments do not have jobs; people in specific circumstances do. The same person has different jobs in different situations.
- **Asking customers what they want** — customers articulate solutions, not jobs. The interviewer must extract the underlying job from stories of behavior.
- **Skipping the switch interview** — focusing only on current users misses the forces that drove adoption and the alternatives that were considered and rejected.
- **Ignoring non-consumption** — sometimes the most important competitor is the customer doing nothing at all; non-consumers reveal jobs that no existing product serves well.
- **Confusing the buyer's job with the user's job** — when the two are different people (parent and child, manager and employee), both jobs must be analyzed.
- **Outcome statements that name a feature** — well-formed outcome statements describe the result the customer wants, not the mechanism for achieving it.

---

## 8. References

- Strategyn — Jobs-to-be-Done: https://strategyn.com/jobs-to-be-done/
- Christensen Institute — Jobs to Be Done theory: https://www.christenseninstitute.org/theory/jobs-to-be-done/
- GoPractice — Jobs-to-be-Done: the theory and the frameworks: https://gopractice.io/product/jobs-to-be-done-the-theory-and-the-frameworks/