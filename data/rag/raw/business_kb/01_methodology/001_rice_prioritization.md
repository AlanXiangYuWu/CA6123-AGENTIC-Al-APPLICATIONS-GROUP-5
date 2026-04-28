# RICE Prioritization Framework

**Category**: methodology
**Source**: Intercom (original), ProductPlan, Whatfix
**Use Case**: Product Agent uses this framework to score and rank features by priority during PRD writing.

---

## 1. Overview

RICE is a quantitative scoring framework that helps product teams prioritize features and initiatives by evaluating four factors: **Reach, Impact, Confidence, and Effort**. Developed by Sean McBride and the product team at Intercom around 2017, RICE was designed to combat common biases in product prioritization—such as favoring "pet projects" or relying on gut feelings—by forcing teams to assign concrete numbers to each idea before comparing them. The framework's core formula divides the multiplied benefits (Reach × Impact × Confidence) by the cost (Effort), producing a single comparable score per initiative.

---

## 2. Key Concepts

- **Reach**: The number of users or events the initiative will affect within a defined time period (e.g., users per quarter).
- **Impact**: How significantly the initiative will contribute to a chosen goal or OKR, scored on a discrete scale.
- **Confidence**: A percentage representing how certain the team is about the Reach and Impact estimates.
- **Effort**: The total resources (typically person-months) required to ship the initiative.
- **RICE Score**: `(Reach × Impact × Confidence) / Effort`. Higher score = higher priority.

The framework is **comparative, not absolute**—a RICE score of 80 only means something next to other scored initiatives.

---

## 3. Framework Details

### Reach
Estimate how many people the initiative will affect in a fixed time window. Use real metrics where possible (e.g., monthly active users, signups per quarter).

| Example | Reach Estimate |
|---|---|
| Affects 80,000 users per quarter | 80,000 |
| Affects 5,000 users per month | 5,000 |

### Impact
Intercom uses a discrete five-point scale to avoid endless debate over precise values:

| Description | Score |
|---|---|
| Massive impact | 3 |
| High impact | 2 |
| Medium impact | 1 |
| Low impact | 0.5 |
| Minimal impact | 0.25 |

### Confidence
Expressed as a percentage:

| Confidence Level | Score |
|---|---|
| High confidence (strong data) | 100% |
| Medium confidence (some data + intuition) | 80% |
| Low confidence (mostly intuition) | 50% |

Anything below 50% is considered a "moonshot" and should likely be deprioritized or further investigated before scoring.

### Effort
Estimate total team-months across product, design, and engineering. Less than one month rounds to 0.5.

### Final Formula

```
RICE Score = (Reach × Impact × Confidence) / Effort
```

---

## 4. Step-by-step Application

1. **List candidate initiatives** — gather all features, fixes, and ideas competing for the next cycle.
2. **Score each factor** — assign Reach, Impact, Confidence, and Effort numbers individually for every initiative.
3. **Calculate the RICE score** — compute the formula for each.
4. **Rank by score** — sort descending. The top items become your highest-priority candidates.
5. **Sanity check** — review the ranking against strategic dependencies, must-haves, and known constraints. RICE is an input to decision-making, not a verdict.
6. **Iterate** — re-score as new data arrives; scores are not permanent.

---

## 5. Example: Educational Coding App for Kids

A product team for an educational Python coding app for ages 6–12 is evaluating three candidate features for the next quarter.

### Feature A: AI Coding Assistant for real-time hints
- **Reach**: 80,000 users/quarter (based on current MAU projections)
- **Impact**: 3 (massive — directly addresses the core "kids get stuck" pain point)
- **Confidence**: 80% (have data from beta cohort showing engagement lift)
- **Effort**: 4 person-months
- **RICE Score**: `(80,000 × 3 × 0.8) / 4 = 48,000`

### Feature B: Parent Dashboard for progress tracking
- **Reach**: 25,000 parents/quarter
- **Impact**: 1 (medium — nice-to-have, drives retention indirectly)
- **Confidence**: 100% (parents have explicitly requested it)
- **Effort**: 2 person-months
- **RICE Score**: `(25,000 × 1 × 1.0) / 2 = 12,500`

### Feature C: Classroom multiplayer mode
- **Reach**: 15,000 users/quarter
- **Impact**: 2 (high — opens new B2B school market)
- **Confidence**: 50% (no validated demand yet — moonshot)
- **Effort**: 6 person-months
- **RICE Score**: `(15,000 × 2 × 0.5) / 6 = 2,500`

**Ranking**: A (48,000) > B (12,500) > C (2,500). The team should ship the AI assistant first, then the parent dashboard. The classroom mode needs more validation before committing.

---

## 6. Common Pitfalls

- **Treating the score as gospel.** RICE is a structured comparison tool, not a strategic decision-maker. Dependencies, table-stakes features, and contractual commitments often justify working "out of order."
- **Manipulating Confidence to win arguments.** If a team consistently scores 100% confidence on weak evidence, the framework loses its value. Use the 50% threshold honestly.
- **Mixing time windows.** All Reach numbers must use the same time period (e.g., all per quarter), or the comparison is meaningless.
- **Skipping the post-launch review.** Recheck whether predicted Reach and Impact actually materialized—this calibrates future scoring accuracy.
- **Using RICE without product/market fit.** For very early-stage products, RICE's reliance on user-volume data is unreliable. Frameworks like JTBD or Kano may be better fits at that stage.

---

## 7. References

- Intercom — *RICE: Simple prioritization for product managers* (original framework article): https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/
- ProductPlan — *RICE Scoring Model*: https://www.productplan.com/glossary/rice-scoring-model
- Whatfix — *RICE Scoring Model of Prioritization with Examples*: https://whatfix.com/blog/rice-scoring-model/
