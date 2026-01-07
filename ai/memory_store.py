"""
Memory store for managing conversation history per thread.
Uses LangChain's InMemoryChatMessageHistory for thread-based memory.
"""
import logging
from typing import Dict, List, Optional, Any

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import config
logger = logging.getLogger(__name__)


class MemoryStore:
    """ Thread-based memory store for conversation history
        Each Slack thread maintains its own conversation history."""
    
    def __init__(self, max_messages: int = config.MAX_MESSAGES_PER_THREAD):
        """ Initialize the memory store
            Args: max_messages: Maximum number of messages to keep per thread (default: 10)"""
        self._store: Dict[str, InMemoryChatMessageHistory] = {}
        self._sql_queries: Dict[str, List[Dict[str, Any]]] = {}  # thread_ts -> list of {sql, question, results, timestamp}
        self._max_messages = max_messages
    
    def get_memory(self, thread_ts: str) -> InMemoryChatMessageHistory:
        """ Get or create memory for a thread.
            Args: thread_ts: Slack thread timestamp (unique identifier)
            Returns: InMemoryChatMessageHistory instance for the thread"""
        if thread_ts not in self._store:
            self._store[thread_ts] = InMemoryChatMessageHistory()
            logger.debug(f"Created new memory for thread: {thread_ts}")
        return self._store[thread_ts]
    
    def add_user_message(self, thread_ts: str, content: str) -> None:
        """ Add a user message to thread memory.
            Args: thread_ts: Slack thread timestamp content: Message content"""
        memory = self.get_memory(thread_ts)
        memory.add_user_message(content)
        self._trim_messages(thread_ts)
        logger.debug(f"Added user message to thread {thread_ts}")
    
    def add_assistant_message(self, thread_ts: str, content: str) -> None:
        """ Add an assistant message to thread memory.
            Args: thread_ts: Slack thread timestamp, content: Message content"""
        memory = self.get_memory(thread_ts)
        memory.add_ai_message(content)
        self._trim_messages(thread_ts)
        logger.debug(f"Added assistant message to thread {thread_ts}")
    
    def get_messages(self, thread_ts: str) -> List[BaseMessage]:
        """ Get all messages for a thread
            Args: thread_ts: Slack thread timestamp
            Returns: List of BaseMessage objects"""
        memory = self.get_memory(thread_ts)
        return memory.messages
    
    def clear_memory(self, thread_ts: str) -> None:
        """ Clear memory for a specific thread
            Args:thread_ts: Slack thread timestamp"""
        if thread_ts in self._store:
            del self._store[thread_ts]
            logger.debug(f"Cleared memory for thread: {thread_ts}")
    
    def store_sql_query(self, thread_ts: str, sql_query: str, question: str, results: Optional[Dict[str, Any]] = None) -> None:
        """ Store SQL query and results for a thread.
            Args: thread_ts: Slack thread timestamp
                  sql_query: SQL query string
                  question: Original user question
                  results: Optional query results"""
        if thread_ts not in self._sql_queries:
            self._sql_queries[thread_ts] = []
        
        from datetime import datetime
        self._sql_queries[thread_ts].append({
            'sql': sql_query,
            'question': question,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 queries per thread
        if len(self._sql_queries[thread_ts]) > 10:
            self._sql_queries[thread_ts] = self._sql_queries[thread_ts][-10:]
        
        logger.debug(f"Stored SQL query for thread {thread_ts}")
    
    def get_sql_queries(self, thread_ts: str) -> List[Dict[str, Any]]:
        """ Get all SQL queries for a thread.
            Args: thread_ts: Slack thread timestamp
            Returns: List of SQL query dictionaries"""
        return self._sql_queries.get(thread_ts, [])
    
    def get_last_sql_query(self, thread_ts: str) -> Optional[Dict[str, Any]]:
        """ Get the last SQL query for a thread.
            Args: thread_ts: Slack thread timestamp
            Returns: Last SQL query dictionary or None"""
        queries = self.get_sql_queries(thread_ts)
        return queries[-1] if queries else None
    
    def get_last_query_results(self, thread_ts: str) -> Optional[Dict[str, Any]]:
        """ Get the last query results for a thread.
            Args: thread_ts: Slack thread timestamp
            Returns: Last query results or None"""
        last_query = self.get_last_sql_query(thread_ts)
        return last_query.get('results') if last_query else None
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation: ~4 chars per token).
        
        Args:
            text: Text to estimate tokens for
        
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def _estimate_message_tokens(self, messages: List[BaseMessage]) -> int:
        """Estimate total token count for messages.
        
        Args:
            messages: List of messages
        
        Returns:
            Estimated total token count
        """
        total = 0
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                total += self._estimate_tokens(str(msg.content))
        return total
    
    def _compress_old_messages(self, thread_ts: str, messages: List[BaseMessage], keep_recent: int = 5) -> List[BaseMessage]:
        """Compress old messages by summarizing them.
        
        Args:
            thread_ts: Thread timestamp
            messages: List of messages to compress
            keep_recent: Number of recent messages to keep in full detail
        
        Returns:
            List with recent messages in full and compressed older messages
        """
        if len(messages) <= keep_recent:
            return messages
        
        # Keep recent messages in full
        recent_messages = messages[-keep_recent:]
        old_messages = messages[:-keep_recent]
        
        # Summarize old messages
        summaries = []
        for i in range(0, len(old_messages), 2):  # Process pairs (user + assistant)
            if i + 1 < len(old_messages):
                user_msg = old_messages[i]
                assistant_msg = old_messages[i + 1]
                
                if isinstance(user_msg, HumanMessage) and isinstance(assistant_msg, AIMessage):
                    user_content = user_msg.content if hasattr(user_msg, 'content') else ""
                    assistant_content = assistant_msg.content if hasattr(assistant_msg, 'content') else ""
                    
                    # Create summary
                    summary = f"User asked: {user_content[:100]}{'...' if len(user_content) > 100 else ''}. Response: {assistant_content[:100]}{'...' if len(assistant_content) > 100 else ''}"
                    summaries.append(HumanMessage(content=summary))
        
        # Combine summaries with recent messages
        return summaries + recent_messages
    
    def _trim_messages(self, thread_ts: str) -> None:
        """ Trim messages to keep only the last N messages per thread.
        If conversation exceeds token limit, compress old messages.
            Args: thread_ts: Slack thread timestamp"""
        memory = self.get_memory(thread_ts)
        messages = memory.messages
        
        if len(messages) <= self._max_messages:
            # Check token count
            token_count = self._estimate_message_tokens(messages)
            max_tokens = getattr(config, 'MAX_CONVERSATION_TOKENS', 4000)
            compression_trigger = int(max_tokens * 0.8)  # 80% of max
            
            if token_count > compression_trigger:
                # Compress old messages
                logger.info(f"Compressing conversation history for thread {thread_ts} (tokens: {token_count})")
                compressed = self._compress_old_messages(thread_ts, messages, keep_recent=5)
                memory.clear()
                for msg in compressed:
                    if isinstance(msg, HumanMessage): 
                        memory.add_user_message(msg.content)
                    elif isinstance(msg, AIMessage): 
                        memory.add_ai_message(msg.content)
                    elif isinstance(msg, SystemMessage): 
                        continue
                logger.debug(f"Compressed messages for thread {thread_ts}: {len(messages)} -> {len(compressed)}")
            return
        
        # If too many messages, trim to max_messages
        messages_to_keep = messages[-self._max_messages:]
        # Clear and re-add messages
        memory.clear()
        for msg in messages_to_keep:
            if isinstance(msg, HumanMessage): memory.add_user_message(msg.content)
            elif isinstance(msg, AIMessage): memory.add_ai_message(msg.content)
            elif isinstance(msg, SystemMessage): continue # System messages are typically not stored in history
        logger.debug(f"Trimmed messages for thread {thread_ts} to {len(messages_to_keep)} messages")


# Global memory store instance
memory_store = MemoryStore(max_messages=config.MAX_MESSAGES_PER_THREAD)

