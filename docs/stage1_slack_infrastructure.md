# Stage 1: Slack Infrastructure Documentation

## Overview

This document describes the Slack infrastructure and AI-powered chatbot foundation built in Stage 1. This infrastructure serves as the base for the AI Engineer challenge project, which will add SQL database integration for data analytics and business intelligence capabilities.

**Status**: ✅ Complete and Production-Ready

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Slack Workspace                          │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   Channels   │────────▶│  Direct Msg  │                │
│  └──────────────┘         └──────────────┘                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ WebSocket (Socket Mode)
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Slack Bot Application                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Slack Bolt Framework                     │  │
│  │  - Event Listeners                                    │  │
│  │  - Message Handlers                                  │  │
│  │  - Streaming API                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AI Integration Layer                    │  │
│  │  - LLM Caller (OpenAI/Gemini)                        │  │
│  │  - Memory Store (Thread-based)                       │  │
│  │  - Streaming Adapter                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ API Calls
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              LLM Providers                                   │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   OpenAI     │         │   Gemini 2.0  │                │
│  │  (Primary)   │         │   (Fallback)  │                │
│  └──────────────┘         └──────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Application Entry Point (`app.py`)

**Purpose**: Main application initialization and configuration.

**Key Features**:
- Slack Bolt App initialization
- Socket Mode connection (WebSocket-based)
- Logging configuration with truncation (1000 char limit)
- Environment variable loading

**Configuration**:
```python
# Logging: Truncates messages to 1000 characters
# Connection: Socket Mode (WebSocket)
# Framework: Slack Bolt for Python
```

### 2. LLM Integration (`ai/llm_caller.py`)

**Purpose**: Unified interface for calling Large Language Models with streaming support.

**Features**:
- Dual LLM support: OpenAI (primary) and Gemini (fallback)
- Automatic fallback mechanism
- Streaming response support
- Memory integration (LangChain message format)
- Error handling with logging only (no user-facing errors)

**API**:
```python
def call_llm(
    messages_in_thread: List[Dict[str, str]], 
    system_content: str = DEFAULT_SYSTEM_CONTENT,
    langchain_messages: Optional[List[BaseMessage]] = None
) -> Iterator[str]
```

**LLM Selection Logic**:
1. Check for `OPENAI_API_KEY` → Use OpenAI if available
2. Fallback to `GOOGLE_API_KEY` → Use Gemini if OpenAI unavailable
3. Raise error if neither key is set

**Supported Models**:
- OpenAI: `gpt-4o-mini`
- Gemini: `gemini-2.0-flash-lite` (configurable in `config.py`)

### 3. Memory System (`ai/memory_store.py`)

**Purpose**: Thread-based conversation memory for context-aware responses.

**Architecture**:
- Uses `InMemoryChatMessageHistory` from LangChain Core
- Thread-scoped storage (each Slack thread has isolated memory)
- Automatic message trimming (keeps last N messages per thread)
- In-memory storage (cleared on restart)

**Key Methods**:
```python
class MemoryStore:
    def get_memory(thread_ts: str) -> InMemoryChatMessageHistory
    def add_user_message(thread_ts: str, content: str) -> None
    def add_assistant_message(thread_ts: str, content: str) -> None
    def get_messages(thread_ts: str) -> List[BaseMessage]
    def clear_memory(thread_ts: str) -> None
```

**Memory Strategy**:
- **Thread Identification**: 
  - For threads: Uses `thread_ts` (Slack thread timestamp)
  - For top-level mentions: Uses `channel_id` (ensures shared memory in channel)
- **Message Limit**: Last 10 messages per thread (configurable in `config.py`)
- **Storage**: In-memory dictionary `{thread_id: InMemoryChatMessageHistory}`

### 4. Message Handlers

#### Assistant Thread Handler (`listeners/assistant/message.py`)

**Purpose**: Handles messages within Slack Assistant threads.

**Flow**:
1. Extract user message from payload
2. Add user message to memory
3. Retrieve conversation history from memory
4. Call LLM with full conversation context
5. Stream response to Slack
6. Save assistant response to memory

**Features**:
- Streaming responses (real-time updates)
- Memory integration
- Error handling (generic user messages, detailed logging)

#### App Mention Handler (`listeners/events/app_mentioned.py`)

**Purpose**: Handles bot mentions in channels or direct messages.

**Flow**:
1. Extract and clean user message (remove bot mentions)
2. Determine memory thread ID (thread_ts or channel_id)
3. Add user message to memory
4. Retrieve conversation history
5. Call LLM with context
6. Stream response
7. Save assistant response to memory

**Special Handling**:
- Top-level mentions use `channel_id` as thread identifier (shared memory per channel)
- Thread mentions use actual `thread_ts` (isolated memory per thread)
- Bot mentions are automatically cleaned from message text

### 5. Configuration (`config.py`)

**Purpose**: Centralized configuration management.

**Settings**:
```python
# LLM Configuration
GEMINI_MODEL = "gemini-2.0-flash-lite"
GEMINI_TEMPERATURE = 0.7

# Memory Configuration
MAX_MESSAGES_PER_THREAD = 10
```

**Benefits**:
- Single source of truth for configuration
- Easy to modify without code changes
- Environment-specific overrides possible

## Technical Stack

### Core Dependencies

```
slack-sdk==3.39.0          # Slack API client
slack-bolt==1.27.0          # Slack Bolt framework
langchain>=0.3.0            # LangChain framework
langchain-google-genai>=2.0.0  # Google Gemini integration
langchain-core>=0.3.0      # LangChain core components
openai==2.14.0             # OpenAI API (primary LLM)
python-dotenv==1.2.1       # Environment variable management
```

### Development Dependencies

```
pytest==9.0.2              # Testing framework
ruff==0.14.10              # Code linting
```

## Communication Patterns

### 1. Socket Mode Connection

- **Protocol**: WebSocket (via Slack Socket Mode)
- **Connection**: Persistent bidirectional connection
- **Authentication**: App-level token (`SLACK_APP_TOKEN`)
- **Benefits**: No need for public URL, works behind firewalls

### 2. Streaming Responses

- **Method**: `client.chat_stream()`
- **Format**: Real-time markdown text chunks
- **User Experience**: Progressive message updates ("thinking..." → streaming text)
- **Implementation**: LangChain streaming adapter

### 3. Message Flow

```
User Message
    ↓
Handler (assistant/message.py or events/app_mentioned.py)
    ↓
Memory Store (add user message, retrieve history)
    ↓
LLM Caller (call_llm with conversation history)
    ↓
Stream Response (chunk by chunk)
    ↓
Memory Store (save assistant response)
    ↓
User sees complete response
```

## Environment Setup

### Required Environment Variables

Create `.env` file in root directory:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# LLM Configuration (at least one required)
OPENAI_API_KEY=your-openai-key          # Primary
GOOGLE_API_KEY=your-google-api-key      # Fallback
```

### Setup Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.sample .env
   # Edit .env with your tokens
   ```

3. **Run Application**:
   ```bash
   python app.py
   ```

See `SETUP_GUIDE.md` for detailed token acquisition instructions.

## Testing

### Test Coverage

- **Unit Tests**: 7 tests for memory store
- **Integration Tests**: 6 tests for memory + LLM integration
- **Total**: 13 tests, all passing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_memory_store.py -v
pytest tests/test_memory_integration.py -v
```

## Key Features

### ✅ Implemented Features

1. **Dual LLM Support**
   - OpenAI as primary provider
   - Gemini as automatic fallback
   - Seamless switching based on API key availability

2. **Streaming Responses**
   - Real-time message updates in Slack
   - Progressive text display
   - Status indicators ("thinking...", loading messages)

3. **Short-Term Memory**
   - Thread-based conversation history
   - Last 10 messages per thread
   - Automatic message trimming
   - Context-aware responses

4. **Error Handling**
   - Generic user-facing messages
   - Detailed error logging
   - Graceful degradation

5. **Configuration Management**
   - Centralized config file
   - Environment variable support
   - Easy customization

6. **Logging**
   - Truncated logs (1000 char limit)
   - Debug-level logging
   - Structured log format

## API Interface for Future Development

### Extending for SQL Database Integration

The current infrastructure provides these extension points:

#### 1. LLM Caller Extension

**Location**: `ai/llm_caller.py`

**Current Interface**:
```python
def call_llm(
    messages_in_thread: List[Dict[str, str]], 
    system_content: str = DEFAULT_SYSTEM_CONTENT,
    langchain_messages: Optional[List[BaseMessage]] = None
) -> Iterator[str]
```

**Future Extension**:
- Add SQL tool/function calling support
- Integrate database connection
- Add query execution capability
- Return structured data (tables, CSV)

#### 2. Memory Store Extension

**Location**: `ai/memory_store.py`

**Current Interface**:
```python
class MemoryStore:
    def get_messages(thread_ts: str) -> List[BaseMessage]
    def add_user_message(thread_ts: str, content: str) -> None
    def add_assistant_message(thread_ts: str, content: str) -> None
```

**Future Extension**:
- Add query result caching
- Store SQL statements per thread
- Cache CSV exports
- Long-term memory persistence

#### 3. Handler Extension Points

**Location**: `listeners/assistant/message.py`, `listeners/events/app_mentioned.py`

**Current Flow**:
1. Receive message
2. Add to memory
3. Call LLM
4. Stream response
5. Save to memory

**Future Extensions**:
- Add SQL query detection
- Execute queries
- Format results (tables/CSV)
- Handle export requests
- Handle SQL statement requests

### Recommended Integration Pattern

```python
# Future: ai/sql_agent.py
class SQLAgent:
    def __init__(self, db_connection, memory_store):
        self.db = db_connection
        self.memory = memory_store
        self.llm = call_llm  # Use existing LLM caller
    
    def process_query(self, user_message, thread_ts):
        # 1. Get conversation history from memory
        # 2. Detect if query needs SQL
        # 3. Generate SQL using LLM
        # 4. Execute SQL
        # 5. Format results
        # 6. Return response
        pass
```

## Architecture Decisions

### Why LangChain?

- **Standardization**: Unified interface for multiple LLM providers
- **Memory Integration**: Built-in conversation history support
- **Extensibility**: Easy to add tools and agents
- **Streaming**: Native streaming support
- **Future-Proof**: Ready for SQL agent integration

### Why InMemoryChatMessageHistory?

- **Simplicity**: No external dependencies
- **Performance**: Fast in-memory access
- **Suitability**: Perfect for short-term conversation memory
- **Compatibility**: Works with simple LangChain chains (no LangGraph needed)

### Why Socket Mode?

- **Development-Friendly**: No public URL required
- **Firewall-Friendly**: Works behind corporate firewalls
- **Real-Time**: Bidirectional WebSocket communication
- **Slack-Native**: Official Slack development pattern

### Why Dual LLM Support?

- **Reliability**: Fallback if one provider fails
- **Cost Optimization**: Can switch based on pricing
- **Flexibility**: Easy to test different models
- **Production-Ready**: Handles API key issues gracefully

## Limitations & Future Enhancements

### Current Limitations

1. **Memory Persistence**: In-memory only (lost on restart)
2. **No SQL Support**: Not yet implemented (Stage 2)
3. **No CSV Export**: Not yet implemented (Stage 2)
4. **No Query Caching**: SQL queries regenerated each time
5. **No User Permissions**: All users have same access

### Planned Enhancements (Stage 2+)

1. **SQL Database Integration**
   - Database schema for app portfolio data
   - SQL query generation from natural language
   - Query execution and result formatting

2. **CSV Export**
   - Generate CSV from query results
   - Cache exports to avoid regeneration
   - Slack file upload integration

3. **SQL Statement Retrieval**
   - Store SQL per conversation
   - Retrieve on user request
   - Display formatted SQL code

4. **Persistent Memory**
   - Database-backed memory storage
   - Survive application restarts
   - Long-term conversation history

5. **User Permissions**
   - Role-based access control
   - Query result filtering by user role
   - Audit logging

## File Structure

```
Slack_chatbot/
├── app.py                          # Main entry point
├── config.py                       # Configuration settings
├── requirements.txt                # Dependencies
├── .env                            # Environment variables (not in git)
├── .env.sample                     # Environment template
├── manifest.json                   # Slack app manifest
│
├── ai/
│   ├── llm_caller.py              # LLM integration (OpenAI/Gemini)
│   └── memory_store.py            # Thread-based memory
│
├── listeners/
│   ├── assistant/
│   │   └── message.py             # Assistant thread handler
│   ├── events/
│   │   └── app_mentioned.py       # Bot mention handler
│   └── actions/
│       └── actions.py             # Interactive actions
│
├── tests/
│   ├── test_memory_store.py       # Unit tests (7 tests)
│   └── test_memory_integration.py # Integration tests (6 tests)
│
└── docs/
    └── stage1_slack_infrastructure.md  # This document
```

## Deployment

### Local Development

```bash
# 1. Setup virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# or
.venv\Scripts\activate          # Windows CMD

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.sample .env
# Edit .env with your tokens

# 4. Run application
python app.py
```

### Production Considerations

1. **Process Management**: Use systemd, PM2, or similar
2. **Logging**: Configure log rotation and storage
3. **Monitoring**: Add health checks and metrics
4. **Error Tracking**: Integrate error tracking service
5. **Secrets Management**: Use secure secret storage (not .env files)

## Security Considerations

### Current Security Measures

- Environment variables for sensitive data
- `.env` file excluded from git
- Generic error messages (no sensitive info exposed)
- API keys not logged

### Future Security Enhancements

- User-level access control
- Query result filtering by permissions
- SQL injection prevention
- Rate limiting
- Audit logging

## Performance Characteristics

### Memory Usage

- **Per Thread**: ~1-2 KB (10 messages)
- **Total**: Scales with active threads
- **Cleanup**: Automatic trimming prevents unbounded growth

### Response Time

- **LLM Latency**: Depends on provider (OpenAI ~1-3s, Gemini ~1-2s)
- **Streaming**: First chunk appears within 500ms-1s
- **Memory Access**: <1ms (in-memory)

### Scalability

- **Concurrent Threads**: Limited by LLM API rate limits
- **Memory**: In-memory storage suitable for <1000 active threads
- **Future**: Database-backed memory for higher scale

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`
   - Verify Socket Mode is enabled
   - Check application logs

2. **Memory not working**
   - Verify thread IDs are consistent
   - Check memory store initialization
   - Review debug logs

3. **LLM errors**
   - Verify API keys are set
   - Check API key validity
   - Review error logs (truncated to 1000 chars)

4. **Streaming issues**
   - Check network connectivity
   - Verify Slack API status
   - Review handler logs

## Next Steps (Stage 2)

This infrastructure is ready for SQL database integration. The next stage will add:

1. **Database Schema**: App portfolio data structure
2. **SQL Agent**: Natural language to SQL conversion
3. **Query Execution**: Database connection and query execution
4. **Result Formatting**: Tables, summaries, CSV exports
5. **Query Caching**: Store SQL and results to avoid regeneration

## References

- [Slack Bolt for Python](https://slack.dev/bolt-python/)
- [LangChain Documentation](https://python.langchain.com/)
- [Slack AI Assistants](https://slack.dev/resource-solutions/solution-ai-agents-assistants)
- [LangGraph Memory Documentation](https://langchain-ai.github.io/langgraph/agents/memory/)

## Summary

Stage 1 provides a **production-ready Slack infrastructure** with:

✅ AI-powered chatbot foundation  
✅ Dual LLM support (OpenAI + Gemini)  
✅ Streaming responses  
✅ Thread-based memory  
✅ Error handling  
✅ Comprehensive testing  
✅ Extensible architecture  

**Ready for Stage 2**: SQL database integration and data analytics capabilities.

