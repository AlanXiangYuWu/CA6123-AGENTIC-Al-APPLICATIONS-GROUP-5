# KANO Model

**Category**: methodology
**Source**: Wikipedia, ProductPlan, Product School
**Use Case**: Product Agent uses this framework to classify features by their effect on customer satisfaction during PRD writing.

---

## 1. Overview

The KANO Model is a product management and quality framework that classifies product features by their effect on customer satisfaction. It was developed in 1984 by Dr. Noriaki Kano, a professor of quality management at the Tokyo University of Science. The model challenges the intuitive assumption that customer satisfaction grows linearly with feature investment. Instead, KANO argues that satisfaction is emotional and non-linear: some features are taken for granted, others scale proportionally with effort, and a few generate disproportionate delight.

The framework sorts features into five categories—Must-be, Performance, Attractive, Indifferent, and Reverse—based on how their presence or absence affects user emotion. By mapping features to these categories, product teams can prioritize roadmaps more deliberately, ensuring foundational expectations are met before investing in differentiation.

KANO is commonly applied to MVP scoping, PRD writing, and competitive analysis. It is also dynamic: customer expectations evolve over time, and features once considered Delighters tend to migrate toward Performance and eventually Must-be status. This temporal dimension makes the model particularly useful for long-term strategic planning and roadmap evolution.

---

## 2. Key Concepts

- **Customer satisfaction is emotional, not linear** — investing more in a feature does not always produce proportionally more satisfaction.
- **Functional vs. dysfunctional perception** — every feature is evaluated by how users feel both when it is present and when it is absent.
- **Five reaction categories** — Must-be, Performance, Attractive, Indifferent, Reverse.
- **Paired KANO questionnaire** — a survey technique using one positive (functional) and one negative (dysfunctional) question per feature.
- **Category decay over time** — features migrate downward in the hierarchy as customer expectations rise.
- **Threshold of acceptability** — Must-be features set the minimum bar for a product to be considered usable.
- **Parity vs. differentiation** — Performance features establish competitive parity; Attractive features create competitive differentiation.

---

## 3. Framework Details

The KANO Model classifies features into five categories based on the relationship between feature implementation and customer satisfaction.

- **Must-be (Basic)**: Taken-for-granted requirements. Their presence does not increase satisfaction, but their absence causes strong dissatisfaction. Customers rarely articulate them because they are assumed. Example: a smartphone that can place calls.
- **Performance (One-dimensional)**: Satisfaction scales linearly with the level of implementation—more is better, less is worse. Customers explicitly ask for these features and compare competitors on them. Example: battery life measured in hours.
- **Attractive (Delighter / Excitement)**: Unexpected features that produce strong positive emotion when present but cause no dissatisfaction when absent. Customers cannot ask for what they have not imagined. These create wow moments and competitive differentiation.
- **Indifferent**: Features that users do not care about. Investing in them yields no measurable satisfaction gain and consumes engineering effort without payoff.
- **Reverse**: Features that at least some users actively dislike. Their presence reduces satisfaction for part of the audience. Example: aggressive onboarding flows or auto-installed bundled software.

| Category | Presence | Absence | Strategic role |
|---|---|---|---|
| Must-be | Neutral | Strong dissatisfaction | Cost of entry |
| Performance | Linear satisfaction | Linear dissatisfaction | Competitive parity |
| Attractive | High delight | Neutral | Differentiation |
| Indifferent | Neutral | Neutral | Avoid investment |
| Reverse | Dissatisfaction | Satisfaction | Remove or make optional |

A central insight is that effort and satisfaction are not symmetrically related across categories. Investing beyond the threshold of a Must-be feature yields no satisfaction gain, while investing in a Performance feature yields a roughly proportional gain. Attractive features can produce outsized returns relative to effort, but they are inherently harder to predict.

A second important insight is temporal evolution. Features tend to drift downward through the hierarchy as customer expectations rise. Long mobile battery life was once an Attractive feature; it became Performance as competitors caught up; it now approaches Must-be status, where users feel actively dissatisfied if a phone cannot last a full day. Smartphone cameras have followed the same trajectory. This decay means that today's Delighter is tomorrow's baseline, and product teams must continuously seek new Attractive features to maintain emotional differentiation.

---

## 4. Step-by-step Application

1. **Enumerate candidate features** — gather proposed features from the roadmap, PRD draft, or backlog.
2. **Design the paired questionnaire** — for each feature, write a functional question ("How would you feel if the product had X?") and a dysfunctional question ("How would you feel if the product did not have X?"). Use a standard five-point scale: I like it, I expect it, I am neutral, I can tolerate it, I dislike it.
3. **Survey representative users** — administer the paired questions to a sample drawn from the target audience. The sample should cover the primary personas, not internal stakeholders.
4. **Map responses to categories** — cross-tabulate each respondent's functional and dysfunctional answers using the standard KANO evaluation table to assign each feature a category per respondent.
5. **Aggregate per feature** — for each feature, compute the dominant category across respondents. Many teams also calculate satisfaction (CS) and dissatisfaction (DS) coefficients to quantify impact magnitude.
6. **Prioritize the roadmap** — first, ensure all Must-be features are covered to clear the threshold of acceptability. Then invest in Performance features to remain competitive. Allocate a deliberate portion of effort to one or two Attractive features for differentiation. Defer Indifferent features. Remove, or make optional, any Reverse features.
7. **Re-evaluate periodically** — repeat the exercise on a cadence (for example, annually) because category assignments drift as expectations evolve.

---

## 5. Example: Educational Coding App for Kids

Consider a Python-based educational app aimed at children aged 6–12. Six candidate features mapped to KANO categories:

| Feature | Category | Rationale |
|---|---|---|
| Reliable code execution without crashes | Must-be | Parents and teachers assume the app runs. Crashes destroy trust immediately. |
| Age-appropriate, safe content (no external links, no ads to minors) | Must-be | Non-negotiable for parents; absence triggers immediate uninstall. |
| Progressively unlocking lesson levels with a clear difficulty curve | Performance | More polished progression yields more engagement; weak progression yields less. |
| Animated character mascot that celebrates milestones with custom animations | Attractive | Unexpected and emotionally engaging for children; absence is not missed. |
| Theme customization for the code editor (fonts, color schemes) | Indifferent | Most children aged 6–12 do not care; engineering investment is wasted. |
| Mandatory daily streak notifications pressuring children to log in | Reverse | Many parents actively dislike gamified pressure on young children; presence reduces parental satisfaction. |

The prioritization implication is clear. The MVP must guarantee stability and child-safe content (Must-bes). It should ship a solid lesson progression (Performance) to be competitive with established platforms. One Attractive feature—the mascot animations—can provide differentiation at modest cost. Theme customization should be deferred. Mandatory streak notifications should be removed or restricted to a strictly opt-in setting with parental controls.

---

## 6. Common Pitfalls

- **Confusing Must-be with Performance** — assuming that improving a Must-be feature beyond its threshold will increase satisfaction. It will not.
- **Over-investing in Delighters before Must-bes are met** — a delightful feature cannot compensate for a missing fundamental. A beautiful onboarding flow does not rescue an app that crashes.
- **Treating the model as static** — failing to re-run the exercise as expectations evolve leads to outdated category assignments and stale roadmaps.
- **Skipping the dysfunctional question** — using only the positive question loses the asymmetry that defines the model. Both questions are required.
- **Surveying the wrong audience** — administering KANO to internal stakeholders or power users instead of the actual target segment skews category assignments.
- **Ignoring Indifferent features** — continuing to invest in features users do not care about, simply because they were already on the roadmap.
- **Misclassifying Reverse features as Attractive** — assuming a flashy or aggressive feature is exciting when it actually annoys a segment of the user base.
- **Aggregating across heterogeneous segments** — a feature can be Attractive for one persona and Reverse for another. Segment before averaging.
- **Confusing absence of complaint with satisfaction** — Must-be features generate silence when present, not praise. Lack of negative feedback is not evidence of delight.

---

## 7. References

- Wikipedia — Kano model: https://en.wikipedia.org/wiki/Kano_model
- ProductPlan — Kano Model glossary: https://www.productplan.com/glossary/kano-model
- Product School — Kano Model article: https://productschool.com/blog/product-fundamentals/kano-model