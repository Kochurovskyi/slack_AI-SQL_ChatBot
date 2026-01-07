import logging
import re
from logging import Logger

from slack_bolt import Say
from slack_sdk import WebClient

from ai.agents.orchestrator import get_orchestrator
from ai.memory_store import memory_store
from ..views.feedback_block import create_feedback_block

logger = logging.getLogger(__name__)


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    """
    Handles the event when the app is mentioned in a Slack conversation
    and generates an AI response.

    Args:
        client: Slack WebClient for making API calls
        event: Event payload containing mention details (channel, user, text, etc.)
        logger: Logger instance for error tracking
        say: Function to send messages to the thread from the app
    """
    try:
        channel_id = event.get("channel")
        team_id = event.get("team")
        text = event.get("text")
        # Get actual thread_ts for Slack API (None if top-level message)
        actual_thread_ts = event.get("thread_ts")
        # Use thread_ts if in a thread, otherwise use channel_id for top-level messages
        # This ensures all mentions in the same channel share memory
        memory_thread_id = actual_thread_ts or channel_id
        user_id = event.get("user")

        client.assistant_threads_setStatus(
            channel_id=channel_id,
            thread_ts=actual_thread_ts or event.get("ts"),
            status="thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        # Clean text - remove bot mention if present
        cleaned_text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
        
        # Add user message to memory (use memory_thread_id for consistent memory)
        memory_store.add_user_message(memory_thread_id, cleaned_text)
        
        # Debug logging
        logger.info(f"Memory Thread ID: {memory_thread_id}, Actual Thread TS: {actual_thread_ts}")
        
        # Initialize orchestrator
        orchestrator = get_orchestrator()
        
        # For streaming, use actual_thread_ts if in thread, otherwise use message ts to create new thread
        stream_thread_ts = actual_thread_ts or event.get("ts")
        
        # Create Slack streamer
        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=stream_thread_ts,
        )

        # Stream agent response through orchestrator
        full_response = ""
        for chunk in orchestrator.stream(
            user_message=cleaned_text,
            thread_ts=memory_thread_id
        ):
            if chunk:
                full_response += chunk
                streamer.append(markdown_text=chunk)
        
        # Check if CSV file was generated and upload it to Slack
        result = orchestrator.process_message(
            user_message=cleaned_text,
            thread_ts=memory_thread_id
        )
        
        if result.get("intent") == "CSV_EXPORT":
            # Get CSV file path from metadata
            metadata = result.get("metadata", {})
            csv_file_path = metadata.get("agent_metadata", {}).get("csv_file_path")
            
            if csv_file_path:
                upload_successful = False
                try:
                    from services.csv_service import CSVService
                    csv_service = CSVService()
                    csv_service.upload_to_slack(
                        csv_path=csv_file_path,
                        client=client,
                        channel=channel_id,
                        thread_ts=stream_thread_ts,
                        title="App Portfolio Export"
                    )
                    upload_successful = True
                    logger.info(f"Uploaded CSV file to Slack: {csv_file_path}")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to upload CSV to Slack: {e}", exc_info=True)
                    
                    # If missing scope, send a message with file path as fallback
                    if "missing_scope" in error_msg.lower() or "files:write" in error_msg.lower():
                        try:
                            # Send file path as message (user can download manually)
                            client.chat_postMessage(
                                channel=channel_id,
                                thread_ts=stream_thread_ts,
                                text=f"⚠️ CSV file generated but couldn't upload to Slack (missing `files:write` permission).\n\nFile location: `{csv_file_path}`\n\n**To fix:** Add `files:write` scope to your Slack app in https://api.slack.com/apps"
                            )
                        except Exception as msg_error:
                            logger.error(f"Failed to send fallback message: {msg_error}")
        
        # Note: Orchestrator already saves response to memory in stream() method

        feedback_block = create_feedback_block()
        streamer.stop(blocks=feedback_block)
    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        # Only log errors, don't show to users in Slack
        say("I'm having trouble processing that request. Please try again.")
