from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .tools import tools

# LLM — Claude Haiku via AWS Bedrock


def _build_llm() -> ChatBedrock:
    return ChatBedrock(
        model_id="anthropic.claude-haiku-20240307-v1:0",
        model_kwargs={
            "temperature": 0,        # deterministic tool use
            "max_tokens": 2048,
        },
    )


# ---------------------------------------------------------------------------
# Agent — one global instance with MemorySaver (in-memory checkpointer)
# Each session_id gets its own isolated conversation thread automatically.
# Swap MemorySaver for SqliteSaver or RedisSaver for persistent memory.
# ---------------------------------------------------------------------------

_checkpointer = MemorySaver()

_agent = create_react_agent(
    model=_build_llm(),
    tools=tools,
    checkpointer=_checkpointer,
)


# Public interface

def run_agent(message: str, session_id: str = "default") -> dict:
    """
    Run the agent for a given message and session.

    Returns:
        {
            "answer": str,
            "session_id": str,
        }
    """
    config = {"configurable": {"thread_id": session_id}}

    result = _agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )

    # Last message in the list is the AI's final answer
    answer = result["messages"][-1].content
    return {"answer": answer, "session_id": session_id}


def get_history(session_id: str) -> list[dict]:
    """
    Return the conversation history for a session as a list of
    {"role": "user"|"assistant", "content": str} dicts.
    """
    config = {"configurable": {"thread_id": session_id}}
    state = _agent.get_state(config)
    messages = state.values.get("messages", [])

    history = []
    for msg in messages:
        role = getattr(msg, "type", None)
        if role == "human":
            history.append({"role": "user", "content": msg.content})
        elif role == "ai":
            # Skip empty AI messages (tool-call intermediates)
            if msg.content:
                history.append({"role": "assistant", "content": msg.content})
    return history


def clear_history(session_id: str) -> None:
    """
    Clear conversation memory for a session by updating state to empty messages.
    """
    config = {"configurable": {"thread_id": session_id}}
    _agent.update_state(config, {"messages": []})
