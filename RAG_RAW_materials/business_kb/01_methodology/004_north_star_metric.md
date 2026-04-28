# North Star Metric

**Category**: methodology
**Source**: Sean Ellis (GrowthHackers/Medium), Intercom, Mixpanel
**Use Case**: Product Agent uses this concept to define a single quantifiable success metric for the product during PRD writing.

---

## 1. Overview

The North Star Metric (NSM) is a single, headline metric that captures the core value a product delivers to its customers and serves as the primary anchor for sustainable growth. The term was coined and popularized by Sean Ellis, who also coined the term "Growth Hacking." Ellis defined the NSM as "the single metric that best captures the core value that your product delivers to customers and is the key to driving sustainable growth across your full customer base."

The purpose of an NSM is alignment. When every team—engineering, design, marketing, sales, support—optimizes against the same metric, decisions become coherent across the organization. Without an NSM, teams tend to optimize for local metrics that conflict at the global level: marketing chases sign-ups, sales chases bookings, product chases engagement, and the resulting product evolves incoherently.

A well-chosen NSM acts as a leading indicator of long-term business health. It precedes revenue rather than measuring it. If the metric grows, the business should grow as a downstream consequence. The NSM is therefore a strategic instrument: it embodies the team's hypothesis about what creates value, and it forces that hypothesis to be measurable, debatable, and falsifiable.

---

## 2. Key Concepts

- **Core value capture**: the NSM must reflect the moment a customer realizes value, not the moment they sign up or pay.
- **Leading vs. lagging indicators**: an NSM is leading (predicts future business outcomes); revenue is typically lagging.
- **Strategic, not tactical**: the NSM is a long-horizon metric that should remain stable for years, not a quarterly target.
- **One Metric That Matters (OMTM)**: a separate concept—a short-term, tactical focus metric used by a specific team in a specific phase. NSM is strategic and persistent; OMTM is tactical and transient.
- **Input metrics**: the smaller sub-metrics whose product or sum equals the NSM. They are the levers teams actually pull.
- **Product/Market Fit (PMF) prerequisite**: a company should reach PMF before locking in an NSM, because pre-PMF the definition of value is still being discovered.
- **Vanity metrics**: counts that grow easily but do not correlate with sustainable value (App Downloads, Total Registered Users).
- **Two-sided marketplaces**: NSM choice must reflect transactions that involve both sides of the market (the rationale behind Uber's Weekly Trips).

---

## 3. Famous Examples

| Company | North Star Metric | Why it works |
|---|---|---|
| Airbnb | Nights Booked | Captures completed transactions, aligning hosts, guests, and platform; correlates with both revenue and ecosystem health. |
| Facebook | Daily Active Users (DAU) | Daily return implies the product is genuinely valuable; engagement compounds into ad revenue downstream. |
| Uber | Weekly Trips | Each trip requires both a rider and a driver, so the metric forces balance across the two-sided marketplace. |
| WhatsApp | Messages Sent | Sending a message is the core value moment; volume reflects active, sustained usage. |
| YouTube | Watch Time / Hours Watched | Time watched correlates with content quality and ad inventory better than view counts, which can be inflated. |
| Spotify | Time Spent Listening | Listening time reflects depth of engagement and is a strong leading indicator of subscription retention. |
| eBay | Gross Merchandise Volume (GMV) | Captures completed marketplace transactions, summing both sides of every successful exchange. |

A pattern across these examples: the metric describes a unit of value delivered, not a unit of attention captured. Sign-ups, downloads, and impressions are absent. Each metric describes something the customer actually got—a night booked, a message delivered, an hour of music, a trip taken—not something the company merely sent or counted.

---

## 4. Choosing Your North Star Metric

A good NSM satisfies several criteria simultaneously:

- **Reflects core value**: rises only when customers experience the product's primary benefit.
- **Leading, not lagging**: precedes revenue and predicts future business performance.
- **Measurable now**: instrumented in product analytics with reliable, real-time data.
- **Simple**: expressible in a single sentence and a single number.
- **Actionable**: teams can identify input metrics they can directly influence.
- **Stable**: durable across product iterations and market shifts; not redefined quarterly.

**Step-by-step process**

1. **Confirm Product/Market Fit** — verify, through retention curves and qualitative signals, that some segment of customers genuinely values the product. Without PMF, an NSM is premature.
2. **Identify the value moment** — pinpoint the specific in-product event where customers realize core value (e.g., booking a night, sending a message, listening to a song).
3. **Draft candidate metrics** — generate three to five possible NSMs that count occurrences of the value moment.
4. **Test each candidate against the criteria** — eliminate candidates that are lagging, vanity-prone, or one-sided in a multi-sided market.
5. **Decompose into input metrics** — verify that the NSM can be expressed as a function of sub-metrics teams can actually move.
6. **Pressure-test against edge cases** — ask whether the metric could grow while customer value declines (e.g., Watch Time growing because of misleading thumbnails). Refine the definition to close such loopholes.
7. **Commit and instrument** — publish the NSM, instrument the input metrics, and align planning cycles around it. Resist the temptation to redefine it every quarter.

---

## 5. Example: Educational Coding App for Kids

Consider a Python-based educational app for children aged 6–12. The product's core value is helping children build real coding skills through enjoyable practice. The NSM should capture that value moment.

**Candidate NSM**: **Weekly Active Learners completing at least one coding lesson** (abbreviated WAL-Lessons).

**Why it works**
- **Reflects core value**: a child only counts if they actually completed a lesson, not merely opened the app.
- **Leading indicator**: sustained weekly lesson completion predicts skill growth, parental satisfaction, and renewal.
- **Excludes vanity**: app downloads, account creations, and brief opens are excluded by construction.
- **Aligns both stakeholders**: parents care that learning happens; children must enjoy it enough to return; both jobs are served by the same number.
- **Avoids the wrong incentives**: counting "lessons completed" instead of "minutes in app" discourages the team from padding session length with low-value content.

**Input metrics that drive WAL-Lessons**

| Input metric | Lever |
|---|---|
| Weekly Active Learners (WAL) | Onboarding quality, push notifications, parental email reminders, content freshness. |
| Lessons started per active learner | Curriculum pacing, recommended next-lesson UX, gamified streaks. |
| Lesson completion rate | Difficulty curve, hint system, lesson length, age-appropriate scaffolding. |

The relationship is approximately: WAL-Lessons ≈ WAL × Lessons Started per WAL × Completion Rate. Each input is owned by an identifiable team (growth, content, learning design), making the NSM actionable rather than abstract.

---

## 6. Common Pitfalls

- **Choosing a vanity metric** — App Downloads, Total Registered Users, Page Views, and Followers grow easily and rarely correlate with sustainable value. Avoid them.
- **Choosing revenue as NSM** — revenue is lagging; it tells you what already happened, not what will happen. It is a result of a healthy NSM, not a substitute for one.
- **Choosing the NSM before PMF** — pre-PMF, the definition of value is still being discovered. Locking in an NSM too early commits the team to optimizing the wrong thing.
- **Confusing NSM with OMTM** — OMTM is a short-term tactical focus for a specific team and phase; NSM is the long-term strategic anchor for the whole company. Treating them as interchangeable produces either short-termism or paralysis.
- **Over-engineering the metric** — composite formulas with many weighted components are hard to explain, hard to instrument, and hard to act on. A good NSM fits in a sentence.
- **Changing it every quarter** — the NSM is meant to be stable. Frequent redefinition signals either premature commitment or a lack of strategic clarity, and it destroys longitudinal comparisons.
- **Ignoring multi-sided dynamics** — in marketplaces, a one-sided metric (e.g., counting only buyers) hides imbalance. Choose a metric that requires both sides to be healthy.
- **Letting the metric drift from value** — periodically audit whether the NSM still reflects genuine customer value, and tighten the definition if loopholes appear.

---

## 7. References

- Sean Ellis — Finding Your North Star Metric: https://medium.com/growthhackers/finding-your-north-star-metric-fc1c1f71cbcb
- Intercom — Sean Ellis on growth: https://www.intercom.com/blog/podcasts/sean-ellis-growth/
- Mixpanel — North Star Metric: https://mixpanel.com/blog/north-star-metric/