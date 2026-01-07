"""
Configuration settings for the Slack chatbot.
"""

# LLM Model Configuration
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.5

# Memory Configuration
MAX_MESSAGES_PER_THREAD = 10
MAX_CONVERSATION_TOKENS = 4000  # Maximum tokens before compression
COMPRESSION_TRIGGER_RATIO = 0.8  # Compress when 80% of max tokens used
KEEP_RECENT_MESSAGES = 5  # Keep last N messages in full detail during compression

