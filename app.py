"""
AI Study Assistant v3 — Web UI
Multi-Agent System with Teacher & Tester agents running in the browser.
Run with: streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

from agents import StudySession, teacher_stream_gen, tester_stream_gen
from providers import PROVIDERS, get_claude_client, get_groq_client
from tools import list_topics, load_notes

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stChatMessage { border-radius: 12px; margin-bottom: 0.5rem; }
    .teacher-badge { background: #1a7a1a; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; }
    .tester-badge  { background: #7a1a7a; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; }
    div[data-testid="stMetric"] { background: #1e1e2e; border-radius: 8px; padding: 0.5rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────

def init_state():
    if "study_session" not in st.session_state:
        st.session_state.study_session = StudySession()
    if "messages" not in st.session_state:
        st.session_state.messages = []   # {"role": "user"/"teacher"/"tester", "content": str}
    if "provider" not in st.session_state:
        st.session_state.provider = None
    if "client" not in st.session_state:
        st.session_state.client = None
    if "note_saved" not in st.session_state:
        st.session_state.note_saved = None

init_state()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🤖 AI Study Assistant")
    st.markdown("**v3 — Web Edition**")
    st.divider()

    # Provider selection
    st.markdown("### ⚙️ AI Provider")
    provider_options = {k: f"{v['name']} — {v['cost']}" for k, v in PROVIDERS.items()}
    selected_key = st.selectbox(
        "Select model",
        options=list(provider_options.keys()),
        format_func=lambda x: provider_options[x],
        label_visibility="collapsed"
    )
    selected_provider = PROVIDERS[selected_key]

    # Check API key availability
    if selected_provider["provider"] == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
        st.error("ANTHROPIC_API_KEY missing in .env")
    elif selected_provider["provider"] == "groq" and not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY missing in .env")
    else:
        # Initialize client if provider changed
        if st.session_state.provider != selected_key:
            st.session_state.provider = selected_key
            if selected_provider["provider"] == "claude":
                st.session_state.client = get_claude_client()
            else:
                st.session_state.client = get_groq_client()
        st.success(f"✅ {selected_provider['name']}")

    st.divider()

    # Mode controls
    st.markdown("### 🎯 Mode")
    session: StudySession = st.session_state.study_session
    mode = session.mode

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 Learn", use_container_width=True,
                     type="primary" if mode == "learning" else "secondary"):
            session.switch_to_learning()
            st.rerun()
    with col2:
        if st.button("🎯 Quiz", use_container_width=True,
                     type="primary" if mode == "testing" else "secondary"):
            topic = session.current_topic
            session.switch_to_testing(topic)
            # Auto-start quiz
            if st.session_state.client:
                st.session_state.messages.append({
                    "role": "tester",
                    "content": "__START_QUIZ__",
                    "topic": topic
                })
            st.rerun()

    if mode == "learning":
        st.info("📚 Learning Mode")
    else:
        st.warning(f"🎯 Quiz Mode — {session.current_topic}")

    st.divider()

    # Score
    st.markdown("### 📊 Your Score")
    score = session.score
    total = score["total"]
    correct = score["correct"]

    if total == 0:
        st.caption("No questions answered yet.")
    else:
        pct = correct / total
        grade = "A" if pct >= 0.9 else "B" if pct >= 0.8 else "C" if pct >= 0.7 else "D" if pct >= 0.6 else "F"
        col1, col2, col3 = st.columns(3)
        col1.metric("Correct", correct)
        col2.metric("Total", total)
        col3.metric("Grade", grade)
        st.progress(pct, text=f"{int(pct * 100)}%")

    st.divider()

    # Notes viewer
    st.markdown("### 📝 Study Notes")
    topics_text = list_topics()
    if "No topics" in topics_text:
        st.caption("No notes yet — start studying!")
    else:
        topic_lines = [t.replace("• ", "") for t in topics_text.split("\n") if t.startswith("•")]
        selected_note = st.selectbox("View notes for:", ["— select —"] + topic_lines)
        if selected_note and selected_note != "— select —":
            notes_content = load_notes(selected_note)
            st.text_area("Notes", notes_content, height=200, disabled=True)

    st.divider()

    # Reset
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.study_session = StudySession()
        st.session_state.messages = []
        st.rerun()


# ─────────────────────────────────────────────
# MAIN CHAT UI
# ─────────────────────────────────────────────

st.markdown("## 🤖 AI Study Assistant")

session: StudySession = st.session_state.study_session
mode = session.mode

if mode == "learning":
    st.info("📚 **Learning Mode** — Ask me anything about AI! When ready, click **Quiz** to be tested.")
else:
    st.warning(f"🎯 **Quiz Mode** — Topic: **{session.current_topic}** — Answer the questions below.")

# Display chat history
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]

    if content == "__START_QUIZ__":
        continue  # handled separately below

    if role == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(content)

    elif role == "teacher":
        with st.chat_message("assistant", avatar="👨‍🏫"):
            st.markdown('<span class="teacher-badge">Teacher</span>', unsafe_allow_html=True)
            st.markdown(content)

    elif role == "tester":
        with st.chat_message("assistant", avatar="📝"):
            st.markdown('<span class="tester-badge">Tester</span>', unsafe_allow_html=True)
            st.markdown(content)

# Auto-start quiz if flag is set
pending = next((m for m in st.session_state.messages if m.get("content") == "__START_QUIZ__"), None)
if pending and st.session_state.client:
    # Remove the flag
    st.session_state.messages = [m for m in st.session_state.messages if m.get("content") != "__START_QUIZ__"]
    topic = pending.get("topic", session.current_topic)
    session.tester_messages = []  # fresh quiz
    session.switch_to_testing(topic)

    with st.chat_message("assistant", avatar="📝"):
        st.markdown('<span class="tester-badge">Tester</span>', unsafe_allow_html=True)
        response = st.write_stream(
            tester_stream_gen(st.session_state.client, selected_provider, session, "")
        )
    st.session_state.messages.append({"role": "tester", "content": response})
    st.rerun()

# Chat input
placeholder = "Ask about any AI concept..." if mode == "learning" else "Type your answer here..."
if prompt := st.chat_input(placeholder):

    # Show user message
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not st.session_state.client:
        st.error("Please select a valid AI provider in the sidebar.")
        st.stop()

    # Route to correct agent
    if mode == "learning":
        session.current_topic = prompt[:60]
        with st.chat_message("assistant", avatar="👨‍🏫"):
            st.markdown('<span class="teacher-badge">Teacher</span>', unsafe_allow_html=True)
            response = st.write_stream(
                teacher_stream_gen(st.session_state.client, selected_provider, session, prompt)
            )
        st.session_state.messages.append({"role": "teacher", "content": response})

    elif mode == "testing":
        with st.chat_message("assistant", avatar="📝"):
            st.markdown('<span class="tester-badge">Tester</span>', unsafe_allow_html=True)
            response = st.write_stream(
                tester_stream_gen(st.session_state.client, selected_provider, session, prompt)
            )
        st.session_state.messages.append({"role": "tester", "content": response})

    st.rerun()
