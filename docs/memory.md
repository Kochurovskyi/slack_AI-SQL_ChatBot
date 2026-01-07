# Memory Management Architecture

**Document Version:** 1.0  
**Last Updated:** 2026-01-07  
**Status:** Production Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Memory Store Implementation](#memory-store-implementation)
4. [Agent Integration Patterns](#agent-integration-patterns)
5. [Why Custom Solution?](#why-custom-solution)
6. [Memory Features](#memory-features)
7. [Configuration](#configuration)
8. [Usage Examples](#usage-examples)
9. [Performance Considerations](#performance-considerations)

---

## Overview

The Slack Chatbot implements a **custom thread-based memory management system** (`ai/memory_store.py`) that provides:

- **Thread-scoped conversation history** (each Slack thread maintains separate memory)
- **SQL query and results caching** (beyond conversation history)
- **Automatic conversation compression** (token-aware memory management)
- **Query history retrieval** (by description matching)
- **Cost optimization** (reuse cached results for CSV exports)

This document explains how agents use the memory store, why a custom solution was chosen over LangGraph/LangChain built-in options, and the specific memory management behaviors.

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Slack Thread (thread_ts)                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           MemoryStore (Global Singleton)             │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  _store: Dict[str, InMemoryChatMessageHistory]      │   │
│  │    └─ thread_ts → Conversation History              │   │
│  │                                                       │   │
│  │  _sql_queries: Dict[str, List[Dict]]                │   │
│  │    └─ thread_ts → [SQL queries with metadata]       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Agent Orchestrator                      │   │
│  │  • Fetches conversation history                      │   │
│  │  • Routes to specialized agents                      │   │
│  │  • Saves assistant responses                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────┬──────────────┬──────────────┐           │
│  │ SQL Query    │ CSV Export   │ SQL Retrieval│           │
│  │ Agent        │ Agent        │ Agent        │           │
│  │              │              │              │           │
│  │ • Stores SQL │ • Retrieves  │ • Retrieves  │           │
│  │ • Stores     │   cached     │   SQL        │           │
│  │   results    │   results    │   history    │           │
│  └──────────────┴──────────────┴──────────────┘           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Tools (LangChain Tools)                │   │
│  │  • get_sql_history_tool                             │   │
│  │  • get_cached_results_tool                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Memory Data Structures

**1. Conversation History (`_store`)**
```python
Dict[str, InMemoryChatMessageHistory]
# Key: thread_ts (e.g., "1234567890.123456")
# Value: LangChain InMemoryChatMessageHistory instance
# Contains: List[BaseMessage] (HumanMessage, AIMessage)
```

**2. SQL Query Cache (`_sql_queries`)**
```python
Dict[str, List[Dict[str, Any]]]
# Key: thread_ts
# Value: List of query dictionaries:
#   {
#     'sql': str,              # SQL query string
#     'question': str,          # Original user question
#     'results': Dict,         # Query execution results
#     'timestamp': str         # ISO timestamp
#   }
```

---

## Memory Store Implementation

### Core Class: `MemoryStore`

**Location:** `ai/memory_store.py`

**Key Methods:**

#### 1. Conversation History Management

```python
def get_memory(thread_ts: str) -> InMemoryChatMessageHistory
```
- **Purpose:** Get or create conversation history for a thread
- **Returns:** LangChain `InMemoryChatMessageHistory` instance
- **Thread Isolation:** Each `thread_ts` has separate memory

```python
def add_user_message(thread_ts: str, content: str) -> None
def add_assistant_message(thread_ts: str, content: str) -> None
```
- **Purpose:** Add messages to thread history
- **Auto-trimming:** Automatically triggers `_trim_messages()` after adding

```python
def get_messages(thread_ts: str) -> List[BaseMessage]
```
- **Purpose:** Retrieve all messages for a thread
- **Returns:** List of `HumanMessage`, `AIMessage` objects
- **Used by:** Agents to get conversation context

#### 2. SQL Query Caching

```python
def store_sql_query(
    thread_ts: str,
    sql_query: str,
    question: str,
    results: Optional[Dict[str, Any]] = None
) -> None
```
- **Purpose:** Store SQL query and results for later retrieval
- **Storage:** Keeps last 10 queries per thread
- **Metadata:** Stores original question, SQL, results, timestamp

```python
def get_sql_queries(thread_ts: str) -> List[Dict[str, Any]]
def get_last_sql_query(thread_ts: str) -> Optional[Dict[str, Any]]
def get_last_query_results(thread_ts: str) -> Optional[Dict[str, Any]]
```
- **Purpose:** Retrieve stored SQL queries and results
- **Used by:** SQL Retrieval Agent, CSV Export Agent

#### 3. Conversation Compression

```python
def _trim_messages(thread_ts: str) -> None
```
- **Purpose:** Manage conversation length and token usage
- **Strategy:**
  1. If message count ≤ `MAX_MESSAGES_PER_THREAD`: Check token count
  2. If tokens > 80% of `MAX_CONVERSATION_TOKENS`: Compress old messages
  3. If message count > `MAX_MESSAGES_PER_THREAD`: Trim to last N messages

```python
def _compress_old_messages(
    thread_ts: str,
    messages: List[BaseMessage],
    keep_recent: int = 5
) -> List[BaseMessage]
```
- **Purpose:** Summarize old messages while preserving recent context
- **Algorithm:**
  - Keep last `keep_recent` messages in full detail
  - Summarize older message pairs (user + assistant)
  - Create `HumanMessage` with summary: `"User asked: {question[:100]}... Response: {response[:100]}..."`

```python
def _estimate_tokens(text: str) -> int
def _estimate_message_tokens(messages: List[BaseMessage]) -> int
```
- **Purpose:** Estimate token count for compression decisions
- **Approximation:** ~4 characters per token (rough estimate)

---

## Agent Integration Patterns

### 1. Agent Orchestrator (`ai/agents/orchestrator.py`)

**Memory Usage Pattern:**

```python
# Pattern: Fetch → Process → Store

# 1. Fetch conversation history
if conversation_history is None:
    conversation_history = memory_store.get_messages(thread_ts)

# 2. Route to agent (passes history)
agent_result = self.sql_query_agent.query(
    question=user_message,
    thread_ts=thread_ts,
    conversation_history=conversation_history
)

# 3. Store assistant response
if response:
    memory_store.add_assistant_message(thread_ts, response)
```

**Responsibilities:**
- ✅ Fetches conversation history before routing
- ✅ Passes history to specialized agents
- ✅ Stores final assistant responses
- ✅ Manages thread-scoped memory lifecycle

**Key Methods:**
- `process_message()`: Non-streaming processing with memory integration
- `stream()`: Streaming processing with memory integration

---

### 2. SQL Query Agent (`ai/agents/sql_query_agent.py`)

**Memory Usage Pattern:**

```python
# Pattern: Fetch → Generate → Execute → Store

# 1. Fetch conversation history
if conversation_history is None:
    conversation_history = memory_store.get_messages(thread_ts)

# 2. Build context-aware user message
if conversation_history:
    context = "\n".join([f"{role}: {msg.content}" 
                        for msg in conversation_history[-3:]])

# 3. Execute query workflow
result = self.agent.invoke({"messages": [HumanMessage(content=user_message)]})

# 4. Store SQL query and results
if sql_query:
    memory_store.store_sql_query(
        thread_ts=thread_ts,
        sql_query=sql_query,
        question=question,
        results=query_results
    )
```

**Responsibilities:**
- ✅ Retrieves conversation history for context-aware SQL generation
- ✅ Stores executed SQL queries for later retrieval
- ✅ Stores query results for CSV export reuse
- ✅ Enables follow-up questions with context

**Key Methods:**
- `query()`: Main query execution with memory storage
- `stream()`: Streaming query execution (calls `query()` internally)

**Memory Storage:**
- **Conversation History:** Used for context (not stored by agent)
- **SQL Queries:** Stored via `memory_store.store_sql_query()`
- **Query Results:** Stored as part of SQL query metadata

---

### 3. SQL Retrieval Agent (`ai/agents/sql_retrieval_agent.py`)

**Memory Usage Pattern:**

```python
# Pattern: Tool-Based Retrieval

# Agent uses get_sql_history_tool (which accesses memory_store)
# Tool internally calls:
queries = memory_store.get_sql_queries(thread_ts)
```

**Responsibilities:**
- ✅ Retrieves stored SQL queries via tools
- ✅ Supports query selection by description
- ✅ Formats SQL for Slack display (code blocks)

**Key Methods:**
- `retrieve()`: Retrieves SQL via `get_sql_history_tool`
- `stream()`: Streams formatted SQL response

**Memory Access:**
- **Indirect:** Uses `get_sql_history_tool` (tool accesses `memory_store`)
- **No Direct Storage:** Only reads from memory store

---

### 4. CSV Export Agent (`ai/agents/csv_export_agent.py`)

**Memory Usage Pattern:**

```python
# Pattern: Tool-Based Retrieval → Generate CSV

# Agent uses get_cached_results_tool (which accesses memory_store)
# Tool internally calls:
last_query = memory_store.get_last_sql_query(thread_ts)
results = last_query.get('results')
```

**Responsibilities:**
- ✅ Retrieves cached query results (no SQL regeneration)
- ✅ Generates CSV from cached results
- ✅ Cost optimization (avoids re-executing SQL)

**Key Methods:**
- `export()`: Retrieves cached results via `get_cached_results_tool`
- `stream()`: Streams CSV export confirmation

**Memory Access:**
- **Indirect:** Uses `get_cached_results_tool` (tool accesses `memory_store`)
- **Cost Benefit:** Reuses cached results instead of regenerating SQL

---

### 5. Router Agent (`ai/agents/router_agent.py`)

**Memory Usage Pattern:**

```python
# Pattern: Fetch → Classify

# 1. Fetch conversation history for context
if conversation_history is None:
    conversation_history = memory_store.get_messages(thread_ts)

# 2. Use history for intent classification
routing_result = self.router_agent.classify_intent(
    user_message=user_message,
    thread_ts=thread_ts,
    conversation_history=conversation_history
)
```

**Responsibilities:**
- ✅ Uses conversation history for context-aware routing
- ✅ Handles follow-up questions (e.g., "export this as csv")
- ✅ No direct memory storage (only reads)

**Key Methods:**
- `classify_intent()`: Uses conversation history for routing decisions

---

### 6. Tools (`ai/agents/tools.py`)

**Memory-Accessing Tools:**

#### `get_sql_history_tool(thread_ts: str, query_description: Optional[str] = None)`

```python
# Direct memory_store access
from ai.memory_store import memory_store

queries = memory_store.get_sql_queries(thread_ts)

# Supports description matching
if query_description:
    # Search for matching query by description
    for query_info in reversed(queries):
        if query_description.lower() in query_info.get('question', '').lower():
            return query_info
```

**Features:**
- ✅ Retrieves SQL queries from memory store
- ✅ Supports description-based search
- ✅ Returns last query if no description provided

#### `get_cached_results_tool(thread_ts: str)`

```python
# Direct memory_store access
from ai.memory_store import memory_store

last_query = memory_store.get_last_sql_query(thread_ts)
results = last_query.get('results') if last_query else None
```

**Features:**
- ✅ Retrieves last query results
- ✅ Used by CSV Export Agent for cost optimization
- ✅ Returns structured data (data, row_count, sql_query, timestamp)

---

## Why Custom Solution?

### Comparison: Custom vs. LangGraph/LangChain Built-in

#### LangChain Built-in Options

**1. `InMemoryChatMessageHistory`**
- ✅ **What we use:** As the underlying storage mechanism
- ❌ **Limitations:**
  - No thread-scoped isolation (we add this)
  - No SQL query caching (we add this)
  - No automatic compression (we add this)
  - No query history retrieval (we add this)

**2. LangGraph StateGraph Memory**
- ✅ **Available:** LangGraph provides state management
- ❌ **Limitations:**
  - Designed for LangGraph workflows (we use LangChain agents)
  - Overkill for our simple multi-agent architecture
  - Doesn't support SQL query/results caching
  - Requires LangGraph state management (we don't use LangGraph)

**3. LangChain Memory Classes (`ConversationBufferMemory`, `ConversationSummaryMemory`)**
- ✅ **Available:** Built-in memory classes
- ❌ **Limitations:**
  - Single conversation scope (no thread isolation)
  - No SQL query caching
  - Summary memory uses LLM calls (costly, we use simple compression)
  - Not designed for Slack thread-based architecture

#### Our Custom Solution Advantages

**1. Thread-Scoped Isolation**
```python
# Each Slack thread has separate memory
memory_store.get_memory("thread_1")  # Separate from thread_2
memory_store.get_memory("thread_2")   # Separate from thread_1
```
- ✅ **Why:** Slack threads are independent conversations
- ✅ **Benefit:** No cross-thread memory leakage
- ❌ **LangChain:** Single conversation scope by default

**2. SQL Query and Results Caching**
```python
# Store SQL queries with metadata
memory_store.store_sql_query(
    thread_ts=thread_ts,
    sql_query="SELECT COUNT(*) FROM app_portfolio",
    question="how many apps do we have?",
    results={"success": True, "data": [{"COUNT(*)": 49}]}
)
```
- ✅ **Why:** Need to retrieve SQL queries and reuse results
- ✅ **Benefit:** CSV export reuses cached results (cost optimization)
- ✅ **Benefit:** SQL retrieval shows past queries
- ❌ **LangChain:** No built-in SQL query caching

**3. Description-Based Query Retrieval**
```python
# Find SQL query by description
get_sql_history_tool(thread_ts="123", query_description="all the apps")
# Returns: SQL query for "how many apps do we have?"
```
- ✅ **Why:** Users ask "show SQL for all the apps" (not thread_ts)
- ✅ **Benefit:** Natural language query matching
- ❌ **LangChain:** No built-in query history retrieval

**4. Token-Aware Compression**
```python
# Automatic compression when approaching token limit
if token_count > compression_trigger:
    compressed = self._compress_old_messages(thread_ts, messages, keep_recent=5)
```
- ✅ **Why:** Long conversations exceed token limits
- ✅ **Benefit:** Simple summarization (no LLM calls)
- ✅ **Benefit:** Keeps recent context in full detail
- ❌ **LangChain SummaryMemory:** Uses LLM calls (costly)

**5. Slack Integration**
```python
# Thread timestamp as unique identifier
thread_ts = event.get("thread_ts") or event.get("ts")
memory_store.get_messages(thread_ts)
```
- ✅ **Why:** Slack uses thread timestamps for conversation threads
- ✅ **Benefit:** Natural integration with Slack API
- ❌ **LangChain:** Not designed for Slack thread model

**6. Cost Optimization**
```python
# CSV export reuses cached results (no SQL regeneration)
cached_results = memory_store.get_last_query_results(thread_ts)
# No need to regenerate SQL or re-execute query
```
- ✅ **Why:** CSV export should reuse previous query results
- ✅ **Benefit:** Avoids redundant SQL generation and execution
- ❌ **LangChain:** No built-in result caching

---

## Memory Features

### 1. Thread-Scoped Isolation

**Implementation:**
```python
self._store: Dict[str, InMemoryChatMessageHistory] = {}
# Key: thread_ts (Slack thread timestamp)
# Value: Separate conversation history per thread
```

**Benefits:**
- ✅ Each Slack thread maintains independent conversation
- ✅ No cross-thread memory leakage
- ✅ Natural Slack integration (thread_ts as identifier)

**Example:**
```python
# Thread 1: "how many apps?"
memory_store.add_user_message("thread_1", "how many apps?")
memory_store.add_assistant_message("thread_1", "49")

# Thread 2: Separate conversation
memory_store.add_user_message("thread_2", "what about iOS?")
# Thread 2 has no context from Thread 1 ✅
```

---

### 2. SQL Query Caching

**Implementation:**
```python
self._sql_queries: Dict[str, List[Dict[str, Any]]] = {}
# Stores: sql, question, results, timestamp per thread
```

**Storage Format:**
```python
{
    'sql': 'SELECT COUNT(*) FROM app_portfolio',
    'question': 'how many apps do we have?',
    'results': {'success': True, 'data': [{'COUNT(*)': 49}]},
    'timestamp': '2026-01-07T10:30:00'
}
```

**Benefits:**
- ✅ SQL Retrieval Agent can show past queries
- ✅ CSV Export Agent reuses cached results (cost optimization)
- ✅ Query history with timestamps and original questions
- ✅ Supports description-based search

**Retention:**
- Keeps last 10 queries per thread
- Automatic cleanup when exceeding limit

---

### 3. Conversation Compression

**Trigger Conditions:**
1. **Message Count:** If messages > `MAX_MESSAGES_PER_THREAD` (default: 10)
2. **Token Count:** If tokens > 80% of `MAX_CONVERSATION_TOKENS` (default: 3200 tokens)

**Compression Algorithm:**
```python
# Keep last 5 messages in full detail
recent_messages = messages[-5:]

# Summarize older messages (user + assistant pairs)
for i in range(0, len(old_messages), 2):
    user_msg = old_messages[i]
    assistant_msg = old_messages[i + 1]
    summary = f"User asked: {user_content[:100]}... Response: {assistant_content[:100]}..."
    summaries.append(HumanMessage(content=summary))

# Combine: summaries + recent messages
return summaries + recent_messages
```

**Benefits:**
- ✅ Enables long conversations without token limit errors
- ✅ Preserves recent context in full detail
- ✅ Simple summarization (no LLM calls, cost-effective)
- ✅ Automatic management (no manual intervention)

**Example:**
```
Before Compression (10 messages, 4000 tokens):
  User: "how many apps?"
  Assistant: "49"
  User: "what about iOS?"
  Assistant: "21"
  ... (6 more messages)

After Compression (7 messages, ~2500 tokens):
  [Summary] User asked: how many apps?... Response: 49...
  [Summary] User asked: what about iOS?... Response: 21...
  ... (last 5 messages in full detail)
```

---

### 4. Description-Based Query Retrieval

**Implementation:**
```python
def get_sql_history_tool(thread_ts: str, query_description: Optional[str] = None):
    queries = memory_store.get_sql_queries(thread_ts)
    
    if query_description:
        # Search for matching query
        query_lower = query_description.lower()
        for query_info in reversed(queries):
            question = query_info.get('question', '').lower()
            if query_lower in question or any(word in question 
                                             for word in query_lower.split() 
                                             if len(word) > 3):
                return query_info  # Found matching query
```

**Benefits:**
- ✅ Natural language query matching
- ✅ Users can ask "show SQL for all the apps" (not thread_ts)
- ✅ Searches by original question text
- ✅ Falls back to last query if no match

**Example:**
```python
# User: "show me the SQL you used to retrieve all the apps"
get_sql_history_tool(thread_ts="123", query_description="all the apps")
# Matches: "how many apps do we have?" → Returns SQL query
```

---

### 5. Cost Optimization

**CSV Export Reuse:**
```python
# Without caching: Regenerate SQL + Re-execute query
# Cost: SQL generation + Query execution

# With caching: Reuse cached results
cached_results = memory_store.get_last_query_results(thread_ts)
# Cost: 0 (no SQL generation, no query execution)
```

**Benefits:**
- ✅ CSV export doesn't regenerate SQL
- ✅ CSV export doesn't re-execute queries
- ✅ Significant cost savings for CSV exports
- ✅ Faster CSV generation (no database query)

---

## Configuration

**File:** `config.py`

```python
# Memory Configuration
MAX_MESSAGES_PER_THREAD = 10          # Max messages before trimming
MAX_CONVERSATION_TOKENS = 4000        # Max tokens before compression
COMPRESSION_TRIGGER_RATIO = 0.8       # Compress at 80% of max tokens
KEEP_RECENT_MESSAGES = 5              # Keep last N messages in full detail
```

**Tuning Guidelines:**

| Parameter | Default | Purpose | When to Increase | When to Decrease |
|-----------|---------|---------|-----------------|------------------|
| `MAX_MESSAGES_PER_THREAD` | 10 | Prevent unbounded growth | More context needed | Memory constraints |
| `MAX_CONVERSATION_TOKENS` | 4000 | Token limit before compression | Longer conversations | Cost optimization |
| `COMPRESSION_TRIGGER_RATIO` | 0.8 | Compression trigger point | Earlier compression | Later compression |
| `KEEP_RECENT_MESSAGES` | 5 | Recent context preservation | More recent context | More compression |

---

## Usage Examples

### Example 1: Simple Query Flow

```python
# User: "how many apps do we have?"

# 1. Orchestrator fetches conversation history
conversation_history = memory_store.get_messages(thread_ts)  # []

# 2. SQL Query Agent executes query
result = sql_query_agent.query(
    question="how many apps do we have?",
    thread_ts=thread_ts,
    conversation_history=conversation_history
)

# 3. SQL Query Agent stores query and results
memory_store.store_sql_query(
    thread_ts=thread_ts,
    sql_query="SELECT COUNT(*) FROM app_portfolio",
    question="how many apps do we have?",
    results={"success": True, "data": [{"COUNT(*)": 49}]}
)

# 4. Orchestrator stores assistant response
memory_store.add_assistant_message(thread_ts, "49")

# Memory State:
# _store[thread_ts]: [HumanMessage("how many apps?"), AIMessage("49")]
# _sql_queries[thread_ts]: [{"sql": "SELECT COUNT(*) ...", "question": "...", ...}]
```

---

### Example 2: Follow-Up Question

```python
# User: "what about iOS?"

# 1. Orchestrator fetches conversation history
conversation_history = memory_store.get_messages(thread_ts)
# Returns: [HumanMessage("how many apps?"), AIMessage("49")]

# 2. SQL Query Agent uses history for context
# Agent understands "what about iOS?" refers to previous "apps" question
result = sql_query_agent.query(
    question="what about iOS?",
    thread_ts=thread_ts,
    conversation_history=conversation_history  # Provides context
)

# 3. Stores new query and results
memory_store.store_sql_query(
    thread_ts=thread_ts,
    sql_query="SELECT COUNT(*) FROM app_portfolio WHERE platform = 'iOS'",
    question="what about iOS?",
    results={"success": True, "data": [{"COUNT(*)": 21}]}
)

# 4. Stores assistant response
memory_store.add_assistant_message(thread_ts, "21")

# Memory State:
# _store[thread_ts]: [HumanMessage("how many apps?"), AIMessage("49"),
#                     HumanMessage("what about iOS?"), AIMessage("21")]
# _sql_queries[thread_ts]: [query1, query2]
```

---

### Example 3: CSV Export (Cost Optimization)

```python
# User: "export this as csv"

# 1. CSV Export Agent uses cached results tool
# Tool internally calls:
last_query = memory_store.get_last_sql_query(thread_ts)
results = last_query.get('results')  # {"success": True, "data": [...]}

# 2. CSV Export Agent generates CSV from cached results
# No SQL regeneration ✅
# No query re-execution ✅
csv_file_path = generate_csv_tool(results['data'])

# Cost Savings:
# Without caching: SQL generation + Query execution = ~$0.001
# With caching: CSV generation only = ~$0.0001
# Savings: 90% cost reduction ✅
```

---

### Example 4: SQL Retrieval by Description

```python
# User: "show me the SQL you used to retrieve all the apps"

# 1. SQL Retrieval Agent uses get_sql_history_tool
# Tool internally calls:
queries = memory_store.get_sql_queries(thread_ts)
# Returns: [query1, query2, ...]

# 2. Tool searches by description
query_description = "all the apps"
for query_info in reversed(queries):
    if "all the apps" in query_info.get('question', '').lower():
        # Matches: "how many apps do we have?"
        return query_info  # Returns SQL query

# 3. Agent formats SQL for Slack display
formatted_response = f"```sql\n{query_info['sql']}\n```"
```

---

### Example 5: Conversation Compression

```python
# Long conversation (15 messages, 5000 tokens)

# 1. User sends new message
memory_store.add_user_message(thread_ts, "another question")

# 2. _trim_messages() checks token count
token_count = _estimate_message_tokens(messages)  # 5000 tokens
compression_trigger = MAX_CONVERSATION_TOKENS * 0.8  # 3200 tokens

# 3. Compression triggered (5000 > 3200)
compressed = _compress_old_messages(thread_ts, messages, keep_recent=5)

# 4. Old messages summarized, recent messages kept
# Before: 15 messages, 5000 tokens
# After: 7 messages, ~2500 tokens
# Recent 5 messages preserved in full detail ✅
```

---

## Performance Considerations

### Memory Footprint

**Per Thread:**
- **Conversation History:** ~10 messages × ~200 tokens = ~2000 tokens
- **SQL Queries:** ~10 queries × ~500 bytes = ~5 KB
- **Total per Thread:** ~2.5 KB (in-memory)

**Global:**
- **Memory Store:** Dict overhead + thread data
- **Scalability:** O(n) where n = number of active threads
- **Cleanup:** Old threads remain in memory (no automatic cleanup)

**Recommendations:**
- ✅ Suitable for moderate thread counts (< 1000 active threads)
- ⚠️ Consider thread cleanup for high-volume scenarios
- ⚠️ Consider persistence for production (currently in-memory only)

---

### Token Estimation Accuracy

**Current Implementation:**
```python
def _estimate_tokens(text: str) -> int:
    return len(text) // 4  # Rough approximation
```

**Accuracy:**
- ✅ **Good enough** for compression decisions
- ⚠️ **Not exact** (actual tokens vary by model)
- ⚠️ **Conservative** (may compress earlier than needed)

**Recommendations:**
- ✅ Current approximation is sufficient
- ⚠️ Consider using `tiktoken` for exact token counting (if needed)
- ⚠️ Consider model-specific tokenizers (if accuracy critical)

---

### Compression Overhead

**Compression Cost:**
- **CPU:** Minimal (string operations only)
- **Memory:** Temporary (compressed messages created, then stored)
- **No LLM Calls:** Simple string summarization (cost-effective)

**Compression Frequency:**
- **Trigger:** When tokens > 80% of max (default: 3200 tokens)
- **Frequency:** Once per conversation (after compression, tokens reduced)
- **Impact:** Negligible (compression is fast)

---

## Summary

### Key Takeaways

1. **Custom Solution Justified:**
   - Thread-scoped isolation (Slack-specific)
   - SQL query/results caching (beyond conversation history)
   - Description-based query retrieval (natural language matching)
   - Token-aware compression (cost-effective)
   - Cost optimization (CSV export reuse)

2. **Agent Integration Patterns:**
   - **Orchestrator:** Fetches history, stores responses
   - **SQL Query Agent:** Stores queries and results
   - **CSV Export Agent:** Retrieves cached results
   - **SQL Retrieval Agent:** Retrieves SQL history
   - **Router Agent:** Uses history for context-aware routing
   - **Tools:** Direct memory_store access

3. **Memory Features:**
   - Thread-scoped isolation
   - SQL query caching (last 10 per thread)
   - Conversation compression (token-aware)
   - Description-based retrieval
   - Cost optimization (CSV reuse)

4. **Why Not LangGraph/LangChain Built-in:**
   - No thread-scoped isolation
   - No SQL query caching
   - No description-based retrieval
   - Compression uses LLM calls (costly)
   - Not designed for Slack thread model



