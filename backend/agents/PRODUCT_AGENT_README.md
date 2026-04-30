# Product Agent README

This document describes the implementation of `product_agent` in `backend/agents/product.py`.

## Purpose

`product_agent` generates a structured PRD JSON from:
- `project_brief`
- selected fields from `research_report`:
  - `research_findings`
  - `goal_status[].resolved_answers`
  - `unresolved_gaps`
- internal RAG context from the business knowledge base

The agent uses **internal Milvus RAG only** and does **not** perform any web search.

## Input / Output Contract

Input from `ProjectState`:
- `project_brief` (dict)
- `research_report` (dict, but only selected fields are consumed as above)

Output written to `ProjectState`:
- `prd` (dict)
- `messages` (includes `[Product] PRD ready, rag_docs=<n>`)
- `trace` (appends `"product"`)

## Internal Flow

0. Select research input
   - `_select_research_input(...)`
   - Extracts only:
     - `research_findings`
     - flattened `goal_status[].resolved_answers`
     - `unresolved_gaps`

1. Build RAG queries from brief + selected research fields
   - Primary: `_build_rag_queries_with_llm(...)` (LLM-generated queries)
   - Fallback: `_build_rag_queries_fallback(...)` (deterministic templates)
   - Queries focus on positioning, feature prioritization/MVP, user flow, and metrics.

2. Retrieve internal docs
   - `_retrieve_rag_context(...)`
   - Calls `get_kb().retrieve(query, agent="Product", k=3)`.
   - Access scope is controlled by `backend/rag/access_control.py`:
     - `Product -> ["business"]`

3. Prepare context for generation
   - `_format_rag_context(...)`
   - Formats evidence as `[source_doc_id] text...` blocks.

4. Generate PRD with LLM
   - Sends `BRIEF`, `RESEARCH`, and `INTERNAL_RAG_CONTEXT` to the model.
   - Requires JSON output with keys:
     - `positioning`
     - `user_flows`
     - `features`
     - `non_functional_requirements`
     - `success_metrics`

5. Fallback for robustness
   - If model JSON is invalid, `_fallback_prd(...)` returns a deterministic PRD skeleton.

## Important Constraints

- No web search tools are called in this agent.
- No external URL fetch is used.
- All retrieval evidence comes from local/internal RAG (`backend/rag/kb.py`).

## Notes

- The prompt asks the model to reference source markers like `[doc_id]` when useful.
- The fallback output is intentionally minimal but schema-stable for downstream agents.
