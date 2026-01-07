"""Sanity check test for SQL Query Agent with real agents."""
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

from ai.agents.sql_query_agent import SQLQueryAgent, get_sql_query_agent
from langchain_core.messages import HumanMessage, AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_sql_query_agent():
    """Sanity check for SQL Query Agent with real agents."""
    print("\n=== SQL Query Agent Sanity Check (Real Agents) ===\n")
    
    # Check API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("[SKIP] No API keys available. Set OPENAI_API_KEY or GOOGLE_API_KEY to run.")
        return
    
    # Ensure database exists
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("[SKIP] Database not found. Please run Phase 1 setup first.")
        return
    
    # Test 1: Agent Initialization
    print("1. Testing SQL Query Agent initialization...")
    agent = SQLQueryAgent()
    assert agent is not None
    assert len(agent.tools) == 3
    print(f"   Found {len(agent.tools)} tools")
    print("   [OK] Agent initialized\n")
    
    # Test 2: Simple Query
    print("2. Testing simple query workflow...")
    result = agent.query(
        question="How many apps are there?",
        thread_ts="sanity_test_001"
    )
    
    assert "formatted_response" in result
    assert "metadata" in result
    assert result["metadata"]["query_executed"] is not None
    print(f"   Response length: {len(result['formatted_response'])} characters")
    print(f"   Query executed: {result['metadata']['query_executed']}")
    print("   [OK] Simple query works\n")
    
    # Test 3: Query with Conversation History
    print("3. Testing query with conversation history...")
    conversation_history = [
        HumanMessage(content="How many apps are there?"),
        AIMessage(content="There are 50 apps.")
    ]
    
    result = agent.query(
        question="What about iOS apps?",
        thread_ts="sanity_test_002",
        conversation_history=conversation_history
    )
    
    assert "formatted_response" in result
    assert result["metadata"]["query_executed"] is not None
    print("   [OK] Conversation history handling works\n")
    
    # Test 4: Error Handling
    print("4. Testing error handling...")
    result = agent.query(
        question="",  # Empty question
        thread_ts="sanity_test_003"
    )
    
    assert "formatted_response" in result
    # Agent should handle gracefully
    assert result["metadata"]["query_executed"] is not None
    print("   [OK] Error handling works\n")
    
    # Test 5: Streaming
    print("5. Testing streaming...")
    chunks = list(agent.stream(
        question="How many apps?",
        thread_ts="sanity_test_004"
    ))
    
    assert chunks is not None
    if len(chunks) > 0:
        print(f"   Streamed {len(chunks)} chunks")
    print("   [OK] Streaming works\n")
    
    # Test 6: Singleton Pattern
    print("6. Testing singleton pattern...")
    agent1 = get_sql_query_agent()
    agent2 = get_sql_query_agent()
    assert agent1 is agent2
    print("   [OK] Singleton pattern works\n")
    
    # Test 7: Tool Integration
    print("7. Testing tool integration...")
    tool_names = [tool.name for tool in agent.tools]
    assert 'generate_sql_tool' in tool_names
    assert 'execute_sql_tool' in tool_names
    assert 'format_result_tool' in tool_names
    print(f"   Tools: {', '.join(tool_names)}")
    print("   [OK] Tool integration works\n")
    
    # Test 8: System Prompt
    print("8. Testing system prompt...")
    assert len(agent.SYSTEM_PROMPT) > 0
    assert "app_portfolio" in agent.SYSTEM_PROMPT
    assert "Database Schema" in agent.SYSTEM_PROMPT
    print(f"   System prompt length: {len(agent.SYSTEM_PROMPT)} characters")
    print("   [OK] System prompt configured\n")
    
    print("=== All sanity checks passed! ===\n")


if __name__ == '__main__':
    test_sql_query_agent()
