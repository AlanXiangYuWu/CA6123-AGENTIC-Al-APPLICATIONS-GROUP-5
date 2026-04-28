# Cloud Platforms for Startups

**Category**: tech_stack
**Source**: AWS, GCP, Supabase, Firebase official sites
**Use Case**: Architect Agent uses this to recommend deployment platform.

---

## 1. Overview

Choosing a cloud platform is one of the earliest infrastructure decisions a startup makes, and the choice shapes development speed, operational burden, and cost trajectory for years. The decision is rarely about which platform is technically superior—each of the major options can host essentially any application—and more often about which platform matches the team's stage, expertise, and willingness to manage infrastructure complexity. A solo founder shipping an MVP, a five-person startup growing to ten thousand users, and a thirty-person company expanding into enterprise sales all have legitimately different best answers.

This document compares four representative options that span the spectrum from full infrastructure-as-a-service to fully managed Backend-as-a-Service: **AWS** (the most comprehensive cloud), **Google Cloud Platform (GCP)** (second/third largest, strong in AI/ML and data), **Firebase** (Google's all-in-one BaaS), and **Supabase** (an open-source Firebase alternative built on PostgreSQL). Each represents a different point on the trade-off curve between control and convenience.

A note on numbers: **free-tier limits and pricing change frequently. Treat all specific limits in this document as approximations and verify current values on the providers' websites before making decisions that depend on them.**

A note on AI projects: for applications whose value comes from LLM-powered features, the cloud platform decision is largely orthogonal to the AI work. What matters more is which LLM API provider is used (OpenAI, Anthropic, Google, or self-hosted), and any of the four platforms below can host an application that calls those APIs.

---

## 2. Major Options

**AWS (Amazon Web Services)**
Launched in 2006 and now the largest cloud platform by market share. AWS offers more than 200 services covering compute, storage, databases, networking, AI/ML, analytics, security, and dozens of other categories. Its strengths are breadth, maturity, and reliability—virtually every infrastructure pattern has an AWS service or reference architecture, and the platform is the de facto standard for enterprise deployment. Its weaknesses are complexity (the surface area is enormous, and most teams use a small fraction of it) and pricing that is harder to predict than its competitors due to per-service billing dimensions, data-egress charges, and a sprawling pricing catalog.

**Google Cloud Platform (GCP)**
The cloud arm of Google, second or third in market share depending on measurement. GCP's strengths are in AI/ML (Vertex AI for managed model deployment, BigQuery for analytics at scale) and Kubernetes (GKE is the most mature managed Kubernetes service, which is unsurprising because Google created Kubernetes). Pricing tends to be simpler and more predictable than AWS, with sustained-use and committed-use discounts that apply automatically. GCP's free tier is generous and is often a strong choice for prototyping, particularly for AI/ML-leaning workloads.

**Firebase (owned by Google)**
A Backend-as-a-Service platform that bundles authentication, realtime and document databases (Realtime Database and Cloud Firestore), hosting, cloud functions, push notifications, analytics, and crash reporting into a single integrated product. Firebase optimizes for developer speed: an MVP can ship without building any traditional backend code. The trade-offs are vendor lock-in (the data model and APIs are Firebase-specific) and pricing that can become expensive at scale, particularly for read-heavy workloads on Firestore.

**Supabase**
An open-source Firebase alternative built on top of PostgreSQL. Supabase provides authentication, a Postgres database (exposed both via SQL and via auto-generated REST and GraphQL APIs), object storage, realtime subscriptions, and Edge Functions for serverless logic. The defining feature is **portability**: because Supabase is PostgreSQL underneath, an application that grows beyond Supabase's hosted service can move to a self-managed PostgreSQL deployment without rewriting its data layer. The free tier is generous and Supabase has become a popular default for new startups that want Firebase-like developer experience without Firebase's lock-in.

---

## 3. Free Tier Comparison

The table below summarizes free-tier offerings as of 2024. **Free-tier limits change frequently—verify current values before making decisions that depend on them.**

| Platform | Free tier (approximate, as of 2024) | Notes |
|---|---|---|
| **AWS Free Tier** | 12 months free on many introductory services for new accounts (e.g., 750 hours/month of t2.micro EC2, 5 GB S3 storage, limited DynamoDB and RDS). Some services have always-free tiers (e.g., Lambda, DynamoDB on-demand). | The free tier is meant for evaluation; production usage typically exceeds it within months. Costs can rise sharply when limits are crossed. |
| **GCP Free Tier** | $300 in credit for new accounts (typically usable over 90 days) plus an "always-free" tier covering modest usage of Cloud Run, Cloud Functions, Firestore, BigQuery, and others. | Generous compared to AWS for prototyping; the $300 credit covers substantial experimentation. |
| **Supabase Free** | 500 MB database, 1 GB file storage, up to ~50,000 monthly active users for authentication, ~5 GB bandwidth, and unlimited API requests within those resource limits. Projects pause after a period of inactivity on the free tier. | Sufficient for many MVPs and small applications. Pricing scales predictably from there. |
| **Firebase Free (Spark plan)** | 1 GB Firestore storage, 10 GB/month bandwidth, 50,000 document reads and 20,000 writes per day on Firestore, 10 GB hosting storage, limited Cloud Functions. | The Spark plan covers small applications. Heavy read patterns can hit limits faster than expected. |

The headline observation: **for an early-stage MVP with up to a few thousand users, Supabase and Firebase are typically free.** AWS and GCP free tiers are more constrained, but the $300 GCP credit comfortably covers experimentation, and AWS's 12-month introductory tier covers most prototyping needs as long as the team is careful about which services they use.

---

## 4. When to Choose Which

The decision between these platforms maps cleanly to project stage and operational appetite.

**MVP / prototype stage.** Choose **Supabase** or **Firebase**. Both let a solo founder or small team ship a working backend in hours rather than weeks. Authentication, database, file storage, and serverless functions are all available out of the box, and free tiers cover early usage. Supabase is the stronger default for teams that want PostgreSQL underneath (for portability and SQL ergonomics); Firebase is the stronger default for teams already invested in Google's ecosystem or wanting Firebase's tight client-SDK integration with mobile platforms.

**Growing startup (post-PMF, scaling toward thousands of users).** Choose **AWS** or **GCP** based on team familiarity. By this stage, the application typically has accumulated infrastructure needs that exceed BaaS offerings: custom background processing, specialized data pipelines, more granular networking, fine-grained IAM. Both AWS and GCP can host these workloads competently. Team experience usually decides—the cost of training a team on a new cloud is real, and the operational benefits of one over the other are typically smaller than that training cost.

**Enterprise stage / regulated industry.** Choose **AWS**, with **GCP** as a credible alternative. AWS has the most comprehensive compliance certifications, the deepest catalog of enterprise-grade services, and the strongest default presence in enterprise procurement processes. GCP is fully credible for enterprise work and is often preferred for AI/ML-heavy workloads, but the conventional default in regulated industries (finance, healthcare, government) is AWS.

**AI/ML-heavy applications.** GCP has historical strength here (Vertex AI, BigQuery, TPUs), though AWS has caught up substantially with Bedrock and SageMaker. The choice is rarely the bottleneck; the application's LLM API provider matters more.

The decision tree, simplified:

- *Solo founder or small team, MVP under construction* → Supabase (preferred for PostgreSQL portability) or Firebase.
- *Growing startup, team has GCP experience* → GCP, possibly migrating Firebase data to GCP-native services.
- *Growing startup, team has AWS experience* → AWS.
- *Enterprise, regulated industry, large scale* → AWS.
- *AI/ML-heavy, especially with custom training or large-scale analytics* → GCP, with AWS as a credible alternative.

---

## 5. Vendor Lock-in Considerations

Vendor lock-in is the degree to which an application is tied to a specific platform such that migration becomes prohibitively expensive. The four options vary substantially.

- **Supabase has the lowest lock-in.** Because Supabase is PostgreSQL underneath, an application that needs to leave can take a `pg_dump` of its database and run on any PostgreSQL host (self-managed, AWS RDS, Google Cloud SQL, or any other Postgres provider). The Supabase-specific APIs (auth, storage, realtime) require some adaptation, but the core data is portable.
- **Firebase has high lock-in.** Firestore's data model is document-based and Firebase-specific; the auth system, the security rules, and the realtime synchronization all depend on Firebase APIs. Migrating off Firebase typically requires rewriting significant portions of the data layer.
- **AWS has moderate lock-in, varying by service.** Generic services (EC2, EBS, S3-compatible storage, RDS for PostgreSQL or MySQL) are largely portable. AWS-specific services (DynamoDB, Step Functions, IAM-tied workflows, proprietary ML services) are less so. Teams that build deliberately on portable primitives can migrate; teams that adopt the full AWS-specific stack cannot easily.
- **GCP has moderate lock-in, similar to AWS.** Generic services are portable; GCP-specific services (Spanner, BigQuery, Vertex AI's deeper features) are not.

A practical principle: **lock-in is acceptable when the productivity benefit justifies it**, and most early-stage startups are correct to accept Firebase or AWS-specific lock-in if it lets them ship faster. The lock-in becomes a problem when the application's growth or strategic direction requires moving and the cost of that move has become prohibitive. Teams that anticipate scaling beyond a single platform are wise to favor portable choices (Supabase over Firebase; PostgreSQL over DynamoDB; standard Kubernetes over proprietary container services) where the portability cost is small.

---

## 6. Example: Educational Coding App for Kids

Consider the infrastructure for **CodeCub**, an educational Python coding app for children aged 6–12. The team is small (3–5 engineers), the goal is to ship an MVP within roughly three months, and the data model includes user accounts, child profiles, lesson progress, billing, AI tutoring conversations, and parent-facing dashboards.

**Recommendation for the MVP: Supabase.**

The factors driving the choice:

- **Small team, short timeline.** Supabase eliminates the need to build authentication, file storage, and realtime subscriptions from scratch. A team that would otherwise spend two weeks setting up infrastructure can ship a working backend in days.
- **PostgreSQL is the right database for this product.** As discussed in the database-selection document, this application's data is structured, relational, and benefits from ACID guarantees. Supabase's PostgreSQL foundation matches that need exactly.
- **Authentication out of the box.** Children's apps require careful authentication (email verification for parents, COPPA-compliant data collection, parental consent workflows). Supabase Auth handles the standard flows; the team adds the COPPA-specific layers on top.
- **Portability.** If CodeCub outgrows Supabase, the PostgreSQL database can be migrated to a self-managed Postgres deployment on AWS or GCP with relatively low friction. The team is not locked in.
- **Cost predictability.** The free tier covers initial development and early users; the paid tier scales predictably (per-database-instance pricing rather than per-operation pricing).

**When to migrate or supplement.**

- **At meaningful scale (tens of thousands of paying users)**, the team may move the database to a managed PostgreSQL service on AWS or GCP for better operational control, larger instance options, and integration with broader cloud services. The application code stays largely the same.
- **For high-volume analytics events** (every lesson interaction, every hint shown), a separate write-optimized store may be added. The Supabase Postgres remains for transactional data; analytics events flow to a dedicated pipeline (e.g., to BigQuery on GCP, to a managed warehouse on AWS, or to a self-hosted ClickHouse).
- **For AI tutoring inference at scale**, the team may adopt a dedicated platform for model serving (Vertex AI on GCP, SageMaker on AWS, or self-hosted GPU infrastructure) while keeping the application backend on Supabase.
- **For school-channel deployments with stricter compliance requirements**, the team may move to AWS or GCP to access compliance certifications (FERPA-aligned configurations, regional data residency) that the Supabase-hosted service may not provide directly.

**Why not Firebase.** Firebase is a credible choice for this product, particularly if the team has prior Firebase experience or if the mobile clients benefit from Firebase's deep client SDKs. The decisive factor against Firebase is the data-model fit: this application's data is genuinely relational (parents to children, children to lessons, lessons to attempts, attempts to AI conversations), and PostgreSQL serves it more naturally than Firestore. Firebase's lock-in compounds the downside.

**Why not AWS or GCP directly.** Both are over-engineered for the MVP stage of this product. The team would spend significant time on infrastructure that Supabase provides for free, and would arrive at the first user launch later for no commercial benefit. The right time to consider AWS or GCP is after product-market fit, when the application's needs have outgrown what BaaS comfortably provides.

---

## 7. Common Pitfalls

- **Over-engineering early.** Adopting AWS or GCP for an MVP that has not yet reached its first hundred users is a common mistake. The infrastructure work consumes engineering time that should be going into product discovery. Use BaaS until the product justifies leaving it.
- **Surprise costs from default settings.** AWS in particular is notorious for unexpected bills—data egress charges, idle resources, NAT gateways running 24/7, S3 request fees on inefficient access patterns. Set up billing alerts on day one, on every cloud platform, and review the bill monthly.
- **Vendor lock-in adopted accidentally.** Teams sometimes choose Firebase or AWS-specific services without recognizing the lock-in cost, then face an expensive migration when the product's trajectory changes. When a portable alternative exists at comparable cost, prefer it; when lock-in is accepted, accept it deliberately.
- **Migrating prematurely.** The opposite mistake: moving from Supabase or Firebase to AWS or GCP before there is a real reason to do so. Migration is operationally expensive; defer it until the current platform is genuinely insufficient.
- **Choosing the cloud for AI/ML reasons that do not apply.** For applications whose AI work is hosted-API calls (OpenAI, Anthropic), the cloud platform's AI/ML capabilities are largely irrelevant. Choose the cloud on its other merits.
- **Underestimating data egress costs at scale.** All major clouds charge for data leaving the cloud, sometimes substantially. Architectures that move large volumes of data between regions or out of the cloud regularly produce surprising bills.
- **Ignoring compliance requirements.** Children's apps, healthcare apps, and financial apps have specific compliance requirements (COPPA, HIPAA, SOC 2) that vary by platform. Confirm compliance posture before committing.
- **Building on a free tier that will not extend.** AWS's 12-month introductory tier ends abruptly; teams that designed around it can be surprised by month-13 bills. Plan for the post-free-tier cost from the beginning.

---

## 8. References

- AWS Free Tier: https://aws.amazon.com/free/
- Google Cloud Free Tier: https://cloud.google.com/free
- Supabase: https://supabase.com/
- Firebase: https://firebase.google.com/
- Wikipedia — Amazon Web Services: https://en.wikipedia.org/wiki/Amazon_Web_Services