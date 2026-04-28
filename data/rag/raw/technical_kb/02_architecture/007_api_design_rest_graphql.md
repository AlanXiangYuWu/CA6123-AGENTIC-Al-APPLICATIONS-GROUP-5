# API Design: REST vs GraphQL

**Category**: architecture
**Source**: GraphQL.org, RESTful API guide, Apollo
**Use Case**: Architect Agent uses this when designing the API layer.

---

## 1. Overview

The choice of API style shapes how clients and servers communicate, how data flows between systems, and how the API evolves over time. **REST** and **GraphQL** are the two dominant paradigms for designing HTTP-based APIs in modern web development. REST is the older, simpler, more widely adopted style: a resource-oriented model that uses standard HTTP verbs and URLs, originally articulated by Roy Fielding in his 2000 PhD thesis. GraphQL is the newer alternative: a query language and runtime created by Facebook in 2012 and open-sourced in 2015, in which clients specify exactly what data they need and the server returns precisely that, no more and no less.

The two are not opposites but different points on a trade-off curve between **simplicity and flexibility**. REST is simpler to design, simpler to cache, and simpler to operate; GraphQL is more flexible for clients and more efficient for use cases where the same backend serves multiple clients with different data needs. Neither is universally better; the choice depends on the application's clients, data shapes, and operational appetite.

This document covers the principles of REST, the features that distinguish GraphQL, a detailed comparison across the dimensions that matter (over-fetching, caching, tooling, the N+1 problem, versioning), guidance on when to choose each, brief notes on modern alternatives (tRPC, gRPC), and a concrete recommendation for an educational coding app for children.

---

## 2. REST Principles

**REST (Representational State Transfer)** was defined by **Roy Fielding** in his 2000 PhD dissertation at UC Irvine. The dissertation articulated REST as an architectural style for distributed hypermedia systems, codifying patterns that had already emerged on the web but had not been formally named. The key principles:

- **Stateless.** The server stores no client context between requests. Every request from a client must contain all the information needed to process it. This property makes REST APIs straightforward to scale horizontally—any instance can handle any request—and simplifies failure recovery.
- **Resource-oriented.** URLs identify resources, and the resource is the central abstraction. `/users/123` identifies a user; `/users/123/orders/456` identifies an order belonging to that user. The URL space is a hierarchy of resources, and clients navigate it by constructing URLs that match the desired resources.
- **Standard HTTP verbs.** Operations on resources map to HTTP methods: `GET` (read), `POST` (create), `PUT` (update or replace), `PATCH` (partial update), `DELETE` (delete). The verb-resource pairing produces a small, predictable vocabulary that any HTTP-aware tool understands.
- **HATEOAS (Hypermedia as the Engine of Application State).** Responses include links to related resources, allowing clients to navigate the API by following links rather than by hard-coding URLs. HATEOAS is the most idealistic of the REST principles and is widely skipped in practice. Most "REST" APIs in production are technically RESTful in resource orientation and HTTP verbs but do not implement HATEOAS.

REST's cumulative effect is an API style that aligns naturally with HTTP, leverages decades of HTTP infrastructure (caches, load balancers, observability tooling), and produces APIs that are easy to discover and reason about. The trade-off is that **the resource boundaries are baked into the API contract**: a client that needs data spread across multiple resources typically makes multiple calls, and a client that needs only part of a resource still receives the whole representation.

---

## 3. GraphQL Features

**GraphQL** was created at Facebook in 2012 to solve a specific problem: the company's mobile clients were over-fetching data on slow networks, and adding new endpoints for every screen-specific data shape was unsustainable. It was open-sourced in 2015 and has since become a major alternative to REST, particularly for applications with multiple clients or complex data relationships. The defining features:

- **Single endpoint.** A GraphQL server typically exposes a single endpoint (commonly `/graphql`) that accepts queries. The endpoint does not vary by resource; it varies by query content.
- **Strongly typed schema.** The server publishes a schema describing the types it can return, the queries clients can issue, and the mutations they can perform. The schema is introspectable—clients (and tooling) can query the API to discover its capabilities at runtime.
- **Client-specified data shape.** Clients send queries that describe exactly which fields they need from which types. The server returns precisely that data, no more and no less. This eliminates the over-fetching and under-fetching that plague REST APIs serving multiple client types.
- **Mutations for writes.** Reads use queries; writes use mutations. The schema describes both, and the same client tooling handles both.
- **Subscriptions for real-time.** A third operation type, subscriptions, supports server-pushed updates over WebSockets or similar transports, providing a built-in path to real-time features.

A typical GraphQL query asks for a parent and a graph of related children in a single request:

```graphql
query GetLearnerProfile($id: ID!) {
  learner(id: $id) {
    name
    ageBand
    progress {
      lessonsCompleted
      currentStreak
    }
    parent {
      email
      notificationPreference
    }
  }
}
```

The server resolves the entire graph and returns one JSON response shaped to the query. The same shape would require three or four REST calls, possibly returning more data per call than the client needed.

---

## 4. Comparison

| Dimension | REST | GraphQL |
|---|---|---|
| **Endpoint model** | Many endpoints, one per resource (`/users/123`, `/users/123/orders`). | One endpoint (`/graphql`); requests vary by query content. |
| **Data shape** | Server-defined per endpoint. | Client-specified per query. |
| **Over-fetching / under-fetching** | Common. Endpoints return fixed shapes; clients often get too much or too little. | Eliminated. Clients ask for exactly the fields they need. |
| **Caching** | Easy. HTTP caching (CDNs, browser caches, reverse proxies) works out of the box on `GET` endpoints. | Harder. Single-endpoint POSTs are not cached by HTTP layers; query-level caching (e.g., Apollo's normalized cache) is required and lives mostly on the client. |
| **Tooling** | Mature. OpenAPI / Swagger for documentation; ecosystem of generators, mock servers, contract-testing tools. | Strong but younger. Apollo, Relay, GraphQL Code Generator. Schema introspection enables strong tooling natively. |
| **N+1 problem** | Less prone—each REST endpoint typically handles its own fetching efficiently. | Highly prone. A query asking for "all users and their last 3 orders" can naïvely produce one query per user. The standard solution is the **DataLoader** pattern, which batches and caches resolver calls within a request. |
| **Versioning** | Common pattern: URL-based versioning (`/v1/users`, `/v2/users`) or header-based. | Schema evolution. Fields are added, deprecated, and eventually removed; there is typically no explicit "v2" of a GraphQL API. |
| **Learning curve** | Familiar to anyone who has used HTTP APIs. | Steeper. Schema design, resolver patterns, query optimization, and DataLoader are all new concepts for teams new to GraphQL. |
| **File uploads / binary data** | Native via multipart form data. | Requires a multipart spec extension; less natural than REST. |
| **Public API suitability** | Excellent. Caching, rate limiting, and developer-portal tooling are well-established. | Trickier. Caching and rate limiting are harder; query complexity must be analyzed to prevent abuse. |
| **Multi-client efficiency** | Each client often needs custom endpoints or accepts inefficiency. | Native strength. Web, mobile, and admin clients all query the same schema for their specific data needs. |

The patterns in the table cluster into a clear theme. **REST is simpler, more cacheable, and better aligned with HTTP infrastructure; GraphQL is more flexible, more efficient for diverse clients, and better at handling complex data relationships.** Both have well-understood operational profiles; the choice depends on which dimensions matter most for the application.

---

## 5. When to Choose Which

**Lean REST when:**
- The API is **public**, where HTTP caching, developer-portal tooling, and broad familiarity matter.
- The application is a straightforward **CRUD system** with stable resource boundaries.
- HTTP caching is critical—high-traffic public endpoints benefit substantially from CDN and edge caching, which work natively on REST GETs but require additional infrastructure for GraphQL.
- The team is **unfamiliar with GraphQL** and the operational learning curve is not justified by the application's needs.
- A small number of clients consume the API and their data needs are stable.

**Lean GraphQL when:**
- The application has **mobile clients** where bandwidth and battery matter, and the data minimization GraphQL provides is genuinely valuable.
- Multiple clients with **different data needs** consume the same backend (web, native mobile, admin dashboard, partner integrations). Each client queries for what it needs without forcing the API to serve a common denominator.
- The data model has **complex relationships** that clients frequently traverse, and REST would require many round trips to assemble the desired view.
- **Frequently changing data requirements** make it valuable for clients to evolve their queries without requiring backend changes for every new screen.

**Either is reasonable when:**
- The application has a single web client and modest data complexity.
- Operational simplicity and team familiarity outweigh the marginal benefits of either style.

---

## 6. Modern Alternatives

REST and GraphQL are not the only API styles in use. Two alternatives are worth brief mention.

**tRPC** ("TypeScript Remote Procedure Call") is a typed RPC layer designed for full-stack TypeScript projects. It eliminates the schema-definition step entirely: the backend defines procedures in TypeScript, and the frontend calls them with full end-to-end type safety, including autocompletion across the network boundary. tRPC is excellent for full-stack TypeScript applications where the same team owns both ends, and it removes most of the boilerplate of API design. The trade-off is that tRPC requires both ends to be TypeScript; it does not produce a portable API contract for non-TypeScript clients.

**gRPC** is Google's RPC framework, built on HTTP/2 with Protocol Buffers as the serialization format. It is high-performance, strongly typed, and well-suited to **service-to-service communication** in polyglot environments. Performance benefits come from binary serialization and HTTP/2 multiplexing. gRPC is rarely used for browser-facing APIs (browser support requires gRPC-Web with limitations), but it is a strong default for internal service-to-service traffic in microservices architectures.

For most browser-facing APIs in 2024–2026, the practical choice is between REST and GraphQL, with tRPC as a strong third option for TypeScript-only projects and gRPC reserved for service-to-service traffic. **REST + JSON Schema (or OpenAPI) remains the dominant choice for public APIs**, while GraphQL is increasingly common for internal APIs serving multiple sophisticated clients.

---

## 7. Example: Educational Coding App for Kids

Consider the API design for **CodeCub**, a Python-based educational coding app for children aged 6–12. The team is small (3–5 engineers), the launch surface is a single web client (with mobile planned later), and the backend is FastAPI on Python.

**Recommendation for the MVP: REST.**

The factors driving the choice:

- **Simplicity matches team size and stage.** A REST API with a handful of endpoints—lessons, learners, attempts, parent dashboards—is straightforward to design, document, and operate. The team avoids GraphQL's learning curve at a moment when shipping speed matters more than client-side flexibility.
- **A single web client at launch.** GraphQL's strongest advantage is serving multiple clients with different data needs. With a single web client, that advantage is muted.
- **FastAPI's auto-generated OpenAPI documentation aligns with REST.** FastAPI produces interactive Swagger UI and ReDoc documentation from Python type hints automatically. This produces documentation parity with what GraphQL would offer through introspection, without GraphQL's operational overhead.
- **The data model is largely tabular.** Lessons, learners, progress, and attempts have stable, tabular shapes that map naturally onto REST resources. Complex graph traversals across the schema are not the dominant access pattern.
- **HTTP caching is straightforward.** Lesson content (which is the same for every learner of a given age band) can be cached aggressively at the CDN layer; learner-specific data is uncached but small. REST makes this caching strategy trivial.

**When the recommendation might shift toward GraphQL:**

- **When mobile clients launch** alongside the web client, and the two have meaningfully different data needs. A child's mobile app needs lesson content, the current attempt, and minimal navigation; the parent's web dashboard needs progress aggregations, billing data, and child profiles. GraphQL's per-client query flexibility becomes attractive here, though many teams successfully ship multi-client products on well-designed REST APIs by composing endpoints carefully.
- **When the school-channel admin dashboard is built**, which has substantially different data needs from both consumer web and mobile (class rosters, assignment management, district-level reporting). At three meaningfully different clients, GraphQL's efficiency case strengthens.
- **When the data model develops complex graph traversals.** If parents of children of teachers in classes assigned to schools start producing legitimately complex query shapes, GraphQL's natural expression of graph queries pays off.

**Pragmatic path:**

Start with REST for the MVP, designed cleanly and documented through FastAPI's auto-generated OpenAPI. Re-evaluate when a second or third client launches with materially different data needs, or when the data model develops complex graph traversals that REST handles awkwardly. The migration from REST to GraphQL is real work but is contained—both can coexist on the same backend during transition, with new query patterns served by GraphQL and existing CRUD endpoints continuing as REST. Adopting GraphQL on day one for an MVP with a single web client would invest in flexibility the application is not yet positioned to use.

---

## 8. References

- GraphQL official site: https://graphql.org/
- RESTful API guide: https://restfulapi.net/
- Apollo — REST vs GraphQL: https://www.apollographql.com/blog/rest-vs-graphql