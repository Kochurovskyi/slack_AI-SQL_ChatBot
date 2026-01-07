"""Sanity check test for Router Agent."""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.agents.router_agent import RouterAgent, get_router_agent
from ai.agents.router_tools import get_router_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_router_agent():
    """Sanity check for Router Agent."""
    print("\n=== Router Agent Sanity Check ===\n")
    
    # Test 1: Router Tools
    print("1. Testing router tools...")
    tools = get_router_tools()
    assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"
    print(f"   Found {len(tools)} routing tools")
    print("   [OK] Router tools work\n")
    
    # Test 2: Router Agent Initialization
    print("2. Testing Router Agent initialization...")
    agent = RouterAgent()
    assert agent is not None
    print("   [OK] Router Agent initialized\n")
    
    # Test 3: SQL Query Intent
    print("3. Testing SQL_QUERY intent classification...")
    result = agent.classify_intent(
        user_message="How many apps are there?",
        thread_ts="1234567890.123456"
    )
    assert result["intent"] == "SQL_QUERY"
    print(f"   Intent: {result['intent']}")
    print(f"   Confidence: {result['confidence']}")
    print("   [OK] SQL_QUERY classification works\n")
    
    # Test 4: CSV Export Intent
    print("4. Testing CSV_EXPORT intent classification...")
    result = agent.classify_intent(
        user_message="Export the results to CSV",
        thread_ts="1234567890.123456"
    )
    assert result["intent"] == "CSV_EXPORT"
    print(f"   Intent: {result['intent']}")
    print("   [OK] CSV_EXPORT classification works\n")
    
    # Test 5: SQL Retrieval Intent
    print("5. Testing SQL_RETRIEVAL intent classification...")
    result = agent.classify_intent(
        user_message="Show me the SQL query that was used",
        thread_ts="1234567890.123456"
    )
    assert result["intent"] == "SQL_RETRIEVAL"
    print(f"   Intent: {result['intent']}")
    print("   [OK] SQL_RETRIEVAL classification works\n")
    
    # Test 6: Off-Topic Intent
    print("6. Testing OFF_TOPIC intent classification...")
    result = agent.classify_intent(
        user_message="Hello, how are you?",
        thread_ts="1234567890.123456"
    )
    assert result["intent"] == "OFF_TOPIC"
    print(f"   Intent: {result['intent']}")
    print("   [OK] OFF_TOPIC classification works\n")
    
    # Test 7: Follow-up Questions
    print("7. Testing follow-up question handling...")
    from langchain_core.messages import HumanMessage, AIMessage
    
    conversation_history = [
        HumanMessage(content="How many apps are there?"),
        AIMessage(content="There are 50 apps.")
    ]
    
    result = agent.classify_intent(
        user_message="What about iOS apps?",
        thread_ts="1234567890.123456",
        conversation_history=conversation_history
    )
    assert result["intent"] == "SQL_QUERY"
    assert result["metadata"]["has_context"] is True
    print(f"   Intent: {result['intent']}")
    print(f"   Has context: {result['metadata']['has_context']}")
    print("   [OK] Follow-up question handling works\n")
    
    # Test 8: Route Method
    print("8. Testing route convenience method...")
    intent = agent.route(
        user_message="Download the results",
        thread_ts="1234567890.123456"
    )
    assert intent == "CSV_EXPORT"
    print(f"   Routed to: {intent}")
    print("   [OK] Route method works\n")
    
    # Test 9: Singleton Pattern
    print("9. Testing singleton pattern...")
    agent1 = get_router_agent()
    agent2 = get_router_agent()
    assert agent1 is agent2
    print("   [OK] Singleton pattern works\n")
    
    # Test 10: Various Message Variations
    print("10. Testing various message variations...")
    test_cases = [
        ("What's the total revenue?", "SQL_QUERY"),
        ("Show me apps by country", "SQL_QUERY"),
        ("Save as CSV file", "CSV_EXPORT"),
        ("What SQL was used?", "SQL_RETRIEVAL"),
    ]
    
    for message, expected_intent in test_cases:
        result = agent.classify_intent(
            user_message=message,
            thread_ts="1234567890.123456"
        )
        assert result["intent"] == expected_intent, f"Failed for: {message}"
        print(f"   [OK] '{message}' -> {result['intent']}")
    
    print("   [OK] Message variations handled correctly\n")
    
    print("=== All sanity checks passed! ===\n")


if __name__ == '__main__':
    test_router_agent()

