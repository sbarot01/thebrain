"""
Orchestrator for OurBrain.

The orchestrator is a Claude agent whose tools are the three specialized 
sub-agents. For any user question, it decides which sub-agent(s) to consult, 
calls them (each running its own agentic loop with MCP tools), and 
synthesizes their answers.

Same agentic loop pattern as run_agent — different tool executor.
"""

from anthropic import Anthropic
from agents.mcp_host import OurBrainMCPHost
from agents.sub_agents import (
    run_nutrition_agent,
    run_planner_agent,
    run_suggestion_agent,
)


ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator for OurBrain, a household intelligence system.

Your job: route the user's question to the right specialist sub-agent(s) and
synthesize their answers into one coherent response.

You have three specialists available as tools:
  - consult_nutrition_agent: nutritional patterns, protein/cuisine variety, dietary balance
  - consult_planner_agent: planning upcoming meals using history, groceries, and preferences
  - consult_suggestion_agent: recommending new meals, finding gaps, surfacing ideas

ROUTING RULES:
- Single-domain question → call ONE sub-agent
- Compound question (e.g. "plan this week AND check it's balanced") → call MULTIPLE sub-agents
- Pass the user's question to the sub-agent faithfully — keep their context
- If no sub-agent is needed (e.g. greetings, meta questions), respond directly

SYNTHESIS RULES:
- Don't repeat every detail from the sub-agents. Lead with the answer.
- For multi-agent answers, weave the perspectives together — don't list them as separate sections
- The user is reading on their phone. Be concise.
"""


# Tool schemas for the orchestrator. Each tool corresponds to one sub-agent.
ORCHESTRATOR_TOOLS = [
    {
        "name": "consult_nutrition_agent",
        "description": (
            "Consult the Nutrition Agent for analysis of eating patterns, "
            "protein/cuisine variety, and dietary balance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The nutrition-related question to ask."
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "consult_planner_agent",
        "description": (
            "Consult the Planner Agent to plan upcoming meals based on history, "
            "preferences, and the grocery list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The meal-planning question to ask."
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "consult_suggestion_agent",
        "description": (
            "Consult the Suggestion Agent for new meal recommendations, gap "
            "analysis, or fuzzy/qualitative meal ideas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The recommendation or suggestion question to ask."
                }
            },
            "required": ["question"]
        }
    }
]


# Map tool names to actual sub-agent functions
SUB_AGENT_DISPATCH = {
    "consult_nutrition_agent": run_nutrition_agent,
    "consult_planner_agent": run_planner_agent,
    "consult_suggestion_agent": run_suggestion_agent,
}


async def run_orchestrator(
    host: OurBrainMCPHost,
    anthropic_client: Anthropic,
    model: str,
    user_question: str,
    max_turns: int = 4,
    verbose: bool = True,
) -> str:
    """
    Route the user's question to relevant sub-agent(s) and synthesize.

    Same agentic loop as run_agent. The difference: when this orchestrator
    calls a 'tool', a full sub-agent loop runs underneath with its own 
    MCP tools. Two-level orchestration.
    """
    if verbose:
        print(f"\n=== ORCHESTRATOR ===")
        print(f"Question: {user_question}\n")

    messages = [{"role": "user", "content": user_question}]

    for turn in range(max_turns):
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=2048,
            system=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=ORCHESTRATOR_TOOLS,
            messages=messages,
        )

        if verbose:
            print(f"[orchestrator turn {turn + 1}: stop_reason={response.stop_reason}]")

        # Case 1: orchestrator is done synthesizing
        if response.stop_reason == "end_turn":
            text_blocks = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_blocks)

        # Case 2: orchestrator wants to consult sub-agent(s)
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    sub_agent_fn = SUB_AGENT_DISPATCH.get(block.name)
                    if sub_agent_fn is None:
                        result = f"[unknown sub-agent: {block.name}]"
                    else:
                        if verbose:
                            print(f"\n--- Routing to {block.name} ---")
                        sub_question = block.input.get("question", user_question)
                        # Each sub-agent runs its own agentic loop here
                        result = await sub_agent_fn(
                            host=host,
                            anthropic_client=anthropic_client,
                            model=model,
                            user_question=sub_question,
                            verbose=verbose,
                        )
                        if verbose:
                            print(f"--- {block.name} done ---\n")

                    if not result or not result.strip():
                        result = "(no answer returned)"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            if not tool_results:
                return "[stop_reason was tool_use but no tool calls were found]"

            messages.append({"role": "user", "content": tool_results})
            continue

        return f"[unexpected stop_reason: {response.stop_reason}]"

    return "[hit max_turns without a final answer]"
