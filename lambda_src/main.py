import json
import os
from telegram_processor import process_channel
from utils import load_config
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import boto3


def get_secrets():
    """
    Fetch secrets from AWS Systems Manager Parameter Store if running in Lambda.
    Otherwise, load from .env for local testing.
    """
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Running in AWS Lambda
        ssm = boto3.client("ssm", region_name="us-west-2")
        param_names = [
            "TELEGRAM_API_ID",
            "TELEGRAM_API_HASH",
            "TELEGRAM_SESSION",
            "OPENAI_API_KEY",
        ]
        secrets = {}
        for name in param_names:
            response = ssm.get_parameter(Name=name, WithDecryption=True)
            secrets[name] = response["Parameter"]["Value"]
        return secrets
    else:
        # Running locally
        load_dotenv()
        return {
            "TELEGRAM_API_ID": os.getenv("TELEGRAM_API_ID"),
            "TELEGRAM_API_HASH": os.getenv("TELEGRAM_API_HASH"),
            "TELEGRAM_SESSION": os.getenv("TELEGRAM_SESSION"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        }


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    try:
        # Load secrets
        secrets = get_secrets()

        # Set environment variables for other modules
        os.environ["TELEGRAM_API_ID"] = secrets["TELEGRAM_API_ID"]
        os.environ["TELEGRAM_API_HASH"] = secrets["TELEGRAM_API_HASH"]
        os.environ["TELEGRAM_SESSION"] = secrets["TELEGRAM_SESSION"]
        os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]

        # Load config
        config = load_config("config.json")

        # Extract LLM configuration
        llm_model_name = config["LLM_MODEL_NAME"]
        llm_temperature = float(config["LLM_TEMPERATURE"])
        image_model_name = config["LLM_IMAGE_MODEL_NAME"]
        reader_timezone = config["READER_TIMEZONE"]

        # Initialize Telegram client
        api_id = int(secrets["TELEGRAM_API_ID"])
        api_hash = secrets["TELEGRAM_API_HASH"]
        session_str = secrets["TELEGRAM_SESSION"]
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
