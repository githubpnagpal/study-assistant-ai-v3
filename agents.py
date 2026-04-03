"""
Multi-Agent System for AI Study Assistant.

Teacher Agent  — explains concepts, adapts to user level, saves notes
Tester Agent   — generates questions, evaluates answers, tracks score
Orchestrator   — manages mode switching and shared session state
"""

import anthropic
from tools import ALL_TOOLS, execute_custom_tool

# ─────────────────────────────────────────────
# AGENT SYSTEM PROMPTS
# ─────────────────────────────────────────────

TEACHER_PROMPT = """You are the Teacher Agent in an AI Study Assistant system.

Your ONLY job is to TEACH. You explain AI/ML concepts clearly and engagingly.

How you teach:
- Start by gauging the user's level (beginner / intermediate / advanced)
- Use simple analogies before technical details
- Give real-world examples for every concept
- Break complex topics into numbered steps
- End each explanation with: "Ready to test your understanding? Type 'quiz' to start!"
- Automatically save key concepts to notes using the save_note tool

Topics you cover:
- ML fundamentals, Neural Networks, Deep Learning
- Transformers, LLMs, Attention mechanisms
- Computer Vision, NLP, Reinforcement Learning
- AI Ethics, Safety, Alignment
- Python frameworks: PyTorch, TensorFlow, scikit-learn

Be encouraging, patient, and enthusiastic about AI."""


TESTER_PROMPT = """You are the Tester Agent in an AI Study Assistant system.

Your ONLY job is to TEST and EVALUATE the user's understanding.

How you test:
- Generate ONE clear question at a time (never multiple at once)
- Mix question types: multiple choice, true/false, short answer, fill-in-the-blank
- Match difficulty to the topic complexity
- After the user answers, give detailed feedback:
  ✅ If correct: confirm why it's right + add an interesting related fact
  ❌ If wrong: gently explain the correct answer + clarify the misconception
- Keep a mental note of weak areas and revisit them
- After every 3 questions, give a mini progress summary

Question format for multiple choice (use this exactly):
Q: [question]
A) [option]
B) [option]
C) [option]
D) [option]

Always end your evaluation with either:
- "Next question? (or type 'learn' to go back to studying)"
- "Great session! Type 'learn' to study more or 'score' to see your results."

Be supportive — learning from mistakes is part of the process."""


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

class StudySession:
    """Tracks the full study session state."""

    def __init__(self):
        self.mode = "learning"          # "learning" or "testing"
        self.current_topic = "AI"       # topic being studied/tested
        self.teacher_messages = []      # Teacher's conversation history
        self.tester_messages = []       # Tester's conversation history
        self.score = {"correct": 0, "total": 0}
        self.questions_asked = []       # track what was asked

    def switch_to_testing(self, topic: str = None):
        if topic:
            self.current_topic = topic
        self.mode = "testing"

    def switch_to_learning(self):
        self.mode = "learning"

    def record_answer(self, correct: bool):
        self.score["total"] += 1
        if correct:
            self.score["correct"] += 1

    def get_score_display(self) -> str:
        total = self.score["total"]
        correct = self.score["correct"]
        if total == 0:
            return "No questions answered yet. Type 'quiz' to start testing!"
        pct = int((correct / total) * 100)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        grade = "A" if pct >= 90 else "B" if pct >= 80 else "C" if pct >= 70 else "D" if pct >= 60 else "F"
        return (
            f"Topic: {self.current_topic}\n"
            f"Score: {correct}/{total} ({pct}%)\n"
            f"Progress: [{bar}]\n"
            f"Grade: {grade}"
        )


# ─────────────────────────────────────────────
# TOOL HANDLING (Claude only)
# ─────────────────────────────────────────────

def handle_tool_calls(content_blocks: list) -> list | None:
    """Execute custom tool calls from Claude's response."""
    tool_blocks = [b for b in content_blocks if hasattr(b, "type") and b.type == "tool_use"]
    if not tool_blocks:
        return None

    results = []
    for block in tool_blocks:
        if block.name == "web_search":
            continue
        result = execute_custom_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": result
        })
    return results if results else None


# ─────────────────────────────────────────────
# TEACHER AGENT
# ─────────────────────────────────────────────

def run_teacher(client, provider: dict, session: StudySession, user_input: str) -> str:
    """Run the Teacher Agent and return its response."""
    session.teacher_messages.append({"role": "user", "content": user_input})

    if provider["provider"] == "claude":
        while True:
            full_text, content_blocks = _stream_claude(
                client, provider["model"], session.teacher_messages, TEACHER_PROMPT
            )
            session.teacher_messages.append({"role": "assistant", "content": content_blocks})

            tool_results = handle_tool_calls(content_blocks)
            if tool_results:
                session.teacher_messages.append({"role": "user", "content": tool_results})
            else:
                break
        return full_text
    else:
        full_text, _ = _stream_openai(client, provider["model"], session.teacher_messages, TEACHER_PROMPT)
        session.teacher_messages.append({"role": "assistant", "content": full_text})
        return full_text


# ─────────────────────────────────────────────
# TESTER AGENT
# ─────────────────────────────────────────────

def run_tester(client, provider: dict, session: StudySession, user_input: str) -> str:
    """Run the Tester Agent and return its response."""

    # On first quiz entry, prime the tester with context
    if not session.tester_messages:
        primer = f"The user has been studying: {session.current_topic}. Start testing them now. Ask your first question."
        session.tester_messages.append({"role": "user", "content": primer})
    else:
        # Detect if answer was correct for scoring (simple heuristic)
        session.tester_messages.append({"role": "user", "content": user_input})

    if provider["provider"] == "claude":
        full_text, content_blocks = _stream_claude(
            client, provider["model"], session.tester_messages, TESTER_PROMPT
        )
        session.tester_messages.append({"role": "assistant", "content": content_blocks})
    else:
        full_text, _ = _stream_openai(client, provider["model"], session.tester_messages, TESTER_PROMPT)
        session.tester_messages.append({"role": "assistant", "content": full_text})

    # Simple scoring: detect correct/incorrect from tester's response
    lower = full_text.lower()
    if any(w in lower for w in ["correct!", "that's right", "well done", "exactly right", "✅"]):
        session.record_answer(correct=True)
    elif any(w in lower for w in ["incorrect", "not quite", "wrong", "❌", "actually"]):
        session.record_answer(correct=False)

    return full_text


# ─────────────────────────────────────────────
# STREAMING GENERATORS (for Streamlit web UI)
# ─────────────────────────────────────────────

def teacher_stream_gen(client, provider: dict, session: "StudySession", user_input: str):
    """Generator — yields text chunks from Teacher. Used by st.write_stream()."""
    session.teacher_messages.append({"role": "user", "content": user_input})

    if provider["provider"] == "claude":
        while True:
            tool_called = False
            with client.messages.stream(
                model=provider["model"],
                max_tokens=1024,
                system=TEACHER_PROMPT,
                tools=ALL_TOOLS,
                messages=session.teacher_messages,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield event.delta.text
                final = stream.get_final_message()
                session.teacher_messages.append({"role": "assistant", "content": final.content})
                tool_results = handle_tool_calls(final.content)
                if tool_results:
                    session.teacher_messages.append({"role": "user", "content": tool_results})
                    tool_called = True
            if not tool_called:
                break
    else:
        openai_messages = [{"role": "system", "content": TEACHER_PROMPT}] + [
            {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else str(m["content"])}
            for m in session.teacher_messages
        ]
        stream = client.chat.completions.create(
            model=provider["model"], messages=openai_messages, stream=True, max_tokens=1024
        )
        full_text = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_text += delta
            yield delta
        session.teacher_messages.append({"role": "assistant", "content": full_text})


def tester_stream_gen(client, provider: dict, session: "StudySession", user_input: str):
    """Generator — yields text chunks from Tester. Used by st.write_stream()."""
    if not session.tester_messages:
        primer = f"The user has been studying: {session.current_topic}. Start testing them now. Ask your first question."
        session.tester_messages.append({"role": "user", "content": primer})
    else:
        session.tester_messages.append({"role": "user", "content": user_input})

    full_text = ""

    if provider["provider"] == "claude":
        with client.messages.stream(
            model=provider["model"],
            max_tokens=1024,
            system=TESTER_PROMPT,
            tools=ALL_TOOLS,
            messages=session.tester_messages,
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    full_text += event.delta.text
                    yield event.delta.text
            final = stream.get_final_message()
            session.tester_messages.append({"role": "assistant", "content": final.content})
    else:
        openai_messages = [{"role": "system", "content": TESTER_PROMPT}] + [
            {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else str(m["content"])}
            for m in session.tester_messages
        ]
        stream = client.chat.completions.create(
            model=provider["model"], messages=openai_messages, stream=True, max_tokens=1024
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_text += delta
            yield delta
        session.tester_messages.append({"role": "assistant", "content": full_text})

    # Score detection after full response
    lower = full_text.lower()
    if any(w in lower for w in ["correct!", "that's right", "well done", "exactly right", "✅"]):
        session.record_answer(correct=True)
    elif any(w in lower for w in ["incorrect", "not quite", "wrong", "❌", "actually"]):
        session.record_answer(correct=False)


# ─────────────────────────────────────────────
# STREAMING HELPERS
# ─────────────────────────────────────────────

def _stream_claude(client: anthropic.Anthropic, model: str, messages: list, system: str) -> tuple[str, list]:
    full_text = ""
    with client.messages.stream(
        model=model,
        max_tokens=1024,
        system=system,
        tools=ALL_TOOLS,
        messages=messages,
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
                full_text += event.delta.text
        print()
        final = stream.get_final_message()
        return full_text, final.content


def _stream_openai(client, model: str, messages: list, system: str) -> tuple[str, list]:
    full_text = ""
    openai_messages = [{"role": "system", "content": system}] + [
        {
            "role": m["role"],
            "content": m["content"] if isinstance(m["content"], str) else str(m["content"])
        }
        for m in messages
    ]
    stream = client.chat.completions.create(
        model=model, messages=openai_messages, stream=True, max_tokens=1024
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
        full_text += delta
    print()
    return full_text, []
