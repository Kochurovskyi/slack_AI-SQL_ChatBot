"""
Integration tests for memory system with LLM caller.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from ai.memory_store import MemoryStore
from ai.llm_caller import call_llm
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class TestMemoryIntegration:
    """Integration tests for memory + LLM caller."""
    
    def test_memory_store_with_conversation_flow(self):
        """Test that memory maintains conversation across multiple interactions."""
        store = MemoryStore(max_messages=10)
        thread_ts = "123.456"
        
        # Simulate conversation flow
        store.add_user_message(thread_ts, "Hello, my name is Alice")
        store.add_assistant_message(thread_ts, "Hi Alice! Nice to meet you.")
        store.add_user_message(thread_ts, "What's my name?")
        
        messages = store.get_messages(thread_ts)
        assert len(messages) == 3
        assert messages[0].content == "Hello, my name is Alice"
        assert messages[1].content == "Hi Alice! Nice to meet you."
        assert messages[2].content == "What's my name?"
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch('ai.llm_caller.ChatGoogleGenerativeAI')
    def test_llm_caller_with_memory_messages(self, mock_gemini):
        """Test LLM caller accepts memory messages."""
        # Mock Gemini response
        mock_llm_instance = MagicMock()
        mock_gemini.return_value = mock_llm_instance
        
        # Mock streaming response
        mock_chunk = MagicMock()
        mock_chunk.content = "Hello"
        mock_llm_instance.stream.return_value = [mock_chunk]
        
        # Create memory messages
        memory_messages = [
            HumanMessage(content="Hi"),
            AIMessage(content="Hello!"),
            HumanMessage(content="How are you?")
        ]
        
        # Call LLM with memory
        result = list(call_llm(
            messages_in_thread=[],
            langchain_messages=memory_messages
        ))
        
        # Verify LLM was called with memory messages
        assert len(result) > 0
        mock_llm_instance.stream.assert_called_once()
        call_args = mock_llm_instance.stream.call_args[0][0]
        assert len(call_args) == 4  # SystemMessage + 3 memory messages
        assert isinstance(call_args[0], SystemMessage)
    
    def test_memory_persistence_across_calls(self):
        """Test that memory persists across multiple LLM calls."""
        store = MemoryStore()
        thread_ts = "789.012"
        
        # First interaction
        store.add_user_message(thread_ts, "I like pizza")
        store.add_assistant_message(thread_ts, "That's great!")
        
        # Second interaction
        store.add_user_message(thread_ts, "What do I like?")
        
        messages = store.get_messages(thread_ts)
        assert len(messages) == 3
        assert messages[0].content == "I like pizza"
        assert messages[1].content == "That's great!"
        assert messages[2].content == "What do I like?"
    
    def test_memory_trimming_in_conversation(self):
        """Test that memory trimming works during active conversation."""
        store = MemoryStore(max_messages=3)
        thread_ts = "345.678"
        
        # Add messages beyond limit
        for i in range(5):
            store.add_user_message(thread_ts, f"Message {i}")
            store.add_assistant_message(thread_ts, f"Response {i}")
        
        # Should only keep last 3 pairs (6 messages total, but trimmed to 3)
        messages = store.get_messages(thread_ts)
        assert len(messages) == 3  # Last 3 messages
        assert "Message 4" in messages[-1].content or "Response 4" in messages[-1].content
    
    def test_multiple_threads_memory_isolation(self):
        """Test that different threads maintain separate memory."""
        store = MemoryStore()
        thread1 = "111.111"
        thread2 = "222.222"
        
        # Add messages to both threads
        store.add_user_message(thread1, "Thread 1: Hello")
        store.add_assistant_message(thread1, "Thread 1: Hi")
        store.add_user_message(thread2, "Thread 2: Hey")
        store.add_assistant_message(thread2, "Thread 2: Hello")
        
        # Verify isolation
        messages1 = store.get_messages(thread1)
        messages2 = store.get_messages(thread2)
        
        assert len(messages1) == 2
        assert len(messages2) == 2
        assert messages1[0].content == "Thread 1: Hello"
        assert messages2[0].content == "Thread 2: Hey"
    
    def test_memory_with_empty_thread(self):
        """Test memory behavior with new/empty thread."""
        store = MemoryStore()
        thread_ts = "999.999"
        
        # Get messages from new thread
        messages = store.get_messages(thread_ts)
        assert len(messages) == 0
        
        # Add first message
        store.add_user_message(thread_ts, "First message")
        messages = store.get_messages(thread_ts)
        assert len(messages) == 1

