import logging
import os

from dotenv import load_dotenv

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from listeners import register_listeners

# Load environment variables
load_dotenv(dotenv_path=".env", override=False)


class TruncatingFormatter(logging.Formatter):
    """Formatter that truncates log messages to 1000 characters."""
    MAX_LENGTH = 1000
    
    def format(self, record):
        # Get the formatted message
        msg = super().format(record)
        # Truncate if too long
        if len(msg) > self.MAX_LENGTH:
            msg = msg[:self.MAX_LENGTH] + "... (truncated)"
        return msg


# Initialization
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Apply truncating formatter to all handlers
for handler in logging.root.handlers:
    handler.setFormatter(TruncatingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    client=WebClient(
        base_url=os.environ.get("SLACK_API_URL", "https://slack.com/api"),
        token=os.environ.get("SLACK_BOT_TOKEN"),
    ),
)
# Register Listeners
register_listeners(app)

# Start Bolt app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
