"""
agent_assistant.py
==================
Agentic AI Engineering Assistant
AI-Powered Structural Intelligence System - Feature 6

=== PREREQUISITES ===
1. pip install -r agent_requirements.txt
2. ollama pull llama3 && ollama pull nomic-embed-text
3. python embeddings/build_vectorstore.py  (one-time)

=== RUN ===
   python agent_assistant.py

=== API INTEGRATION ===
   from agent_assistant import run_query
   response = run_query("Summarize structural health")
"""

import re
import sys
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from agent_config import (
    LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE,
    EMBEDDING_MODEL, FAISS_INDEX_DIR,
    AGENT_MAX_ITERATIONS, VERBOSE_AGENT,
)
from tools.health_analyzer         import analyze_infrastructure_health
from tools.risk_explainer          import explain_high_risk
from tools.maintenance_prioritizer import prioritize_maintenance
from tools.anomaly_timeline        import inspect_anomaly_timeline
from tools.health_summary          import generate_health_summary

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------
TOOLS = {
    "analyze_infrastructure_health": {
        "fn": analyze_infrastructure_health,
        "description": (
            "Fleet-level health overview: mean/max anomaly scores, risk scores, "
            "behavioral state clusters across all datasets. "
            "Use for: 'how are the bridges?', 'infrastructure overview'."
        ),
    },
    "explain_high_risk": {
        "fn": explain_high_risk,
        "description": (
            "Explains WHY an asset has high risk (anomaly breakdown, behavioral shift, "
            "sensor context, recommendation). Input: asset name or ID like 'B001'. "
            "Use for: 'why was X flagged?', 'what caused the high risk?'."
        ),
    },
    "prioritize_maintenance": {
        "fn": prioritize_maintenance,
        "description": (
            "Ranks all assets by Predicted_Risk_Score into Critical / High / Routine "
            "tiers with recommended actions. "
            "Use for: 'what maintenance is needed?', 'maintenance schedule this month'."
        ),
    },
    "inspect_anomaly_timeline": {
        "fn": inspect_anomaly_timeline,
        "description": (
            "Shows timestamped anomaly alert events and burst clusters. "
            "Use for: 'show latest anomalies', 'when were alerts triggered?'."
        ),
    },
    "generate_health_summary": {
        "fn": generate_health_summary,
        "description": (
            "Full per-asset structural health report: anomaly trends, behavioral drift, "
            "risk levels, recommendations, fleet summary. "
            "Use for: 'summarize health', 'full report', 'abnormal vibration patterns'."
        ),
    },
}

# ---------------------------------------------------------------------------
# FAISS Retriever (optional RAG context)
# ---------------------------------------------------------------------------
_retriever = None


def _load_retriever():
    global _retriever
    if _retriever is not None:
        return _retriever
    if not FAISS_INDEX_DIR.exists():
        return None
    try:
        from langchain_ollama import OllamaEmbeddings
        from langchain_community.vectorstores import FAISS

        emb = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=LLM_BASE_URL)
        vs = FAISS.load_local(str(FAISS_INDEX_DIR), emb, allow_dangerous_deserialization=True)
        _retriever = vs.as_retriever(search_kwargs={"k": 3})
        print("[AGENT] FAISS vector store loaded.")
        return _retriever
    except Exception as e:
        logger.warning(f"FAISS retriever unavailable: {e}")
        return None


# ---------------------------------------------------------------------------
# LLM (lazy init)
# ---------------------------------------------------------------------------
_llm = None


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm
    try:
        from langchain_ollama import ChatOllama
        _llm = ChatOllama(model=LLM_MODEL, base_url=LLM_BASE_URL, temperature=LLM_TEMPERATURE)
        print(f"[AGENT] LLM ready: {LLM_MODEL}")
        return _llm
    except Exception as e:
        logger.error(f"Could not load LLM: {e}")
        return None


# ---------------------------------------------------------------------------
# Custom ReAct loop (avoids broken langchain.agents import)
# ---------------------------------------------------------------------------
def _build_system_prompt() -> str:
    tools_desc = "\n".join(f"- {n}: {info['description']}" for n, info in TOOLS.items())
    return f"""You are a specialized AI Engineering Assistant for a Structural Intelligence System monitoring national infrastructure.

You interpret AI-generated structural monitoring outputs (anomaly scores, risk predictions, behavioral shifts) and provide clear, actionable engineering insights. Always use a tool to retrieve real data before answering.

AVAILABLE TOOLS:
{tools_desc}

Follow this format EXACTLY:
Thought: [reasoning about which tool to call]
Action: [exact tool name]
Action Input: [input string for the tool]

After receiving the Observation, respond:
Thought: [interpretation of the result]
Final Answer: [engineering response with specific numbers and recommendations]

Rules:
- Call at least one tool before Final Answer.
- Never invent numbers — only report what tools return.
- Always include an engineering recommendation.
"""


def _parse_action(text: str):
    """Returns (action, action_input, final_answer_text_or_None)."""
    if "Final Answer:" in text:
        return None, None, text.split("Final Answer:", 1)[1].strip()

    a = re.search(r"Action:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    i = re.search(r"Action Input:\s*(.+?)(?:\n|Action:|Thought:|$)", text, re.IGNORECASE | re.DOTALL)
    return (
        a.group(1).strip() if a else None,
        i.group(1).strip() if i else "",
        None,
    )


def _match_tool(name: str):
    """Fuzzy-matches user-supplied tool name to registry key."""
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    for t in TOOLS:
        if key == t or key in t or t in key:
            return t
    return None


def _run_react_loop(query: str, context: str = "") -> str:
    llm = _get_llm()
    if llm is None:
        return _direct_tool_fallback(query)

    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    messages = [SystemMessage(content=_build_system_prompt())]
    user_msg = query if not context else f"{query}\n\n[Context]:\n{context}"
    messages.append(HumanMessage(content=user_msg))

    last_observation = ""
    for step in range(AGENT_MAX_ITERATIONS):
        try:
            resp = llm.invoke(messages)
            text = resp.content if hasattr(resp, "content") else str(resp)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            break

        if VERBOSE_AGENT:
            print(f"\n--- Agent Step {step + 1} ---\n{text}\n")

        action, action_input, final = _parse_action(text)

        if final is not None:
            return final

        if action is None:
            # No structured output — return text if it looks substantial
            return text if len(text) > 200 else _direct_tool_fallback(query)

        tool_key = _match_tool(action)
        if tool_key is None:
            observation = f"Unknown tool '{action}'. Available: {', '.join(TOOLS)}"
        else:
            if VERBOSE_AGENT:
                print(f"[TOOL] {tool_key}({action_input!r})")
            try:
                observation = TOOLS[tool_key]["fn"](action_input)
            except Exception as e:
                observation = f"Tool error: {e}"

        last_observation = observation
        messages.append(AIMessage(content=text))
        messages.append(HumanMessage(
            content=f"Observation:\n{observation}\n\nNow write your Final Answer based on the data above."
        ))

    # Exhausted iterations — return last tool output
    return last_observation if last_observation else _direct_tool_fallback(query)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def run_query(query: str) -> str:
    """Main interface — call from CLI, Streamlit, or FastAPI."""
    # RAG context
    retriever = _load_retriever()
    context = ""
    if retriever:
        try:
            docs = retriever.invoke(query)
            context = "\n".join(d.page_content for d in docs)
        except Exception:
            pass

    return _run_react_loop(query, context)


# ---------------------------------------------------------------------------
# Keyword fallback (works without Ollama)
# ---------------------------------------------------------------------------
def _direct_tool_fallback(query: str) -> str:
    q = query.lower()
    print("[FALLBACK] Routing directly to analysis tool...\n")
    if any(k in q for k in ["priorit", "maintenance", "schedule", "urgent", "month"]):
        return prioritize_maintenance(query)
    if any(k in q for k in ["why", "flagged", "high risk", "explain", "cause"]):
        return explain_high_risk(query)
    if any(k in q for k in ["anomaly", "alert", "timeline", "event", "latest", "show"]):
        return inspect_anomaly_timeline(query)
    if any(k in q for k in ["summary", "report", "health", "vibration", "structure", "summarize"]):
        return generate_health_summary(query)
    return analyze_infrastructure_health(query)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
EXAMPLE_QUERIES = [
    "Summarize the structural health of monitored assets.",
    "What maintenance action should be prioritized this month?",
    "Show the latest anomaly events.",
    "Which structures show abnormal vibration patterns?",
    "Why was a structure flagged as high risk?",
]


def main():
    print("=" * 65)
    print("  AI-POWERED STRUCTURAL INTELLIGENCE SYSTEM")
    print("  Agentic AI Engineering Assistant  v1.0")
    print("=" * 65)
    print(f"\nLLM  : {LLM_MODEL}  |  Embeddings: {EMBEDDING_MODEL}\n")
    print("Example queries:")
    for i, q in enumerate(EXAMPLE_QUERIES, 1):
        print(f"  {i}. {q}")
    print("\nType a number (1-5) for an example, or type your query.")
    print("Type 'quit' to exit.\n" + "─" * 65 + "\n")

    while True:
        try:
            user_input = input("Engineer Query >> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[AGENT] Goodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("[AGENT] Session ended.")
            break
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(EXAMPLE_QUERIES):
                user_input = EXAMPLE_QUERIES[idx]
                print(f"[Running]: {user_input}\n")

        print("\n[AGENT] Processing...\n")
        print("─" * 65)
        print(run_query(user_input))
        print("─" * 65 + "\n")


if __name__ == "__main__":
    main()
