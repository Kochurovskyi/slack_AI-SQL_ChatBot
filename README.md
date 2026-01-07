# Slack AI SQL ChatBot

**A production-ready Slack chatbot for SQL database analytics using LangChain ReAct multi-agent architecture.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-green.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

This Slack chatbot enables natural language querying of an app portfolio database through a sophisticated multi-agent system. Users can ask questions in plain English, and the system automatically generates SQL queries, executes them, formats results, and even exports data to CSV—all directly within Slack.

**Key Capabilities:**
- 🤖 **Natural Language to SQL**: Convert questions like "how many iOS apps do we have?" into SQL queries
- 📊 **Intelligent Formatting**: Automatically formats results as simple text or tables based on complexity
- 💾 **CSV Export**: Download query results directly from Slack GUI
- 🔍 **SQL Retrieval**: View the SQL queries used to generate answers
- 💬 **Follow-up Questions**: Maintains conversation context for natural interactions
- 🎯 **Cost Optimized**: Smart caching prevents redundant SQL generation and execution

---

## Features

### Core Features

- ✅ **Natural Language Querying**: Ask questions in plain English, get SQL-powered answers
- ✅ **Multi-Agent Architecture**: Specialized agents for different tasks (SQL queries, CSV export, SQL retrieval)
- ✅ **Intent Classification**: Automatic routing to appropriate agents based on user intent
- ✅ **Conversation Context**: Maintains thread-based memory for follow-up questions
- ✅ **Result Formatting**: Intelligent formatting (simple text vs. markdown tables)
- ✅ **Error Handling**: Graceful error handling with user-friendly messages
- ✅ **Streaming Responses**: Real-time response streaming for better UX

### CSV Export Feature

**Direct CSV Download from Slack GUI**

Users can export query results directly to CSV files that are automatically uploaded to Slack:

1. **Request Export**: Simply ask "export this as csv" or "save to csv"
2. **Automatic Generation**: System retrieves cached query results (no SQL regeneration)
3. **Slack Upload**: CSV file is automatically uploaded to the Slack thread
4. **Simple Confirmation**: User receives a clean message: "CSV report generated and uploaded."

**Benefits:**
- ✅ **Cost Efficient**: Reuses cached results (no SQL regeneration or re-execution)
- ✅ **Fast**: No database query needed, instant CSV generation
- ✅ **User-Friendly**: Files appear directly in Slack thread, accessible to all team members
- ✅ **Cross-Platform**: Works on Windows, macOS, and Linux

**Example Flow:**
```
User: "how many iOS apps do we have?"
Bot: "21"

User: "export this as csv"
Bot: "CSV report generated and uploaded." [CSV file attached to thread]
```

---

## Run the Application

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kochurovskyi/slack_AI-SQL_ChatBot.git
   cd slack_AI-SQL_ChatBot
   ```

2. **Set up environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.sample .env
   # Edit .env with your tokens (see Setup Instructions below)
   ```

4. **Initialize database**
   ```bash
   python -m data.db_manager
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

### Demo Screenshots

#### Demo 1: Simple Query and SQL Retrieval
![Demo 1: Simple Query Flow](demo1.png)

**Features Demonstrated:**
- Natural language querying ("how many android apps do we have?")
- Simple answer format (just "29")
- SQL query retrieval ("which sql query have you used?")
- Formatted SQL display in code blocks

#### Demo 2: Complex Query and CSV Export
![Demo 2: Complex Query and CSV Export](demo2.png)

**Features Demonstrated:**
- Complex query with table formatting ("top 5 revenue iOS apps")
- CSV export request ("save this report to csv")
- CSV file automatically uploaded to Slack thread
- SQL query retrieval for the report

---

## Architecture Overview

The system uses a **Router-based Multi-Agent Architecture** with specialized agents for different intents:

```
User Message (Slack)
    ↓
Agent Orchestrator (Coordinator)
    ↓
Router Agent (Intent Classification)
    ↓
    ├─→ SQL Query Agent (Unified: generation + execution + formatting)
    ├─→ CSV Export Agent (uses cached results)
    ├─→ SQL Retrieval Agent (uses cached SQL)
    └─→ Off-Topic Handler
    ↓
Stream Response to Slack
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Slack Thread (thread_ts)                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Agent Orchestrator (Coordinator)            │   │
│  │  • Receives messages from Slack                       │   │
│  │  • Routes to Router Agent                             │   │
│  │  • Streams responses                                  │   │
│  │  • Manages memory store                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Router Agent                             │   │
│  │  • Classifies intent                                 │   │
│  │  • Routes to specialized agents                      │   │
│  └──────────────────────────────────────────────────────┘   │
│         ↓           ↓           ↓           ↓                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   SQL    │ │   CSV    │ │   SQL    │ │  Off-    │       │
│  │  Query   │ │  Export  │ │Retrieval │ │  Topic   │       │
│  │  Agent   │ │  Agent   │ │  Agent   │ │ Handler  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Memory Store (Thread-Scoped)              │   │
│  │  • Conversation history                               │   │
│  │  • SQL query cache                                    │   │
│  │  • Query results cache                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Services Layer                           │   │
│  │  • SQL Service (query execution)                      │   │
│  │  • Formatting Service (result formatting)            │   │
│  │  • CSV Service (file generation & upload)            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SQLite Database                          │   │
│  │  • app_portfolio table                               │   │
│  │  • Sample data (50 records)                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**For detailed architecture documentation, see:** [`docs/architecture.md`](docs/architecture.md)

---

## Process Flow

### Complete User Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant Slack
    participant Orchestrator
    participant Router
    participant SQLAgent
    participant Memory
    participant Database
    
    User->>Slack: "how many iOS apps?"
    Slack->>Orchestrator: User message + thread_ts
    Orchestrator->>Memory: Get conversation history
    Memory-->>Orchestrator: History (empty)
    Orchestrator->>Router: Classify intent
    Router-->>Orchestrator: SQL_QUERY
    Orchestrator->>SQLAgent: Route to SQL Query Agent
    SQLAgent->>SQLAgent: Generate SQL (generate_sql_tool)
    SQLAgent->>Database: Execute SQL
    Database-->>SQLAgent: Results
    SQLAgent->>SQLAgent: Format results (format_result_tool)
    SQLAgent->>Memory: Store SQL query & results
    SQLAgent-->>Orchestrator: Formatted response: "21"
    Orchestrator->>Memory: Save assistant response
    Orchestrator->>Slack: Stream response
    Slack-->>User: "21"
```

### CSV Export Flow

```mermaid
sequenceDiagram
    participant User
    participant Slack
    participant Orchestrator
    participant Router
    participant CSVAgent
    participant Memory
    participant CSVService
    
    User->>Slack: "export this as csv"
    Slack->>Orchestrator: User message + thread_ts
    Orchestrator->>Router: Classify intent
    Router-->>Orchestrator: CSV_EXPORT
    Orchestrator->>CSVAgent: Route to CSV Export Agent
    CSVAgent->>Memory: get_cached_results_tool(thread_ts)
    Memory-->>CSVAgent: Cached query results
    CSVAgent->>CSVService: Generate CSV file
    CSVService-->>CSVAgent: CSV file path
    CSVAgent->>Slack: Upload CSV file
    CSVAgent-->>Orchestrator: "CSV report generated and uploaded."
    Orchestrator->>Slack: Stream response
    Slack-->>User: "CSV report generated and uploaded." [File attached]
```

---

## Agents

The system consists of **5 specialized agents** plus an orchestrator:

### 1. Router Agent
**Purpose**: Classifies user intent and routes to appropriate specialized agents

**Intents:**
- `SQL_QUERY`: Database queries and analytics questions
- `CSV_EXPORT`: Export requests ("export to csv", "save as csv")
- `SQL_RETRIEVAL`: SQL query viewing requests ("show me the SQL")
- `OFF_TOPIC`: Non-database questions

**Implementation**: Uses LangChain `create_agent` with routing tools  
**Prompt**: [`prompts/router_prompt.py`](prompts/router_prompt.py)

### 2. SQL Query Agent
**Purpose**: Unified agent handling SQL generation, execution, and formatting

**Workflow:**
1. Generate SQL from natural language (`generate_sql_tool`)
2. Execute SQL query (`execute_sql_tool`)
3. Format results (`format_result_tool`)
4. Store query and results in memory store

**Features:**
- Context-aware SQL generation (uses conversation history)
- Automatic format selection (simple text vs. tables)
- Assumption generation for complex queries
- Follow-up question support

**Implementation**: LangChain `create_agent` with 3 tools  
**Prompt**: [`prompts/sql_query_prompt.py`](prompts/sql_query_prompt.py)

### 3. CSV Export Agent
**Purpose**: Generates CSV files from cached query results

**Workflow:**
1. Retrieve cached results (`get_cached_results_tool`)
2. Generate CSV file (`generate_csv_tool`)
3. Return simple confirmation message

**Features:**
- ✅ **Cost Efficient**: Reuses cached results (no SQL regeneration)
- ✅ **Fast**: No database query needed
- ✅ **Simple Response**: Returns "CSV report generated and uploaded."

**Implementation**: LangChain `create_agent` with 2 tools  
**Prompt**: [`prompts/csv_export_prompt.py`](prompts/csv_export_prompt.py)

### 4. SQL Retrieval Agent
**Purpose**: Retrieves and displays previously executed SQL queries

**Workflow:**
1. Retrieve SQL queries from memory (`get_sql_history_tool`)
2. Support query selection by description
3. Format SQL in code blocks for Slack

**Features:**
- Description-based query matching ("show SQL for all the apps")
- Returns last query if no description provided
- Clean SQL formatting in Slack code blocks

**Implementation**: LangChain `create_agent` with 1 tool  
**Prompt**: [`prompts/sql_retrieval_prompt.py`](prompts/sql_retrieval_prompt.py)

### 5. Off-Topic Handler
**Purpose**: Politely handles non-database questions

**Features:**
- Friendly responses explaining specialization
- Use case suggestions
- Polite decline of off-topic questions

**Implementation**: LangChain `create_agent` (no tools)  
**Prompt**: [`prompts/off_topic_prompt.py`](prompts/off_topic_prompt.py)

### Agent Orchestrator
**Purpose**: Coordinates agent execution and Slack integration

**Responsibilities:**
- Receives messages from Slack handlers
- Fetches conversation history from memory store
- Routes to Router Agent for intent classification
- Routes to appropriate specialized agent
- Streams responses back to Slack
- Manages memory store integration

**Note**: Orchestrator is a **coordinator/service**, not an agent itself.

**For detailed agent documentation, see:** [`docs/phase3_agents.md`](docs/phase3_agents.md)

---

## Prompts

All agent prompts are centralized in the `prompts/` directory for easy maintenance and optimization:

| Prompt File | Agent | Purpose |
|------------|-------|---------|
| [`prompts/router_prompt.py`](prompts/router_prompt.py) | Router Agent | Intent classification instructions |
| [`prompts/sql_query_prompt.py`](prompts/sql_query_prompt.py) | SQL Query Agent | SQL generation with database schema |
| [`prompts/csv_export_prompt.py`](prompts/csv_export_prompt.py) | CSV Export Agent | CSV export workflow instructions |
| [`prompts/sql_retrieval_prompt.py`](prompts/sql_retrieval_prompt.py) | SQL Retrieval Agent | SQL retrieval and formatting |
| [`prompts/off_topic_prompt.py`](prompts/off_topic_prompt.py) | Off-Topic Handler | Polite off-topic handling |
| [`prompts/formatting_prompt.py`](prompts/formatting_prompt.py) | Formatting Service | Result formatting guidelines |

**Benefits of Centralized Prompts:**
- ✅ Easy to update and optimize
- ✅ Version control for prompt changes
- ✅ Consistent prompt management
- ✅ Clear separation of concerns

**For prompt optimization details, see:** [`docs/phase4_optimization.md`](docs/phase4_optimization.md)

---

## Services Implemented

### 1. SQL Service (`services/sql_service.py`)
**Purpose**: Secure SQL query execution

**Features:**
- ✅ SELECT-only queries (security whitelist)
- ✅ SQL injection prevention
- ✅ Query validation and error handling
- ✅ Automatic query type detection
- ✅ Schema introspection support

**Key Methods:**
- `execute_query(sql_query: str) -> Dict[str, Any]`
- `validate_sql(sql_query: str) -> bool`
- `get_schema() -> str`

### 2. Formatting Service (`services/formatting_service.py`)
**Purpose**: Intelligent result formatting for Slack

**Features:**
- ✅ Automatic format selection (simple text vs. tables)
- ✅ Threshold-based decisions (5 rows, 3 columns)
- ✅ Slack markdown table support
- ✅ Assumption generation for complex queries
- ✅ Context-aware formatting

**Key Methods:**
- `format_result(results: Dict, question: str) -> str`
- `format_simple(data: List[Dict]) -> str`
- `format_table(data: List[Dict]) -> str`

### 3. CSV Service (`services/csv_service.py`)
**Purpose**: CSV file generation and Slack upload

**Features:**
- ✅ Automatic CSV generation from query results
- ✅ Timestamp-based filename generation
- ✅ UTF-8 encoding support
- ✅ Special character handling
- ✅ Direct Slack file upload
- ✅ Automatic temporary file cleanup

**Key Methods:**
- `generate_csv(data: List[Dict], filename: Optional[str] = None) -> str`
- `upload_to_slack(file_path: str, channel_id: str, thread_ts: Optional[str] = None) -> bool`

**For detailed service documentation, see:** [`docs/phase2_services.md`](docs/phase2_services.md)

---

## Memory Management

The system implements a **custom thread-based memory management system** (`ai/memory_store.py`) that provides:

- **Thread-Scoped Isolation**: Each Slack thread maintains separate conversation history
- **SQL Query Caching**: Stores SQL queries and results for later retrieval
- **Conversation Compression**: Token-aware compression for long conversations
- **Description-Based Retrieval**: Find SQL queries by natural language description
- **Cost Optimization**: CSV export reuses cached results (no SQL regeneration)

### Key Features

**1. Thread-Scoped Memory**
```python
# Each Slack thread has separate memory
memory_store.get_messages("thread_1")  # Separate from thread_2
memory_store.get_messages("thread_2")  # Separate from thread_1
```

**2. SQL Query Caching**
```python
# Store SQL queries with metadata
memory_store.store_sql_query(
    thread_ts=thread_ts,
    sql_query="SELECT COUNT(*) FROM app_portfolio",
    question="how many apps do we have?",
    results={"success": True, "data": [{"COUNT(*)": 49}]}
)
```

**3. Conversation Compression**
- Automatically compresses old messages when approaching token limits
- Keeps recent messages (last 5) in full detail
- Summarizes older messages (simple string summarization, no LLM calls)

**Why Custom Solution?**
- Thread-scoped isolation (Slack-specific requirement)
- SQL query/results caching (beyond conversation history)
- Description-based query retrieval (natural language matching)
- Cost-effective compression (simple summarization vs. LLM calls)

**For comprehensive memory documentation, see:** [`docs/memory.md`](docs/memory.md)

---

## Testing Strategy

The project includes comprehensive testing across multiple levels:

### Test Suites

| Test Suite | Location | Tests | Status |
|-----------|----------|-------|--------|
| **Unit Tests** | `tests/test_*.py` | 136 tests | ✅ 100% Pass |
| **Integration Tests** | `tests/test_integration_*.py` | 25 tests | ✅ 100% Pass |
| **Sanity Checks** | `tests/sanity/` | 10 scripts | ✅ 100% Pass |
| **Scenario Tests** | `tests/scenarios/` | 13 scenarios | ✅ 100% Pass |
| **LangSmith Experiments** | `tests/langsmith/` | 3 experiments | ✅ 93.3% Pass |

### Test Execution

**Unit & Integration Tests (Pytest):**
```bash
pytest tests/ -v
```

**Sanity Checks (Scripts):**
```bash
python tests/sanity/sanity_database.py
python tests/sanity/sanity_orchestrator_e2e.py
# ... (10 sanity scripts)
```

**Scenario Tests (Scripts):**
```bash
python tests/scenarios/test_assignment_scenarios.py
```

**LangSmith Experiments:**
```bash
python tests/langsmith/run_all_experiments.py
```

### Test Reports

- **Post Code Review Report**: [`tests/reports/POST_CODE_REVIEW_TEST_REPORT.md`](tests/reports/POST_CODE_REVIEW_TEST_REPORT.md)
- **Comprehensive Test Report**: All test results and analysis

**For detailed testing documentation, see:** [`docs/phase6_functional_testing.md`](docs/phase6_functional_testing.md)

---

## Setup Instructions

### Prerequisites

- **Python**: 3.10 or higher
- **Slack Workspace**: Development workspace with app installation permissions
- **Google Account**: For Gemini API access
- **Git**: For cloning the repository

### Step 1: Clone Repository

```bash
git clone https://github.com/Kochurovskyi/slack_AI-SQL_ChatBot.git
cd slack_AI-SQL_ChatBot
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Slack App

**Option A: Using Slack CLI (Recommended)**

1. Install Slack CLI: https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli
2. Login: `slack login`
3. Install app: `slack install` (uses `manifest.json`)

**Option B: Using Web Interface**

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From an app manifest"**
3. Copy contents of [`manifest.json`](manifest.json) into the text box
4. Click **"Create"** → **"Install to Workspace"**

### Step 5: Get Slack Tokens

**SLACK_BOT_TOKEN:**
1. Go to https://api.slack.com/apps → Select your app
2. **"OAuth & Permissions"** → Copy **"Bot User OAuth Token"** (starts with `xoxb-`)

**SLACK_APP_TOKEN:**
1. **"Basic Information"** → **"App-Level Tokens"**
2. Click **"Generate Token and Scopes"**
3. Add scope: `connections:write`
4. Copy token (starts with `xapp-`)

### Step 6: Get Google Gemini API Key

See [Google Gemini API Setup](#google-gemini-api) section below.

### Step 7: Create .env File

```bash
cp .env.sample .env
```

Edit `.env` with your tokens:
```
SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
SLACK_APP_TOKEN=xapp-YOUR-APP-TOKEN-HERE
GOOGLE_API_KEY=YOUR-GOOGLE-API-KEY-HERE
```

### Step 8: Initialize Database

```bash
python -m data.db_manager
```

This will:
- Create SQLite database (`data/app_portfolio.db`)
- Initialize schema from `data/schema.sql`
- Load sample data from `data/sample_data.csv` (50 records)

### Step 9: Run Application

```bash
python app.py
```

The app will start and connect to Slack via Socket Mode.

**For detailed setup guide, see:** [`SETUP_GUIDE.md`](SETUP_GUIDE.md)

---

## Google Gemini API

### Getting API Key

1. **Visit Google AI Studio**
   - Go to: https://makersuite.google.com/app/apikey
   - Or: https://aistudio.google.com/app/apikey

2. **Sign In**
   - Sign in with your Google account

3. **Create API Key**
   - Click **"Create API Key"**
   - Select or create a Google Cloud project
   - Copy the generated API key

4. **Add to .env File**
   ```
   GOOGLE_API_KEY=your-actual-api-key-here
   ```

### API Configuration

The system uses **Gemini 2.5 Flash** model by default (configured in `config.py`):

```python
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.5
```

### API Limits

- **Rate Limits**: Vary by model and tier
- **Quota**: Check your Google Cloud Console for current quotas
- **Cost**: Pay-per-use pricing, check [Google AI Pricing](https://ai.google.dev/pricing)

### Free Tier

Google Gemini API offers a free tier with generous limits:
- Free tier available for development and testing
- Check current limits at: https://ai.google.dev/pricing

### Troubleshooting

**"API key not found" error:**
- Verify `GOOGLE_API_KEY` is set in `.env` file
- Ensure no extra spaces or quotes around the key
- Restart the application after adding the key

**"Quota exceeded" error:**
- Check your Google Cloud Console for quota limits
- Consider upgrading your API tier if needed

---

## Dependency Management

### Core Dependencies

**Slack Integration:**
- `slack-sdk==3.39.0` - Slack SDK for Python
- `slack-bolt==1.27.0` - Bolt framework for Slack apps

**LLM & Agents:**
- `langchain>=0.3.0` - LangChain framework
- `langchain-core>=0.3.0` - LangChain core components
- `langchain-google-genai>=2.0.0` - Google Gemini integration
- `openai==2.14.0` - OpenAI API (optional, fallback)

**Utilities:**
- `python-dotenv==1.2.1` - Environment variable management
- `pytest==9.0.2` - Testing framework
- `ruff==0.14.10` - Linting and formatting
- `langsmith>=0.1.0` - LangSmith observability (optional)

### Installation

All dependencies are specified in [`requirements.txt`](requirements.txt):

```bash
pip install -r requirements.txt
```

### Version Constraints

- **Python**: 3.10+ required
- **LangChain**: 0.3.0+ (modern agent patterns)
- **Slack SDK**: Latest stable versions

### Optional Dependencies

- **LangSmith**: For experiment tracking and observability
- **OpenAI**: Alternative LLM provider (fallback if Gemini unavailable)

---

## Example Queries

The chatbot can handle various types of questions about the app portfolio database:

### Simple Questions

**Count Queries:**
- "how many apps do we have?"
- "how many android apps do we have?"
- "what about iOS?" (follow-up question)

**Expected Response**: Simple numeric answer (e.g., "49", "29", "21")

### Complex Questions

**Revenue Analysis:**
- "which country generates the most revenue?"
- "show me the top 5 revenue iOS apps"
- "what are the top 3 countries by total revenue?"

**Expected Response**: Formatted table with country/revenue data, plus assumptions note

**Aggregation Queries:**
- "show in a table format the top 5 revenue iOS apps. Include details for each app such as total revenue, country and other fields"
- "list all iOS apps sorted by their popularity"
- "compare revenue and profit margins across product categories"

**Expected Response**: Markdown table with multiple columns, sorted appropriately

**Comparative Analysis:**
- "which apps had the biggest change in UA spend comparing Jan 2025 to Dec 2024?"
- "compare sales performance by traffic source"
- "analyze gender-based purchasing preferences across product categories"

**Expected Response**: Table with comparative data, optional assumptions note

### CSV Export Requests

- "export this as csv"
- "save this report to csv"
- "download the results"

**Expected Response**: "CSV report generated and uploaded." [CSV file attached]

### SQL Retrieval Requests

- "show me the SQL you used to retrieve all the apps"
- "what SQL did you use?"
- "show me the SQL query for android apps"

**Expected Response**: SQL query in code block format:
```sql
SELECT COUNT(DISTINCT app_name) FROM app_portfolio WHERE platform = 'Android'
```

### Off-Topic Questions

- "Hello, how are you?"
- "What's the weather today?"
- "Tell me a joke"

**Expected Response**: Polite message explaining specialization and suggesting appropriate use cases

**For more example queries, see:** [`tests/scenarios/assignment_queries.md`](tests/scenarios/assignment_queries.md)

---

## Project Structure

```
slack_AI-SQL_ChatBot/
├── README.md                    # This file
├── SETUP_GUIDE.md              # Detailed setup instructions
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project configuration
├── manifest.json                # Slack app manifest
├── config.py                    # Application configuration
├── app.py                       # Main application entry point
├── app_oauth.py                # OAuth implementation (optional)
│
├── ai/                          # AI and agent modules
│   ├── agents/                  # LangChain ReAct agents
│   │   ├── orchestrator.py      # Agent orchestrator (coordinator)
│   │   ├── router_agent.py     # Intent classification
│   │   ├── sql_query_agent.py # SQL generation & execution
│   │   ├── csv_export_agent.py # CSV export agent
│   │   ├── sql_retrieval_agent.py # SQL retrieval agent
│   │   ├── off_topic_handler.py  # Off-topic handler
│   │   ├── tools.py             # LangChain tools
│   │   └── router_tools.py      # Router-specific tools
│   ├── llm_caller.py            # LLM integration (Gemini/OpenAI)
│   └── memory_store.py          # Thread-based memory management
│
├── services/                    # Core services
│   ├── sql_service.py           # SQL query execution
│   ├── formatting_service.py   # Result formatting
│   └── csv_service.py           # CSV generation & upload
│
├── prompts/                     # Centralized prompts
│   ├── router_prompt.py         # Router agent prompt
│   ├── sql_query_prompt.py     # SQL query agent prompt
│   ├── csv_export_prompt.py    # CSV export agent prompt
│   ├── sql_retrieval_prompt.py # SQL retrieval agent prompt
│   ├── off_topic_prompt.py     # Off-topic handler prompt
│   └── formatting_prompt.py   # Formatting guidelines
│
├── listeners/                   # Slack event listeners
│   ├── assistant/               # Slack Assistant integration
│   │   ├── message.py           # Message handler
│   │   └── assistant_thread_started.py
│   ├── events/                  # Slack events
│   │   └── app_mentioned.py     # @mention handler
│   └── actions/                 # Slack actions
│       └── actions.py
│
├── data/                        # Database and data
│   ├── schema.sql               # Database schema
│   ├── sample_data.csv          # Sample data (50 records)
│   ├── db_manager.py           # Database manager
│   └── generate_sample_data.py  # Data generation script
│
├── docs/                        # Documentation
│   ├── architecture.md          # Architecture documentation
│   ├── memory.md                # Memory management docs
│   ├── phase1_database.md       # Phase 1 documentation
│   ├── phase2_services.md       # Phase 2 documentation
│   ├── phase3_agents.md         # Phase 3 documentation
│   ├── phase3_tools.md          # Tools documentation
│   ├── phase4_optimization.md   # Optimization documentation
│   ├── phase5_integration.md    # Integration documentation
│   ├── phase6_functional_testing.md # Testing documentation
│   ├── requirements.md          # Requirements documentation
│   └── stage1_slack_infrastructure.md # Slack infrastructure docs
│
├── tests/                       # Test suite
│   ├── test_*.py                # Unit tests (136 tests)
│   ├── test_integration_*.py    # Integration tests (25 tests)
│   ├── sanity/                  # Sanity checks (10 scripts)
│   │   ├── sanity_database.py
│   │   ├── sanity_orchestrator_e2e.py
│   │   └── ...
│   ├── scenarios/               # Scenario tests (13 scenarios)
│   │   ├── test_assignment_scenarios.py
│   │   └── assignment_queries.md
│   ├── langsmith/               # LangSmith experiments
│   │   ├── run_all_experiments.py
│   │   └── ...
│   └── reports/                 # Test reports
│       └── POST_CODE_REVIEW_TEST_REPORT.md
│
└── demo1.png, demo2.png        # Demo screenshots
```

---

## Key Features Summary

### ✅ Production Ready

- **Comprehensive Testing**: 200+ tests across unit, integration, sanity, scenario, and LangSmith experiments
- **100% Pass Rate**: All critical tests passing
- **Error Handling**: Graceful error handling with user-friendly messages
- **Documentation**: Complete documentation in `docs/` directory

### ✅ Modern Architecture

- **LangChain ReAct Agents**: Modern agent pattern using `create_agent`
- **Multi-Agent System**: Specialized agents for different intents
- **Router Pattern**: Efficient intent classification and routing
- **Tool-Based Design**: Clear boundaries and reusability

### ✅ Cost Optimized

- **Smart Caching**: CSV export reuses cached results (no SQL regeneration)
- **SQL Retrieval**: Uses cached SQL (no regeneration)
- **Conversation Compression**: Token-aware compression for long conversations
- **Efficient Prompts**: Optimized prompts reduce token usage

### ✅ User Experience

- **Natural Language**: Ask questions in plain English
- **Intelligent Formatting**: Automatic format selection (simple vs. tables)
- **Follow-up Questions**: Maintains conversation context
- **CSV Export**: Direct download from Slack GUI
- **SQL Transparency**: View SQL queries used for answers

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- Built with [LangChain](https://www.langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Uses [Slack Bolt for Python](https://slack.dev/bolt-python/)
- Powered by [Google Gemini](https://ai.google.dev/) API
- Inspired by modern multi-agent architectures

---

## Support

For issues, questions, or contributions:
- **GitHub Issues**: https://github.com/Kochurovskyi/slack_AI-SQL_ChatBot/issues
- **Documentation**: See `docs/` directory for detailed documentation

---

**Status**: ✅ **PRODUCTION READY**  
**Last Updated**: 2026-01-07  
**Version**: 1.0.0
