# Database: PostgreSQL vs MongoDB

**Category**: tech_stack
**Source**: AWS, MongoDB official, DataCamp
**Use Case**: Architect Agent uses this when designing the data layer of a system.

---

## 1. Overview

**PostgreSQL** and **MongoDB** are the two most prominent open-source databases representing two distinct data-model traditions. PostgreSQL is a relational, SQL-based database with a four-decade pedigree of strong consistency, structured schemas, and rich query capabilities. MongoDB is a document-oriented NoSQL database designed for flexible schemas, horizontal scaling, and the storage of semi-structured data in JSON-like form. The choice between them is one of the most consequential decisions in backend architecture: it shapes data modeling, query patterns, scaling approach, and the boundary between application code and database code for years.

The traditional framing of the choice was clean—PostgreSQL for structured transactional data, MongoDB for unstructured high-volume data—but the line has blurred substantially over the past decade. PostgreSQL added robust JSONB support, enabling document-style storage and querying inside a relational system. MongoDB added multi-document ACID transactions in version 4.0 (2018), narrowing one of the historic gaps between the two. Both databases now overlap meaningfully on the middle ground, and the decision often comes down to the dominant access pattern, scaling profile, and team experience rather than to a strict feature gap.

This document compares the two databases across architecture, consistency guarantees, and scaling models; presents a decision matrix for when to choose each; describes the common hybrid pattern of using both; and applies the analysis to a concrete example—the data layer for an educational coding app for children aged 6–12.

---

## 2. Architecture Differences

The fundamental architectural distinction is the **data model** and the **schema philosophy**.

**PostgreSQL** is a **relational database** in the SQL tradition. It was originally developed as **Postgres** at UC Berkeley starting in 1986, evolved through several phases, and emerged as PostgreSQL with full SQL support in 1996. Data is stored in **tables** consisting of **rows** and **columns**, where each table has a **predefined schema** that specifies column names, types, constraints, and relationships. Relationships between tables are expressed as foreign keys and queried via SQL `JOIN` operations. The schema is **enforced at write time**: a row that does not match the table's schema is rejected.

**MongoDB** is a **document database** in the NoSQL tradition. It was created in 2009 by the company that became MongoDB Inc. Data is stored as **documents**—JSON-like records encoded in a binary format called **BSON** (Binary JSON)—grouped into **collections**, which are roughly analogous to tables but without enforced schemas. Each document is self-describing and can have a different shape from other documents in the same collection. Relationships can be expressed either by embedding related data inside a document (denormalization) or by referencing other documents (similar to foreign keys, but resolved by the application or via MongoDB's `$lookup` aggregation stage).

The schema philosophy diverges sharply.

- **PostgreSQL is schema-on-write.** The schema is defined up front and enforced as data is inserted. Changing the schema requires a migration. The benefit is strong data integrity and predictable structure; the cost is rigidity when the data shape evolves frequently.
- **MongoDB is schema-flexible.** Documents in the same collection can have different fields, and adding a new field is as simple as inserting a document with that field. The benefit is fast iteration and easy accommodation of varied data; the cost is that the application becomes responsible for handling shape variation, and inconsistencies can creep in over time. (MongoDB does support optional **schema validation** for collections, providing a middle ground.)

A second architectural difference: PostgreSQL has rich, expressive **SQL** as its query language, with decades of tooling, optimizer maturity, and ecosystem support. MongoDB has its own query language—JSON-based filter documents and an **aggregation pipeline** for complex transformations—which is powerful but distinct from SQL and requires its own learning curve.

The line between the two has narrowed in one important respect: **PostgreSQL supports JSON and JSONB columns** that allow document-style data to be stored, indexed, and queried inside a relational table. JSONB in particular offers full indexing and efficient access. This gives PostgreSQL applications the option of keeping flexible-schema data in JSONB columns while keeping core transactional data in conventional relational tables, capturing much of MongoDB's flexibility without leaving the relational model.

---

## 3. ACID and Consistency

**ACID** stands for **Atomicity, Consistency, Isolation, Durability**—the properties that define reliable transaction processing. ACID compliance is critical for any system where partial updates would corrupt the data: financial transactions, inventory, identity, billing.

**PostgreSQL provides strong ACID compliance by default.** Transactions span multiple statements and multiple tables; they either fully commit or fully roll back. Multiple isolation levels (Read Committed, Repeatable Read, Serializable) are supported, and the database has decades of hardening around concurrency control. ACID guarantees in PostgreSQL are not opt-in or qualified—they are the default behavior of the system.

**MongoDB historically did not provide multi-document ACID transactions.** Single-document operations were always atomic, but operations that touched multiple documents had no transactional guarantees. This was a deliberate trade-off: in exchange for relaxing transaction scope, MongoDB could scale horizontally more easily and handle write-heavy workloads with less coordination overhead.

**MongoDB 4.0, released in 2018, added multi-document ACID transactions** for replica sets, and **MongoDB 4.2 (2019) extended this to sharded clusters**. This was a significant evolution: applications that had previously been forced to choose between MongoDB's flexibility and ACID guarantees could now have both. The transactional model in MongoDB is functional and credible, but it remains less mature, less performant per transaction, and less idiomatic than PostgreSQL's transaction support. Multi-document transactions in MongoDB are best treated as an exception rather than the default access pattern; applications that need transactions on every write are still better served by PostgreSQL.

The practical guidance: **if multi-record ACID transactions are a frequent and central access pattern, PostgreSQL is the safer default.** If transactions are rare and the dominant access pattern is single-document reads and writes, MongoDB's transactional support is sufficient.

---

## 4. Scaling Models

PostgreSQL and MongoDB take different approaches to scaling, and the difference becomes consequential at high data volumes or write rates.

**PostgreSQL scales primarily vertically.** Larger machines—more CPU, more memory, faster storage—handle larger PostgreSQL workloads. **Read replicas** scale read traffic horizontally, but write traffic is concentrated on a single primary. For workloads that exceed what a single primary can handle, PostgreSQL applications historically resorted to **application-level sharding** (partitioning data across multiple PostgreSQL instances and routing queries from the application). The **Citus** extension provides distributed PostgreSQL capabilities, allowing transparent horizontal scaling for many workloads, and managed PostgreSQL services (e.g., AWS Aurora, Google Cloud SQL, CockroachDB as a Postgres-compatible alternative) further extend horizontal options. But the default PostgreSQL story is "scale up, with read replicas for read scaling."

**MongoDB scales horizontally as a first-class feature.** **Sharding** is built into the database: a sharded cluster automatically partitions data across multiple shards based on a chosen shard key, and the cluster routes reads and writes accordingly. MongoDB clusters routinely scale to dozens or hundreds of nodes handling very high write volumes (e.g., IoT telemetry, activity logs at internet scale). Replica sets within each shard provide redundancy and read scaling. The horizontal model means that scaling a MongoDB deployment by adding nodes is operationally well-trodden, and the database's design assumes that distributed deployment is the common case rather than the exception.

The scaling difference matters most at the extremes. For the great majority of applications, a single well-provisioned PostgreSQL primary with read replicas handles all the load they will ever produce; vertical scaling is sufficient and simpler. For applications with genuinely high write volumes—activity streams, sensor data, real-time analytics, large-scale logging—MongoDB's horizontal scaling is a meaningful advantage and avoids the complexity of application-level sharding.

A practical heuristic: **if write volume is expected to exceed what a single high-end PostgreSQL primary can handle, MongoDB's horizontal model becomes attractive. Below that threshold, PostgreSQL's vertical scaling is simpler and more than sufficient.**

---

## 5. When to Choose Which

The decision between PostgreSQL and MongoDB depends on the data model, consistency requirements, scaling profile, and team experience.

| Factor | Lean PostgreSQL | Lean MongoDB |
|---|---|---|
| Data model | Structured, with clear entity types and stable schemas | Semi-structured or unstructured; document-oriented |
| Relationships | Many-to-many, complex joins, normalized data | Few relationships; data accessed as self-contained documents |
| Schema evolution | Stable; changes are deliberate and infrequent | Frequent; rapid prototyping or evolving formats |
| Transactional needs | Multi-record ACID is central | Single-document operations dominate |
| Query complexity | Rich SQL, complex joins, analytics, aggregations | Document filters, basic aggregation pipelines |
| Scaling profile | Vertical scaling with read replicas | Horizontal scaling, very high write volume |
| Team experience | SQL-comfortable, relational-modeling experience | NoSQL or document-modeling experience |
| Compliance / integrity | Strict regulatory or financial integrity | Flexible, eventual-consistency tolerance |

**Lean PostgreSQL when:**
- The application is a financial system, banking, accounting, billing, or anywhere strong ACID is non-negotiable.
- Data has complex relationships—users, organizations, projects, permissions, billing—that benefit from normalization and joins.
- Reporting, analytics, and ad-hoc complex queries are central to the application's value.
- Strict data integrity, foreign-key constraints, and referential integrity are required.
- The team has SQL expertise and benefits from PostgreSQL's mature tooling.

**Lean MongoDB when:**
- The application is a content management system, IoT platform, or real-time analytics service where data shape varies and write volume is high.
- The schema is expected to evolve frequently—rapid prototyping, frequent format changes, or ingestion of varied external formats.
- Data is naturally unstructured or semi-structured: logs, sensor data, activity events, user-generated content with variable shape.
- Horizontal scaling at high write volume is required and application-level sharding of PostgreSQL would be a significant burden.
- Documents are largely self-contained and access patterns rarely require joins across many entities.

**Either is reasonable when:**
- The application is a standard CRUD system without strong consistency or scale requirements at the extremes.
- The team has experience with one and not the other—operational familiarity often outweighs theoretical fit.

A useful frame: **PostgreSQL is the conservative, default choice for most applications**, and many systems that initially considered MongoDB are well-served by PostgreSQL with JSONB columns for the flexible-schema portions of their data. **MongoDB is the right choice when the data model, scale profile, or schema flexibility specifically calls for it**, and the application is willing to accept the trade-offs (less mature transaction support, no native joins, application-level enforcement of cross-document integrity).

---

## 6. Hybrid Approach

A common pattern in mature applications is to use **both databases together**, each for the workloads it serves best.

The typical division:

- **PostgreSQL for transactional data**: user accounts, billing, organizations, permissions, core domain entities, financial records. The data is structured, the access patterns benefit from joins and SQL, and ACID guarantees are essential.
- **MongoDB for high-volume, schema-flexible data**: activity logs, application telemetry, audit trails, user-generated content with variable structure, real-time analytics events, IoT or sensor streams.

This hybrid pattern is not a hedge or a compromise—it reflects a recognition that different workloads have genuinely different requirements, and using the right tool for each is operationally cleaner than forcing one database to handle everything. The trade-off is operational: running two databases means two backup strategies, two monitoring stacks, two sets of expertise, and a clear architectural boundary about which data lives where.

A simpler version of the same pattern is to use **PostgreSQL alone with JSONB** for the flexible-schema portions. This avoids the operational cost of running two databases at the price of MongoDB's horizontal scaling and document-native ergonomics. For applications where the flexible-schema workload is modest, the JSONB approach is often sufficient and simpler.

---

## 7. Example: Educational Coding App for Kids

Consider the data layer for **CodeCub**, a Python-based educational coding app for children aged 6–12. The product's data falls into several categories: user accounts (parents and children), subscriptions and billing, lesson curriculum, learner progress, code submissions, AI tutoring conversations, and learning-analytics events.

**Recommendation: PostgreSQL as the primary database, with MongoDB (or PostgreSQL JSONB) considered for high-volume analytics events as the data scales.**

The reasoning:

- **User accounts, subscriptions, and billing demand strong ACID.** A failed subscription renewal that partially updates the database would produce billing disputes and trust failures. Strong ACID in PostgreSQL handles these cases by default.
- **Relationships are real and central.** Parents have multiple children; children have lesson progress; schools have classes that have students that have assignments. The data is genuinely relational, and PostgreSQL's join capabilities map cleanly onto these access patterns.
- **Compliance environments favor PostgreSQL.** COPPA, FERPA, and similar regulations require strict data handling, audit trails, and integrity guarantees that are operationally easier to provide on a relational system with foreign-key constraints and well-understood transaction semantics.
- **Reporting and analytics are central.** Parent dashboards (weekly progress emails), teacher dashboards (class-level views), and internal product analytics (cohort retention, lesson-completion rates) all benefit from PostgreSQL's SQL expressiveness and analytical features (window functions, CTEs, JSON aggregation).
- **Schema is reasonably stable.** Lessons, learners, attempts, and progress have clear stable shapes; the schema evolves through deliberate migrations rather than per-document variation.

**Where MongoDB (or JSONB) becomes attractive:**

- **High-volume analytics events.** As the user base grows, fine-grained event telemetry—every lesson interaction, every hint shown, every code edit—can produce write volumes that strain a single PostgreSQL primary. At that point, sending raw event data to a write-optimized store (MongoDB, ClickHouse, or a managed analytics platform) and keeping aggregated summaries in PostgreSQL is a clean separation.
- **AI tutoring conversation logs.** The full text of AI tutoring conversations is semi-structured, growing rapidly, and rarely accessed transactionally. Storing these as documents (in MongoDB or as JSONB rows in a dedicated PostgreSQL table) decouples the high-volume write path from the transactional core.
- **User-generated content with variable shape.** Kid-built games and shared projects have nested, variable structure; representing them as documents simplifies storage and retrieval.

**Pragmatic guidance for this product:**

Start with **PostgreSQL alone**, using JSONB columns for the few cases where document-style flexibility is genuinely needed (AI conversation transcripts, kid-built project structures, semi-structured event payloads). This keeps the operational footprint small, the team focused on a single database, and the data model coherent. Introduce MongoDB only when measured write volume on a specific workload (most likely analytics events) exceeds what JSONB and read replicas can handle comfortably. The decision to add a second database should be made on observed evidence, not on speculative scaling concerns.

This matches the general pattern observed across mature SaaS products: **most applications never outgrow PostgreSQL**, and many applications that anticipated needing MongoDB ended up serving the same workloads on PostgreSQL with JSONB. Adding MongoDB is a real operational commitment; it should be made when the data justifies it, not by default.

---

## 8. References

- AWS — The difference between MongoDB and PostgreSQL: https://aws.amazon.com/compare/the-difference-between-mongodb-and-postgresql/
- MongoDB — Compare MongoDB vs PostgreSQL: https://www.mongodb.com/resources/compare/mongodb-postgresql
- DataCamp — PostgreSQL vs MongoDB: https://www.datacamp.com/blog/postgresql-vs-mongodb