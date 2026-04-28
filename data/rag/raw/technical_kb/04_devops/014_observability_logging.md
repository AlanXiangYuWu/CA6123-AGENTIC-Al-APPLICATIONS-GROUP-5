# Observability: Logs, Metrics, Traces

**Category**: devops
**Source**: OpenTelemetry, Datadog, Google SRE Book
**Use Case**: Architect Agent uses this when designing observability for technical spec.

---

## 1. Overview

**Observability** is the ability to understand a system's internal state from its external outputs. The term comes from control theory and was adapted to software systems as the older paradigm of **monitoring**—a fixed set of dashboards and alerts on known failure modes—proved inadequate for distributed systems whose failure modes are too varied to predict in advance. A monitored system tells you whether the things you thought to check are working; an observable system lets you ask new questions about the system's behavior after the fact, including questions you did not anticipate.

Observability rests on **three pillars**: logs, metrics, and traces. Each captures a different aspect of system behavior, and together they form the foundation of operational understanding. Logs provide rich detail about discrete events; metrics provide numeric measurements that can be aggregated, alerted on, and graphed over time; traces follow individual requests as they flow across services in a distributed system. The three are complementary, not interchangeable. A team that has only one of them will routinely encounter problems that only one of the others can answer.

This document covers the three pillars in depth, the role of OpenTelemetry as the emerging standard for instrumentation, the major tools in each category, the best practices that distinguish useful observability from noisy observability, the specialized observability needs of AI-agent applications, and a concrete observability plan for an educational coding app. It closes with the pitfalls that produce expensive, unhelpful observability stacks.

---

## 2. Three Pillars: Logs, Metrics, Traces

**Logs.** Discrete event records emitted by the application as things happen. A log entry typically includes a timestamp, a severity level (DEBUG, INFO, WARN, ERROR, CRITICAL), a message, and contextual metadata (which user, which request, which service). Logs are the high-detail, high-volume pillar—the natural place to ask "what exactly happened during this specific failure?" Their strength is fidelity: a well-instrumented log captures the precise context of an event in a way that aggregated metrics cannot. Their weakness is volume: at scale, logs become expensive to store and slow to search, and signal gets lost in noise.

**Metrics.** Numeric measurements taken at intervals: CPU utilization, request rate, error rate, response time, queue depth, memory usage. Metrics are aggregated by design—the system records counts, sums, histograms, and percentiles rather than individual events—which makes them cheap to store and fast to query. Metrics are the natural foundation for **alerting** ("page me if error rate exceeds 1% for more than 5 minutes") and **dashboards** ("show me the p95 latency over the last 24 hours"). Their strength is summarization; their weakness is that aggregation loses individual-event detail. A metric tells you that latency spiked at 3:14 PM; it does not tell you what specific request caused the spike.

**Traces.** Records of how individual requests flow through a distributed system. A trace consists of multiple **spans**, each representing a unit of work performed in some service. A user's API call might produce a trace with spans for the API gateway, the application service, the database query, the cache lookup, and the call to a downstream service—each span timestamped, parented to its caller, and annotated with metadata. Traces are the natural tool for understanding **latency** in distributed systems ("which service in the chain is slow?") and for understanding **dependencies** ("when this endpoint is called, what other systems does it touch?"). Their strength is request-level visibility across service boundaries; their weakness is that they are typically sampled (storing every trace at production scale is expensive), and the sampling can miss the rare events that matter most.

The three pillars are complementary because they answer different questions. Metrics tell you that something is wrong; traces tell you where in the request flow the problem is; logs tell you what specifically happened at the point of failure. Investigating a production incident usually involves moving fluidly between all three: an alert on a metric prompts an investigation; traces narrow the investigation to a specific service and operation; logs reveal the precise error or context. A team operating without one of the pillars finds itself reaching for the missing tool repeatedly.

---

## 3. OpenTelemetry as the Standard

**OpenTelemetry (OTel)** is an open standard for generating, collecting, and exporting telemetry data—logs, metrics, and traces—from applications. It is a **CNCF graduated project**, formed in 2019 from the merger of two earlier projects (OpenTracing and OpenCensus) that were independently trying to solve the same problem. OpenTelemetry has since become the dominant cross-language, cross-vendor instrumentation standard.

The value of OpenTelemetry is **vendor neutrality**. An application instrumented with OpenTelemetry libraries can export its telemetry to any OTel-compatible backend: Datadog, New Relic, Honeycomb, Jaeger, Prometheus, Grafana Tempo, Splunk, or self-hosted solutions. Switching backends is a configuration change, not a re-instrumentation project. This decouples instrumentation (which is application code) from observability platform (which is operational infrastructure), and it has measurably reduced the cost of changing observability vendors over time.

OpenTelemetry comprises three components: the **SDKs** (language-specific libraries for instrumenting application code), the **API** (the abstract interface that instrumentation calls), and the **Collector** (a vendor-agnostic agent that receives telemetry from applications, processes it, and forwards it to one or more backends). Most modern instrumentation libraries—FastAPI middleware, Django middleware, Express middleware, database drivers—now have OpenTelemetry support either built in or as a thin add-on.

The practical guidance for new applications: **use OpenTelemetry as the instrumentation layer, regardless of the chosen backend**. Backends will likely change over a project's lifetime; the instrumentation effort should not be repeated each time.

---

## 4. Tools Compared

The major tools cluster by pillar, with several platforms providing all three.

| Pillar | Self-hosted / open source | Managed / commercial | Notes |
|---|---|---|---|
| **Logging** | ELK stack (Elasticsearch + Logstash + Kibana), Loki (lightweight, pairs with Grafana), Vector | Datadog Logs, CloudWatch Logs (AWS), Cloud Logging (GCP), Splunk, Sumo Logic | Loki has gained share for its lower cost relative to Elasticsearch on log-heavy workloads. CloudWatch is the default on AWS. |
| **Metrics** | Prometheus + Grafana (the de facto open-source standard), VictoriaMetrics, M3 | Datadog Metrics, CloudWatch Metrics, Cloud Monitoring (GCP), New Relic, Grafana Cloud | Prometheus is the dominant open-source choice. Grafana provides visualization on top of Prometheus and many other sources. |
| **Tracing** | Jaeger, Zipkin, Grafana Tempo | Datadog APM, Honeycomb, New Relic, Lightstep, AWS X-Ray | Honeycomb is notable for its high-cardinality query model, well-suited to debugging novel issues. |

A few cross-cutting platforms worth naming. **Datadog** offers all three pillars in a single integrated product and is the most common choice for teams that want a unified vendor. **Grafana Cloud** combines Grafana visualization with Loki (logs), Prometheus-compatible metrics, and Tempo (traces), forming an integrated open-source-aligned stack. **Cloud-provider tools** (CloudWatch, Cloud Monitoring/Logging) are convenient defaults for teams already on AWS or GCP and often cover early needs without additional vendor management.

The choice of tools matters less than instrumentation discipline. A team using Prometheus + Loki + Tempo with thoughtful instrumentation produces better observability than a team using a premium platform with sloppy instrumentation. The instrumentation determines what questions can be asked; the platform determines how easily they can be answered.

---

## 5. Best Practices per Pillar

**Logging.**

- **Use structured logging.** Emit logs as JSON with named fields (`{"timestamp": "...", "level": "ERROR", "request_id": "...", "user_id": "...", "message": "..."}`) rather than free-text strings. Structured logs are queryable by field and aggregatable in ways that string logs are not.
- **Use log levels meaningfully.** DEBUG for verbose troubleshooting, INFO for normal operational events, WARN for unusual but non-failure conditions, ERROR for handled errors, CRITICAL for unrecoverable failures. A system where everything is logged at INFO produces noise and obscures real signal.
- **Never log secrets.** PII, API keys, passwords, JWT tokens, OAuth secrets, full credit-card numbers, full session cookies. Audit log pipelines for accidental secret emission; configure log libraries with redaction filters where possible.
- **Include correlation IDs.** A unique identifier attached to each request, passed through all downstream service calls and included in every log line, allows logs from multiple services to be joined into a single request narrative. Without correlation IDs, debugging a distributed failure is forensic archaeology.
- **Timestamps in UTC.** Logs from systems in different timezones cannot be correlated reliably without a consistent time standard. UTC is the universal default.
- **Watch the cost.** Log volume scales with traffic, and managed log services charge per GB ingested. Sample DEBUG and INFO logs in production; emit ERROR and CRITICAL at full fidelity.

**Metrics.**

Two complementary frameworks dominate metric design.

- **The RED method** (Rate, Errors, Duration) for service-level metrics. For each service or endpoint, instrument three metrics: how many requests per second (Rate), how many of them failed (Errors), how long they took (Duration, typically as a latency histogram). RED metrics describe the user-facing behavior of a service and are the right starting point for service instrumentation.
- **The USE method** (Utilization, Saturation, Errors) for resource-level metrics. For each resource (CPU, memory, disk, network), instrument utilization (how busy is it?), saturation (how queued or contended is it?), and errors. USE metrics describe infrastructure health.
- **Google's Four Golden Signals** (latency, traffic, errors, saturation) from the SRE book are essentially RED + saturation, formulated for distributed-systems monitoring.

Additional disciplines: **define alerts on the metrics that indicate user-visible failure**, not on every metric. Alerts on resource utilization without user-visible impact produce noise; alerts on user-visible latency or error rate produce action. **Use percentiles, not averages**, for latency. The 95th and 99th percentile latency tell you what real users at the tail of the distribution experience; the average obscures them.

**Traces.**

- **Instrument every service in the request path.** A trace that covers four out of five services has a gap precisely where the problem might be. OpenTelemetry's automatic instrumentation libraries make near-complete coverage feasible.
- **Sample intelligently.** Storing every trace at production scale is expensive. Common patterns: sample a fixed percentage (e.g., 1%) of all traces, plus 100% of traces with errors or with latency above a threshold. **Tail-based sampling** (deciding whether to keep a trace after seeing the full trace) produces better results than head-based sampling but requires more infrastructure.
- **Add useful span attributes.** A span enriched with the user ID, request ID, and key business identifiers becomes diagnostic; a span with only timing is much weaker. Avoid putting secrets or extremely high-cardinality data in span attributes.

---

## 6. Special Case: AI Agent Observability

LLM-powered applications—chatbots, agents, retrieval-augmented generation systems—have observability needs that the general-purpose stack does not natively address. Specialized tools have emerged to fill this gap.

**LangSmith** (from the LangChain team) and **Langfuse** (open-source) are two of the most prominent. They capture, for each LLM call:

- The prompt (user message plus system message plus retrieval context, if any)
- The completion returned by the model
- The model used and its parameters (temperature, max tokens, etc.)
- Token usage (input tokens, output tokens)
- Latency
- Cost (computed from token usage and provider pricing)
- The tools or functions the model called, if any
- Errors and retries

For multi-step agents, these tools also capture the **full chain of reasoning**: which tool the agent decided to call, what it returned, how the agent's state evolved across steps. This level of detail is essential for debugging agent behavior, evaluating prompt quality, and controlling cost.

The general-purpose observability stack (logs, metrics, traces) still applies to LLM applications—the API gateway, business logic, and database calls all emit standard telemetry. The LLM-specific layer sits on top, capturing the AI-specific concerns. Many AI-application architectures use both: standard OpenTelemetry for the application backbone, LangSmith or Langfuse for the LLM-specific layer.

The principles transfer from general observability: capture enough to ask new questions later, do not log secrets (prompts can contain PII), control cost by sampling judiciously, and measure what corresponds to user-visible behavior (response quality, response latency, cost per session).

---

## 7. Example: Educational Coding App for Kids

Consider the observability plan for **CodeCub**, a Python-based educational coding app with a FastAPI backend, a Vue web frontend, PostgreSQL on Supabase or AWS RDS, Redis for caching, and an AI tutoring layer using LLM APIs. The team is small, the goal is launch-ready observability without over-engineering.

**Minimum viable observability stack:**

**Logs — structured JSON to the cloud provider's logging service.**

Configure FastAPI and supporting Python services to emit JSON-formatted logs through a structured logging library (`structlog` is a strong default in Python). Logs include: timestamp (UTC, ISO 8601), level, request_id, learner_id (where relevant, hashed for child-data minimization), service name, and message. Logs ship to **CloudWatch Logs** (AWS) or **Cloud Logging** (GCP) directly from the application or from a Docker logging driver. Cost is bounded by sampling DEBUG and INFO at production volume.

**Metrics — Prometheus-compatible, exposed via FastAPI middleware.**

Use a Prometheus client library (`prometheus_client` for Python) to expose RED metrics: request rate, error rate, and request duration histograms, broken down by endpoint. Expose a `/metrics` endpoint that the cloud provider's managed Prometheus or a small self-hosted Prometheus scrapes at regular intervals. Visualize in **Grafana**.

Specific metrics worth instrumenting on day one:

- `http_requests_total` (counter, labeled by endpoint and status code)
- `http_request_duration_seconds` (histogram, labeled by endpoint)
- `lesson_attempts_total` (counter, labeled by outcome: passed, failed, error)
- `ai_tutoring_calls_total` (counter, labeled by outcome and model)
- `ai_tutoring_tokens_total` (counter, labeled by direction: input, output)
- `ai_tutoring_cost_dollars_total` (counter, computed from token usage)
- Database query duration histograms

Alerts on day one:

- p95 request latency above a defined threshold for 10+ minutes (user-impact)
- Error rate above 1% for 5+ minutes (user-impact)
- AI tutoring cost above the daily budget (cost control)
- Database connection pool saturation (resource health)

**Traces — OpenTelemetry to a managed backend, sampled.**

Instrument the FastAPI service with OpenTelemetry's auto-instrumentation library, which captures spans for HTTP requests, database queries, Redis calls, and outbound HTTP calls (including LLM API calls). Sample at 5–10% in production, with 100% sampling for traces containing errors or exceeding a latency threshold. Ship to a managed backend; **Honeycomb**, **Datadog APM**, or **Grafana Tempo** are all credible choices.

The trace context flows from the frontend (web client adds a `traceparent` header) through the API to the database and AI service, producing a single trace per user action that crosses service boundaries.

**LLM-specific layer — Langfuse for AI tutoring observability.**

The AI tutoring code wraps each LLM call with Langfuse instrumentation, capturing the prompt, completion, model, token usage, and latency. This produces a per-session view of the agent's behavior that is invaluable for debugging unexpected outputs, monitoring cost, and evaluating prompt quality. Langfuse data complements (does not replace) the general-purpose telemetry above.

**Implementation sequence:**

1. Day-one launch: structured JSON logs to CloudWatch, RED metrics on every endpoint, basic alerts on user-impacting metrics.
2. Within the first month: OpenTelemetry tracing across FastAPI and the database; Langfuse for AI tutoring calls.
3. As the system grows: tail-based sampling for traces, custom dashboards for product-specific metrics (lesson completion rates, parental dashboard latency), and SLO-based alerting on the user-facing critical paths.

The plan is deliberately modest. A small team can implement and operate this stack without a dedicated SRE; the components are well-supported, the costs are bounded, and the resulting observability is sufficient to debug all but the most exotic production issues.

---

## 8. Common Pitfalls

- **Too many logs blowing up the bill.** Log volume scales with traffic, and managed log services charge per GB. Sample aggressively at DEBUG and INFO levels in production; emit warnings and errors at full fidelity. Audit log volume monthly.
- **No correlation IDs across services.** Without a request_id passed from service to service and emitted in every log line, debugging cross-service failures is nearly impossible. Add correlation IDs from day one—retrofitting them later is harder.
- **Logs without UTC timestamps.** Timestamps in local time, or worse, with no timezone, make logs from multiple regions impossible to correlate. UTC, always.
- **Metrics without alerting.** A metric that no one alerts on or graphs is dead weight—it costs to collect and produces no operational value. Either alert on it, dashboard it, or stop collecting it.
- **Alerting on the wrong things.** Alerts on resource utilization (CPU above 80%) without user-visible impact produce noise and alert fatigue. Alert on user-visible signals: error rate, latency, failure of critical workflows.
- **Tracing only some services.** A trace with a gap in the middle is worse than no trace at all—it suggests visibility you do not have. Instrument every service in the request path, and verify trace continuity.
- **Logging secrets accidentally.** PII, API keys, password fields, full session tokens. Audit log output regularly; use libraries with redaction filters; never log raw request bodies for endpoints that accept secrets.
- **Drowning in dashboards.** Twenty unmaintained dashboards are worse than three well-maintained ones. Curate a small set of dashboards that operators actually use.
- **Treating observability as someone else's job.** When developers do not engage with telemetry, the instrumentation drifts and the observability decays. Make telemetry quality part of code review, and surface it in incident retrospectives.
- **No retention policy.** Logs and traces accumulate indefinitely without explicit retention. Define retention by data class (errors longer than INFO, security-relevant longer than operational), and review costs against the policy.

---

## 9. References

- OpenTelemetry: https://opentelemetry.io/
- Datadog — Observability Knowledge Center: https://www.datadoghq.com/knowledge-center/observability/
- Google SRE Book — Monitoring Distributed Systems: https://sre.google/sre-book/monitoring-distributed-systems/