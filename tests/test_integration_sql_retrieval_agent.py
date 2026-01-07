"""Integration tests for SQL Retrieval Agent with real agents."""
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

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def require_api_key():
    """Skip tests if no API key is available."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API keys available - skipping real agent tests")


class TestSQLRetrievalAgentIntegration:
    """Integration tests for SQL Retrieval Agent with real agents."""
    
    def test_end_to_end_retrieval_workflow(self, require_api_key):
        """Test complete end-to-end retrieval workflow with real agent."""
        agent = SQLRetrievalAgent()
        
        result = agent.retrieve(
            thread_ts="test_thread_retrieval_integration_001"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["sql_found"] is not None
        assert len(result["formatted_response"]) > 0
    
    def test_cache_miss_workflow(self, require_api_key):
        """Test retrieval workflow when cache is empty."""
        agent = SQLRetrievalAgent()
        
        result = agent.retrieve(
            thread_ts="test_thread_retrieval_integration_002"  # New thread with no cache
        )
        
        assert "formatted_response" in result
        # Should handle cache miss gracefully
        assert result["metadata"]["sql_found"] is not None
    
    def test_get_sql_retrieval_agent_singleton(self, require_api_key):
        """Test that get_sql_retrieval_agent returns singleton instance."""
        agent1 = get_sql_retrieval_agent()
        agent2 = get_sql_retrieval_agent()
        
        assert agent1 is agent2
    
    def test_multiple_retrieval_requests(self, require_api_key):
        """Test multiple retrieval requests."""
        agent = SQLRetrievalAgent()
        thread_ts = "test_thread_retrieval_integration_003"
        
        # Request 1
        result1 = agent.retrieve(thread_ts=thread_ts)
        assert result1["metadata"]["sql_found"] is not None
        
        # Request 2
        result2 = agent.retrieve(thread_ts=thread_ts)
        assert result2["metadata"]["sql_found"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
