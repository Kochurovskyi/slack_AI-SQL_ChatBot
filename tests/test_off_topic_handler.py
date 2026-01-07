"""Unit tests for Off-Topic Handler Agent with real agents."""
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


class TestOffTopicHandler:
    """Tests for Off-Topic Handler Agent with real agents."""
    
    def test_off_topic_handler_initialization(self, require_api_key):
        """Test Off-Topic Handler initialization."""
        handler = OffTopicHandler()
        
        assert handler is not None
        assert handler.llm is not None
        assert len(handler.tools) == 0  # No tools needed
        assert handler.agent is not None
    
    def test_handle_method(self, require_api_key):
        """Test handle method with real agent."""
        handler = OffTopicHandler()
        
        result = handler.handle(
            user_message="Hello, how are you?",
            thread_ts="test_thread_offtopic_001"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["handled_as_off_topic"] is True
        assert len(result["formatted_response"]) > 0
    
    def test_handle_with_greeting(self, require_api_key):
        """Test handle with greeting message."""
        handler = OffTopicHandler()
        
        result = handler.handle(
            user_message="Hi there!",
            thread_ts="test_thread_offtopic_002"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["handled_as_off_topic"] is True
        # response_type may or may not be present
        if "response_type" in result["metadata"]:
            assert result["metadata"]["response_type"] in ["off_topic_decline", "error"]
        assert len(result["formatted_response"]) > 0
    
    def test_handle_with_general_question(self, require_api_key):
        """Test handle with general off-topic question."""
        handler = OffTopicHandler()
        
        result = handler.handle(
            user_message="What's the capital of France?",
            thread_ts="test_thread_offtopic_003"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["handled_as_off_topic"] is True
        assert len(result["formatted_response"]) > 0
    
    def test_handle_error_handling(self, require_api_key):
        """Test error handling within the handle method."""
        handler = OffTopicHandler()
        
        # Test with empty message might cause issues
        result = handler.handle(
            user_message="",
            thread_ts="test_thread_offtopic_004"
        )
        
        assert "formatted_response" in result
        assert result["metadata"]["handled_as_off_topic"] is True
    
    def test_stream_method(self, require_api_key):
        """Test stream method with real agent."""
        handler = OffTopicHandler()
        
        # Check if stream method exists
        if hasattr(handler, 'stream'):
            chunks = list(handler.stream(
                user_message="Tell me a joke",
                thread_ts="test_thread_offtopic_005"
            ))
            
            # Stream may return empty or various types - just verify it doesn't crash
            assert chunks is not None
            # If chunks exist, verify they're iterable
            if len(chunks) > 0:
                pass  # Just verify stream completes without error
        else:
            pytest.skip("Stream method not implemented in OffTopicHandler")


class TestOffTopicHandlerIntegration:
    """Integration tests for Off-Topic Handler Agent with real agents."""
    
    def test_get_off_topic_handler_singleton(self, require_api_key):
        """Test that get_off_topic_handler returns singleton instance."""
        handler1 = get_off_topic_handler()
        handler2 = get_off_topic_handler()
        
        assert handler1 is handler2
    
    def test_system_prompt_present(self, require_api_key):
        """Test that the system prompt is correctly set."""
        handler = OffTopicHandler()
        assert "Off-Topic Handler Agent" in handler.SYSTEM_PROMPT
        assert len(handler.SYSTEM_PROMPT) > 0
    
    def test_real_off_topic_handling(self, require_api_key):
        """Test real off-topic handling end-to-end."""
        handler = OffTopicHandler()
        
        result = handler.handle(
            user_message="What's the weather today?",
            thread_ts="test_thread_offtopic_006"
        )
        
        assert "formatted_response" in result
        assert "metadata" in result
        assert result["metadata"]["handled_as_off_topic"] is True
        assert len(result["formatted_response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
