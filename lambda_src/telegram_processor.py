import logging
import aiohttp
from datetime import datetime, timedelta, timezone
from summarizer import summarize_messages, generate_image
from telethon import TelegramClient
from typing import Dict, List

logger = logging.getLogger(__name__)


async def process_channel(client: TelegramClient, channel_config: Dict, secrets: Dict[str, str],
                          num_of_messages_limit: int, llm_model_name: str, llm_temperature: float, reader_timezone: str,
                          llm_image_model_name: str, system_channel_id: int) -> None:
    try:
        source_channel_id = channel_config["SOURCE_CHANNEL_ID"]
        summary_channel_id = channel_config["SUMMARY_CHANNEL_ID"]
        generate_image_flag = channel_config.get("GENERATE_IMAGE", 0)
        summary_period_hours = channel_config.get("SUMMARY_PERIOD_HOURS", 24)

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=summary_period_hours)
        all_messages: List = []

        channel = await client.get_entity(source_channel_id)
        last_date = None
        total_messages_fetched = 0

        while True:
            batch = await client.get_messages(channel, limit=100, offset_date=last_date)
            if not batch:
                break

            for msg in batch:
                if msg.date >= start_date:
                    all_messages.append(msg)
                else:
                    break

                total_messages_fetched += 1
                if total_messages_fetched >= num_of_messages_limit:
                    break

            last_date = batch[-1].date if batch else None
            if last_date and last_date < start_date:
                break
            if total_messages_fetched >= num_of_messages_limit:
                break

        all_messages.reverse()

        if not all_messages:
            info_message = f"No new messages found for channel {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}"
            logger.info(info_message)
            await client.send_message(system_channel_id, info_message)
            return

        logger.info(f"Generating summary for channel: {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}")
        summary_text = summarize_messages(
            all_messages, start_date, end_date,
            llm_model_name, llm_temperature, reader_timezone,
            secrets["OPENAI_API_KEY"]
        )

        if not summary_text.strip():
            summary_text = "**[No meaningful messages were found to summarize]**"

        await client.send_message(summary_channel_id, summary_text)
        logger.info(f"Summary sent to channel: {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}")

        if generate_image_flag:
            logger.info(f"Generating image for channel: {channel_config.get('SOURCE_CHANNEL_NAME', 'Unknown')}")
            image_url = await generate_image(summary_text, llm_image_model_name, secrets["OPENAI_API_KEY"])

            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as image_data:
                    if image_data.status == 200:
                        image_path = "/tmp/summary_image.png"
                        with open(image_path, "wb") as f:
                            f.write(await image_data.read())
                        await client.send_file(summary_channel_id, image_path, caption="Illustration for the summary "
                                                                                       "above")
                        logger.info("Image sent successfully.")
    except Exception as e:
        logger.error(f"Error processing channel: {e}")