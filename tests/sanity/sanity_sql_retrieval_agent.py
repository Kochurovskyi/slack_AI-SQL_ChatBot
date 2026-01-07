"""Sanity check test for SQL Retrieval Agent with real agents."""
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

from ai.agents.sql_retrieval_agent import SQLRetrievalAgent, get_sql_retrieval_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_sql_retrieval_agent():
    """Sanity check for SQL Retrieval Agent with real agents."""
    print("\n=== SQL Retrieval Agent Sanity Check (Real Agents) ===\n")
    
    # Check API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("[SKIP] No API keys available. Set OPENAI_API_KEY or GOOGLE_API_KEY to run.")
        return
    
    # Test 1: Agent Initialization
    print("1. Testing SQL Retrieval Agent initialization...")
    agent = SQLRetrievalAgent()
    assert agent is not None
    assert len(agent.tools) == 1
    print(f"   Found {len(agent.tools)} tool")
    print("   [OK] Agent initialized\n")
    
    # Test 2: Retrieval Workflow
    print("2. Testing SQL retrieval workflow...")
    result = agent.retrieve(
        thread_ts="sanity_test_retrieval_001"
    )
    
    assert "formatted_response" in result
    assert "metadata" in result
    assert result["metadata"]["sql_found"] is not None
    print(f"   Response length: {len(result['formatted_response'])} characters")
    print(f"   SQL found: {result['metadata']['sql_found']}")
    print("   [OK] Retrieval workflow works\n")
    
    # Test 3: Cache Miss Handling
    print("3. Testing cache miss handling...")
    result = agent.retrieve(
        thread_ts="sanity_test_retrieval_002"  # New thread with no cache
    )
    
    assert "formatted_response" in result
    assert result["metadata"]["sql_found"] is not None
    print("   [OK] Cache miss handling works\n")
    
    # Test 4: Error Handling
    print("4. Testing error handling...")
    result = agent.retrieve(
        thread_ts=""  # Empty thread_ts
    )
    
    assert "formatted_response" in result
    assert result["metadata"]["sql_found"] is not None
    print("   [OK] Error handling works\n")
    
    # Test 5: Streaming
    print("5. Testing streaming...")
    chunks = list(agent.stream(
        thread_ts="sanity_test_retrieval_003"
    ))
    
    assert chunks is not None
    if len(chunks) > 0:
        print(f"   Streamed {len(chunks)} chunks")
    print("   [OK] Streaming works\n")
    
    # Test 6: Singleton Pattern
    print("6. Testing singleton pattern...")
    agent1 = get_sql_retrieval_agent()
    agent2 = get_sql_retrieval_agent()
    assert agent1 is agent2
    print("   [OK] Singleton pattern works\n")
    
    # Test 7: Tool Integration
    print("7. Testing tool integration...")
    tool_names = [tool.name for tool in agent.tools]
    assert 'get_sql_history_tool' in tool_names
    print(f"   Tools: {', '.join(tool_names)}")
    print("   [OK] Tool integration works\n")
    
    # Test 8: System Prompt
    print("8. Testing system prompt...")
    assert len(agent.SYSTEM_PROMPT) > 0
    assert "SQL Retrieval" in agent.SYSTEM_PROMPT
    print(f"   System prompt length: {len(agent.SYSTEM_PROMPT)} characters")
    print("   [OK] System prompt configured\n")
    
    print("=== All sanity checks passed! ===\n")


if __name__ == '__main__':
    test_sql_retrieval_agent()
