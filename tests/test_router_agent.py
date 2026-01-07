"""Unit tests for Router Agent."""
import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.agents.router_agent import RouterAgent, get_router_agent
from ai.agents.router_tools import (
    route_to_sql_agent_tool,
    route_to_csv_export_tool,
    route_to_sql_retrieval_tool,
    route_to_off_topic_tool,
    get_router_tools,
    ROUTER_TOOLS
)
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


class TestRouterTools:
    """Tests for router tools."""
    
    def test_route_to_sql_agent_tool(self):
        """Test SQL agent routing tool."""
        result = route_to_sql_agent_tool.invoke({
            "user_message": "How many apps are there?",
            "conversation_context": ""
        })
        
        assert result["intent"] == "SQL_QUERY"
        assert "reasoning" in result
        assert result["confidence"] == 1.0
    
    def test_route_to_csv_export_tool(self):
        """Test CSV export routing tool."""
        result = route_to_csv_export_tool.invoke({
            "user_message": "Export this to CSV",
            "conversation_context": ""
        })
        
        assert result["intent"] == "CSV_EXPORT"
        assert "reasoning" in result
        assert result["confidence"] == 1.0
    
    def test_route_to_sql_retrieval_tool(self):
        """Test SQL retrieval routing tool."""
        result = route_to_sql_retrieval_tool.invoke({
            "user_message": "Show me the SQL query",
            "conversation_context": ""
        })
        
        assert result["intent"] == "SQL_RETRIEVAL"
        assert "reasoning" in result
        assert result["confidence"] == 1.0
    
    def test_route_to_off_topic_tool(self):
        """Test off-topic routing tool."""
        result = route_to_off_topic_tool.invoke({
            "user_message": "Hello, how are you?",
            "conversation_context": ""
        })
        
        assert result["intent"] == "OFF_TOPIC"
        assert "reasoning" in result
        assert result["confidence"] == 1.0
    
    def test_get_router_tools(self):
        """Test router tools registry."""
        tools = get_router_tools()
        
        assert len(tools) == len(ROUTER_TOOLS)
        assert len(tools) == 4
        assert route_to_sql_agent_tool in tools
        assert route_to_csv_export_tool in tools
        assert route_to_sql_retrieval_tool in tools
        assert route_to_off_topic_tool in tools


class TestRouterAgent:
    """Tests for Router Agent."""
    
    def test_router_agent_initialization(self):
        """Test Router Agent initialization."""
        agent = RouterAgent()
        
        assert agent is not None
        assert len(agent.router_tools) == 4
    
    def test_classify_intent_sql_query(self):
        """Test intent classification for SQL queries."""
        agent = RouterAgent()
        
        result = agent.classify_intent(
            user_message="How many iOS apps are there?",
            thread_ts="1234567890.123456"
        )
        
        assert result["intent"] == "SQL_QUERY"
        assert "reasoning" in result
        assert "confidence" in result
        assert "metadata" in result
        assert result["metadata"]["routing_decision"] == "SQL_QUERY"
    
    def test_classify_intent_csv_export(self):
        """Test intent classification for CSV export."""
        agent = RouterAgent()
        
        result = agent.classify_intent(
            user_message="Export the results to CSV",
            thread_ts="1234567890.123456"
        )
        
        assert result["intent"] == "CSV_EXPORT"
        assert result["metadata"]["routing_decision"] == "CSV_EXPORT"
    
    def test_classify_intent_sql_retrieval(self):
        """Test intent classification for SQL retrieval."""
        agent = RouterAgent()
        
        result = agent.classify_intent(
            user_message="Show me the SQL query that was used",
            thread_ts="1234567890.123456"
        )
        
        assert result["intent"] == "SQL_RETRIEVAL"
        assert result["metadata"]["routing_decision"] == "SQL_RETRIEVAL"
    
    def test_classify_intent_off_topic(self):
        """Test intent classification for off-topic questions."""
        agent = RouterAgent()
        
        result = agent.classify_intent(
            user_message="Hello, how are you today?",
            thread_ts="1234567890.123456"
        )
        
        assert result["intent"] == "OFF_TOPIC"
        assert result["metadata"]["routing_decision"] == "OFF_TOPIC"
    
    def test_classify_intent_with_conversation_history(self):
        """Test intent classification with conversation context."""
        agent = RouterAgent()
        
        conversation_history = [
            HumanMessage(content="How many apps are there?"),
            AIMessage(content="There are 50 apps in the database.")
        ]
        
        result = agent.classify_intent(
            user_message="What about iOS apps?",
            thread_ts="1234567890.123456",
            conversation_history=conversation_history
        )
        
        assert result["intent"] == "SQL_QUERY"
        assert result["metadata"]["has_context"] is True
    
    def test_classify_intent_follow_up_csv(self):
        """Test intent classification for follow-up CSV export."""
        agent = RouterAgent()
        
        conversation_history = [
            HumanMessage(content="Show me top 5 apps"),
            AIMessage(content="Here are the top 5 apps...")
        ]
        
        result = agent.classify_intent(
            user_message="Export this to CSV",
            thread_ts="1234567890.123456",
            conversation_history=conversation_history
        )
        
        assert result["intent"] == "CSV_EXPORT"
    
    def test_route_method(self):
        """Test route convenience method."""
        agent = RouterAgent()
        
        intent = agent.route(
            user_message="How many apps are there?",
            thread_ts="1234567890.123456"
        )
        
        assert intent in ["SQL_QUERY", "CSV_EXPORT", "SQL_RETRIEVAL", "OFF_TOPIC"]
        assert intent == "SQL_QUERY"
    
    def test_classify_intent_error_handling(self):
        """Test error handling in intent classification."""
        agent = RouterAgent()
        
        # Test with invalid thread_ts (should still work, defaults to SQL_QUERY)
        result = agent.classify_intent(
            user_message="Test message",
            thread_ts="invalid_thread"
        )
        
        assert result["intent"] in ["SQL_QUERY", "CSV_EXPORT", "SQL_RETRIEVAL", "OFF_TOPIC"]
        assert "reasoning" in result
        assert "confidence" in result


class TestRouterAgentIntegration:
    """Integration tests for Router Agent."""
    
    def test_get_router_agent_singleton(self):
        """Test that get_router_agent returns singleton instance."""
        agent1 = get_router_agent()
        agent2 = get_router_agent()
        
        assert agent1 is agent2
    
    def test_intent_classification_variations(self):
        """Test various message variations for intent classification."""
        agent = RouterAgent()
        
        test_cases = [
            ("How many apps?", "SQL_QUERY"),
            ("What's the total revenue?", "SQL_QUERY"),
            ("Show me apps by country", "SQL_QUERY"),
            ("Export to CSV", "CSV_EXPORT"),
            ("Download the results", "CSV_EXPORT"),
            ("Save as CSV file", "CSV_EXPORT"),
            ("Show me the SQL", "SQL_RETRIEVAL"),
            ("What SQL was used?", "SQL_RETRIEVAL"),
            ("Display the query", "SQL_RETRIEVAL"),
            ("Hello", "OFF_TOPIC"),
            ("What can you do?", "OFF_TOPIC"),
        ]
        
        for message, expected_intent in test_cases:
            result = agent.classify_intent(
                user_message=message,
                thread_ts="1234567890.123456"
            )
            assert result["intent"] == expected_intent, f"Failed for: {message}"
    
    def test_confidence_scores(self):
        """Test that confidence scores are reasonable."""
        agent = RouterAgent()
        
        result = agent.classify_intent(
            user_message="How many apps are there?",
            thread_ts="1234567890.123456"
        )
        
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["confidence"] > 0.5  # Should have reasonable confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

