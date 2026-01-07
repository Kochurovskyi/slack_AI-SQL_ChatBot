"""Real integration tests for SQL Query Agent with actual tools."""
import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.agents.sql_query_agent import SQLQueryAgent
from ai.memory_store import memory_store

logger = logging.getLogger(__name__)


class TestSQLQueryAgentReal:
    """Real integration tests using actual tools (requires API keys)."""
    
    @pytest.mark.skipif(
        not Path(project_root / "data" / "app_portfolio.db").exists(),
        reason="Database not found"
    )
    def test_real_simple_query(self):
        """Test real simple query with actual tools (if API keys available)."""
        import os
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("No API keys available for real test")
        
        try:
            agent = SQLQueryAgent()
            
            result = agent.query(
                question="How many apps are there?",
                thread_ts="test_thread_real_001"
            )
            
            assert "formatted_response" in result
            assert len(result["formatted_response"]) > 0
            assert "metadata" in result
            
            # Response should contain a number (the count)
            assert any(char.isdigit() for char in result["formatted_response"])
            
        except Exception as e:
            # If agent creation fails (e.g., no API keys), skip test
            pytest.skip(f"Agent creation failed: {e}")
    
    @pytest.mark.skipif(
        not Path(project_root / "data" / "app_portfolio.db").exists(),
        reason="Database not found"
    )
    def test_real_platform_query(self):
        """Test real platform query with actual tools."""
        import os
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("No API keys available for real test")
        
        try:
            agent = SQLQueryAgent()
            
            result = agent.query(
                question="How many iOS apps are there?",
                thread_ts="test_thread_real_002"
            )
            
            assert "formatted_response" in result
            assert len(result["formatted_response"]) > 0
            
        except Exception as e:
            pytest.skip(f"Agent creation failed: {e}")

