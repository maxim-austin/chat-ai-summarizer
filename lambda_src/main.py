import json
import os
from telegram_processor import process_channel
from utils import load_config
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

def lambda_handler(event, context):
    """AWS Lambda handler function."""
    try:
        # Load config
        config = load_config("config.json")

        # Extract LLM configuration
        llm_model_name = config["LLM_MODEL_NAME"]
        llm_temperature = float(config["LLM_TEMPERATURE"])
        image_model_name = config["LLM_IMAGE_MODEL_NAME"]
        reader_timezone = config["READER_TIMEZONE"]

        # Initialize Telegram client
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        session_str = os.getenv("TELEGRAM_SESSION")
        client = TelegramClient(StringSession(session_str), api_id, api_hash)

        with client:
            # Now iterate over config["channels"]
            for channel_config in config["channels"]:
                process_channel(
                    client,
                    channel_config,
                    llm_model_name,
                    llm_temperature,
                    image_model_name,
                    reader_timezone
                )

        return {"statusCode": 200, "body": "Successfully processed all channels."}
    except Exception as e:
        return {"statusCode": 500, "body": f"Error: {str(e)}"}


# For local testing
if __name__ == "__main__":
    # Simulate an event for local testing
    fake_event = {}
    fake_context = {}
    response = lambda_handler(fake_event, fake_context)
    print(json.dumps(response, indent=4))
