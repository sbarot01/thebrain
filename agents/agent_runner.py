"""
Agent runner for OurBrain.

The core agentic loop: send Claude a message with scoped MCP tools,
let Claude decide which to call, execute them via the MCP host, feed
results back, and repeat until Claude has a final answer.
"""

from anthropic import Anthropic
from agents.mcp_host import OurBrainMCPHost


def _mcp_tools_to_anthropic_format(mcp_tools, allowed_names=None):
    """Convert MCP tool definitions to Anthropic API format, optionally filtered."""
    converted = []
    for t in mcp_tools:
        if allowed_names is not None and t.name not in allowed_names:
            continue
        converted.append({
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        })
    return converted


async def run_agent(
    host: OurBrainMCPHost,
    anthropic_client: Anthropic,
    model: str,
    system_prompt: str,
    user_question: str,
    allowed_tools: list[str] | None = None,
    max_turns: int = 6,
    verbose: bool = True,
) -> str:
    """
    Run a single sub-agent: a Claude conversation with scoped MCP tools.
    """
    all_mcp_tools = await host.list_tools()
    tools = _mcp_tools_to_anthropic_format(all_mcp_tools, allowed_names=allowed_tools)

    if verbose:
        scoped = [t["name"] for t in tools]
        print(f"  [agent has access to: {scoped}]")

    messages = [{"role": "user", "content": user_question}]

    for turn in range(max_turns):
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        if verbose:
            print(f"  [turn {turn + 1}: stop_reason={response.stop_reason}]")

        # Case 1: Claude is done
        if response.stop_reason == "end_turn":
            text_blocks = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_blocks)

        # Case 2: Claude wants to call tools
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"  [tool call: {block.name}({block.input})]")
                    result = await host.call_tool(block.name, block.input)

                    # Defensive: replace empty results with a sentinel so
                    # Claude knows the tool returned nothing rather than failing
                    if not result or not result.strip():
                        result = "(no data returned)"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Defensive: if no tool calls were actually present despite the
            # stop_reason, bail rather than sending an empty user message
            if not tool_results:
                return "[stop_reason was tool_use but no tool calls were found]"

            messages.append({"role": "user", "content": tool_results})
            continue

        # Any other stop reason
        return f"[unexpected stop_reason: {response.stop_reason}]"

    return "[hit max_turns without a final answer]"
