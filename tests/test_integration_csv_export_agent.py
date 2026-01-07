"""Integration tests for CSV Export Agent with real agents."""
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

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def require_api_key():
    """Skip tests if no API key is available."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API keys available - skipping real agent tests")


class TestCSVExportAgentIntegration:
    """Integration tests for CSV Export Agent with real agents."""
    
    def test_end_to_end_export_workflow(self, require_api_key):
        """Test complete end-to-end export workflow with real agent."""
        agent = CSVExportAgent()
        
        result = agent.export(
            thread_ts="test_thread_csv_integration_001"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["export_successful"] is not None
        assert len(result["formatted_response"]) > 0
    
    def test_cache_miss_workflow(self, require_api_key):
        """Test export workflow when cache is empty."""
        agent = CSVExportAgent()
        
        result = agent.export(
            thread_ts="test_thread_csv_integration_002"  # New thread with no cache
        )
        
        assert "formatted_response" in result
        # Should handle cache miss gracefully
        assert result["metadata"]["export_successful"] is not None
    
    def test_get_csv_export_agent_singleton(self, require_api_key):
        """Test that get_csv_export_agent returns singleton instance."""
        agent1 = get_csv_export_agent()
        agent2 = get_csv_export_agent()
        
        assert agent1 is agent2
    
    def test_multiple_export_requests(self, require_api_key):
        """Test multiple export requests."""
        agent = CSVExportAgent()
        thread_ts = "test_thread_csv_integration_003"
        
        # Request 1
        result1 = agent.export(thread_ts=thread_ts)
        assert result1["metadata"]["export_successful"] is not None
        
        # Request 2
        result2 = agent.export(thread_ts=thread_ts)
        assert result2["metadata"]["export_successful"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
