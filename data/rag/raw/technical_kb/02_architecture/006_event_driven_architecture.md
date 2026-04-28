# Event-Driven Architecture

**Category**: architecture
**Source**: Martin Fowler, AWS
**Use Case**: Architect Agent uses this when system needs loose coupling, high throughput, or audit trails.

---

## 1. Overview

**Event-Driven Architecture (EDA)** is a software design style in which components communicate by emitting and reacting to **events**—immutable records that something has happened—rather than by calling each other directly through synchronous APIs. Instead of Service A calling Service B and waiting for a response, Service A publishes an event ("OrderPlaced") to an event bus, and any number of services that care about that event subscribe and react in their own time. The event itself becomes the unit of communication and the integration boundary between components.

The pattern's appeal lies in **decoupling**. Producers and consumers do not need to know about each other; they only need to agree on event schemas. New consumers can be added without modifying producers. Failures in one consumer do not cascade to others. Replay and audit become natural because the event log is itself the system's history. The trade-off is operational and conceptual complexity: distributed event flows are harder to reason about than synchronous calls, schema evolution becomes a recurring discipline, and **eventual consistency**—the property that the system's various views converge but are not identical at any given instant—becomes the default rather than the exception.

This document covers the core concepts of EDA, the major patterns that fit within it (Event Notification, Event-Carried State Transfer, Event Sourcing, CQRS), the tooling landscape, when EDA earns its complexity, and the common pitfalls. It applies the analysis to a concrete example—an educational coding app for children—where EDA is likely overkill at the MVP stage but may become justified later as the analytics and integration surface grows.

---

## 2. Core Concepts

Four primitives recur across all event-driven systems.

**Event.** An immutable record that something has happened. Events are named in the past tense ("OrderPlaced," "UserSignedUp," "LessonCompleted") because they describe facts about the past, not commands to be executed. An event typically includes an event type, a timestamp, an identifier for the entity it concerns, and a payload describing what happened. Events are append-only by nature; once emitted, they are not modified.

**Producer.** A component that emits events. Producers are concerned with their own domain and do not know which consumers (if any) will react. A user-account service might emit `UserSignedUp` events; an order service might emit `OrderPlaced` events. The producer's responsibility ends once the event is published.

**Consumer.** A component that subscribes to events and reacts to them. A consumer might update a denormalized view, send an email, trigger a downstream workflow, or emit further events of its own. Multiple consumers can subscribe to the same event, each reacting independently.

**Event bus / broker.** The middleware that routes events from producers to consumers. The broker decouples the two—producers publish without knowing which consumers will receive, and consumers subscribe without knowing which producers will emit. Different brokers offer different guarantees: durable storage with replay (Kafka), reliable queueing with acknowledgment (RabbitMQ, SQS), fan-out pub/sub (SNS), or lightweight in-memory streams (Redis Streams).

A useful distinction: **events are not commands**. A command ("PlaceOrder") expresses an intention and expects to be acted upon by a specific receiver. An event ("OrderPlaced") expresses a fact and is broadcast for any interested party to consume. Conflating the two—using events as a thin disguise for direct RPC—loses the decoupling that makes EDA valuable.

---

## 3. Patterns Within EDA

Martin Fowler's 2017 article on event-driven architecture distinguishes several patterns that travel under the same umbrella. They differ in how much state they carry and how much architectural change they impose.

**Event Notification.** The simplest pattern: a service emits an event saying "something happened, you might care," with minimal payload. Consumers that care receive the notification and call back to the producer or other systems for additional data. Event Notification provides loose coupling and clear integration semantics, but it does not eliminate synchronous coupling—consumers still need to call the producer to fetch details. *Example: a `UserSignedUp` event containing only the user ID; consumers that need profile details query the user service.*

**Event-Carried State Transfer.** The event payload carries all the data a consumer needs, eliminating the need to call back to the producer. This further reduces coupling and avoids the load and availability dependencies that Event Notification creates, at the cost of larger events and the need to keep payloads in sync as the producer's data model evolves. *Example: a `UserSignedUp` event containing the user's ID, email, name, and signup metadata, so that the email service can send a welcome email without calling the user service.*

**Event Sourcing.** A more profound architectural shift: instead of storing the current state of an entity in a database, the system stores the full sequence of events that produced that state, and current state is derived by replaying the event log. The pattern provides a complete audit trail by construction, supports time-travel queries (the state of the system as of any past moment), and enables rebuilding new views without re-running production traffic. The cost is significant: every read becomes a replay (often optimized with snapshots), schema evolution must handle historical events forever, and the mental model is unfamiliar to most developers. *Example: a banking ledger where the account balance is computed by replaying every deposit and withdrawal event.*

**CQRS (Command Query Responsibility Segregation).** A pattern often paired with Event Sourcing but usable independently. CQRS separates the **write model** (commands that change state) from the **read model** (queries that retrieve state). The write side processes commands and emits events; the read side subscribes to events and maintains denormalized views optimized for queries. The two sides can use different storage technologies, scale independently, and evolve their data shapes independently. *Example: an e-commerce system where the write side handles `PlaceOrder` commands against a normalized PostgreSQL store while the read side maintains a denormalized order-history view in a search index.*

The four patterns are progressively more invasive. Event Notification is the lightest; Event Sourcing combined with CQRS is the heaviest and represents a wholesale architectural commitment. Most teams should default to the lighter patterns and adopt the heavier ones only when the benefits clearly justify the cost.

---

## 4. Tools and Technologies

| Tool | Strengths | When to use | Trade-offs |
|---|---|---|---|
| **Apache Kafka** | High-throughput, durable, replayable event log. Strong ordering within partitions, retention measurable in days or longer, ecosystem (Kafka Connect, Kafka Streams) for stream processing. | High-volume event streaming, audit logs, event sourcing, multi-consumer fan-out where replay matters. | Operationally complex to self-host; managed offerings (Confluent Cloud, AWS MSK) reduce burden but add cost. |
| **RabbitMQ** | Mature message broker with rich routing (topic, fanout, direct exchanges). Reliable queueing with acknowledgments, dead-letter queues, and standard AMQP protocol. | Traditional task queues, work distribution, request-response patterns over messaging, when retention beyond delivery is not needed. | Not designed as a long-term event log; messages are typically deleted after acknowledgment. |
| **AWS SNS + SQS** | Fully managed; SNS for fan-out pub/sub, SQS for durable queueing. Simple to operate, integrates deeply with other AWS services. | Cloud-native applications already on AWS, moderate event volumes, teams that want minimal operational overhead. | AWS-specific; less portable than Kafka or RabbitMQ. Long-term retention requires additional services (e.g., S3 for archival). |
| **Redis Streams** | Lightweight, in-memory event log with consumer groups. Fast, simple, low operational overhead. | Small-scale event flows, real-time use cases where latency matters more than durability, teams already running Redis. | Limited durability guarantees compared to Kafka; not suited for high-volume long-retention event sourcing. |

The choice often follows existing infrastructure. A team already on AWS will reach for SNS/SQS; a team running Kubernetes with mixed cloud presence will more often choose Kafka; a team that needs traditional task queueing without long-term retention will pick RabbitMQ. There is no universally correct answer; the question is which tool's profile matches the team's workload and operational appetite.

---

## 5. When to Use EDA

Event-Driven Architecture earns its complexity in specific situations. Adopting it without one of these justifications typically introduces operational cost without proportional benefit.

**EDA is justified when:**
- **Multiple downstream systems need to react to the same event.** A `UserSignedUp` event might trigger a welcome email, a CRM record creation, an analytics event, and a free-trial start. With direct calls, the user-account service must know about every consumer; with EDA, it emits one event and the consumers self-register.
- **Loose coupling between teams is required.** Different teams own different services and want to evolve their data models, deployment cadences, and technology choices independently. Events provide a stable contract while the implementations behind them change.
- **Audit logs or replay capability are needed.** Financial systems, compliance-sensitive workflows, and any application where "what happened, when, in what order" is itself valuable benefit from durable event logs.
- **High throughput with backpressure handling.** When traffic spikes exceed downstream capacity, events queue naturally and consumers process at their own pace. Synchronous calls would either overload the consumer or fail under load.
- **Real-time integrations and stream processing.** Analytics pipelines, fraud detection, recommendation engines, and operational telemetry are natural fits for event streams.

**EDA is not justified when:**
- **The application is a simple CRUD system.** A service with a handful of endpoints serving a single client does not benefit from the indirection.
- **Strong consistency is required across the affected data.** Events introduce eventual consistency by default; applications where two values must always be in lockstep (e.g., account balances and transaction records that must agree atomically) are better served by relational transactions.
- **The team is small and the operational burden is meaningful.** Running an event broker, managing schemas, monitoring lag, debugging distributed flows—all add to the operational load. Small teams should evaluate whether the benefits outweigh this load.
- **The domain is poorly understood.** Locking in event schemas requires confidence in what the right events are. Premature event design often produces events that need to be redesigned later, which is operationally expensive once consumers depend on them.

---

## 6. Example: Educational Coding App for Kids

Consider the architecture for **CodeCub**, an educational Python coding app for children aged 6–12 at the MVP-to-early-growth stage. The system handles user accounts, lesson delivery, code execution, AI tutoring, parent dashboards, and learning analytics. The team is small (3–5 engineers).

**Verdict: EDA is overkill for the MVP. Defer until v2 for specific use cases.**

The reasoning:

- **The team is small and the operational appetite is limited.** Running Kafka or even SNS/SQS reliably requires monitoring, schema management, and debugging tooling that consume engineering time better spent on product. The modular monolith pattern, with in-process method calls between modules, is simpler and sufficient at this scale.
- **Service-to-service decoupling is not yet needed.** All modules deploy together. There are no independent teams whose deployment cadences need to be decoupled.
- **The dominant access patterns are CRUD-shaped.** A child completes a lesson, a parent views progress, a subscription renews. These are well-served by synchronous calls and relational transactions in a single PostgreSQL database.
- **Eventual consistency would be a hindrance, not a help.** If a child completes a lesson and the parent immediately checks the dashboard, both expect the lesson to show as completed. Synchronous transactional updates produce that expectation by default; an event-driven update would introduce a window where the data is inconsistent.

**Where EDA becomes attractive in a v2 architecture:**

- **Analytics event pipeline.** As the user base grows, fine-grained learning telemetry (every lesson interaction, every hint shown, every code edit) produces high-volume write traffic that should not share the transactional database. Emitting these as events to a stream (Kafka, Kinesis, or even a managed analytics ingestion service) and consuming them into a warehouse for analysis is a clean separation. This use case alone often justifies introducing an event bus.
- **Multiple downstream reactions to user signups.** As marketing automation, CRM integration, school-channel onboarding, and parent-facing welcome flows accumulate, an event-driven `UserSignedUp` flow is cleaner than a chain of synchronous calls inside the user-account module.
- **AI tutoring observability.** Logging every AI hint request, response, and learner reaction as events supports later evaluation, fine-tuning, and quality auditing without coupling the inference path to those concerns.
- **School-channel integrations.** When the product integrates with school information systems (Clever, ClassLink, district SIS), events provide a stable contract that survives the partner-by-partner variation in those integrations.

**Recommended path:**

Start with a modular monolith and synchronous communication. Introduce an event bus when a specific use case (most likely the analytics pipeline) justifies it. Use Event Notification or Event-Carried State Transfer for early flows; defer Event Sourcing and CQRS unless audit-trail requirements specifically demand them. Keep the event schemas under deliberate change control from the moment they exist, because schema evolution becomes the most operationally painful part of EDA over time.

---

## 7. Common Pitfalls

- **Schema evolution that breaks consumers.** Events are stable contracts; changing them carelessly breaks downstream consumers in production. Adopt a schema registry, prefer additive changes, and version events explicitly. Plan for the fact that old events live in the log forever and new code must still be able to handle them.
- **Eventual consistency confusion.** Engineers and product managers accustomed to synchronous flows are routinely surprised when "the data isn't updated yet" two seconds after an event was emitted. Document where consistency is eventual, design UI affordances for it, and avoid mixing eventual-consistency patterns with strong-consistency expectations in the same workflow.
- **Hidden coupling through shared event schemas.** When many consumers depend on the exact shape of an event, the producer cannot evolve its data model without coordinating with all of them. The decoupling that EDA was supposed to provide quietly disappears. Limit schema breadth, treat schemas as published APIs, and version them deliberately.
- **Distributed monolith via events.** Services that emit events but functionally cannot operate without each other (e.g., service A always waits for service B's response event before continuing) are not benefiting from EDA—they are paying its operational cost while keeping the synchronous coupling. Either accept synchronous calls or genuinely decouple.
- **Premature event sourcing.** Event Sourcing is a profound architectural commitment with significant ongoing cost. Adopting it because "events are good" without a concrete reason (audit trail, time-travel queries, replay-driven view rebuilding) typically produces complexity without payoff.
- **Lost or duplicated events.** Most brokers offer at-least-once delivery; consumers must be **idempotent** (processing the same event twice produces the same result as processing it once). Forgetting idempotency produces subtle bugs that surface only under load.
- **Underestimating the observability burden.** Distributed event flows are harder to debug than synchronous calls. Investment in distributed tracing, event-flow visualization, and dead-letter handling is necessary, not optional, once production traffic begins.
- **No clear ownership of event schemas.** When events cross team boundaries without a clear owner, schemas drift and contracts erode. Assign explicit ownership for every event type, and treat schema changes with the same rigor as public API changes.

---

## 8. References

- Martin Fowler — What do you mean by "Event-Driven"?: https://martinfowler.com/articles/201701-event-driven.html
- AWS — Event-Driven Architecture: https://aws.amazon.com/event-driven-architecture/