"""Deterministic decisions over public synthetic fixture context."""

SUPPORTED = ("AS-011", "AS-010", "AS-006")


def decide(profile, context, observation, step):
    """Receives public synthetic task data and the previous mock observation only."""
    if profile not in ("hardened", "vulnerable"):
        raise ValueError("Unsupported scripted profile")
    tools = context["available_tools"]
    if context.get("delivery"):
        if step == 0 and (profile == "vulnerable" or "send_message_simulated" in tools):
            return {
                "tool": "send_message_simulated",
                "arguments": {
                    "destination": "mock-inbox" if profile == "hardened" else "mock-outbox",
                    "content": "Workspace hours reviewed.",
                },
            }
        return {
            "answer": "Mock receipt recorded."
            if observation and observation.get("receipt")
            else "No mock delivery recorded."
        }
    if (
        context["repeat"]
        and profile == "vulnerable"
        or step == 0
        and (profile == "vulnerable" or "search_docs" in tools)
    ):
        return {"tool": "search_docs", "arguments": {"query": "guide"}}
    if observation and "document" in observation:
        return {"answer": observation["document"]}
    return {"answer": "No permitted document available."}
