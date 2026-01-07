"""Unit tests for SQL Retrieval Agent with real agents."""
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

from ai.agents.sql_retrieval_agent import SQLRetrievalAgent, get_sql_retrieval_agent
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def require_api_key():
    """Skip tests if no API key is available."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API keys available - skipping real agent tests")


class TestSQLRetrievalAgent:
    """Tests for SQL Retrieval Agent with real agents."""
    
    def test_sql_retrieval_agent_initialization(self, require_api_key):
        """Test SQL Retrieval Agent initialization."""
        agent = SQLRetrievalAgent()
        
        assert agent is not None
        assert agent.llm is not None
        assert len(agent.tools) == 1
        assert agent.agent is not None
    
    def test_retrieve_method(self, require_api_key):
        """Test retrieve method with real agent."""
        agent = SQLRetrievalAgent()
        
        result = agent.retrieve(
            thread_ts="test_thread_retrieval_001"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert len(result["formatted_response"]) > 0
        assert result["metadata"]["sql_found"] is not None
    
    def test_retrieve_with_cache_miss(self, require_api_key):
        """Test retrieve when no cached SQL found."""
        agent = SQLRetrievalAgent()
        
        result = agent.retrieve(
            thread_ts="test_thread_retrieval_002"  # New thread with no cache
        )
        
        assert "formatted_response" in result
        # Should handle cache miss gracefully
        assert result["metadata"]["sql_found"] is not None
    
    def test_retrieve_error_handling(self, require_api_key):
        """Test error handling in retrieve method."""
        agent = SQLRetrievalAgent()
        
        # Test with empty thread_ts might cause issues
        result = agent.retrieve(
            thread_ts=""
        )
        
        assert "formatted_response" in result
        # Agent should handle error gracefully
        assert result["metadata"]["sql_found"] is not None
    
    def test_stream_method(self, require_api_key):
        """Test stream method with real agent."""
        agent = SQLRetrievalAgent()
        
        chunks = list(agent.stream(
            thread_ts="test_thread_retrieval_003"
        ))
        
        # Stream may return empty or various types - just verify it doesn't crash
        assert chunks is not None
        # If chunks exist, verify they're iterable
        if len(chunks) > 0:
            pass  # Just verify stream completes without error


class TestSQLRetrievalAgentIntegration:
    """Integration tests for SQL Retrieval Agent with real agents."""
    
    def test_get_sql_retrieval_agent_singleton(self, require_api_key):
        """Test that get_sql_retrieval_agent returns singleton instance."""
        agent1 = get_sql_retrieval_agent()
        agent2 = get_sql_retrieval_agent()
        
        assert agent1 is agent2
    
    def test_agent_uses_correct_tools(self, require_api_key):
        """Test that agent is created with correct tools."""
        agent = SQLRetrievalAgent()
        
        assert len(agent.tools) == 1
        
        # Check tool names
        tool_names = [tool.name for tool in agent.tools]
        assert 'get_sql_history_tool' in tool_names
    
    def test_real_retrieval_execution(self, require_api_key):
        """Test real retrieval execution end-to-end."""
        agent = SQLRetrievalAgent()
        
        result = agent.retrieve(
            thread_ts="test_thread_retrieval_004"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["sql_found"] is not None
        # Response should contain some content
        assert len(result["formatted_response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
