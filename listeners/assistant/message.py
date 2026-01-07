from logging import Logger
from typing import Dict, List

from slack_bolt import BoltContext, Say, SetStatus
from slack_sdk import WebClient

from ai.agents.orchestrator import get_orchestrator
from ai.memory_store import memory_store

from ..views.feedback_block import create_feedback_block


def message(
    client: WebClient,
    context: BoltContext,
    logger: Logger,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    """
    Handles when users send messages or select a prompt in an assistant thread and generate AI responses:

    Args:
        client: Slack WebClient for making API calls
        context: Bolt context containing channel and thread information
        logger: Logger instance for error tracking
        payload: Event payload with message details (channel, user, text, etc.)
        say: Function to send messages to the thread
        set_status: Function to update the assistant's status
    """
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id

        set_status(
            status="thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        # Get current user message
        current_user_message = payload.get("text", "")
        
        # Add user message to memory
        memory_store.add_user_message(thread_ts, current_user_message)
        
        # Initialize orchestrator
        orchestrator = get_orchestrator()
        
        # Create Slack streamer
        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
        )

        # Stream agent response through orchestrator
        full_response = ""
        for chunk in orchestrator.stream(
            user_message=current_user_message,
            thread_ts=thread_ts
        ):
            if chunk:
                full_response += chunk
                streamer.append(markdown_text=chunk)
        
        # Check if CSV file was generated and upload it to Slack
        result = orchestrator.process_message(
            user_message=current_user_message,
            thread_ts=thread_ts
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
                        thread_ts=thread_ts,
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
                                thread_ts=thread_ts,
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
