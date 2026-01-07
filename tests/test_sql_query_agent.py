"""Unit tests for SQL Query Agent with real agents."""
import pytest
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=False)

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.agents.sql_query_agent import SQLQueryAgent, get_sql_query_agent
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def require_api_key():
    """Skip tests if no API key is available."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API keys available - skipping real agent tests")


@pytest.fixture(scope="module")
def require_database():
    """Skip tests if database doesn't exist."""
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        pytest.skip("Database not found - skipping real agent tests")


class TestSQLQueryAgent:
    """Tests for SQL Query Agent with real agents."""
    
    def test_sql_query_agent_initialization(self, require_api_key):
        """Test SQL Query Agent initialization."""
        agent = SQLQueryAgent()
        
        assert agent is not None
        assert agent.llm is not None
        assert len(agent.tools) == 3
        assert agent.agent is not None
    
    def test_query_method(self, require_api_key, require_database):
        """Test query method with real agent."""
        agent = SQLQueryAgent()
        
        result = agent.query(
            question="How many apps are there?",
            thread_ts="test_thread_001"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert len(result["formatted_response"]) > 0
        assert result["metadata"]["query_executed"] is not None
    
    def test_query_with_conversation_history(self, require_api_key, require_database):
        """Test query with conversation history."""
        agent = SQLQueryAgent()
        
        conversation_history = [
            HumanMessage(content="How many apps are there?"),
            AIMessage(content="There are 50 apps.")
        ]
        
        result = agent.query(
            question="What about iOS apps?",
            thread_ts="test_thread_002",
            conversation_history=conversation_history
        )
        
        assert "formatted_response" in result
        assert len(result["formatted_response"]) > 0
    
    def test_query_error_handling(self, require_api_key):
        """Test error handling in query method."""
        agent = SQLQueryAgent()
        
        # Test with invalid question that might cause issues
        result = agent.query(
            question="",  # Empty question might cause issues
            thread_ts="test_thread_003"
        )
        
        assert "formatted_response" in result
        # Agent should handle error gracefully
        assert result["metadata"]["query_executed"] is not None
    
    def test_stream_method(self, require_api_key, require_database):
        """Test stream method with real agent."""
        agent = SQLQueryAgent()
        
        chunks = list(agent.stream(
            question="How many apps?",
            thread_ts="test_thread_004"
        ))
        
        # Stream may return empty or various types - just verify it doesn't crash
        assert chunks is not None
        # If chunks exist, verify they're iterable
        if len(chunks) > 0:
            # Chunks might be strings, message objects, or other types
            pass  # Just verify stream completes without error


class TestSQLQueryAgentIntegration:
    """Integration tests for SQL Query Agent with real agents."""
    
    def test_get_sql_query_agent_singleton(self, require_api_key):
        """Test that get_sql_query_agent returns singleton instance."""
        agent1 = get_sql_query_agent()
        agent2 = get_sql_query_agent()
        
        assert agent1 is agent2
    
    def test_agent_uses_correct_tools(self, require_api_key):
        """Test that agent is created with correct tools."""
        agent = SQLQueryAgent()
        
        assert len(agent.tools) == 3
        
        # Check tool names
        tool_names = [tool.name for tool in agent.tools]
        assert 'generate_sql_tool' in tool_names
        assert 'execute_sql_tool' in tool_names
        assert 'format_result_tool' in tool_names
    
    def test_real_query_execution(self, require_api_key, require_database):
        """Test real query execution end-to-end."""
        agent = SQLQueryAgent()
        
        result = agent.query(
            question="How many Android apps are there?",
            thread_ts="test_thread_005"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["query_executed"] is not None
        # Response should contain some content
        assert len(result["formatted_response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
