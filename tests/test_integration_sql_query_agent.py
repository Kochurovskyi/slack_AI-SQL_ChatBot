"""Integration tests for SQL Query Agent with real agents."""
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


class TestSQLQueryAgentIntegration:
    """Integration tests for SQL Query Agent with real agents."""
    
    def test_end_to_end_query_workflow(self, require_api_key, require_database):
        """Test complete end-to-end query workflow with real agent."""
        agent = SQLQueryAgent()
        
        result = agent.query(
            question="How many apps are there?",
            thread_ts="test_thread_integration_001"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["query_executed"] is not None
        assert len(result["formatted_response"]) > 0
    
    def test_follow_up_query(self, require_api_key, require_database):
        """Test follow-up query with conversation history."""
        agent = SQLQueryAgent()
        
        # First query
        result1 = agent.query(
            question="How many Android apps are there?",
            thread_ts="test_thread_integration_002"
        )
        
        assert result1["metadata"]["query_executed"] is not None
        
        # Follow-up query
        conversation_history = [
            HumanMessage(content="How many Android apps are there?"),
            AIMessage(content=result1["formatted_response"])
        ]
        
        result2 = agent.query(
            question="What about iOS apps?",
            thread_ts="test_thread_integration_002",
            conversation_history=conversation_history
        )
        
        assert "formatted_response" in result2
        assert result2["metadata"]["query_executed"] is not None
    
    def test_complex_query(self, require_api_key, require_database):
        """Test complex aggregation query."""
        agent = SQLQueryAgent()
        
        result = agent.query(
            question="Which country generates the most revenue?",
            thread_ts="test_thread_integration_003"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["query_executed"] is not None
        assert len(result["formatted_response"]) > 0
    
    def test_get_sql_query_agent_singleton(self, require_api_key):
        """Test that get_sql_query_agent returns singleton instance."""
        agent1 = get_sql_query_agent()
        agent2 = get_sql_query_agent()
        
        assert agent1 is agent2
    
    def test_multiple_queries_same_thread(self, require_api_key, require_database):
        """Test multiple queries in the same thread."""
        agent = SQLQueryAgent()
        thread_ts = "test_thread_integration_004"
        
        # Query 1
        result1 = agent.query(
            question="How many apps are there?",
            thread_ts=thread_ts
        )
        assert result1["metadata"]["query_executed"] is not None
        
        # Query 2
        result2 = agent.query(
            question="How many Android apps?",
            thread_ts=thread_ts
        )
        assert result2["metadata"]["query_executed"] is not None
        
        # Query 3
        result3 = agent.query(
            question="What about iOS?",
            thread_ts=thread_ts
        )
        assert result3["metadata"]["query_executed"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
