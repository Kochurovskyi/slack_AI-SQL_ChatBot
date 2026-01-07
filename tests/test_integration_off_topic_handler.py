"""Integration tests for Off-Topic Handler Agent with real agents."""
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

from ai.agents.off_topic_handler import OffTopicHandler, get_off_topic_handler
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def require_api_key():
    """Skip tests if no API key is available."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API keys available - skipping real agent tests")


class TestOffTopicHandlerIntegration:
    """Integration tests for Off-Topic Handler Agent with real agents."""
    
    def test_end_to_end_greeting_workflow(self, require_api_key):
        """Test complete end-to-end greeting handling workflow with real agent."""
        handler = OffTopicHandler()
        
        result = handler.handle(
            user_message="Hello, how are you?",
            thread_ts="test_thread_offtopic_integration_001"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["handled_as_off_topic"] is True
        assert len(result["formatted_response"]) > 0
    
    def test_end_to_end_general_question_workflow(self, require_api_key):
        """Test complete end-to-end general question handling workflow."""
        handler = OffTopicHandler()
        
        result = handler.handle(
            user_message="What's the capital of France?",
            thread_ts="test_thread_offtopic_integration_002"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["handled_as_off_topic"] is True
        assert len(result["formatted_response"]) > 0
    
    def test_end_to_end_use_case_suggestion_workflow(self, require_api_key):
        """Test workflow where agent suggests appropriate use cases."""
        handler = OffTopicHandler()
        
        result = handler.handle(
            user_message="What can you do for me?",
            thread_ts="test_thread_offtopic_integration_003"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["handled_as_off_topic"] is True
        assert len(result["formatted_response"]) > 0
    
    def test_error_recovery_workflow(self, require_api_key):
        """Test agent's error recovery and fallback response."""
        handler = OffTopicHandler()
        
        # Test with empty message
        result = handler.handle(
            user_message="",
            thread_ts="test_thread_offtopic_integration_004"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["handled_as_off_topic"] is True
    
    def test_multiple_message_types(self, require_api_key):
        """Test handling with various message types."""
        handler = OffTopicHandler()
        
        # Test different types of off-topic messages
        result1 = handler.handle(
            user_message="Hi",
            thread_ts="test_thread_offtopic_integration_005a"
        )
        assert result1["metadata"]["handled_as_off_topic"] is True
        
        result2 = handler.handle(
            user_message="What's the news?",
            thread_ts="test_thread_offtopic_integration_005b"
        )
        assert result2["metadata"]["handled_as_off_topic"] is True
        
        result3 = handler.handle(
            user_message="What's up?",
            thread_ts="test_thread_offtopic_integration_005c"
        )
        assert result3["metadata"]["handled_as_off_topic"] is True
    
    def test_thread_isolation(self, require_api_key):
        """Test that different threads are handled independently."""
        handler = OffTopicHandler()
        
        result_a = handler.handle(
            user_message="Hello",
            thread_ts="test_thread_offtopic_integration_A"
        )
        
        result_b = handler.handle(
            user_message="Hi there",
            thread_ts="test_thread_offtopic_integration_B"
        )
        
        assert result_a["metadata"]["handled_as_off_topic"] is True
        assert result_b["metadata"]["handled_as_off_topic"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
