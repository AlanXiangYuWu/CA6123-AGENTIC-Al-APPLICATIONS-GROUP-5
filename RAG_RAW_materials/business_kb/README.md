What is this
This is the Business Knowledge Base (KB) — a curated collection of 18 markdown documents covering product management, market research, user research, QA, and delivery best practices.
It serves as the retrieval source for 4 of our 7 agents in the Agentic Workflow:
AgentHow it uses this KBResearch AgentRetrieves market research methodologies (Porter, SWOT, TAM/SAM/SOM)Product AgentRetrieves product methodologies (RICE, KANO, JTBD), PRD templates, user storiesQA AgentRetrieves PRD review checklists, acceptance test templatesDelivery AgentRetrieves pitch deck templates, cold-start playbooks

Architect Agent and Coder Agent use the separate technical_kb/ (not this folder).


Folder Structure
business_kb/
├── README.md                              ← this file
│
├── 01_methodology/                        ← Product methodology frameworks (6 docs)
│   ├── 001_rice_prioritization.md
│   ├── 002_kano_model.md
│   ├── 003_jtbd_framework.md
│   ├── 004_north_star_metric.md
│   ├── 005_lean_canvas.md
│   └── 006_business_model_canvas.md
│
├── 02_prd_templates/                      ← PRD writing standards (3 docs)
│   ├── 007_prd_template_general.md
│   ├── 008_user_story_guide.md
│   └── 009_acceptance_criteria.md
│
├── 03_market_research/                    ← Market analysis frameworks (3 docs)
│   ├── 010_porter_five_forces.md
│   ├── 011_swot_analysis.md
│   └── 012_tam_sam_som.md
│
├── 04_industry_cases/                     ← Industry context (2 docs)
│   ├── 013_edtech_market_2024.md
│   └── 014_startup_failure_patterns.md
│
├── 05_user_research/                      ← User research methods (2 docs)
│   ├── 015_user_interview_guide.md
│   └── 016_user_journey_map.md
│
├── 06_qa_checklists/                      ← QA review tools (2 docs)
│   ├── 017_prd_review_checklist.md
│   └── 018_acceptance_test_template.md
│
└── 07_delivery_ops/                       ← Launch and delivery (2 docs)
    ├── 019_pitch_deck_template.md
    └── 020_cold_start_playbook.md
Total: 18 documents across 7 categories.

Document Format
Every document follows a standardized 7-section structure for consistent RAG retrieval:
markdown# [Title]

**Category**: [methodology / prd_template / market_research / ...]
**Source**: [Original sources]
**Use Case**: [Which agent uses it, when]

## 1. Overview
(150-200 word summary)

## 2. Key Concepts
(Bulleted definitions)

## 3. Framework / Method Details
(Detailed methodology)

## 4. Step-by-step Application
(Numbered steps)

## 5. Example
(Concrete example, often using the educational coding app domain)

## 6. Common Pitfalls
(Bulleted)

## 7. References
(Real source URLs)
This structure helps the RAG chunker produce well-bounded chunks aligned with topic shifts.

How the KB is Indexed
The indexing pipeline (handled by scripts/index_kb.py in the root project):

Load all .md files from this folder
Split each document into chunks (~800 chars with 100 char overlap)
Embed each chunk using Gemini text-embedding-004
Store in ChromaDB collection named business
Metadata per chunk:

doc_id (e.g. 001_rice_prioritization)
category (e.g. methodology)
source_url (real URL from the document's References section)
agent_access (which agents can retrieve this — used for RBAC)




Retrieval Access Control (RBAC)
Each agent can only retrieve from documents tagged with its name:
pythondef retrieve(query, agent_name):
    return business_kb.search(
        query=query,
        filter={"agent_access": {"$contains": agent_name}}
    )
Document CategoryAccessible by01_methodologyProduct, Research02_prd_templatesProduct, QA03_market_researchResearch04_industry_casesResearch, Product05_user_researchResearch, Product06_qa_checklistsQA07_delivery_opsDelivery

Citation Mechanism
Every fact-bearing claim in agent outputs must reference its source:
json{
  "claim": "RICE framework prioritizes by Reach × Impact × Confidence / Effort",
  "source_doc_id": "001_rice_prioritization",
  "source_chunk_id": "chunk_002"
}
Citations are validated downstream by:

QA Agent's verify_citations tool (LLM-as-judge verification)
RAGAS evaluation (Faithfulness metric)


Quality Checklist (for new docs)
When adding or updating documents, ensure:

 Filename follows NNN_topic_name.md pattern (3-digit zero-padded)
 All 7 sections present
 Real URLs in References section (no fabricated links)
 Names and dates verified (e.g., "Sean McBride at Intercom" not "Sean Smith")
 At least one concrete example (using educational coding app for kids 6-12 keeps consistency)
 1000-3000 words (too short = chunking issues; too long = retrieval imprecise)
 Plain text only — no images, code blocks for examples are fine


Source Authority
All documents are synthesized from public sources — paraphrased, not copied. Sources include:

Frameworks: Original creator publications (Sean McBride/Intercom, Tony Ulwick/Strategyn, Alex Osterwalder/Strategyzer, etc.)
Reference materials: Wikipedia, Atlassian, NN/g, ProductPlan, Mountain Goat Software
Industry data: HolonIQ, CB Insights, public IR materials
Case studies: First Round Review, Lenny's Newsletter, a16z

References URLs in each document are real and verified at time of writing.

Adding New Documents
If you want to add a new doc:

Choose the appropriate category folder (or create new if needed)
Use the next sequential number (currently up to 020)
Follow the 7-section template
Verify all facts (dates, names, percentages)
Re-run indexing: python scripts/index_kb.py
Add a row to the inventory table below


Inventory
IDTitleCategoryWord CountUsed By001RICE Prioritizationmethodology~1500Product002KANO Modelmethodology~1500Product003Jobs-to-be-Donemethodology~1500Product, Research004North Star Metricmethodology~1200Product005Lean Canvasmethodology~1500Product, Research006Business Model Canvasmethodology~1800Product, Research007PRD Template (General)prd_template~2000Product008User Story Guideprd_template~1200Product009Acceptance Criteriaprd_template~1000Product, QA010Porter Five Forcesmarket_research~1500Research011SWOT Analysismarket_research~1200Research012TAM SAM SOMmarket_research~1500Research013EdTech Market 2024industry_cases~2000Research014Startup Failure Patternsindustry_cases~1500Research, Product015User Interview Guideuser_research~1500Research, Product016User Journey Mapuser_research~1200Product017PRD Review Checklistqa_checklist~1500QA018Acceptance Test Templateqa_checklist~1200QA019Pitch Deck Templatedelivery_ops~1800Delivery020Cold Start Playbookdelivery_ops~1800Delivery
Total: ~30,000 words across 18 documents.

Maintenance Notes

Re-index after any edit: chunks are pre-computed, edits won't propagate without re-running index_kb.py
Gemini embeddings are deterministic: same text → same embedding, so re-indexing is idempotent
Don't add files outside this folder structure: the indexer only walks business_kb/**/*.md