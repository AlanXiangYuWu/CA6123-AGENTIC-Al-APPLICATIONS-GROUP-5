What is this
This is the Technical Knowledge Base (KB) — a curated collection of 20 markdown documents covering technology stack selection, system architecture, data design, DevOps, security, and engineering quality best practices.
It serves as the retrieval source for 3 of our 7 agents in the Agentic Workflow:
AgentHow it uses this KBArchitect AgentRetrieves architecture patterns, tech stack comparisons, data modeling, security frameworks, and infrastructure best practicesCoder AgentRetrieves design patterns, Docker configs, testing strategies, and code-level best practicesQA AgentRetrieves OWASP Top 10, code review checklists, testing pyramid for systematic code and security review

Customer / Research / Product / Delivery Agents use the separate business_kb/ (not this folder).


Folder Structure
technical_kb/
├── README.md                                ← this file
│
├── 01_tech_stack/                           ← Technology stack selection (4 docs)
│   ├── 001_frontend_react_vue.md
│   ├── 002_backend_fastapi_express.md
│   ├── 003_database_postgres_mongo.md
│   └── 004_cloud_aws_gcp_supabase.md
│
├── 02_architecture/                         ← System architecture patterns (4 docs)
│   ├── 005_monolith_microservices.md
│   ├── 006_event_driven_architecture.md
│   ├── 007_api_design_rest_graphql.md
│   └── 008_caching_strategies.md
│
├── 03_data_design/                          ← Data modeling and database (3 docs)
│   ├── 009_data_modeling_basics.md
│   ├── 010_database_indexing.md
│   └── 011_data_migration_strategies.md
│
├── 04_devops/                               ← DevOps and deployment (3 docs)
│   ├── 012_docker_basics.md
│   ├── 013_ci_cd_pipelines.md
│   └── 014_observability_logging.md
│
├── 05_security/                             ← Security and compliance (3 docs)
│   ├── 015_owasp_top10_2024.md
│   ├── 016_authentication_authorization.md
│   └── 017_data_privacy_gdpr_pdpa.md
│
└── 06_quality/                              ← Engineering quality (3 docs)
    ├── 018_software_design_patterns.md
    ├── 019_testing_pyramid.md
    └── 020_code_review_best_practices.md
Total: 20 documents across 6 categories.

Document Format
Every document follows a standardized 7–10 section structure for consistent RAG retrieval:
markdown# [Title]

**Category**: [tech_stack / architecture / data_design / devops / security / quality]
**Source**: [Original sources]
**Use Case**: [Which agent uses it, when]

## 1. Overview
(150–200 word summary)

## 2. Key Concepts / Background
## 3. Detailed Comparison or Framework
## 4. When to Use Which / Best Practices
## 5. Modern Patterns / Variations
## 6. Example: Educational Coding App for Kids
(concrete example using the same demo domain as business KB)
## 7. Common Pitfalls
## 8. References
(real source URLs)
This structure mirrors the business_kb/ to keep RAG chunking consistent across both knowledge bases.

How the KB is Indexed
The indexing pipeline (handled by scripts/index_kb.py in the root project):

Load all .md files from this folder
Split each document into chunks (~800 chars with 100 char overlap)
Embed each chunk using Gemini text-embedding-004
Store in ChromaDB collection named technical
Metadata per chunk:

doc_id (e.g., 001_frontend_react_vue)
category (e.g., tech_stack, security, quality)
source_url (real URL from the document's References section)
agent_access (which agents can retrieve this — used for RBAC)




Retrieval Access Control (RBAC)
Each agent can only retrieve from documents tagged with its name:
pythondef retrieve(query, agent_name):
    return technical_kb.search(
        query=query,
        filter={"agent_access": {"$contains": agent_name}}
    )
Document CategoryAccessible by01_tech_stackArchitect, Coder02_architectureArchitect03_data_designArchitect, Coder04_devopsArchitect, Coder05_securityArchitect, Coder, QA06_qualityCoder, QA

Citation Mechanism
Every fact-bearing claim in agent outputs must reference its source:
json{
  "claim": "FastAPI generates OpenAPI documentation automatically based on Python type hints",
  "source_doc_id": "002_backend_fastapi_express",
  "source_chunk_id": "chunk_004"
}
Citations are validated downstream by:

QA Agent's verify_citations tool (LLM-as-judge verification)
RAGAS evaluation (Faithfulness metric)


Quality Checklist (for new docs)
When adding or updating documents, ensure:

 Filename follows NNN_topic_name.md pattern (3-digit zero-padded)
 All required sections present (Overview, Key Concepts, Comparison, When to Use, Example, Pitfalls, References)
 Real URLs in References section (no fabricated links)
 Version numbers and dates verified (e.g., GDPR effective May 25, 2018; React released 2013)
 Tool/framework names spelled correctly (FastAPI not Fast API; PostgreSQL not Postgres SQL; OWASP not OWSAP)
 At least one concrete example using educational coding app for kids 6-12 (consistent with business KB)
 1500-2000 words for technical docs (denser than business KB due to technical detail)
 Code blocks use proper syntax highlighting (python, yaml, ```sql, etc.)
 No fabricated benchmarks or unverifiable performance claims


Source Authority
All documents are synthesized from public, authoritative sources — paraphrased, not copied. Sources include:

Official documentation: FastAPI docs, PostgreSQL docs, Docker docs, OAuth.net, GraphQL.org, OpenTelemetry
Industry standards: OWASP Foundation, IETF RFCs (e.g., RFC 7519 for JWT), GDPR.eu, Singapore PDPC
Authoritative voices: Martin Fowler, Google Engineering Practices, Google SRE Book, AWS architecture guides
Tutorials and comparisons: BrowserStack, DataCamp, Refactoring.Guru, Use The Index Luke

References URLs in each document are real and verified at time of writing.

Adding New Documents
If you want to add a new doc:

Choose the appropriate category folder (or create new if needed)
Use the next sequential number (currently up to 020)
Follow the standardized section template
Verify all technical facts — version numbers, dates, framework features
Re-run indexing: python scripts/index_kb.py
Add a row to the inventory table below


Inventory
IDTitleCategoryWord CountUsed By001Frontend: React vs Vuetech_stack~1500Architect, Coder002Backend: FastAPI vs Expresstech_stack~1500Architect, Coder003Database: PostgreSQL vs MongoDBtech_stack~1800Architect, Coder004Cloud: AWS vs GCP vs Supabasetech_stack~1500Architect005Monolith vs Microservicesarchitecture~1500Architect006Event-Driven Architecturearchitecture~1500Architect007API Design: REST vs GraphQLarchitecture~1500Architect008Caching Strategiesarchitecture~1500Architect009Data Modeling Basicsdata_design~1500Architect, Coder010Database Indexingdata_design~1500Architect, Coder011Data Migration Strategiesdata_design~1500Architect012Docker Basicsdevops~1500Architect, Coder013CI/CD Pipelinesdevops~1800Architect, Coder014Observability and Loggingdevops~1800Architect015OWASP Top 10security~2000Architect, Coder, QA016Authentication & Authorizationsecurity~1800Architect, Coder017Data Privacy: GDPR/PDPA/COPPAsecurity~2000Architect, QA018Software Design Patternsquality~1800Coder, QA019Testing Pyramidquality~1500Coder, QA020Code Review Best Practicesquality~1500QA, Coder
Total: ~33,000 words across 20 documents.

Maintenance Notes

Re-index after any edit: chunks are pre-computed, edits won't propagate without re-running index_kb.py
Gemini embeddings are deterministic: same text → same embedding, so re-indexing is idempotent
Don't add files outside this folder structure: the indexer only walks technical_kb/**/*.md
Keep technical accuracy current: tech ecosystem changes fast; review version-specific claims annually


Special Considerations
Security & Privacy Docs (Category 05)
The security category documents (OWASP Top 10, Auth, GDPR/PDPA/COPPA) require extra accuracy verification because:

Wrong information can lead to compliance violations
These docs are referenced by QA Agent for actual code review
Penalties and dates must be exact

When updating these, always cross-check against official sources (owasp.org, gdpr.eu, ftc.gov).
AI/ML-specific topics
For our agentic AI application, we may want to add v2 documents on:

LangGraph state machine patterns
Vector database tradeoffs (ChromaDB vs Pinecone vs Weaviate)
LLM cost optimization strategies
Prompt engineering principles

These are not in v1 — keep current 20 docs stable for now.

Relationship to Business KB
business_kbtechnical_kbAudienceResearch / Product / QA / Delivery agentsArchitect / Coder / QA agentsTopicsProduct methodology, market analysis, business casesTech stack, architecture, data, security, qualityDoc count2020Total words~30,000~33,000StyleMethodology-heavy, frameworks, business casesTechnical-heavy, comparisons, code examplesQA Agent usesYes (PRD review, market validity)Yes (code security, testing standards)
QA Agent is the only agent with dual KB access — it pulls from both business_kb (PRD review checklists, business validation) and technical_kb (OWASP, testing pyramid, code review) depending on the artifact being reviewed.