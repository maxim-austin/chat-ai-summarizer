import logging
import asyncio
from utils import get_secrets, load_config, initialize_telegram_client
from telegram_processor import process_channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def async_main(event: dict, context) -> dict:
    client = None
    system_channel_id = None

    try:
        secrets = get_secrets()
        config = load_config("config.json")

        system_channel_id = config.get("SYSTEM_CHANNEL_ID")
        if not isinstance(system_channel_id, int):
            raise ValueError("SYSTEM_CHANNEL_ID is missing or invalid in config.json")

        num_of_messages_limit = config.get("NUM_OF_MESSAGES_LIMIT", 300)
        llm_model_name = config.get("LLM_MODEL_NAME", "gpt-4o-mini")
        llm_temperature = float(config.get("LLM_TEMPERATURE", 0.0))
        llm_image_model_name = config.get("LLM_IMAGE_MODEL_NAME", "dall-e-3")
        reader_timezone = config.get("READER_TIMEZONE", "US/Central")

        client = await initialize_telegram_client(secrets)

        tasks = []
        for channel_config in config["channels"]:
            if channel_config.get("ENABLED", 1) == 0:
                logger.info(f"Skipping disabled channel: {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}")
                await client.send_message(system_channel_id,
                                          f"Skipping disabled channel: {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}")
            else:
                tasks.append(
                    process_channel(
                        client, channel_config, secrets, num_of_messages_limit,
                        llm_model_name, llm_temperature, reader_timezone, llm_image_model_name, system_channel_id
                    )
                )

        await asyncio.gather(*tasks)
        logger.info("All channels processed successfully.")
        return {"statusCode": 200, "body": "Successfully processed all channels."}

    except Exception as e:
        critical_error_msg = f"Critical error in Lambda execution: {e}"
        logger.critical(critical_error_msg)

        if client and isinstance(system_channel_id, int):
            try:
                await client.send_message(system_channel_id, critical_error_msg)
            except Exception as telegram_error:
                logger.critical(f"Failed to send error to SYSTEM_CHANNEL_ID: {telegram_error}")
        else:
            logger.critical("SYSTEM_CHANNEL_ID is missing; cannot send error to Telegram.")

        return {"statusCode": 500, "body": f"Error: {str(e)}"}


def lambda_handler(event, context):
    """AWS Lambda Entry Point (Non-Async)."""
    return asyncio.run(async_main(event, context))  # Runs async functions inside a sync function


if __name__ == "__main__":
    asyncio.run(async_main({}, {}))
