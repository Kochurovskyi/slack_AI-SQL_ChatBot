"""
Unit tests for memory_store module.
"""
import pytest
from ai.memory_store import MemoryStore
import config
from langchain_core.messages import HumanMessage, AIMessage


class TestMemoryStore:
    """Test cases for MemoryStore class."""
    
    def test_initialization(self):
        """Test MemoryStore initialization."""
        store = MemoryStore()
        assert store._max_messages == config.MAX_MESSAGES_PER_THREAD
        assert len(store._store) == 0
    
    def test_add_and_get_user_message(self):
        """Test adding and retrieving user messages."""
        store = MemoryStore()
        thread_ts = "123.456"
        
        store.add_user_message(thread_ts, "Hello")
        messages = store.get_messages(thread_ts)
        
        assert len(messages) == 1
        assert isinstance(messages[0], HumanMessage)
        assert messages[0].content == "Hello"
    
    def test_add_and_get_assistant_message(self):
        """Test adding and retrieving assistant messages."""
        store = MemoryStore()
        thread_ts = "123.456"
        
        store.add_assistant_message(thread_ts, "Hi there!")
        messages = store.get_messages(thread_ts)
        
        assert len(messages) == 1
        assert isinstance(messages[0], AIMessage)
        assert messages[0].content == "Hi there!"
    
    def test_conversation_history(self):
        """Test maintaining conversation history."""
        store = MemoryStore()
        thread_ts = "123.456"
        
        store.add_user_message(thread_ts, "Hello")
        store.add_assistant_message(thread_ts, "Hi!")
        store.add_user_message(thread_ts, "How are you?")
        store.add_assistant_message(thread_ts, "I'm good!")
        
        messages = store.get_messages(thread_ts)
        assert len(messages) == 4
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi!"
        assert messages[2].content == "How are you?"
        assert messages[3].content == "I'm good!"
    
    def test_message_trimming(self):
        """Test that messages are trimmed to max limit."""
        store = MemoryStore(max_messages=3)
        thread_ts = "123.456"
        
        # Add 5 messages (should trim to 3)
        for i in range(5):
            store.add_user_message(thread_ts, f"Message {i}")
        
        messages = store.get_messages(thread_ts)
        assert len(messages) == 3
        assert messages[0].content == "Message 2"
        assert messages[1].content == "Message 3"
        assert messages[2].content == "Message 4"
    
    def test_clear_memory(self):
        """Test clearing memory for a thread."""
        store = MemoryStore()
        thread_ts = "123.456"
        
        store.add_user_message(thread_ts, "Hello")
        assert len(store.get_messages(thread_ts)) == 1
        
        store.clear_memory(thread_ts)
        assert thread_ts not in store._store
    
    def test_multiple_threads_isolation(self):
        """Test that different threads have isolated memory."""
        store = MemoryStore()
        thread1 = "111.111"
        thread2 = "222.222"
        
        store.add_user_message(thread1, "Thread 1 message")
        store.add_user_message(thread2, "Thread 2 message")
        
        messages1 = store.get_messages(thread1)
        messages2 = store.get_messages(thread2)
        
        assert len(messages1) == 1
        assert len(messages2) == 1
        assert messages1[0].content == "Thread 1 message"
        assert messages2[0].content == "Thread 2 message"

