# Architecture: Monolith vs Microservices

**Category**: architecture
**Source**: Martin Fowler, AWS
**Use Case**: Architect Agent uses this to choose system decomposition strategy.

---

## 1. Overview

The choice between a **monolithic** and a **microservices** architecture is one of the most consequential decisions in software system design. The monolith is the older, simpler pattern: the entire application lives in a single codebase, runs as a single process, and deploys as a single unit. Microservices is the newer pattern that emerged in the early 2010s: the system is decomposed into many small, independently deployable services, each owning its data and communicating with others through well-defined APIs.

The decision between them shapes development speed, operational complexity, hiring profile, and the cost of change for years. The conventional wisdom of the mid-2010s—that microservices were the modern, scalable, "correct" architecture—has been substantially revised through hard experience. Many companies that adopted microservices early discovered that the operational cost outweighed the benefits at their scale, and several high-profile teams (Segment is the most cited example) consolidated microservices back into monoliths in the late 2010s. The current consensus, articulated most clearly by Martin Fowler, is that **most teams should start with a monolith** and decompose into services only when concrete pressures demand it.

This document defines the two patterns, traces their history, examines the trade-offs across development, operations, scaling, and team structure, presents Fowler's "MonolithFirst" principle, identifies when microservices are genuinely justified, introduces the **modular monolith** as a middle-ground pattern, and applies the analysis to a concrete example—an educational coding app for children at an early-startup stage.

---

## 2. Definitions and History

**Monolith.** A monolithic application is delivered as a single deployable unit. All features live in one codebase, run in one process (or a horizontally replicated cluster of identical processes), share one database (or a small number of related databases), and are released together. The components inside the monolith may be modular, but the deployment boundary is singular. Most successful software in history—including the early versions of nearly every major internet company—was built as a monolith.

**Microservices.** A microservices architecture decomposes the system into many small, independently deployable services. Each service owns a specific business capability, is developed and operated independently, owns its own data store, and communicates with other services through APIs—most commonly REST over HTTP or asynchronous messaging through a queue or event bus. The defining property is **independent deployability**: each service can be released without coordinating a release of any other service.

The term "microservices" was popularized in 2014 by **Martin Fowler and James Lewis** in a widely cited article on Fowler's website. The article codified patterns that had been emerging at companies like Netflix, Amazon, and others through the early 2010s, and it gave the resulting architectural style a name and a vocabulary. The pattern spread rapidly through the industry over the following years, becoming a near-default for new systems at large companies and aspirationally for many smaller ones. By the late 2010s, the limitations of the pattern—particularly its operational cost when adopted prematurely—were becoming widely recognized, and the conversation shifted from "should we adopt microservices?" to "when does microservices make sense?"

---

## 3. Trade-offs

| Dimension | Monolith | Microservices |
|---|---|---|
| **Development speed (early)** | Fast. Single codebase, single deployment, single set of patterns. New developers ramp quickly. | Slow. Many services to set up, deploy, and coordinate. Operational scaffolding must be built before features. |
| **Local development** | Simple. Run the application locally with one command. | Complex. Running the full system locally requires Docker Compose, service mesh emulation, or extensive mocking. |
| **Testing** | Straightforward. Integration tests run against the running monolith. | Harder. Cross-service integration testing requires running multiple services or sophisticated test doubles. |
| **Deployment** | Single artifact, single pipeline. Releases are coordinated by definition. | Independent deployment per service. Each service has its own pipeline, release cadence, and versioning. |
| **Scaling** | Vertical scaling and horizontal replication of the entire application. Can be inefficient if only one part of the app is hot. | Independent scaling per service. Hot services can scale independently of cold ones. |
| **Fault isolation** | A bug in one feature can crash the entire application. | A failure in one service can be contained, with graceful degradation in others. |
| **Technology choices** | One stack for everything. Polyglot is hard. | Each service can use the language and database that fits it best. |
| **Team structure** | Suits small teams or small numbers of teams sharing a codebase. | Suits many teams, each owning one or a few services and deploying independently. |
| **Operational complexity** | Low. One thing to monitor, log, alert on, secure. | High. Service discovery, distributed tracing, retries, circuit breakers, network reliability, eventual consistency, and cross-service authorization all become first-order concerns. |
| **Data consistency** | Strong consistency is the default; one database, one transaction boundary. | Eventual consistency by default; cross-service transactions require sagas, event sourcing, or other patterns. |
| **Cost of changes spanning multiple capabilities** | Low. One commit, one deployment. | High. May require coordinated changes across multiple services and their teams. |

The pattern in the table is consistent: **the monolith is simpler at every dimension where development speed and operational simplicity matter, and the microservices architecture is more flexible at every dimension where independent scaling, independent deployment, and team autonomy matter.** Neither is universally superior; the right choice depends on which dimensions matter most for the team and the system at hand.

---

## 4. Martin Fowler's MonolithFirst Principle

In a 2015 article titled "MonolithFirst," Martin Fowler argued that **almost all successful microservice architectures were built by extracting services from a monolith, and almost all microservice architectures built from scratch ran into serious trouble**. The principle has shaped industry thinking on the topic ever since.

The reasoning: microservices require well-understood service boundaries to work well. Service boundaries that are wrong—too granular, too coarse, or sliced along the wrong dimensions—produce operational pain that the architecture is designed specifically to avoid. Getting the boundaries right requires knowing the domain deeply, and that knowledge is gained by building the system. A monolith built first allows the team to discover where the natural boundaries actually are. Once those boundaries are clear, the team can extract services along them with reasonable confidence that the resulting decomposition will be stable.

A related principle: **operational complexity is real and is paid up front in microservices architectures, but only at scale in monoliths.** A small team running a monolith pays minimal operational cost for its first several years; a small team running microservices pays substantial operational cost on day one. For startups operating under capital and time constraints, this front-loaded cost is often the difference between shipping and not shipping.

The MonolithFirst principle does not say that microservices are always wrong. It says that **the path to a good microservice architecture usually runs through a monolith**, and that teams that try to skip the monolith stage typically fail. The implication for new projects is clear: start with a monolith, design it modularly so that future extraction is feasible, and decompose only when concrete pressures justify it.

---

## 5. When to Choose Microservices

Microservices are genuinely the right choice in several specific situations, even allowing for the MonolithFirst principle.

- **Different parts of the system have genuinely different scaling profiles.** A read-heavy product catalog, a write-heavy order service, and a CPU-intensive image-processing service have different scaling needs. Decomposing them allows each to scale independently and to use storage and compute appropriate to its workload.
- **Multiple teams need to deploy independently.** When the engineering organization grows past roughly 30–50 engineers in many cases, monolithic deployment becomes a coordination bottleneck. Independent service deployment lets teams ship without coordinating with every other team.
- **Different parts of the system need different technology stacks.** A common case: an ML inference service in Python alongside a high-throughput payments service in Java or Go alongside a customer-facing web app in TypeScript. Forcing all of these into a single monolith means choosing one language and accepting compromises on the others.
- **Fault isolation is a hard requirement.** Some systems (financial transactions, safety-critical systems) require that the failure of one capability not affect others. Microservices provide stronger fault isolation than a single-process monolith, though they introduce their own failure modes (network partitions, cascading retries) that must be managed.
- **The system is genuinely large enough that a monolith would be unmanageable.** This case is real but rarer than commonly believed. Most startups operate at scales where a well-designed monolith is comfortably manageable.

The signs that microservices are **not** justified yet are equally important:

- The team has fewer than ten engineers. Operational overhead of microservices typically exceeds the productivity benefit at this scale.
- The product is pre-PMF or in early growth. The codebase is changing rapidly; service boundaries set now will likely be wrong.
- The application is a single coherent product without clear independent scaling profiles.
- Multiple services share a single database—a sign that the decomposition has not actually achieved independence (the **distributed monolith** anti-pattern).

---

## 6. Modular Monolith — The Middle Ground

The **modular monolith** is a middle-ground pattern that captures most of the monolith's operational simplicity while preserving the option to extract services later. The application deploys as a single unit, but inside that unit the code is organized into strict modules with explicit interfaces between them. Modules cannot reach into each other's internal data structures; they communicate only through published interfaces. The database is logically partitioned by module, even though it physically sits in one Postgres instance.

The benefits accumulate:

- **Operationally simple.** One process, one deployment, one set of monitoring and alerting.
- **Boundaries are explicit.** The code looks like a microservice architecture from the inside, even though it deploys monolithically.
- **Future extraction is feasible.** When a module's scaling profile, deployment cadence, or technology needs justify a split, extracting it into a standalone service is a refactor rather than a rewrite, because the boundary already exists.
- **Boundaries can be wrong without disaster.** If a module boundary turns out to be in the wrong place, fixing it is a code change inside the monolith—much cheaper than reorganizing services in production.

The modular monolith is the pattern most aligned with Fowler's MonolithFirst principle. It is the form a monolith takes when the team takes seriously the possibility of future decomposition. For most early-stage and mid-stage products, the modular monolith is the right default: simpler than microservices, more disciplined than an unstructured monolith, and well-positioned to evolve as the system grows.

---

## 7. Example: Educational Coding App for Kids

Consider the architecture for **CodeCub**, a Python-based educational coding app for children aged 6–12. The team is small (3–5 engineers), the product is at the MVP-to-early-growth stage, and the system includes user accounts, lesson delivery, a code-execution sandbox, AI-tutoring integration, parent dashboards, and analytics events.

**Recommendation: modular monolith.**

The factors driving the choice:

- **Team size is small.** Operational overhead of microservices would consume an outsized share of a five-engineer team's capacity. Time spent on service mesh configuration, distributed tracing setup, and cross-service contract management is time not spent on product.
- **Boundaries are not yet clear.** The team has hypotheses about how the system should decompose (lesson delivery vs. AI tutoring vs. parent-facing services), but those hypotheses have not been validated by traffic patterns, scaling pressures, or team-structure changes. Locking in service boundaries now would risk getting them wrong.
- **Most parts of the system have similar scaling profiles.** Lesson delivery, parent dashboards, and account management are all standard CRUD-shaped workloads that scale together. Independent scaling is not required.
- **The exception is the AI tutoring layer.** AI inference has a distinct scaling profile—calls are slow, expensive per call, and bursty. Even within the monolith, this work should be isolated behind a clean interface and run on a separate process pool or background queue. If it eventually requires extraction into a standalone service (for cost reasons, scaling reasons, or to share with other products), the clean interface makes extraction a contained change.
- **The code-execution sandbox is a candidate for early extraction.** Running untrusted user-submitted code (even from children) requires strict isolation, typically through containerization or microVMs. The sandbox is naturally a separate component for security reasons and may be the first piece to live outside the main monolith—not because of microservices philosophy, but because of practical isolation requirements.

**Recommended module boundaries inside the monolith:**

| Module | Responsibility |
|---|---|
| `accounts` | Parent and child user accounts, authentication, parental consent flows. |
| `subscriptions` | Billing, plan management, subscription lifecycle. |
| `curriculum` | Lesson library, age-band logic, lesson sequencing. |
| `progress` | Learner progress, attempts, completion tracking. |
| `ai_tutor` | AI hint generation, conversational debugging—isolated behind a clean interface for likely future extraction. |
| `dashboards` | Parent and teacher views, weekly progress emails. |
| `events` | Analytics event capture for downstream analysis. |

Each module owns its data (logically partitioned within a single PostgreSQL database), exposes a clear interface to other modules, and is structured so that future extraction is a refactor rather than a rewrite.

**When to extract services:**

- **Code-execution sandbox**: extract early, for security isolation, regardless of scale.
- **AI tutoring**: extract when AI inference cost or scaling becomes a meaningful operational concern, or when a separate inference team forms.
- **Analytics events**: extract when event volume justifies a write-optimized pipeline (the `events` module's data flows to a dedicated warehouse).
- **Other modules**: extract only when concrete pressures emerge—different scaling profile, different team ownership, or different technology need.

The discipline is to extract reluctantly and only on evidence, not enthusiastically and on speculation.

---

## 8. References

- Martin Fowler — Microservices: https://martinfowler.com/microservices/
- Martin Fowler — MonolithFirst: https://martinfowler.com/bliki/MonolithFirst.html
- AWS — What is Microservices: https://aws.amazon.com/microservices/