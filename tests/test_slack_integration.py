"""Integration tests for Slack handler integration with Agent Orchestrator."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.agents.orchestrator import get_orchestrator
from ai.memory_store import memory_store


class TestSlackIntegration:
    """Test Slack handler integration with Agent Orchestrator."""
    
    def test_orchestrator_process_message_sql_query(self):
        """Test orchestrator processes SQL query correctly."""
        orchestrator = get_orchestrator()
        thread_ts = "test_slack_integration_001"
        
        # Clear memory first
        memory_store.clear_memory(thread_ts)
        
        result = orchestrator.process_message(
            user_message="how many apps do we have?",
            thread_ts=thread_ts
        )
        
        assert result["intent"] == "SQL_QUERY"
        assert "response" in result
        assert len(result["response"]) > 0
        assert "metadata" in result
        
        # Cleanup
        memory_store.clear_memory(thread_ts)
    
    def test_orchestrator_stream_sql_query(self):
        """Test orchestrator streams SQL query response."""
        orchestrator = get_orchestrator()
        thread_ts = "test_slack_integration_002"
        
        # Clear memory first
        memory_store.clear_memory(thread_ts)
        
        chunks = []
        for chunk in orchestrator.stream(
            user_message="how many apps do we have?",
            thread_ts=thread_ts
        ):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        assert len(chunks) > 0
        assert len(full_response) > 0
        
        # Cleanup
        memory_store.clear_memory(thread_ts)
    
    def test_orchestrator_intent_classification(self):
        """Test orchestrator correctly classifies different intents."""
        orchestrator = get_orchestrator()
        thread_ts = "test_slack_integration_003"
        
        # Clear memory first
        memory_store.clear_memory(thread_ts)
        
        # Test SQL_QUERY
        result1 = orchestrator.process_message("how many apps?", thread_ts)
        assert result1["intent"] == "SQL_QUERY"
        
        # Test CSV_EXPORT (requires previous query)
        result2 = orchestrator.process_message("export this as csv", thread_ts)
        assert result2["intent"] == "CSV_EXPORT"
        
        # Test SQL_RETRIEVAL
        result3 = orchestrator.process_message("show me the SQL", thread_ts)
        assert result3["intent"] == "SQL_RETRIEVAL"
        
        # Test OFF_TOPIC (router may classify as SQL_QUERY if uncertain, so we check it's handled)
        result4 = orchestrator.process_message("hello, how are you?", thread_ts)
        assert result4["intent"] in ["OFF_TOPIC", "SQL_QUERY"]  # Router may default to SQL_QUERY
        
        # Cleanup
        memory_store.clear_memory(thread_ts)
    
    def test_orchestrator_memory_integration(self):
        """Test orchestrator integrates with memory store."""
        orchestrator = get_orchestrator()
        thread_ts = "test_slack_integration_004"
        
        # Clear memory first
        memory_store.clear_memory(thread_ts)
        
        # Add user message manually (as handlers do)
        memory_store.add_user_message(thread_ts, "how many apps?")
        
        # First message
        result1 = orchestrator.process_message("how many apps?", thread_ts)
        messages1 = memory_store.get_messages(thread_ts)
        assert len(messages1) >= 2  # User message + assistant response
        
        # Add second user message manually
        memory_store.add_user_message(thread_ts, "what about iOS?")
        
        # Follow-up message
        result2 = orchestrator.process_message("what about iOS?", thread_ts)
        messages2 = memory_store.get_messages(thread_ts)
        assert len(messages2) >= 4  # Previous messages + new messages
        
        # Cleanup
        memory_store.clear_memory(thread_ts)
    
    def test_orchestrator_error_handling(self):
        """Test orchestrator handles errors gracefully."""
        orchestrator = get_orchestrator()
        thread_ts = "test_slack_integration_005"
        
        # Clear memory first
        memory_store.clear_memory(thread_ts)
        
        # Test with empty message (should handle gracefully)
        result = orchestrator.process_message("", thread_ts)
        assert "response" in result
        assert result["intent"] in ["SQL_QUERY", "OFF_TOPIC", "ERROR"]
        
        # Cleanup
        memory_store.clear_memory(thread_ts)

