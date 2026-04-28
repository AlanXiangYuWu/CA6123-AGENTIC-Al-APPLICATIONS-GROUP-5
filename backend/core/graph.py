"""LangGraph assembly: nodes + conditional edges + checkpointer."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.agents.architect import architect_agent
from backend.agents.coder import coder_agent
from backend.agents.customer import customer_agent
from backend.agents.delivery import delivery_agent
from backend.agents.orchestrator import orchestrator_router, qa_post
from backend.agents.product import product_agent
from backend.agents.qa import qa_agent
from backend.agents.research import research_agent
from backend.core.state import ProjectState

ROUTE_MAP = {
    "customer": "customer",
    "research": "research",
    "product": "product",
    "architect": "architect",
    "coder": "coder",
    "qa": "qa",
    "delivery": "delivery",
    "__end__": END,
}


def build_graph():
    g = StateGraph(ProjectState)

    g.add_node("customer", customer_agent)
    g.add_node("research", research_agent)
    g.add_node("product", product_agent)
    g.add_node("architect", architect_agent)
    g.add_node("coder", coder_agent)
    g.add_node("qa", qa_agent)
    g.add_node("qa_post", qa_post)
    g.add_node("delivery", delivery_agent)

    for node in ("customer", "research", "product", "architect", "coder", "delivery"):
        g.add_conditional_edges(node, orchestrator_router, ROUTE_MAP)

    g.add_edge("qa", "qa_post")
    g.add_conditional_edges("qa_post", orchestrator_router, ROUTE_MAP)

    g.add_edge(START, "customer")
    return g.compile(checkpointer=MemorySaver())


_app = None


def get_app():
    global _app
    if _app is None:
        _app = build_graph()
    return _app
