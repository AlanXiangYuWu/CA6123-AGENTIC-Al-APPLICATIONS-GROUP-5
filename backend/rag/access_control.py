"""Role-based KB access mapping (draft 5.2)."""

AGENT_KB_ACCESS: dict[str, list[str]] = {
    "Research": ["business"],
    "Product": ["business"],
    "Architect": ["technical"],
    "Coder": ["technical"],
    "QA": ["business", "technical"],
    "Delivery": ["business", "technical"],
}
