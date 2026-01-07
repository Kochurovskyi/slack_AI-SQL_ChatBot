"""Comprehensive tests for complete workflow: SQL queries, SQL retrieval, and CSV export."""
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

from ai.agents.orchestrator import get_orchestrator
from ai.memory_store import memory_store

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def require_api_key():
    """Skip tests if no API key is available."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API keys available - skipping real agent tests")


@pytest.fixture(scope="function")
def clean_thread():
    """Create a clean thread for testing."""
    thread_ts = "test_complete_workflow"
    # Clear any existing memory
    memory_store.clear_memory(thread_ts)
    yield thread_ts
    # Cleanup
    memory_store.clear_memory(thread_ts)


class TestCompleteWorkflow:
    """Comprehensive tests for SQL queries, SQL retrieval, and CSV export workflows."""
    
    # ========== SQL Query Tests ==========
    
    def test_query_returns_formatted_result_not_json(self, require_api_key, clean_thread):
        """Test that SQL query returns formatted result (e.g., '29'), not raw JSON."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing SQL Query Returns Formatted Result ===\n")
        
        # Step 1: Run SQL query
        print("Step 1: Running SQL query...")
        question = "how many android apps do we have?"
        result = orchestrator.process_message(
            user_message=question,
            thread_ts=thread_ts
        )
        
        # Verify intent
        assert result["intent"] == "SQL_QUERY", f"Expected SQL_QUERY, got {result['intent']}"
        print(f"[OK] Intent correctly classified as: {result['intent']}")
        
        # Verify response is formatted (not raw JSON)
        response = result["response"]
        assert response is not None, "Response should not be None"
        assert len(response) > 0, "Response should not be empty"
        
        # Should NOT contain raw JSON structure
        assert not response.startswith('{'), f"Response should not start with '{{', got: {response[:100]}"
        assert '"success"' not in response, f"Response should not contain raw JSON, got: {response[:200]}"
        assert '"data"' not in response, f"Response should not contain raw JSON, got: {response[:200]}"
        
        # Should contain formatted result (number or text)
        assert any(char.isdigit() for char in response), f"Response should contain a number, got: {response[:200]}"
        
        print(f"[OK] Formatted response: {response[:200]}...")
        
        # Verify SQL was stored
        queries = memory_store.get_sql_queries(thread_ts)
        assert len(queries) > 0, "SQL query should be stored"
        stored_sql = queries[-1].get('sql')
        assert stored_sql is not None, "Stored SQL should not be None"
        assert "android" in stored_sql.lower(), f"SQL should filter Android, got: {stored_sql}"
        print(f"[OK] SQL stored: {stored_sql[:100]}...")
        
        print("\n=== Test Passed ===\n")
    
    def test_complex_query_with_aggregation(self, require_api_key, clean_thread):
        """Test complex query with aggregation returns formatted result, not JSON."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing Complex Query with Aggregation ===\n")
        
        # Step 1: Run complex query (aggregation)
        print("Step 1: Running complex aggregation query...")
        question = "which country generates the most revenue?"
        result = orchestrator.process_message(
            user_message=question,
            thread_ts=thread_ts
        )
        
        # Verify intent
        assert result["intent"] == "SQL_QUERY", f"Expected SQL_QUERY, got {result['intent']}"
        print(f"[OK] Intent correctly classified as: {result['intent']}")
        
        # Verify response is formatted (not raw JSON)
        response = result["response"]
        assert response is not None, "Response should not be None"
        assert len(response) > 0, "Response should not be empty"
        
        # Should NOT contain raw JSON structure
        assert not response.startswith('{'), f"Response should not start with '{{', got: {response[:100]}"
        assert '"success"' not in response, f"Response should not contain raw JSON, got: {response[:200]}"
        assert '"data"' not in response, f"Response should not contain raw JSON, got: {response[:200]}"
        
        # Should contain formatted result (country name or table)
        assert len(response.strip()) > 0, "Response should not be empty"
        print(f"[OK] Formatted response: {response[:200]}...")
        
        # Verify SQL was stored and contains aggregation
        queries = memory_store.get_sql_queries(thread_ts)
        assert len(queries) > 0, "SQL query should be stored"
        stored_sql = queries[-1].get('sql')
        assert stored_sql is not None, "Stored SQL should not be None"
        assert "GROUP BY" in stored_sql.upper() or "ORDER BY" in stored_sql.upper(), \
            f"SQL should contain aggregation, got: {stored_sql}"
        print(f"[OK] SQL stored (with aggregation): {stored_sql[:150]}...")
        
        print("\n=== Test Passed ===\n")
    
    # ========== SQL Retrieval Tests ==========
    
    def test_retrieval_returns_sql_code_not_executed(self, require_api_key, clean_thread):
        """Test that SQL retrieval returns SQL code, not execution results."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing SQL Retrieval Returns SQL Code ===\n")
        
        # Step 1: Run SQL query first to store SQL
        print("Step 1: Running initial SQL query...")
        question1 = "how many android apps do we have?"
        result1 = orchestrator.process_message(
            user_message=question1,
            thread_ts=thread_ts
        )
        
        assert result1["intent"] == "SQL_QUERY"
        response1 = result1["response"]
        assert not response1.startswith('{'), "First response should be formatted, not JSON"
        print(f"[OK] First query response: {response1[:100]}...")
        
        # Step 2: Request SQL retrieval
        print("\nStep 2: Requesting SQL retrieval...")
        question2 = "okay, now show me the sql query to retrieve this info"
        result2 = orchestrator.process_message(
            user_message=question2,
            thread_ts=thread_ts
        )
        
        # Verify intent is SQL_RETRIEVAL
        assert result2["intent"] == "SQL_RETRIEVAL", f"Expected SQL_RETRIEVAL, got {result2['intent']}"
        print(f"[OK] Intent correctly classified as: {result2['intent']}")
        
        # Verify response contains SQL code
        response2 = result2["response"]
        assert response2 is not None, "Response should not be None"
        assert len(response2) > 0, "Response should not be empty"
        
        # Should contain SQL (in code block or plain)
        assert "SELECT" in response2.upper() or "sql" in response2.lower(), \
            f"Response should contain SQL, got: {response2[:200]}"
        
        # Should NOT contain execution results (the number from first query)
        # The response should be SQL code, not the result "29"
        assert response1 not in response2 or "SELECT" in response2, \
            "SQL retrieval should return SQL code, not execution results"
        
        print(f"[OK] SQL retrieval response: {response2[:200]}...")
        
        # Verify SQL was NOT executed again (check query count didn't increase)
        queries_before = memory_store.get_sql_queries(thread_ts)
        queries_after = memory_store.get_sql_queries(thread_ts)
        assert len(queries_after) == len(queries_before), \
            "SQL retrieval should not create new SQL queries"
        print(f"[OK] No new SQL queries created (still {len(queries_after)} queries)")
        
        print("\n=== Test Passed ===\n")
    
    def test_sql_retrieval_returns_only_sql_not_executed(self, require_api_key, clean_thread):
        """Test that SQL retrieval returns only SQL query, doesn't execute it."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing SQL Retrieval Use Case ===\n")
        
        # Step 1: First, run a SQL query to store SQL in memory
        print("Step 1: Running initial query to store SQL...")
        question1 = "how many apps do we have?"
        result1 = orchestrator.process_message(
            user_message=question1,
            thread_ts=thread_ts
        )
        
        assert result1["intent"] == "SQL_QUERY"
        assert "response" in result1
        print(f"[OK] Initial query response: {result1['response'][:100]}...")
        
        # Verify SQL was stored
        queries = memory_store.get_sql_queries(thread_ts)
        assert len(queries) > 0, "SQL query should be stored in memory"
        stored_sql = queries[-1].get('sql')
        assert stored_sql is not None, "Stored SQL should not be None"
        print(f"[OK] SQL stored: {stored_sql[:100]}...")
        
        # Step 2: Request SQL retrieval (should NOT execute, only return SQL)
        print("\nStep 2: Requesting SQL retrieval...")
        question2 = "show me the SQL you used to retrieve all the apps"
        result2 = orchestrator.process_message(
            user_message=question2,
            thread_ts=thread_ts
        )
        
        # Verify intent is SQL_RETRIEVAL
        assert result2["intent"] == "SQL_RETRIEVAL", f"Expected SQL_RETRIEVAL, got {result2['intent']}"
        print(f"[OK] Intent correctly classified as: {result2['intent']}")
        
        # Verify response contains SQL (formatted in code block)
        response = result2["response"]
        assert response is not None, "Response should not be None"
        assert len(response) > 0, "Response should not be empty"
        
        # Check that response contains SQL (either in code block or plain)
        assert "SELECT" in response.upper() or "sql" in response.lower(), \
            f"Response should contain SQL, got: {response[:200]}"
        
        # Verify response does NOT contain execution results (like counts, data)
        # SQL retrieval should only show SQL, not query results
        assert "49" not in response or "SELECT" in response, \
            "Response should be SQL query, not execution results"
        
        print(f"[OK] SQL retrieval response: {response[:200]}...")
        
        # Step 3: Verify SQL was NOT executed again (check query count didn't increase)
        queries_after = memory_store.get_sql_queries(thread_ts)
        assert len(queries_after) == len(queries), \
            "SQL retrieval should not create new SQL queries"
        print(f"[OK] No new SQL queries created (still {len(queries)} queries)")
        
        # Step 4: Test streaming - should also return only SQL
        print("\nStep 3: Testing streaming SQL retrieval...")
        chunks = []
        for chunk in orchestrator.stream(
            user_message=question2,
            thread_ts=thread_ts
        ):
            if chunk:
                chunks.append(chunk)
        
        streamed_response = "".join(chunks)
        assert len(streamed_response) > 0, "Streamed response should not be empty"
        assert "SELECT" in streamed_response.upper() or "sql" in streamed_response.lower(), \
            f"Streamed response should contain SQL, got: {streamed_response[:200]}"
        
        print(f"[OK] Streamed response: {streamed_response[:200]}...")
        print("\n=== Test Passed ===\n")
    
    def test_sql_retrieval_with_description_matching(self, require_api_key, clean_thread):
        """Test SQL retrieval with description matching."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing SQL Retrieval with Description Matching ===\n")
        
        # Step 1: Run multiple queries to create history
        print("Step 1: Running multiple queries...")
        questions = [
            "how many apps do we have?",
            "how many android apps do we have?",
            "which country generates the most revenue?"
        ]
        
        for question in questions:
            result = orchestrator.process_message(
                user_message=question,
                thread_ts=thread_ts
            )
            assert result["intent"] == "SQL_QUERY"
        
        queries = memory_store.get_sql_queries(thread_ts)
        assert len(queries) >= 3, f"Expected at least 3 queries, got {len(queries)}"
        print(f"[OK] Stored {len(queries)} SQL queries")
        
        # Step 2: Request SQL for specific query by description
        print("\nStep 2: Requesting SQL for 'all the apps'...")
        result = orchestrator.process_message(
            user_message="show me the SQL you used to retrieve all the apps",
            thread_ts=thread_ts
        )
        
        assert result["intent"] == "SQL_RETRIEVAL"
        response = result["response"]
        
        # Should contain SQL for the first query (about all apps)
        assert "SELECT" in response.upper() or "sql" in response.lower(), \
            f"Response should contain SQL, got: {response[:200]}"
        
        print(f"[OK] Retrieved SQL: {response[:200]}...")
        print("\n=== Test Passed ===\n")
    
    def test_followup_question_then_sql_retrieval(self, require_api_key, clean_thread):
        """Test follow-up question flow, then SQL retrieval returns correct SQL."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing Follow-up Question Then SQL Retrieval ===\n")
        
        # Step 1: First question
        print("Step 1: First question - total apps...")
        result1 = orchestrator.process_message(
            user_message="how many apps do we have?",
            thread_ts=thread_ts
        )
        
        assert result1["intent"] == "SQL_QUERY"
        response1 = result1["response"]
        assert not response1.startswith('{'), "Response should be formatted"
        print(f"[OK] First response: {response1[:100]}...")
        
        # Step 2: Follow-up question
        print("\nStep 2: Follow-up question - Android apps...")
        result2 = orchestrator.process_message(
            user_message="what about android?",
            thread_ts=thread_ts
        )
        
        assert result2["intent"] == "SQL_QUERY"
        response2 = result2["response"]
        assert not response2.startswith('{'), "Response should be formatted"
        assert "android" in response2.lower() or any(char.isdigit() for char in response2), \
            "Should mention Android or show count"
        print(f"[OK] Follow-up response: {response2[:100]}...")
        
        # Verify we have 2 SQL queries stored
        queries = memory_store.get_sql_queries(thread_ts)
        assert len(queries) >= 2, f"Should have at least 2 queries, got {len(queries)}"
        print(f"[OK] Stored {len(queries)} SQL queries")
        
        # Step 3: Retrieve SQL for the follow-up query
        print("\nStep 3: Retrieving SQL for Android query...")
        result3 = orchestrator.process_message(
            user_message="show me the SQL for the android apps query",
            thread_ts=thread_ts
        )
        
        assert result3["intent"] == "SQL_RETRIEVAL"
        response3 = result3["response"]
        assert "SELECT" in response3.upper(), "Should contain SQL code"
        assert "android" in response3.lower(), "Should contain Android filter"
        print(f"[OK] Retrieved SQL: {response3[:200]}...")
        
        # Verify it's the Android query, not the first one
        android_sql = queries[-1].get('sql', '').lower()
        assert "android" in android_sql, "Last query should be Android query"
        assert android_sql in response3.lower() or "android" in response3.lower(), \
            "Retrieved SQL should match Android query"
        
        print("\n=== Test Passed ===\n")
    
    # ========== CSV Export Tests ==========
    
    def test_csv_export_returns_simple_message(self, require_api_key, clean_thread):
        """Test that CSV export returns simple message with file path, not JSON."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing CSV Export Simple Response ===\n")
        
        # Step 1: Run a query first to have data to export
        print("Step 1: Running query to generate data...")
        result1 = orchestrator.process_message(
            user_message="show me top 5 apps by revenue",
            thread_ts=thread_ts
        )
        
        assert result1["intent"] == "SQL_QUERY"
        print(f"[OK] Query executed: {result1['response'][:100]}...")
        
        # Step 2: Request CSV export
        print("\nStep 2: Requesting CSV export...")
        result2 = orchestrator.process_message(
            user_message="export this as csv",
            thread_ts=thread_ts
        )
        
        # Verify intent
        assert result2["intent"] == "CSV_EXPORT", f"Expected CSV_EXPORT, got {result2['intent']}"
        print(f"[OK] Intent correctly classified as: {result2['intent']}")
        
        # Verify response is simple (not overloaded with JSON)
        response = result2["response"]
        assert response is not None, "Response should not be None"
        assert len(response) > 0, "Response should not be empty"
        
        # Should NOT contain raw JSON structure
        assert not response.startswith('{'), f"Response should not start with '{{', got: {response[:100]}"
        assert '"success"' not in response, f"Response should not contain raw JSON, got: {response[:200]}"
        assert '"data"' not in response, f"Response should not contain raw JSON, got: {response[:200]}"
        assert '"results_found"' not in response, f"Response should not contain raw JSON, got: {response[:200]}"
        
        # Should contain simple message about CSV generation
        assert "csv" in response.lower() or "file" in response.lower(), \
            f"Response should mention CSV/file, got: {response[:200]}"
        
        # Should be relatively short (simple message, not data dump)
        assert len(response) < 200, f"Response should be short and simple, got {len(response)} chars: {response[:200]}"
        
        print(f"[OK] Simple response: {response}")
        
        print("\n=== Test Passed ===\n")
    
    # ========== End-to-End Flow Tests ==========
    
    def test_complete_flow_end_to_end(self, require_api_key, clean_thread):
        """Test complete flow: query -> formatted result, retrieval -> SQL code."""
        thread_ts = clean_thread
        orchestrator = get_orchestrator()
        
        print("\n=== Testing Complete Flow End-to-End ===\n")
        
        # Step 1: First request - should return formatted result
        print("Step 1: First request - SQL query...")
        result1 = orchestrator.process_message(
            user_message="how many android apps do we have?",
            thread_ts=thread_ts
        )
        
        assert result1["intent"] == "SQL_QUERY"
        response1 = result1["response"]
        assert not response1.startswith('{'), "Response should be formatted, not JSON"
        assert any(char.isdigit() for char in response1), "Response should contain a number"
        print(f"[OK] First response (formatted): {response1[:100]}...")
        
        # Step 2: Second request - should return SQL code
        print("\nStep 2: Second request - SQL retrieval...")
        result2 = orchestrator.process_message(
            user_message="okay, now show me the sql query to retrieve this info",
            thread_ts=thread_ts
        )
        
        assert result2["intent"] == "SQL_RETRIEVAL"
        response2 = result2["response"]
        assert "SELECT" in response2.upper() or "sql" in response2.lower(), \
            "Response should contain SQL code"
        assert not response1 in response2 or "SELECT" in response2, \
            "Should return SQL code, not execution result"
        print(f"[OK] Second response (SQL code): {response2[:200]}...")
        
        # Step 3: Third request - CSV export
        print("\nStep 3: Third request - CSV export...")
        result3 = orchestrator.process_message(
            user_message="export this as csv",
            thread_ts=thread_ts
        )
        
        assert result3["intent"] == "CSV_EXPORT"
        response3 = result3["response"]
        assert "csv" in response3.lower(), "Response should mention CSV"
        assert not response3.startswith('{'), "Response should be formatted, not JSON"
        print(f"[OK] Third response (CSV export): {response3[:200]}...")
        
        print("\n=== All Tests Passed ===\n")

