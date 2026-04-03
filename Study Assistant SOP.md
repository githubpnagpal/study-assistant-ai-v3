# Study Assistant AI — Standard Operating Procedure (SOP)

## Project Overview
A conversational AI Study Assistant for learning Artificial Intelligence concepts,
built with Python and the Anthropic Claude API.

---

## Phase 1: Project Planning

### Goal Definition
- Build an interactive AI-powered study assistant
- Focus area: Learning AI/ML concepts
- Target user: Anyone learning AI from beginner to advanced level

### Key Features Decided
- Conversational chat interface in the terminal
- Streaming responses (real-time token-by-token output)
- Note saving and loading (persist study notes as .md files)
- Topic tracker (see everything you've studied)
- Web search (optional, for latest AI resources)
- Cost-efficient model selection

### Tech Stack Chosen
| Component        | Choice                        | Reason                          |
|------------------|-------------------------------|---------------------------------|
| Language         | Python                        | Best ecosystem for AI projects  |
| AI Model         | Claude Haiku 4.5              | Cheap, fast, great for Q&A      |
| API SDK          | `anthropic` (official)        | Direct access to Claude models  |
| UI               | `rich` (terminal formatting)  | Beautiful terminal output       |
| Config           | `python-dotenv`               | Secure API key management       |

---

## Phase 2: Environment Setup

### Step 1 — Create Project Directory
```
c:\Users\pnagp\study-assistant-ai\
```

### Step 2 — Create Folder Structure
```
study-assistant-ai/
├── main.py              ← Main app entry point
├── tools.py             ← Custom tool definitions
├── requirements.txt     ← Python dependencies
├── .env                 ← API key (never share this)
├── .env.example         ← Template for .env
└── notes/               ← Auto-created; stores study notes
```

### Step 3 — Define Dependencies (`requirements.txt`)
```
anthropic       ← Claude API SDK
python-dotenv   ← Load .env file securely
rich            ← Beautiful terminal UI
```

### Step 4 — Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 5 — API Key Setup
1. Go to console.anthropic.com
2. Create an API key (starts with sk-ant-)
3. Add billing/credits
4. Save key in `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```

---

## Phase 3: Building the Tools Layer (`tools.py`)

### Purpose
Define what actions the assistant can take beyond just chatting.

### Custom Tools Built
| Tool          | Function                                      |
|---------------|-----------------------------------------------|
| `save_note`   | Save a study note to a .md file by topic      |
| `load_notes`  | Read previously saved notes for a topic       |
| `list_topics` | List all topics with saved notes              |

### Tool Definition Format (Claude API)
Each tool needs:
- `name` — what Claude calls the tool
- `description` — tells Claude when/why to use it
- `input_schema` — JSON schema defining required parameters

### Notes Storage
- Location: `study-assistant-ai/notes/`
- Format: One `.md` file per topic (e.g., `neural_networks.md`)
- Each save appends a timestamped entry

---

## Phase 4: Building the Main App (`main.py`)

### Step 1 — System Prompt
Defined Claude's role and behavior:
- Expert AI tutor
- Explains concepts at any level
- Saves notes automatically
- Offers quizzes after explanations
- Suggests next learning topics

### Step 2 — Streaming Response Function
- Used `client.messages.stream()` for real-time output
- Tokens appear as Claude generates them (no waiting)
- Returns full content blocks for tool call detection

### Step 3 — Tool Call Handler
Logic to detect and execute tool calls in Claude's response:
- Check for `tool_use` blocks in response content
- Execute the matching Python function (`save_note`, etc.)
- Return results back to Claude to continue the conversation

### Step 4 — Agentic Loop
A `while True` loop that:
1. Sends user message to Claude
2. Streams the response
3. Detects if Claude wants to use a tool
4. Executes tool → sends result back to Claude
5. Repeats until Claude gives a final answer (no more tool calls)

### Step 5 — Conversation History
- Maintained as a `messages` list
- Every user message and assistant response is appended
- Passed to Claude on every request (API is stateless)

### Step 6 — Welcome UI + Chat Loop
- Used `rich` library for colored panels and prompts
- `while True` loop reads user input
- Special commands: `notes` (list topics), `quit` (exit)

---

## Phase 5: Cost Optimization

### Initial Setup
- Model: `claude-opus-4-6` (most capable)
- max_tokens: `4096`
- Had web search tool enabled

### Issue Encountered
- Haiku model doesn't support programmatic tool calling (web search)
- Got 400 error on first run with Haiku

### Fix Applied
- Removed web search tool from `tools.py`
- Custom note tools still work perfectly on Haiku

### Final Cost-Optimized Config
| Setting    | Value              | Impact                    |
|------------|--------------------|---------------------------|
| Model      | `claude-haiku-4-5` | 80% cheaper than Opus     |
| max_tokens | `1024`             | Shorter, focused answers  |
| Web search | Disabled           | Not supported on Haiku    |

### Cost Estimate Per Study Session (~50K tokens)
| Model      | Approx. Cost |
|------------|-------------|
| Opus 4.6   | ~$1.50      |
| Sonnet 4.6 | ~$0.90      |
| Haiku 4.5  | ~$0.30      |

---

## Phase 6: Running the App

```cmd
cd c:\Users\pnagp\study-assistant-ai
python main.py
```

### Available Commands Inside the App
| Input         | Action                        |
|---------------|-------------------------------|
| Any question  | Ask Claude about AI concepts  |
| `notes`       | View all studied topics       |
| `quit`/`exit` | Close the app                 |

### Example Prompts to Try
- "Explain neural networks like I'm a beginner"
- "What is the difference between supervised and unsupervised learning?"
- "Quiz me on transformers"
- "What should I learn after understanding backpropagation?"

---

## Troubleshooting Log

| Error                          | Cause                          | Fix                              |
|--------------------------------|--------------------------------|----------------------------------|
| `ModuleNotFoundError: dotenv`  | Wrong Python environment       | Run `pip install python-dotenv`  |
| `401 invalid x-api-key`        | Wrong/old API key in .env      | Get new key from console.anthropic.com |
| `400 tool calling not supported` | Haiku doesn't support web search | Removed web search tool        |

---

## Future Improvements (Optional)
- [ ] Switch to Sonnet 4.6 to re-enable web search
- [ ] Add a quiz scoring system
- [ ] Build a web UI (Flask or Streamlit)
- [ ] Add a progress tracker (topics mastered vs. in progress)
- [ ] Export notes as PDF

---

*Created: April 2026*
*Project Location: c:\Users\pnagp\study-assistant-ai\*
