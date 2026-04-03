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

## Phase 7: Pushing to GitHub

### Step 1 — Create .gitignore
Protect sensitive files before pushing:
```
# .gitignore
.env                ← API key (never push this)
__pycache__/
*.pyc
notes/
.vscode/
```

### Step 2 — Initialize Git Locally
```cmd
cd c:\Users\pnagp\study-assistant-ai
git init
git add .
git commit -m "Initial commit: AI Study Assistant"
```

> If you see "Author identity unknown", set your identity first:
> ```cmd
> git config --global user.email "you@example.com"
> git config --global user.name "Your Name"
> ```
> Then repeat the `git add .` and `git commit` commands.

### Step 3 — Create GitHub Repository
1. Go to github.com → Sign in
2. Click **+** (top right) → **New repository**
3. Name: `study-assistant-ai`
4. Description: `AI-powered Study Assistant for learning Artificial Intelligence concepts. Built with Python & Claude API. Features streaming chat, note saving, topic tracking, and adaptive explanations for all levels.`
5. Set Public or Private
6. **Do NOT** check Add README or Add .gitignore (already created locally)
7. Click **Create repository**

### Step 4 — Create a Personal Access Token (PAT)
GitHub no longer accepts passwords — use a PAT instead:
1. GitHub → Profile photo → **Settings**
2. Scroll down → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. Click **Generate new token (classic)**
5. Name it: `study-assistant`
6. Check the **repo** checkbox
7. Click **Generate token**
8. **Copy the token immediately** (shown only once)

### Step 5 — Connect and Push
```cmd
git remote add origin https://github.com/githubpnagpal/study-assistant-ai.git
git branch -M main
git remote set-url origin https://githubpnagpal:YOUR_TOKEN@github.com/githubpnagpal/study-assistant-ai.git
git push -u origin main
```

### What Gets Pushed vs Protected
| File                    | Pushed? | Reason                    |
|-------------------------|---------|---------------------------|
| `main.py`               | ✅ Yes  | Safe                      |
| `tools.py`              | ✅ Yes  | Safe                      |
| `requirements.txt`      | ✅ Yes  | Safe                      |
| `.env.example`          | ✅ Yes  | Template only, no secrets |
| `Study Assistant SOP.md`| ✅ Yes  | Safe                      |
| `.gitignore`            | ✅ Yes  | Safe                      |
| `.env`                  | ❌ No   | Contains API key          |
| `notes/`                | ❌ No   | Personal study data       |

### Troubleshooting GitHub Errors
| Error                              | Cause                        | Fix                                      |
|------------------------------------|------------------------------|------------------------------------------|
| `remote origin already exists`     | Already added remote         | Run `git remote set-url origin <url>`    |
| `src refspec main does not match`  | Nothing committed yet        | Run `git add .` then `git commit` first  |
| `403 Write access not granted`     | No PAT or wrong credentials  | Use PAT in remote URL (Step 5)           |
| `Author identity unknown`          | Git user not configured      | Run `git config --global user.email/name`|

### Live Repository
https://github.com/githubpnagpal/study-assistant-ai

---

## Phase 8: Saving GitHub Credentials Permanently

By default, CMD does not remember your GitHub credentials between sessions.
Fix this so you never have to enter your token again.

### Option 1 — Git Credential Manager (Recommended)
Git for Windows includes this built-in. Run once:
```cmd
git config --global credential.helper manager
```
Next time you push, it asks once and saves forever in Windows Credential Manager.

**To verify it's saved:**
1. Press `Win + R` → type `control` → Enter
2. Go to **Credential Manager** → **Windows Credentials**
3. You should see `git:https://github.com` stored there

### Option 2 — GitHub CLI (Easiest Long-Term)
Install GitHub CLI and authenticate via browser — no tokens needed manually:
```cmd
winget install GitHub.cli
gh auth login
```
Follow the prompts → choose **GitHub.com** → **HTTPS** → **Login with browser**.
Done. All future `git push` commands work without any credentials.

### After Setup
Just run from your project folder:
```cmd
git add .
git commit -m "your message"
git push
```
No username, no token, no prompts — it just works.

### Troubleshooting Credentials
| Issue                          | Fix                                              |
|--------------------------------|--------------------------------------------------|
| Still asking for credentials   | Run `git config --global credential.helper manager` |
| Wrong credentials saved        | Go to Windows Credential Manager → delete `git:https://github.com` → push again |
| Token expired                  | Generate new PAT on GitHub → update in Credential Manager |

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
