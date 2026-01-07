"""End-to-end sanity check for Agent Orchestrator using 3 scenarios from test_assignment_scenarios.

This test validates the complete orchestrator flow:
1. SQL Query scenario (Q1.1)
2. CSV Export scenario (Q3.1) 
3. Multi-step workflow scenario (Q8.1)
"""
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

from ai.agents.orchestrator import get_orchestrator
from ai.memory_store import memory_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_orchestrator_e2e():
    """End-to-end sanity check for Agent Orchestrator with 3 scenarios."""
    print("\n" + "="*80)
    print("AGENT ORCHESTRATOR END-TO-END SANITY CHECK")
    print("="*80 + "\n")
    
    # Check API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("[SKIP] No API keys available. Set OPENAI_API_KEY or GOOGLE_API_KEY to run.")
        return
    
    # Ensure database exists
    db_path = project_root / "data" / "app_portfolio.db"
    if not db_path.exists():
        print("[SKIP] Database not found. Please run Phase 1 setup first.")
        return
    
    # Initialize orchestrator
    print("1. Initializing Agent Orchestrator...")
    orchestrator = get_orchestrator()
    assert orchestrator is not None
    assert orchestrator.router_agent is not None
    assert orchestrator.sql_query_agent is not None
    assert orchestrator.csv_export_agent is not None
    assert orchestrator.sql_retrieval_agent is not None
    assert orchestrator.off_topic_handler is not None
    print("   [OK] Orchestrator initialized with all agents\n")
    
    # Scenario 1: SQL Query (Q1.1)
    print("="*80)
    print("SCENARIO 1: SQL Query (Q1.1)")
    print("="*80)
    print("User Message: 'how many apps do we have?'")
    print("Expected Intent: SQL_QUERY\n")
    
    thread_ts_1 = "sanity_e2e_scenario_1"
    memory_store.clear_memory(thread_ts_1)  # Clear any existing memory
    
    try:
        result = orchestrator.process_message(
            user_message="how many apps do we have?",
            thread_ts=thread_ts_1
        )
        
        assert result is not None
        assert "response" in result
        assert "intent" in result
        assert result["intent"] == "SQL_QUERY"
        
        # Handle response format (could be string or list)
        response_text = result["response"]
        if isinstance(response_text, list):
            # Extract text from list format
            response_text = " ".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in response_text])
        
        assert len(response_text) > 0
        
        print(f"   Intent: {result['intent']}")
        print(f"   Response length: {len(response_text)} characters")
        print(f"   Response preview: {response_text[:100]}...")
        print("   [OK] Scenario 1 passed\n")
        
    except Exception as e:
        print(f"   [FAIL] Scenario 1 failed: {e}")
        raise
    
    # Scenario 2: CSV Export (Q3.1)
    print("="*80)
    print("SCENARIO 2: CSV Export (Q3.1)")
    print("="*80)
    print("User Message: 'export this as csv'")
    print("Expected Intent: CSV_EXPORT")
    print("Note: This requires a previous query in the same thread\n")
    
    thread_ts_2 = "sanity_e2e_scenario_2"
    memory_store.clear_memory(thread_ts_2)
    
    try:
        # First, execute a query to have results to export
        print("   Step 1: Executing initial query...")
        query_result = orchestrator.process_message(
            user_message="how many apps do we have?",
            thread_ts=thread_ts_2
        )
        assert query_result["intent"] == "SQL_QUERY"
        print("   [OK] Initial query executed")
        
        # Then request CSV export
        print("   Step 2: Requesting CSV export...")
        export_result = orchestrator.process_message(
            user_message="export this as csv",
            thread_ts=thread_ts_2
        )
        
        assert export_result is not None
        assert "response" in export_result
        assert "intent" in export_result
        assert export_result["intent"] == "CSV_EXPORT"
        
        # Handle response format (could be string or list)
        response_text = export_result["response"]
        if isinstance(response_text, list):
            response_text = " ".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in response_text])
        
        print(f"   Intent: {export_result['intent']}")
        print(f"   Response length: {len(response_text)} characters")
        print(f"   Response preview: {response_text[:100]}...")
        print("   [OK] Scenario 2 passed\n")
        
    except Exception as e:
        print(f"   [FAIL] Scenario 2 failed: {e}")
        raise
    
    # Scenario 3: Multi-step Workflow (Q8.1)
    print("="*80)
    print("SCENARIO 3: Multi-step Workflow (Q8.1)")
    print("="*80)
    print("Workflow: SQL Query -> CSV Export -> SQL Retrieval")
    print("This tests the complete orchestrator flow with multiple intents\n")
    
    thread_ts_3 = "sanity_e2e_scenario_3"
    memory_store.clear_memory(thread_ts_3)
    
    try:
        # Step 1: SQL Query
        print("   Step 1: SQL Query - 'which country generates the most revenue?'")
        step1_result = orchestrator.process_message(
            user_message="which country generates the most revenue?",
            thread_ts=thread_ts_3
        )
        assert step1_result["intent"] == "SQL_QUERY"
        step1_response = step1_result["response"]
        if isinstance(step1_response, list):
            step1_response = " ".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in step1_response])
        assert len(step1_response) > 0
        print(f"      Intent: {step1_result['intent']} OK")
        print(f"      Response: {step1_response[:80]}...")
        
        # Step 2: CSV Export
        print("\n   Step 2: CSV Export - 'export this as csv'")
        step2_result = orchestrator.process_message(
            user_message="export this as csv",
            thread_ts=thread_ts_3
        )
        assert step2_result["intent"] == "CSV_EXPORT"
        step2_response = step2_result["response"]
        if isinstance(step2_response, list):
            step2_response = " ".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in step2_response])
        assert len(step2_response) > 0
        print(f"      Intent: {step2_result['intent']} OK")
        print(f"      Response: {step2_response[:80]}...")
        
        # Step 3: SQL Retrieval
        print("\n   Step 3: SQL Retrieval - 'show me the SQL'")
        step3_result = orchestrator.process_message(
            user_message="show me the SQL",
            thread_ts=thread_ts_3
        )
        assert step3_result["intent"] == "SQL_RETRIEVAL"
        step3_response = step3_result["response"]
        if isinstance(step3_response, list):
            step3_response = " ".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in step3_response])
        assert len(step3_response) > 0
        print(f"      Intent: {step3_result['intent']} OK")
        print(f"      Response: {step3_response[:80]}...")
        
        print("\n   [OK] Scenario 3 passed - All workflow steps completed\n")
        
    except Exception as e:
        print(f"   [FAIL] Scenario 3 failed: {e}")
        raise
    
    # Test streaming functionality
    print("="*80)
    print("BONUS: Testing Streaming Functionality")
    print("="*80)
    
    thread_ts_stream = "sanity_e2e_streaming"
    memory_store.clear_memory(thread_ts_stream)
    
    try:
        print("   Streaming response for: 'how many apps do we have?'")
        chunks = []
        for chunk in orchestrator.stream(
            user_message="how many apps do we have?",
            thread_ts=thread_ts_stream
        ):
            if chunk:
                chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        
        print(f"   Streamed {len(chunks)} chunks")
        print(f"   Total response length: {len(full_response)} characters")
        print("   [OK] Streaming works\n")
        
    except Exception as e:
        print(f"   [FAIL] Streaming test failed: {e}")
        raise
    
    # Summary
    print("="*80)
    print("END-TO-END SANITY CHECK SUMMARY")
    print("="*80)
    print("[OK] Scenario 1: SQL Query - PASSED")
    print("[OK] Scenario 2: CSV Export - PASSED")
    print("[OK] Scenario 3: Multi-step Workflow - PASSED")
    print("[OK] Streaming Functionality - PASSED")
    print("\n[SUCCESS] All end-to-end sanity checks passed!")
    print("="*80 + "\n")


if __name__ == '__main__':
    try:
        test_orchestrator_e2e()
    except Exception as e:
        logger.exception("End-to-end sanity check failed")
        print(f"\n[FAIL] End-to-end sanity check failed: {e}")
        sys.exit(1)

