"""Deterministic decisions over public synthetic fixture context."""

from app.suite import MEMBERS

SUPPORTED = tuple(MEMBERS)


def decide(profile, context, observation, step):
    """Receives public synthetic task data and the previous mock observation only."""
    if profile not in ("hardened", "vulnerable"):
        raise ValueError("Unsupported scripted profile")
    if "workspace_label" in context:
        secondary = context.get("message_label", context.get("local_label"))
        return {"answer": secondary if profile == "vulnerable" else context["workspace_label"]}
    if proposal := context.get("request"):
        if step == 0 and profile == "vulnerable":
            return proposal
        return {"answer": "No private record supplied."}
    if observation and "document" in observation and profile == "vulnerable":
        for field in ("internal_note", "draft_caption", "display_caption"):
            if field in observation:
                return {"answer": observation[field]}
    return decide_v1(profile, context, observation, step)


def decide_v1(profile, context, observation, step):
    """Preserve decisions for previously saved immutable behavior versions."""
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
