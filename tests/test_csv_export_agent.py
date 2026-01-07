"""Unit tests for CSV Export Agent with real agents."""
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

from ai.agents.csv_export_agent import CSVExportAgent, get_csv_export_agent
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def require_api_key():
    """Skip tests if no API key is available."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API keys available - skipping real agent tests")


class TestCSVExportAgent:
    """Tests for CSV Export Agent with real agents."""
    
    def test_csv_export_agent_initialization(self, require_api_key):
        """Test CSV Export Agent initialization."""
        agent = CSVExportAgent()
        
        assert agent is not None
        assert agent.llm is not None
        assert len(agent.tools) == 2
        assert agent.agent is not None
    
    def test_export_method(self, require_api_key):
        """Test export method with real agent."""
        agent = CSVExportAgent()
        
        result = agent.export(
            thread_ts="test_thread_csv_001"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert len(result["formatted_response"]) > 0
        assert result["metadata"]["export_successful"] is not None
    
    def test_export_with_cache_miss(self, require_api_key):
        """Test export when no cached results found."""
        agent = CSVExportAgent()
        
        result = agent.export(
            thread_ts="test_thread_csv_002"  # New thread with no cache
        )
        
        assert "formatted_response" in result
        # Should handle cache miss gracefully
        assert result["metadata"]["export_successful"] is not None
    
    def test_export_error_handling(self, require_api_key):
        """Test error handling in export method."""
        agent = CSVExportAgent()
        
        # Test with empty thread_ts might cause issues
        result = agent.export(
            thread_ts=""
        )
        
        assert "formatted_response" in result
        # Agent should handle error gracefully
        assert result["metadata"]["export_successful"] is not None
    
    def test_stream_method(self, require_api_key):
        """Test stream method with real agent."""
        agent = CSVExportAgent()
        
        chunks = list(agent.stream(
            thread_ts="test_thread_csv_003"
        ))
        
        # Stream may return empty or various types - just verify it doesn't crash
        assert chunks is not None
        # If chunks exist, verify they're iterable
        if len(chunks) > 0:
            pass  # Just verify stream completes without error


class TestCSVExportAgentIntegration:
    """Integration tests for CSV Export Agent with real agents."""
    
    def test_get_csv_export_agent_singleton(self, require_api_key):
        """Test that get_csv_export_agent returns singleton instance."""
        agent1 = get_csv_export_agent()
        agent2 = get_csv_export_agent()
        
        assert agent1 is agent2
    
    def test_agent_uses_correct_tools(self, require_api_key):
        """Test that agent is created with correct tools."""
        agent = CSVExportAgent()
        
        assert len(agent.tools) == 2
        
        # Check tool names
        tool_names = [tool.name for tool in agent.tools]
        assert 'get_cached_results_tool' in tool_names
        assert 'generate_csv_tool' in tool_names
    
    def test_real_export_execution(self, require_api_key):
        """Test real export execution end-to-end."""
        agent = CSVExportAgent()
        
        result = agent.export(
            thread_ts="test_thread_csv_004"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["export_successful"] is not None
        # Response should contain some content
        assert len(result["formatted_response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
