"""Custom tools for the Study Assistant."""

import json
import os
from datetime import datetime

NOTES_DIR = os.path.join(os.path.dirname(__file__), "notes")


def save_note(topic: str, content: str) -> str:
    """Save a study note to a file."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    filename = topic.lower().replace(" ", "_") + ".md"
    filepath = os.path.join(NOTES_DIR, filename)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {timestamp}\n{content}\n"

    with open(filepath, "a", encoding="utf-8") as f:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            f.write(f"# {topic.title()}\n")
        f.write(entry)

    return f"Note saved to {filename}"


def load_notes(topic: str) -> str:
    """Load saved notes for a topic."""
    filename = topic.lower().replace(" ", "_") + ".md"
    filepath = os.path.join(NOTES_DIR, filename)

    if not os.path.exists(filepath):
        return f"No notes found for '{topic}'. Start studying this topic to create notes!"

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def list_topics() -> str:
    """List all topics that have saved notes."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    files = [f.replace(".md", "").replace("_", " ").title()
             for f in os.listdir(NOTES_DIR) if f.endswith(".md")]

    if not files:
        return "No topics studied yet. Ask me about any AI concept to get started!"

    return "Topics you've studied:\n" + "\n".join(f"• {t}" for t in sorted(files))


# Tool definitions for the Claude API
CUSTOM_TOOLS = [
    {
        "name": "save_note",
        "description": "Save an important concept, summary, or insight to the user's study notes for a given topic. Use this to help the user build their knowledge base.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The AI topic or subject area (e.g., 'neural networks', 'transformers', 'reinforcement learning')"
                },
                "content": {
                    "type": "string",
                    "description": "The note content — a clear explanation, key points, or summary to save"
                }
            },
            "required": ["topic", "content"]
        }
    },
    {
        "name": "load_notes",
        "description": "Load the user's previously saved study notes for a specific topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to retrieve notes for"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "list_topics",
        "description": "List all AI topics the user has studied and saved notes for.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# Server-side tools (not supported on Haiku — use Sonnet/Opus for web search)
SERVER_TOOLS = []

ALL_TOOLS = SERVER_TOOLS + CUSTOM_TOOLS


def execute_custom_tool(name: str, tool_input: dict) -> str:
    """Execute a custom tool and return its result."""
    if name == "save_note":
        return save_note(tool_input["topic"], tool_input["content"])
    elif name == "load_notes":
        return load_notes(tool_input["topic"])
    elif name == "list_topics":
        return list_topics()
    else:
        return f"Unknown tool: {name}"
