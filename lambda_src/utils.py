import json
import logging
import boto3
import os
from typing import Dict
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_secrets() -> Dict[str, str]:
    """Fetch secrets from AWS Secrets Manager for Lambda, or .env for local execution."""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Running in AWS Lambda - fetch from Secrets Manager
        try:
            secrets_client = boto3.client("secretsmanager", region_name="us-west-2")
            response = secrets_client.get_secret_value(SecretId="GenAI_Telegram_Secrets")
            secrets = json.loads(response["SecretString"])
            return secrets  # Fetch only when needed (not stored as environment variables)
        except Exception as e:
            logger.critical(f"Failed to retrieve secrets from AWS Secrets Manager: {e}")
            raise
    else:
        # Running locally - load from .env
        logger.info("Loading secrets from .env file for local execution.")
        load_dotenv()  # Load .env variables

        secrets = {
            "TELEGRAM_API_ID": os.getenv("TELEGRAM_API_ID"),
            "TELEGRAM_API_HASH": os.getenv("TELEGRAM_API_HASH"),
            "TELEGRAM_SESSION": os.getenv("TELEGRAM_SESSION"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        }

        # Ensure all secrets are present
        missing_keys = [key for key, value in secrets.items() if value is None]
        if missing_keys:
            raise Exception(f"Missing keys in .env file: {', '.join(missing_keys)}")

        return secrets


def load_config(config_path: str) -> Dict:
    """Load the JSON configuration file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


async def initialize_telegram_client(secrets: Dict[str, str]) -> TelegramClient:
    """Initialize and connect to the Telegram client securely."""
    try:
        client = TelegramClient(
            StringSession(secrets["TELEGRAM_SESSION"]),
            int(secrets["TELEGRAM_API_ID"]),
            secrets["TELEGRAM_API_HASH"]
        )

        await client.connect()

        if not await client.is_user_authorized():
            raise Exception("Telegram session is not authorized. Please generate a new session string.")

        return client
    except Exception as e:
        logger.error(f"Failed to initialize Telegram client: {e}")
        raise
