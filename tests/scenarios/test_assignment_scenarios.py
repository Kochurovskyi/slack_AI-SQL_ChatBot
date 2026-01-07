"""Comprehensive sanity check for assignment query scenarios with ReAct step tracing.

This test file validates the multi-agent system against the assignment requirements
and traces all ReAct agent steps (Reasoning, Acting, Observation) for each query.
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Dict, List, Any, Optional
from pprint import pprint
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(dotenv_path=project_root / ".env", override=False)

from ai.agents.router_agent import get_router_agent
from ai.agents.sql_query_agent import get_sql_query_agent
from ai.agents.csv_export_agent import get_csv_export_agent
from ai.agents.sql_retrieval_agent import get_sql_retrieval_agent
from ai.agents.off_topic_handler import get_off_topic_handler
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, BaseMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "scenarios": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    },
    "react_traces": {}  # Store ReAct step traces for each scenario
}


class AssignmentScenarioTester:
    """Test assignment scenarios with multi-agent system and ReAct step tracing."""
    
    def __init__(self, trace_react_steps: bool = True, use_real_agents: bool = False):
        self.router = None
        self.sql_agent = None
        self.csv_agent = None
        self.sql_retrieval_agent = None
        self.off_topic_handler = None
        self.conversation_history = {}  # thread_ts -> list of messages
        self.trace_react_steps = trace_react_steps  # Enable/disable ReAct tracing
        self.use_real_agents = use_real_agents  # Use real agents instead of mocks
        
    def setup_agents(self):
        """Initialize all agents with optional ReAct tracing support."""
        try:
            # Always initialize router (it doesn't need LLM for basic tests)
            try:
                self.router = get_router_agent()
                logger.info("Router agent initialized")
            except Exception as e:
                logger.warning(f"Router agent initialization failed: {e}")
                self.router = None
            
            # For ReAct agents, try to initialize real agents if tracing is enabled OR use_real_agents is True
            # Otherwise, use mocks for faster execution
            if self.trace_react_steps or self.use_real_agents:
                # Try to initialize real agents for actual ReAct tracing
                try:
                    self.sql_agent = get_sql_query_agent()
                    logger.info("SQL Query agent initialized (real agent)")
                except Exception as e:
                    if self.use_real_agents:
                        logger.error(f"SQL Query agent initialization failed (real agents required): {e}")
                        raise
                    logger.warning(f"SQL Query agent initialization failed: {e}")
                    # Create mock agent for testing (only if not requiring real agents)
                    with patch('ai.agents.sql_query_agent._get_llm_model') as mock_llm, \
                         patch('ai.agents.sql_query_agent.create_agent') as mock_create:
                        mock_llm.return_value = Mock()
                        mock_create.return_value = Mock()
                        self.sql_agent = get_sql_query_agent()
                
                try:
                    self.csv_agent = get_csv_export_agent()
                    logger.info("CSV Export agent initialized (real agent)")
                except Exception as e:
                    if self.use_real_agents:
                        logger.error(f"CSV Export agent initialization failed (real agents required): {e}")
                        raise
                    logger.warning(f"CSV Export agent initialization failed: {e}")
                    with patch('ai.agents.csv_export_agent._get_llm_model') as mock_llm, \
                         patch('ai.agents.csv_export_agent.create_agent') as mock_create:
                        mock_llm.return_value = Mock()
                        mock_create.return_value = Mock()
                        self.csv_agent = get_csv_export_agent()
                
                try:
                    self.sql_retrieval_agent = get_sql_retrieval_agent()
                    logger.info("SQL Retrieval agent initialized (real agent)")
                except Exception as e:
                    if self.use_real_agents:
                        logger.error(f"SQL Retrieval agent initialization failed (real agents required): {e}")
                        raise
                    logger.warning(f"SQL Retrieval agent initialization failed: {e}")
                    with patch('ai.agents.sql_retrieval_agent._get_llm_model') as mock_llm, \
                         patch('ai.agents.sql_retrieval_agent.create_agent') as mock_create:
                        mock_llm.return_value = Mock()
                        mock_create.return_value = Mock()
                        self.sql_retrieval_agent = get_sql_retrieval_agent()
                
                try:
                    self.off_topic_handler = get_off_topic_handler()
                    logger.info("Off-Topic Handler initialized (real agent)")
                except Exception as e:
                    if self.use_real_agents:
                        logger.error(f"Off-Topic Handler initialization failed (real agents required): {e}")
                        raise
                    logger.warning(f"Off-Topic Handler initialization failed: {e}")
                    with patch('ai.agents.off_topic_handler._get_llm_model') as mock_llm, \
                         patch('ai.agents.off_topic_handler.create_agent') as mock_create:
                        mock_llm.return_value = Mock()
                        mock_create.return_value = Mock()
                        self.off_topic_handler = get_off_topic_handler()
            else:
                # Tracing disabled - use mocks for faster execution
                with patch('ai.agents.sql_query_agent._get_llm_model') as mock_sql_llm, \
                     patch('ai.agents.csv_export_agent._get_llm_model') as mock_csv_llm, \
                     patch('ai.agents.sql_retrieval_agent._get_llm_model') as mock_retrieval_llm, \
                     patch('ai.agents.off_topic_handler._get_llm_model') as mock_off_topic_llm, \
                     patch('ai.agents.sql_query_agent.create_agent') as mock_sql_create, \
                     patch('ai.agents.csv_export_agent.create_agent') as mock_csv_create, \
                     patch('ai.agents.sql_retrieval_agent.create_agent') as mock_retrieval_create, \
                     patch('ai.agents.off_topic_handler.create_agent') as mock_off_topic_create:
                    
                    mock_llm = Mock()
                    mock_agent = Mock()
                    mock_sql_llm.return_value = mock_llm
                    mock_csv_llm.return_value = mock_llm
                    mock_retrieval_llm.return_value = mock_llm
                    mock_off_topic_llm.return_value = mock_llm
                    mock_sql_create.return_value = mock_agent
                    mock_csv_create.return_value = mock_agent
                    mock_retrieval_create.return_value = mock_agent
                    mock_off_topic_create.return_value = mock_agent
                    
                    self.sql_agent = get_sql_query_agent()
                    self.csv_agent = get_csv_export_agent()
                    self.sql_retrieval_agent = get_sql_retrieval_agent()
                    self.off_topic_handler = get_off_topic_handler()
            
            logger.info("All agents initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}", exc_info=True)
            return False
    
    def _capture_react_steps(self, agent, input_data: Dict, agent_type: str) -> List[Dict[str, Any]]:
        """Trace all ReAct agent steps (Reasoning, Action, Observation).
        
        Args:
            agent: The agent instance to trace
            input_data: Input data for the agent
            agent_type: Type of agent (sql_query, csv_export, sql_retrieval, off_topic)
        
        Returns:
            List of ReAct steps with Reasoning, Action, and Observation
        """
        react_steps = []
        step_num = 0
        
        # Check if agent has the necessary attributes for tracing
        if agent is None:
            logger.warning(f"Agent is None, cannot trace ReAct steps for {agent_type}")
            return react_steps
        
        if not hasattr(agent, 'agent'):
            logger.warning(f"Agent {agent_type} does not have 'agent' attribute (may be mocked)")
            return react_steps
        
        agent_instance = agent.agent
        
        # Check if agent has stream method
        if not hasattr(agent_instance, 'stream'):
            logger.warning(f"Agent {agent_type} does not have 'stream' method (may be mocked)")
            return react_steps
        
        try:
            logger.info(f"[TRACE] Starting ReAct tracing for {agent_type} agent")
            # Use stream_mode="updates" to capture all intermediate steps
            # This captures state updates at each step of the ReAct loop
            for chunk in agent_instance.stream(input_data, stream_mode="updates"):
                step_num += 1
                step = {
                    "step": step_num,
                    "agent_type": agent_type,
                    "loop_iteration": step_num
                }
                
                # Log chunk structure for debugging
                logger.debug(f"[TRACE] Step {step_num}: chunk type = {type(chunk)}, chunk keys = {list(chunk.keys()) if isinstance(chunk, dict) else 'N/A'}")
                
                # Extract messages from chunk - LangGraph returns state updates
                messages = []
                if isinstance(chunk, dict):
                    # Try different possible keys
                    if "messages" in chunk:
                        messages = chunk["messages"]
                    elif "state" in chunk and isinstance(chunk["state"], dict) and "messages" in chunk["state"]:
                        messages = chunk["state"]["messages"]
                    else:
                        # Check if chunk itself is a list of messages
                        if isinstance(chunk, list):
                            messages = chunk
                        else:
                            # Try to find any list in the chunk
                            for key, value in chunk.items():
                                if isinstance(value, list) and len(value) > 0:
                                    # Check if it looks like messages
                                    if hasattr(value[0], 'content') or isinstance(value[0], dict):
                                        messages = value
                                        break
                
                logger.debug(f"[TRACE] Step {step_num}: found {len(messages)} messages")
                
                # If still no messages, log the full chunk for debugging
                if not messages:
                    logger.debug(f"[TRACE] Step {step_num}: No messages found, chunk = {str(chunk)[:500]}")
                
                for msg in messages:
                    # Reasoning: AIMessage content (agent thinking/reasoning)
                    if isinstance(msg, AIMessage) and msg.content:
                        reasoning_text = msg.content
                        # Truncate very long reasoning
                        if len(reasoning_text) > 1000:
                            reasoning_text = reasoning_text[:1000] + "..."
                        
                        if "Reasoning" not in step:
                            step["Reasoning"] = reasoning_text
                        else:
                            step["Reasoning"] += "\n" + reasoning_text
                        logger.debug(f"[TRACE] Step {step_num}: Captured Reasoning ({len(reasoning_text)} chars)")
                    
                    # Action: Tool calls (agent decides to use a tool)
                    if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                        if "Action" not in step:
                            step["Action"] = []
                        for tool_call in msg.tool_calls:
                            action_info = {
                                "tool": tool_call.get("name", "unknown"),
                                "args": tool_call.get("args", {}),
                                "id": tool_call.get("id", "")
                            }
                            # Truncate long args for readability
                            if isinstance(action_info["args"], dict):
                                truncated_args = {}
                                for key, value in action_info["args"].items():
                                    if isinstance(value, str) and len(value) > 200:
                                        truncated_args[key] = value[:200] + "..."
                                    else:
                                        truncated_args[key] = value
                                action_info["args"] = truncated_args
                            step["Action"].append(action_info)
                        logger.debug(f"[TRACE] Step {step_num}: Captured Action - {len(msg.tool_calls)} tool calls")
                    
                    # Observation: Tool results (tool execution result)
                    if isinstance(msg, ToolMessage):
                        if "Observation" not in step:
                            step["Observation"] = []
                        obs_content = msg.content
                        # Truncate very long observations
                        if isinstance(obs_content, str) and len(obs_content) > 500:
                            obs_content = obs_content[:500] + "..."
                        step["Observation"].append({
                            "tool_call_id": msg.tool_call_id,
                            "content": obs_content
                        })
                        logger.debug(f"[TRACE] Step {step_num}: Captured Observation from tool_call_id={msg.tool_call_id}")
                
                # Always add step if it has any content (even if minimal)
                if len(step) > 3:  # step, agent_type, loop_iteration + at least one of Reasoning/Action/Observation
                    react_steps.append(step)
                elif step_num == 1:
                    # Always add first step even if empty (to show tracing started)
                    step["note"] = "Tracing started but no content captured yet"
                    react_steps.append(step)
            
            logger.info(f"[TRACE] Completed ReAct tracing for {agent_type}: {len(react_steps)} steps captured")
            
            if len(react_steps) == 0:
                logger.warning(f"[TRACE] No ReAct steps captured for {agent_type} - check stream_mode and agent configuration")
        
        except AttributeError as e:
            # Agent is likely mocked and doesn't support streaming
            logger.warning(f"Agent {agent_type} does not support streaming (likely mocked): {e}")
            react_steps.append({
                "step": 1,
                "agent_type": agent_type,
                "note": "Agent is mocked - ReAct steps not available",
                "error": "Mocked agent does not support stream()"
            })
        except Exception as e:
            logger.error(f"Error tracing ReAct steps for {agent_type}: {e}", exc_info=True)
            react_steps.append({
                "step": step_num + 1,
                "agent_type": agent_type,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
            })
        
        return react_steps
    
    def print_react_trace(self, react_steps: List[Dict], scenario_id: str, agent_type: str):
        """Pretty print ReAct trace using pprint.
        
        Args:
            react_steps: List of ReAct steps
            scenario_id: Scenario identifier
            agent_type: Type of agent
        """
        if not react_steps:
            return
        
        print("\n" + "="*80)
        print(f"REACT TRACE: {scenario_id} - {agent_type.upper()} AGENT")
        print("="*80)
        print(f"Total Steps: {len(react_steps)}\n")
        
        for step in react_steps:
            print(f"\n--- Step {step.get('step', '?')} ---")
            pprint(step, width=120, depth=10, sort_dicts=False)
        
        print("\n" + "="*80 + "\n")
    
    def test_scenario(self, scenario_id: str, user_message: str, 
                     expected_intent: str, thread_ts: str = None) -> Dict[str, Any]:
        """Test a single scenario with ReAct step tracing."""
        if thread_ts is None:
            thread_ts = f"test_{scenario_id}_{datetime.now().timestamp()}"
        
        result = {
            "scenario_id": scenario_id,
            "user_message": user_message,
            "expected_intent": expected_intent,
            "thread_ts": thread_ts,
            "actual_intent": None,
            "response": None,
            "passed": False,
            "error": None,
            "react_trace": []  # Store ReAct steps
        }
        
        try:
            # Step 1: Route intent
            router_result = self.router.classify_intent(
                user_message=user_message,
                thread_ts=thread_ts
            )
            
            actual_intent = router_result["intent"]
            result["actual_intent"] = actual_intent
            result["routing_confidence"] = router_result.get("confidence", 0)
            
            # Step 2: Execute based on intent with ReAct tracing
            if actual_intent == "SQL_QUERY":
                # Use real agent if available, otherwise mock
                if self.use_real_agents and self.sql_agent and hasattr(self.sql_agent, 'query'):
                    try:
                        # If tracing enabled, capture steps during actual execution
                        if self.trace_react_steps and hasattr(self.sql_agent, 'agent'):
                            from ai.memory_store import memory_store
                            conversation_history = memory_store.get_messages(thread_ts)
                            
                            # Build user message for tracing (same as agent.query would use)
                            user_msg = user_message
                            if conversation_history:
                                context_parts = []
                                for msg in conversation_history[-3:]:
                                    if hasattr(msg, 'content'):
                                        role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                                        context_parts.append(f"{role}: {msg.content}")
                                if context_parts:
                                    context = "\n".join(context_parts)
                                    user_msg = f"""Question: {user_message}

Previous conversation:
{context}

Please answer the question using the available tools."""
                            
                            input_data = {"messages": [HumanMessage(content=user_msg)]}
                            react_steps = self._capture_react_steps(self.sql_agent, input_data, "sql_query")
                            result["react_trace"] = react_steps
                            
                            # Always print trace (even if empty) for visibility
                            self.print_react_trace(react_steps, scenario_id, "sql_query")
                            if react_steps:
                                test_results["react_traces"][scenario_id] = react_steps
                        
                        # Execute actual query
                        query_result = self.sql_agent.query(
                            question=user_message,
                            thread_ts=thread_ts
                        )
                        result["response"] = query_result.get("formatted_response", "")
                        result["sql_query"] = query_result.get("sql_query")
                        result["metadata"] = query_result.get("metadata", {})
                    except Exception as e:
                        logger.error(f"Real SQL agent query failed: {e}", exc_info=True)
                        result["error"] = str(e)
                        result["response"] = f"Error: {str(e)}"
                else:
                    # Mock SQL query agent
                    with patch.object(self.sql_agent, 'query') as mock_query:
                        mock_query.return_value = {
                            "formatted_response": f"Mock response for: {user_message}",
                            "sql_query": "SELECT COUNT(*) FROM app_portfolio",
                            "metadata": {"query_executed": True}
                        }
                        query_result = self.sql_agent.query(
                            question=user_message,
                            thread_ts=thread_ts
                        )
                        result["response"] = query_result["formatted_response"]
                        result["sql_query"] = query_result.get("sql_query")
                    
            elif actual_intent == "CSV_EXPORT":
                # Use real agent if available, otherwise mock
                if self.use_real_agents and self.csv_agent and hasattr(self.csv_agent, 'export'):
                    try:
                        # If tracing enabled, capture steps during actual execution
                        if self.trace_react_steps and hasattr(self.csv_agent, 'agent'):
                            user_msg = f"Export the previous query results to CSV for thread {thread_ts}"
                            input_data = {"messages": [HumanMessage(content=user_msg)]}
                            react_steps = self._capture_react_steps(self.csv_agent, input_data, "csv_export")
                            result["react_trace"] = react_steps
                            
                            # Always print trace (even if empty) for visibility
                            self.print_react_trace(react_steps, scenario_id, "csv_export")
                            if react_steps:
                                test_results["react_traces"][scenario_id] = react_steps
                        
                        # Execute actual export
                        export_result = self.csv_agent.export(thread_ts=thread_ts)
                        result["response"] = export_result.get("formatted_response", "")
                        result["csv_path"] = export_result.get("csv_file_path")
                        result["metadata"] = export_result.get("metadata", {})
                    except Exception as e:
                        logger.error(f"Real CSV agent export failed: {e}", exc_info=True)
                        result["error"] = str(e)
                        result["response"] = f"Error: {str(e)}"
                else:
                    # Mock CSV export agent
                    with patch.object(self.csv_agent, 'export') as mock_export:
                        mock_export.return_value = {
                            "csv_file_path": "/tmp/test_export.csv",
                            "formatted_response": "CSV file generated successfully",
                            "metadata": {"export_successful": True}
                        }
                        export_result = self.csv_agent.export(thread_ts=thread_ts)
                        result["response"] = export_result["formatted_response"]
                        result["csv_path"] = export_result.get("csv_file_path")
                    
            elif actual_intent == "SQL_RETRIEVAL":
                # Use real agent if available, otherwise mock
                if self.use_real_agents and self.sql_retrieval_agent and hasattr(self.sql_retrieval_agent, 'retrieve'):
                    try:
                        # If tracing enabled, capture steps during actual execution
                        if self.trace_react_steps and hasattr(self.sql_retrieval_agent, 'agent'):
                            user_msg = f"Show me the SQL query for thread {thread_ts}"
                            input_data = {"messages": [HumanMessage(content=user_msg)]}
                            react_steps = self._capture_react_steps(self.sql_retrieval_agent, input_data, "sql_retrieval")
                            result["react_trace"] = react_steps
                            
                            # Always print trace (even if empty) for visibility
                            self.print_react_trace(react_steps, scenario_id, "sql_retrieval")
                            if react_steps:
                                test_results["react_traces"][scenario_id] = react_steps
                        
                        # Execute actual retrieval
                        retrieve_result = self.sql_retrieval_agent.retrieve(thread_ts=thread_ts)
                        result["response"] = retrieve_result.get("formatted_response", "")
                        result["sql_statement"] = retrieve_result.get("sql_statement")
                        result["metadata"] = retrieve_result.get("metadata", {})
                    except Exception as e:
                        logger.error(f"Real SQL retrieval agent failed: {e}", exc_info=True)
                        result["error"] = str(e)
                        result["response"] = f"Error: {str(e)}"
                else:
                    # Mock SQL retrieval agent
                    with patch.object(self.sql_retrieval_agent, 'retrieve') as mock_retrieve:
                        mock_retrieve.return_value = {
                            "sql_statement": "SELECT COUNT(*) FROM app_portfolio",
                            "formatted_response": "```sql\nSELECT COUNT(*) FROM app_portfolio\n```",
                            "metadata": {"sql_found": True}
                        }
                        retrieve_result = self.sql_retrieval_agent.retrieve(thread_ts=thread_ts)
                        result["response"] = retrieve_result["formatted_response"]
                        result["sql_statement"] = retrieve_result.get("sql_statement")
                    
            elif actual_intent == "OFF_TOPIC":
                # Use real agent if available, otherwise use default response
                if self.use_real_agents and self.off_topic_handler and hasattr(self.off_topic_handler, 'handle'):
                    try:
                        # If tracing enabled, capture steps during actual execution
                        if self.trace_react_steps and hasattr(self.off_topic_handler, 'agent'):
                            input_data = {"messages": [HumanMessage(content=user_message)]}
                            react_steps = self._capture_react_steps(self.off_topic_handler, input_data, "off_topic")
                            result["react_trace"] = react_steps
                            
                            # Always print trace (even if empty) for visibility
                            self.print_react_trace(react_steps, scenario_id, "off_topic")
                            if react_steps:
                                test_results["react_traces"][scenario_id] = react_steps
                        
                        # Execute actual handling
                        handle_result = self.off_topic_handler.handle(
                            user_message=user_message,
                            thread_ts=thread_ts
                        )
                        result["response"] = handle_result.get("formatted_response", "")
                        result["metadata"] = handle_result.get("metadata", {})
                    except Exception as e:
                        logger.error(f"Real off-topic handler failed: {e}", exc_info=True)
                        result["error"] = str(e)
                        result["response"] = "I'm focused on app portfolio analytics. How can I help you with data queries?"
                else:
                    result["response"] = "I'm focused on app portfolio analytics. How can I help you with data queries?"
            
            # Step 3: Validate
            result["passed"] = (actual_intent == expected_intent)
            
        except Exception as e:
            result["error"] = str(e)
            result["passed"] = False
            logger.error(f"Error in scenario {scenario_id}: {e}", exc_info=True)
        
        return result
    
    def test_follow_up_scenario(self, scenario_id: str, messages: List[Dict], 
                                thread_ts: str) -> Dict[str, Any]:
        """Test follow-up scenario with conversation history and ReAct tracing."""
        result = {
            "scenario_id": scenario_id,
            "messages": messages,
            "thread_ts": thread_ts,
            "responses": [],
            "passed": False,
            "error": None,
            "react_traces": {}  # Store ReAct traces for each message in the conversation
        }
        
        try:
            for i, msg in enumerate(messages):
                user_msg = msg["user_message"]
                expected_intent = msg.get("expected_intent", "SQL_QUERY")
                
                # Route intent
                router_result = self.router.classify_intent(
                    user_message=user_msg,
                    thread_ts=thread_ts
                )
                
                actual_intent = router_result["intent"]
                response = {
                    "message_index": i,
                    "user_message": user_msg,
                    "expected_intent": expected_intent,
                    "actual_intent": actual_intent,
                    "passed": (actual_intent == expected_intent),
                    "confidence": router_result.get("confidence", 0),
                    "react_trace": []  # Store ReAct steps for this message
                }
                
                # Trace ReAct steps for this message if enabled
                if self.trace_react_steps:
                    try:
                        if actual_intent == "SQL_QUERY" and hasattr(self.sql_agent, 'agent'):
                            from ai.memory_store import memory_store
                            conversation_history = memory_store.get_messages(thread_ts)
                            
                            user_message_for_agent = user_msg
                            if conversation_history:
                                context_parts = []
                                for hist_msg in conversation_history[-3:]:
                                    if hasattr(hist_msg, 'content'):
                                        role = "User" if hist_msg.__class__.__name__ == "HumanMessage" else "Assistant"
                                        context_parts.append(f"{role}: {hist_msg.content}")
                                if context_parts:
                                    context = "\n".join(context_parts)
                                    user_message_for_agent = f"""Question: {user_msg}

Previous conversation:
{context}

Please answer the question using the available tools."""
                            
                            input_data = {"messages": [HumanMessage(content=user_message_for_agent)]}
                            react_steps = self._capture_react_steps(self.sql_agent, input_data, "sql_query")
                            response["react_trace"] = react_steps
                            
                            if react_steps:
                                trace_key = f"{scenario_id}_msg_{i}"
                                result["react_traces"][trace_key] = react_steps
                                self.print_react_trace(react_steps, f"{scenario_id}_msg_{i}", "sql_query")
                        
                        elif actual_intent == "CSV_EXPORT" and hasattr(self.csv_agent, 'agent'):
                            user_msg_for_agent = f"Export the previous query results to CSV for thread {thread_ts}"
                            input_data = {"messages": [HumanMessage(content=user_msg_for_agent)]}
                            react_steps = self._capture_react_steps(self.csv_agent, input_data, "csv_export")
                            response["react_trace"] = react_steps
                            
                            if react_steps:
                                trace_key = f"{scenario_id}_msg_{i}"
                                result["react_traces"][trace_key] = react_steps
                                self.print_react_trace(react_steps, f"{scenario_id}_msg_{i}", "csv_export")
                        
                        elif actual_intent == "SQL_RETRIEVAL" and hasattr(self.sql_retrieval_agent, 'agent'):
                            user_msg_for_agent = f"Show me the SQL query for thread {thread_ts}"
                            input_data = {"messages": [HumanMessage(content=user_msg_for_agent)]}
                            react_steps = self._capture_react_steps(self.sql_retrieval_agent, input_data, "sql_retrieval")
                            response["react_trace"] = react_steps
                            
                            if react_steps:
                                trace_key = f"{scenario_id}_msg_{i}"
                                result["react_traces"][trace_key] = react_steps
                                self.print_react_trace(react_steps, f"{scenario_id}_msg_{i}", "sql_retrieval")
                    except Exception as e:
                        logger.warning(f"Failed to trace ReAct steps for message {i}: {e}")
                
                # Execute with real agents if enabled
                if self.use_real_agents:
                    try:
                        if actual_intent == "SQL_QUERY" and self.sql_agent and hasattr(self.sql_agent, 'query'):
                            query_result = self.sql_agent.query(
                                question=user_msg,
                                thread_ts=thread_ts
                            )
                            response["agent_response"] = query_result.get("formatted_response", "")
                            response["sql_query"] = query_result.get("sql_query")
                        elif actual_intent == "CSV_EXPORT" and self.csv_agent and hasattr(self.csv_agent, 'export'):
                            export_result = self.csv_agent.export(thread_ts=thread_ts)
                            response["agent_response"] = export_result.get("formatted_response", "")
                            response["csv_path"] = export_result.get("csv_file_path")
                        elif actual_intent == "SQL_RETRIEVAL" and self.sql_retrieval_agent and hasattr(self.sql_retrieval_agent, 'retrieve'):
                            retrieve_result = self.sql_retrieval_agent.retrieve(thread_ts=thread_ts)
                            response["agent_response"] = retrieve_result.get("formatted_response", "")
                            response["sql_statement"] = retrieve_result.get("sql_statement")
                        elif actual_intent == "OFF_TOPIC" and self.off_topic_handler and hasattr(self.off_topic_handler, 'handle'):
                            handle_result = self.off_topic_handler.handle(
                                user_message=user_msg,
                                thread_ts=thread_ts
                            )
                            response["agent_response"] = handle_result.get("formatted_response", "")
                    except Exception as e:
                        logger.error(f"Real agent execution failed for message {i}: {e}", exc_info=True)
                        response["agent_error"] = str(e)
                
                result["responses"].append(response)
            
            # Overall pass if all individual responses passed
            result["passed"] = all(r["passed"] for r in result["responses"])
            
        except Exception as e:
            result["error"] = str(e)
            result["passed"] = False
        
        return result
    
    def run_all_scenarios(self):
        """Run all assignment scenarios."""
        scenarios = [
            # Simple questions
            ("Q1.1", "how many apps do we have?", "SQL_QUERY"),
            ("Q1.2", "how many android apps do we have?", "SQL_QUERY"),
            
            # CSV Export
            ("Q3.1", "export this as csv", "CSV_EXPORT"),
            ("Q3.2", "export to csv", "CSV_EXPORT"),
            ("Q3.3", "Export all apps to CSV", "CSV_EXPORT"),
            
            # SQL Retrieval
            ("Q4.1", "show me the SQL you used to retrieve all the apps", "SQL_RETRIEVAL"),
            ("Q4.2", "what SQL did you use?", "SQL_RETRIEVAL"),
            ("Q4.3", "show me the SQL", "SQL_RETRIEVAL"),
            
            # Off-topic
            ("Q6.1", "Hello, how are you?", "OFF_TOPIC"),
            ("Q6.2", "What's the weather today?", "OFF_TOPIC"),
            ("Q6.3", "Tell me a joke", "OFF_TOPIC"),
        ]
        
        # Test simple scenarios
        for scenario_id, user_message, expected_intent in scenarios:
            test_results["summary"]["total"] += 1
            result = self.test_scenario(scenario_id, user_message, expected_intent)
            test_results["scenarios"].append(result)
            
            if result["passed"]:
                test_results["summary"]["passed"] += 1
                logger.info(f"[OK] {scenario_id}: PASSED")
            else:
                test_results["summary"]["failed"] += 1
                logger.error(f"[FAIL] {scenario_id}: FAILED - Expected {expected_intent}, got {result['actual_intent']}")
        
        # Test follow-up scenarios
        follow_up_scenarios = [
            ("Q1.3", "test_thread_001", [
                {"user_message": "how many android apps do we have?", "expected_intent": "SQL_QUERY"},
                {"user_message": "what about ios?", "expected_intent": "SQL_QUERY"}
            ]),
            ("Q8.1", "test_thread_002", [
                {"user_message": "which country generates the most revenue?", "expected_intent": "SQL_QUERY"},
                {"user_message": "export this as csv", "expected_intent": "CSV_EXPORT"},
                {"user_message": "show me the SQL", "expected_intent": "SQL_RETRIEVAL"}
            ]),
        ]
        
        for scenario_id, thread_ts, messages in follow_up_scenarios:
            test_results["summary"]["total"] += 1
            result = self.test_follow_up_scenario(scenario_id, messages, thread_ts)
            test_results["scenarios"].append(result)
            
            if result["passed"]:
                test_results["summary"]["passed"] += 1
                logger.info(f"[OK] {scenario_id}: PASSED")
            else:
                test_results["summary"]["failed"] += 1
                logger.error(f"[FAIL] {scenario_id}: FAILED")


def main():
    """Run assignment scenario tests with ReAct step tracing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test assignment scenarios with ReAct tracing')
    parser.add_argument('--no-trace', action='store_true', 
                       help='Disable ReAct step tracing (faster execution)')
    parser.add_argument('--trace-only', action='store_true',
                       help='Only show ReAct traces, skip test validation')
    parser.add_argument('--real-agents', action='store_true',
                       help='Use real agents instead of mocks (requires API keys)')
    args = parser.parse_args()
    
    trace_enabled = not args.no_trace
    use_real_agents = args.real_agents
    
    print("\n" + "="*80)
    print("ASSIGNMENT SCENARIO TESTING")
    if trace_enabled:
        print("WITH REACT STEP TRACING")
    if use_real_agents:
        print("WITH REAL AGENTS (requires API keys)")
    print("="*80 + "\n")
    
    tester = AssignmentScenarioTester(trace_react_steps=trace_enabled, use_real_agents=use_real_agents)
    
    if not tester.setup_agents():
        print("[FAIL] Failed to initialize agents")
        sys.exit(1)
    
    tester.run_all_scenarios()
    
    # Save results
    results_file = project_root / "tests" / "scenarios" / "assignment_test_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    summary = test_results["summary"]
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total scenarios: {summary['total']}")
    print(f"[OK] Passed: {summary['passed']}")
    print(f"[FAIL] Failed: {summary['failed']}")
    print(f"[SKIP] Skipped: {summary['skipped']}")
    print(f"Success rate: {(summary['passed']/summary['total']*100):.1f}%" if summary['total'] > 0 else "N/A")
    
    # Print ReAct trace summary
    if trace_enabled and test_results.get("react_traces"):
        trace_count = len(test_results["react_traces"])
        print(f"\nReAct Traces Captured: {trace_count}")
        print("ReAct steps saved in test_results['react_traces']")
    
    print("="*80 + "\n")
    
    print(f"Results saved to: {results_file}")
    
    return 0 if summary['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

