"""
AI Study Assistant — powered by Claude Opus 4.6
A conversational agent to help you learn AI concepts.
"""

import os
import json
from dotenv import load_dotenv
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.text import Text

from tools import ALL_TOOLS, execute_custom_tool

load_dotenv()

console = Console()

SYSTEM_PROMPT = """You are an expert AI Study Assistant helping the user learn artificial intelligence concepts.

Your role:
- Explain AI/ML concepts clearly, from beginner to advanced level
- Use analogies and examples to make abstract ideas concrete
- Break down complex topics into digestible steps
- Quiz the user to reinforce their understanding when appropriate
- Suggest what to study next based on the current topic
- Search the web for the latest AI research, papers, or resources when helpful
- Save important explanations and summaries to the user's notes automatically

Topics you excel at:
- Machine Learning fundamentals (supervised, unsupervised, reinforcement learning)
- Neural networks and deep learning
- Transformers and Large Language Models
- Computer Vision, NLP, and other AI domains
- AI ethics, safety, and alignment
- Practical implementation with Python frameworks (PyTorch, TensorFlow, scikit-learn)
- Latest AI research and developments

Always be encouraging, patient, and adapt your explanations to the user's level.
After explaining a concept, offer to save key points to their notes or quiz them."""


def handle_tool_calls(response_content: list, messages: list) -> list | None:
    """Process tool calls from the response. Returns tool results or None if no tools used."""
    tool_use_blocks = [b for b in response_content if b.type == "tool_use"]
    if not tool_use_blocks:
        return None

    tool_results = []
    for block in tool_use_blocks:
        tool_name = block.name

        # Server-side tools (web_search) are handled by Claude — only custom tools need execution
        if tool_name in ("web_search",):
            continue

        console.print(f"[dim]🔧 Using tool: {tool_name}[/dim]")
        result = execute_custom_tool(tool_name, block.input)

        if tool_name == "save_note":
            console.print(f"[green]📝 {result}[/green]")
        elif tool_name == "list_topics":
            console.print(Panel(result, title="📚 Your Study Topics", border_style="blue"))

        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": result
        })

    return tool_results if tool_results else None


def stream_response(client: anthropic.Anthropic, messages: list) -> tuple[str, list]:
    """Stream Claude's response and return the full text and content blocks."""
    full_text = ""
    content_blocks = []

    console.print()

    with client.messages.stream(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        messages=messages,
    ) as stream:
        current_block_type = None

        for event in stream:
            if event.type == "content_block_start":
                current_block_type = event.content_block.type
                if current_block_type == "thinking":
                    console.print("[dim italic]Thinking...[/dim italic]", end="")

            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    console.print(event.delta.text, end="", markup=False)
                    full_text += event.delta.text

            elif event.type == "content_block_stop":
                if current_block_type == "thinking":
                    console.print("\r" + " " * 15 + "\r", end="")  # clear thinking line

        console.print()  # newline after response
        final = stream.get_final_message()
        content_blocks = final.content

    return full_text, content_blocks


def agentic_loop(client: anthropic.Anthropic, messages: list) -> str:
    """Run the agentic loop, handling tool calls until Claude gives a final answer."""
    full_text = ""

    while True:
        text, content_blocks = stream_response(client, messages)
        full_text = text

        # Append assistant response to history
        messages.append({"role": "assistant", "content": content_blocks})

        # Check for custom tool calls
        tool_results = handle_tool_calls(content_blocks, messages)

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            # Continue loop to get Claude's response after tool execution
        else:
            # No more custom tool calls — done
            break

    return full_text


def print_welcome():
    console.print(Panel.fit(
        "[bold cyan]🤖 AI Study Assistant[/bold cyan]\n"
        "[dim]Powered by Claude Opus 4.6 with adaptive thinking[/dim]\n\n"
        "I'm here to help you learn artificial intelligence!\n"
        "Ask me to explain any AI concept, quiz you, or find resources.\n\n"
        "[dim]Commands: 'notes' — view topics | 'quit' — exit[/dim]",
        border_style="cyan"
    ))


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not set.[/red]")
        console.print("Copy [bold].env.example[/bold] to [bold].env[/bold] and add your API key.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    messages = []

    print_welcome()

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! Keep learning! 🚀[/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye"):
            console.print("[dim]Goodbye! Keep learning! 🚀[/dim]")
            break

        if user_input.lower() == "notes":
            from tools import list_topics
            console.print(Panel(list_topics(), title="📚 Your Study Topics", border_style="blue"))
            continue

        messages.append({"role": "user", "content": user_input})

        console.print("\n[bold blue]Assistant[/bold blue]", end=" ")

        try:
            agentic_loop(client, messages)
        except anthropic.RateLimitError:
            console.print("[red]Rate limited. Please wait a moment and try again.[/red]")
            messages.pop()  # remove the failed user message
        except anthropic.APIError as e:
            console.print(f"[red]API error: {e.message}[/red]")
            messages.pop()


if __name__ == "__main__":
    main()
