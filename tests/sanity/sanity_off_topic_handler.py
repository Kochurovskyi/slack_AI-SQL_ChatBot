"""Sanity check test for Off-Topic Handler Agent with real agents."""
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env", override=False)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.agents.off_topic_handler import OffTopicHandler, get_off_topic_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_off_topic_handler():
    """Sanity check for Off-Topic Handler Agent with real agents."""
    print("\n=== Off-Topic Handler Agent Sanity Check (Real Agents) ===\n")
    
    # Check API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("[SKIP] No API keys available. Set OPENAI_API_KEY or GOOGLE_API_KEY to run.")
        return
    
    # Test 1: Agent Initialization
    print("1. Testing Off-Topic Handler initialization...")
    handler = OffTopicHandler()
    assert handler is not None
    assert len(handler.tools) == 0  # No tools needed
    print(f"   Found {len(handler.tools)} tools (expected: 0)")
    print("   [OK] Handler initialized\n")
    
    # Test 2: Handling Greeting
    print("2. Testing greeting handling...")
    result = handler.handle(
        user_message="Hello, how are you?",
        thread_ts="sanity_test_offtopic_001"
    )
    
    assert "formatted_response" in result
    assert result["metadata"]["handled_as_off_topic"] is True
    print(f"   Response length: {len(result['formatted_response'])} characters")
    print("   [OK] Greeting handling works\n")
    
    # Test 3: Handling General Question
    print("3. Testing general question handling...")
    result = handler.handle(
        user_message="What's the weather today?",
        thread_ts="sanity_test_offtopic_002"
    )
    
    assert "formatted_response" in result
    assert result["metadata"]["handled_as_off_topic"] is True
    print("   [OK] General question handling works\n")
    
    # Test 4: Error Handling
    print("4. Testing error handling...")
    result = handler.handle(
        user_message="",  # Empty message
        thread_ts="sanity_test_offtopic_003"
    )
    
    assert "formatted_response" in result
    assert result["metadata"]["handled_as_off_topic"] is True
    print("   [OK] Error handling works\n")
    
    # Test 5: Singleton Pattern
    print("5. Testing singleton pattern...")
    handler1 = get_off_topic_handler()
    handler2 = get_off_topic_handler()
    assert handler1 is handler2
    print("   [OK] Singleton pattern works\n")
    
    # Test 6: System Prompt
    print("6. Testing system prompt...")
    assert len(handler.SYSTEM_PROMPT) > 0
    assert "Off-Topic" in handler.SYSTEM_PROMPT or "off-topic" in handler.SYSTEM_PROMPT.lower()
    assert "database" in handler.SYSTEM_PROMPT.lower()
    print(f"   System prompt length: {len(handler.SYSTEM_PROMPT)} characters")
    print("   [OK] System prompt configured\n")
    
    # Test 7: Response Format
    print("7. Testing response format...")
    result = handler.handle(
        user_message="Thanks for your help",
        thread_ts="sanity_test_offtopic_004"
    )
    
    assert "formatted_response" in result
    assert len(result["formatted_response"]) > 0
    assert "metadata" in result
    assert "thread_ts" in result["metadata"]
    print("   [OK] Response format correct\n")
    
    # Test 8: Use Case Suggestions
    print("8. Testing use case suggestions...")
    result = handler.handle(
        user_message="What can you do?",
        thread_ts="sanity_test_offtopic_005"
    )
    
    assert "formatted_response" in result
    # Check that response mentions capabilities
    response_lower = result["formatted_response"].lower()
    assert any(keyword in response_lower for keyword in ["app", "database", "query", "csv", "sql"])
    print("   [OK] Use case suggestions work\n")
    
    print("=== All sanity checks passed! ===\n")


if __name__ == '__main__':
    test_off_topic_handler()
